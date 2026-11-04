import os
import re
import json
import hashlib
from typing import List, Dict, Any, Optional

# =====================================================================
# Google OKF v0.2 / LangExtract Schema Definitions
# =====================================================================

class SourceGrounding:
    def __init__(self, start_char: int, end_char: int, snippet: str):
        self.start_char = start_char
        self.end_char = end_char
        self.snippet = snippet

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_char": self.start_char,
            "end_char": self.end_char,
            "snippet": self.snippet
        }

class LangExtractEngine:
    def __init__(self, cache_dir: str = ".extraction_cache", client=None, model: str = "qwen"):
        self.cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', cache_dir))
        os.makedirs(self.cache_dir, exist_ok=True)
        self.client = client
        self.model = model
        
        # Load authoritative LOINC & SNOMED CT terminology crosswalk
        crosswalk_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'okf_data', 'terminology_crosswalk.json'))
        self.crosswalk = {}
        if os.path.exists(crosswalk_file):
            try:
                with open(crosswalk_file, 'r', encoding='utf-8') as f:
                    self.crosswalk = json.load(f).get('crosswalk', {})
            except Exception:
                pass

    @staticmethod
    def find_grounded_spans(full_text: str, pattern: str) -> Optional[Dict[str, Any]]:
        """
        Locates the exact start_char and end_char offsets of a pattern or substring in full_text.
        """
        if not pattern or not full_text:
            return None
        
        # Exact literal match first
        idx = full_text.find(pattern)
        if idx != -1:
            return {
                "start_char": idx,
                "end_char": idx + len(pattern),
                "snippet": pattern
            }
        
        # Case-insensitive or regex match fallback
        try:
            m = re.search(re.escape(pattern), full_text, re.IGNORECASE)
            if m:
                return {
                    "start_char": m.start(),
                    "end_char": m.end(),
                    "snippet": full_text[m.start():m.end()]
                }
        except Exception:
            pass
        return None

    def extract_section_rules(self, section_number: str, section_title: str, full_text: str, 
                              known_indications: List[str] = None, known_labs: List[str] = None) -> Dict[str, Any]:
        """
        Extracts structured clinical rules, operators, numerical thresholds, prior authorizations,
        and stopping rules with precise character-level source grounding.
        """
        cache_key = hashlib.md5(f"{section_number}_{full_text}".encode('utf-8')).hexdigest()
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        # 1. Extract Prior Authorization (事前審查)
        prior_auth = False
        prior_auth_span = None
        pa_match = re.search(r'(?:須?經?健保署|健保|保險人)?(?:事前審查|事前核准|事前報備|專案申請|事前申請|申請事前審查)', full_text)
        if pa_match:
            prior_auth = True
            prior_auth_span = {
                "start_char": pa_match.start(),
                "end_char": pa_match.end(),
                "snippet": full_text[pa_match.start():pa_match.end()]
            }

        # 2. Extract Biomarker & Laboratory Constraints with Operators and Thresholds
        biomarker_patterns = [
            # Precision Oncology, Targeted Genetics & Tumor Markers
            (r'(alpha-?\s*fetoprotein|AFP|胎兒蛋白)\s*(?:\(AFP\))?\s*(?:值)?\s*([≧≥>≦≤<=＝=~至\-])\s*([0-9\.]+)\s*(ng/mL)?', 'AFP', 'ng/mL'),
            (r'(FGFR[1-4]?|纖維母細胞生長因子受體)\s*(?:基因)?\s*(融合|重排|突變|變異|陽性|fusion|rearrangement)', 'FGFR', ''),
            (r'(HER2|HER-2|第2型人類上皮細胞生長因子受體|ERBB2)\s*(?:為|呈|表現為)?\s*(陽性|過度表現|IHC\s*3\+|IHC\s*2\+|FISH\s*陽性|FISH\+|3\+|2\+)', 'HER2', ''),
            (r'(EGFR)\s*(?:基因)?\s*(突變|變異|陽性|Exon\s*19\s*(?:del|deletion)?|Exon\s*20|Exon\s*21|L858R|T790M)', 'EGFR', ''),
            (r'(ALK)\s*(?:基因)?\s*(陽性|融合|重排|translocation|positive)', 'ALK', ''),
            (r'(BRAF)\s*(?:基因)?\s*(V600E?|突變|變異|陽性)', 'BRAF', ''),
            (r'(All-RAS|RAS|K-RAS|KRAS|N-RAS|NRAS)\s*(?:基因)?\s*(原生型|wild-type|突變|變異|陽性|G12C)', 'RAS', ''),
            (r'(BRCA(?:[12]|1/2)?)\s*(?:基因)?\s*(?:致病性)?\s*(突變|變異|陽性|germline|somatic)', 'BRCA', ''),
            (r'(NTRK[1-3]?)\s*(?:基因)?\s*(融合|重排|陽性|fusion)', 'NTRK', ''),
            (r'(ROS-?1)\s*(?:基因)?\s*(融合|重排|陽性)', 'ROS1', ''),
            (r'(MET)\s*(?:基因)?\s*(?:exon\s*14|外顯子14)?\s*(跳躍突變|擴增|突變|變異)', 'MET', ''),
            (r'(RET)\s*(?:基因)?\s*(融合|重排|突變|變異|陽性|fusion)', 'RET', ''),
            (r'(BCR-ABL|費城染色體|Ph\+?)\s*(?:為|呈)?\s*(陽性|突變|變異|T315I|positive)', 'BCR-ABL', ''),
            (r'(JAK2)\s*(?:基因)?\s*(V617F|突變|變異|陽性)', 'JAK2', ''),
            (r'(FLT3)\s*(?:基因)?\s*(ITD|TKD|突變|變異|陽性)', 'FLT3', ''),
            (r'(MSI-H|dMMR|微衛星不穩定高|錯配修復缺陷)', 'MSI-H/dMMR', ''),
            (r'(IDH[12])\s*(?:基因)?\s*(突變|變異|陽性)', 'IDH', ''),
            (r'(HRD|同源重組修復缺失|同源重組缺陷)\s*(?:為|呈)?\s*(陽性|positive)', 'HRD', ''),
            (r'(?:(PD-L1|TPS|CPS)\s*(?:表現量|評分|比率)?\s*([≧≥>≦≤<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(%|分)?|(TC|IC)\s*(?:表現量|評分|比率)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(%|分))', 'PD-L1', '%'),
            (r'(PSA|前列腺特異抗原)\s*(?:值)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(ng/mL)?', 'PSA', 'ng/mL'),
            (r'(ECOG)\s*(?:PS|performance\s*status)?\s*(?:體能狀態)?\s*(?:評分|分數)?\s*(?:為|呈|：|:|介於)?\s*([0-4](?:\s*~?\s*[0-4])?|[≦≤<=＝=~至\-]\s*[0-4])', 'ECOG', 'Score'),
            (r'(CD20)\s*(?:抗原)?\s*(?:細胞)?\s*(?:為|呈|具)?\s*(陽性|\+|陰性|\-)', 'CD20', ''),
            (r'(CD30)\s*(?:為|呈)?\s*(\+|\-|陽性|陰性)', 'CD30', ''),
            (r'(CD30)\s*(需於超過|須大於|大於|超過|≧|≥|>)\s*([0-9\.]+)\s*(%)\s*的腫瘤細胞呈現陽性', 'CD30', '%'),
            (r'(CD19)\s*(?:抗原)?\s*(?:為|呈)?\s*(陽性|\+|陰性|\-)', 'CD19', ''),
            (r'(CD22)\s*(?:為|呈)?\s*(陽性|\+|陰性|\-)', 'CD22', ''),
            (r'(有絲分裂指數)\s*([≧≥>≦≤<=＝=~至\-])\s*([0-9]+/[0-9]+\s*HPF)', 'Mitotic Index', 'HPF'),

            # Infectious & Viral
            (r'(HBV\s*DNA|B型肝炎病毒量|B型肝炎病毒DNA)\s*(?:值|量)?\s*([≧≥>≦≤<=＝=~至\-])\s*([0-9\.,]+(?:\s*[xX×]\s*10\^?[0-9]+)?(?:\s*~?\s*[0-9\.,]+)?)\s*(IU/mL|copies/mL|國際單位/毫升|萬IU/mL)?', 'HBV DNA', 'IU/mL'),
            (r'(HBeAg|e抗原)\s*(?:為|呈)?\s*(陽性|陰性|\+|\-)', 'HBeAg', ''),
            (r'(HBsAg|B型肝炎表面抗原)\s*(?:為|呈|均為)?\s*(陽性|\+|\-)', 'HBsAg', ''),
            (r'(Anti-HCV|抗-HCV|C型肝炎抗體)\s*(?:與|及|和)?\s*(?:HCV\s*RNA)?\s*(?:均為|為|呈)?\s*(陽性|\+|\-)', 'Anti-HCV', ''),
            (r'(HCV\s*RNA|C型肝炎病毒量)\s*(?:為|呈|值|均為)?\s*(陽性|陰性|檢出|[≧≥>≦≤<=＝=~至\-]\s*[0-9\.,]+)', 'HCV RNA', ''),
            (r'(CD4|CD4淋巴球|CD4\+)\s*(?:數值|計數)?\s*([≧≥>≦≤<=＝=~至\-])\s*([0-9\.,]+)\s*(/cumm|/uL|/μL|cells/mm3|cells/μL)?', 'CD4', '/μL'),
            (r'(METAVIR)\s*(?:system)?\s*(?:證實)?\s*(?:輕度)?\s*(?:纖維化)?\s*([≧≥>≦<=＝=~至\-]| (?:大於或等於|大於|小於|等於) )?\s*(F[0-4])', 'METAVIR', 'Stage'),

            # Cardiometabolic, Renal & Liver Function
            (r'(Child-Pugh)\s*(?:class|\s*級)?\s*([A-C])(?:\s*class|\s*級)?', 'Child-Pugh', 'Class'),
            (r'(HbA1c|糖化血色素)\s*(?:值|數值)?\s*([≧≥>≦≤<=＝=~至\-]| (?:低於|高於|大於|小於) )\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(%)?', 'HbA1c', '%'),
            (r'(eGFR|腎絲球過濾率)\s*(?:值)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(mL/min(?:/1\.73m[2²])?)?', 'eGFR', 'mL/min/1.73m²'),
            (r'(LVEF|左心室射出分率|左心室射出分數)\s*(?:值)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(%)?', 'LVEF', '%'),
            (r'(NT-proBNP|proBNP|BNP)\s*(?:數值)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.,]+)\s*(pg/mL|pg/ml)?', 'NT-proBNP', 'pg/mL'),
            (r'(NYHA)\s*(?:Class|級|分級)?\s*([I|V|1-4]+(?:\s*~?\s*[I|V|1-4]+)?)\s*(?:級|class)?', 'NYHA', 'Class'),
            (r'(Total Cholesterol|總膽固醇)\s*(?:值)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(mg/dL)?', 'Total Cholesterol', 'mg/dL'),
            (r'(?:TC)\s*(?:值)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(mg/dL)', 'Total Cholesterol', 'mg/dL'),
            (r'(LDL|LDL-C|低密度脂蛋白膽固醇)\s*(?:值)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(mg/dL)?', 'LDL-C', 'mg/dL'),
            (r'(TG|三酸甘油[酯脂])\s*(?:值)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(mg/dL)?', 'TG', 'mg/dL'),
            (r'(HDL|HDL-C|高密度脂蛋白膽固醇)\s*(?:值)?\s*([<≦≤<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(mg/dL)?', 'HDL-C', 'mg/dL'),
            (r'(UACR|UPCR|尿液蛋白質與肌酸酐比值|微量白蛋白尿)\s*(?:值)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(mg/g|mg/mmol)?', 'UACR', 'mg/g'),
            (r'(Scr|serum\s*creatinine|血清肌酸酐|血清肌酐酸)\s*(?:值)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(mg/dL)?', 'Scr', 'mg/dL'),
            (r'(ALT|GPT)\s*(?:值)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(?:倍|U/L)?', 'ALT', 'U/L'),
            (r'(AST|GOT)\s*(?:值)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(?:倍|U/L)?', 'AST', 'U/L'),
            (r'(Total\s*Bilirubin|總膽紅素|Bilirubin)\s*(?:值)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(mg/dL)?', 'Total Bilirubin', 'mg/dL'),
            (r'(INR|凝血酶原時間國際標準化比值)\s*(?:值)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*', 'INR', ''),
            (r'(BMI|身體質量指數)\s*(?:值)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(kg/m[2²])?', 'BMI', 'kg/m²'),
            (r'(收縮壓|舒張壓)\s*(?:值)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+)\s*(mmHg)?', 'Blood Pressure', 'mmHg'),
            (r'(空腹血糖|飯前血糖|血糖)\s*(?:值)?\s*([<≦≤<=≧≥>＝=~至\-]|大於|小於)\s*([0-9\.]+)\s*(mg/dL|mg/mL)?', 'Blood Glucose', 'mg/dL'),

            # Rheumatology, Dermatology & Immunology Scores
            (r'(PASI)\s*(?:評分|分數|指數)?\s*([≧≥>≦≤<=＝=~至\-])\s*([0-9\.]+)', 'PASI', 'Score'),
            (r'(EASI)\s*(?:評分|分數|指數)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+)', 'EASI', 'Score'),
            (r'(?:(BSA)|(體表面積))\s*(?:受累面積)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+)\s*(%)?', 'BSA', '%'),
            (r'(DAS28)\s*(?:評分|分數)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+)', 'DAS28', 'Score'),
            (r'(BASDAI)\s*(?:評分|分數)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+)', 'BASDAI', 'Score'),
            (r'(EDSS)(?:\s*\([^\)]*\))?\s*(?:評分|分數|量表)?\s*(?:應|須|需)?\s*([≦≤<=≧≥>＝=~至\-]|大於或等於|大於等於|小於或等於|小於等於|大於|小於|未滿)\s*([0-9\.]+)\s*(分)?', 'EDSS', 'Score'),
            (r'(Mayo)\s*(?:score|評分|分數)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+)', 'Mayo', 'Score'),
            (r'(CDAI)\s*(?:評分|分數)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+)', 'CDAI', 'Score'),
            (r'(CRP|C反應蛋白|C-反應蛋白)\s*(?:值)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+)\s*(mg/dL|mg/L)?', 'CRP', 'mg/dL'),
            (r'(ESR|紅血球沉降率)\s*(?:值)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+)\s*(mm/hr)?', 'ESR', 'mm/hr'),
            (r'(SLEDAI(?:-2K)?)\s*(?:評分|分數|積分)?\s*(?:均)?\s*([≧≥>≦≤<=＝=~至]|大於等於|大於或等於|小於等於|小於或等於|大於|小於|均≧|均≥)\s*([0-9\.]+)\s*(分)?', 'SLEDAI', 'Score'),
            (r'(anti-dsDNA|抗雙股DNA抗體)\s*(?:為|呈)?\s*(陽性|\+|\-)', 'anti-dsDNA', ''),
            (r'(NMO-IgG|Aquaporin-4|AQP-?4)\s*(?:抗體)?\s*(?:為|呈)?\s*(陽性|\+|\-)', 'AQP4/NMO', ''),

            # Neurology, Stroke & Rare Diseases
            (r'(MMSE)\s*(?:評分|分數)?\s*([≦≤<=≧≥>＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(分)?', 'MMSE', '分'),
            (r'(NIHSS)\s*(?:評分|分數)?\s*([<≦≤<=≧≥>＝=~至\-]|大於|小於)\s*([0-9\.]+)\s*(分)?', 'NIHSS', 'Score'),
            (r'(SMN2)\s*(?:基因)?\s*(?:拷貝數|套數)\s*(?:應|須|需)?\s*([≦≤<=≧≥>＝=~至\-]|大於等於|小於等於|大於|小於)?\s*([0-9]+)\s*(?:套|copy|copies)?', 'SMN2', 'copies'),

            # Pulmonary, Bone, Hematology & Ophthalmology
            (r'(SpO2|血氧飽和度)\s*(?:值)?\s*([<≦≤<=＝=~至\-]|低於|小於)\s*([0-9\.]+)\s*(%)?', 'SpO2', '%'),
            (r'(T-score|骨密度(?:T值)?|BMD\s*T-score)\s*([≦≤<=＝=~至\-])\s*(-?[0-9\.]+)', 'T-score', ''),
            (r'(FEV1|第1秒用力吐氣容積)\s*(?:佔預測值)?\s*([≦≤<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(%)?', 'FEV1', '%'),
            (r'(白血球|WBC)\s*(?:數值|計數)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(/cumm|/uL|/μL)?', 'WBC', '/μL'),
            (r'(血小板|Platelet)\s*(?:數值|計數)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(/cumm|/uL|/μL)?', 'Platelet', '/μL'),
            (r'(ANC|嗜中性白血球|絕對嗜中性白血球)\s*(?:數值|計數)?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.,]+)\s*(/cumm|/uL|/μL)?', 'ANC', '/μL'),
            (r'(?:血色素|血紅素|Hemoglobin|Hb)\s*(?:值)?\s*([≦≤<=＝=~至\-])\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(g/dL)?', 'Hemoglobin', 'g/dL'),
            (r'(?:中央視網膜厚度|CRT)\s*(?:\(CRT\))?\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+)\s*(μm|um)?', 'CRT', 'μm'),
            (r'(?:最佳矯正視力|矯正後視力)\s*(?:介於)?\s*([0-9\.]+)\s*(?:~|至|和|-)\s*([0-9\.]+)', 'BCVA', ''),

            # Pass 2 Discovery Additions: Pulmonology, Allergy & Critical Care
            (r'(?:用力肺活量|FVC)(?:\s*預測值|\s*預估值)?\s*(?:之)?\s*([<≦≤<=≧≥>＝=~至\-]|\b(?:大於|小於|高於|低於)\b)?\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(%)?', 'FVC', '%'),
            (r'(?:DLCO)\s*(?:預測值|\s*預估值)?\s*(?:之|為)?\s*([<≦≤<=≧≥>＝=~至\-]|為預估值之)?\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(%)?', 'DLCO', '%'),
            (r'(?:Total\s*IgE|IgE|免疫球蛋白E)\s*(?:檢驗結果)?\s*(?:必須)?\s*(?:介於)?\s*([0-9\.]+)\s*(?:~|至|-)\s*([0-9\.]+)\s*(IU/mL|kU/L)?', 'IgE', 'IU/mL'),
            (r'(?:嗜伊紅性(?:\(嗜酸性\))?白血球|嗜酸性白血球|Eosinophil)\s*([≧≥>≦≤<=＝=~至\-])\s*([0-9\.,]+)\s*(cells/mcL|cells/μL|/cumm|/uL)?', 'Eosinophil', 'cells/mcL'),
            (r'(?:PaO2/FiO2|P/F\s*ratio)\s*([<≦≤<=＝=~至\-])\s*([0-9\.]+)\s*(mmHg)?', 'PaO2/FiO2', 'mmHg'),

            (r'(獨自坐立|獨自站立|獨自行走)\s*([≧≥>≦≤<=＝=~至\-])\s*([0-9]+)\s*(秒|步)', 'Motor_Milestones', ''),
            (r'(?:Anti-AAV9|AAV9抗體)\s*(?:效價)?\s*([>≧≥])\s*(1\s*:\s*[0-9]+)', 'Anti-AAV9', 'Titer'),
            (r'(?:血氨|血氨值)\s*(高於|大於|[>≧≥])\s*([0-9\.]+)\s*(μ\s*mol/L|μmol/L|umol/L)?', 'Ammonia', 'μmol/L'),
            (r'(?:phenylalanine|苯丙胺酸)\s*(高於|大於|[>≧≥])\s*([0-9\.]+)\s*(μmol/L|umol/L)?', 'Phenylalanine', 'μmol/L'),
            (r'(?:free carnitine|肉鹼)\s*(低於|小於|[<≦≤<=])\s*([0-9\.]+)\s*(μmol/L|umol/L)?', 'Carnitine', 'μmol/L'),
            (r'(?:tHcy|同半胱胺酸|高胱胺酸)\s*(高於|大於|[>≧≥])\s*([0-9\.]+)\s*(uM|μM)?', 'tHcy', 'uM'),

            # Pass 2 Discovery Additions: Renal Bone Minerals, Dermatology & Somatic Genetics
            (r'(?:血鈣\s*[*xX×]\s*血磷|鈣磷乘積)\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+)\s*(mg2/dL2|mg²/dL²)?', 'Ca_x_P', 'mg²/dL²'),
            (r'(?:血中鈣濃度|血清鈣|血鈣)\s*(?:在)?\s*([0-9\.]+)\s*(mg/dL)\s*(以上|以下)', 'Calcium', 'mg/dL'),
            (r'(?:PTH-i|iPTH)\s*(?:大於正常值)?\s*([一二三四五六七八九0-9\.]+)\s*(倍以上|倍)?', 'PTH-i', '倍'),
            (r'(?:Investigator[\'’]s\s*Global\s*Assessment|\(IGA\)|IGA)\s*(?:[:：]|≧|≥|>|=|＝)\s*([0-9](?:\s*~?\s*[0-9])?)', 'IGA', 'Score'),
            (r'(HLA-B\s*(?:\*?\s*1502|\*?\s*5801))\s*(?:基因)?\s*(?:檢測結果為|檢測為|為)?\s*(陽性|\+|\-)', 'HLA-B', ''),
            (r'(CALR|MPL)\s*(?:之)?\s*(?:基因)?\s*(突變|變異|陽性)', 'MPN_Mutations', ''),

            # Pass 3 Discovery Additions: Hematologic Blasts, Iron Overload, Electrolytes, Minimal Residual Disease & Precision Targets
            (r'(?:骨髓(?:中之)?|血液(?:中之)?|周邊血(?:或骨髓)?之?)?(芽細胞|骨髓芽細胞)\s*(?:比例|比率)?\s*(?:（myeloblast）)?\s*([≧≥>≦≤<=＝=~至\-]|大於|小於|超過|低於|高於)\s*([0-9\.]+(?:\s*~?\s*[0-9\.]+)?)\s*(%)', 'Bone_Marrow_Blasts', '%'),
            (r'(?:芽細胞數值)\s*([≧≥>≦<=＝=~至\-])\s*([0-9\.]+×109/L|[0-9\.]+x10\^?9/L)', 'Bone_Marrow_Blasts', '/L'),
            (r'(?:血清(?:內)?鐵蛋白|鐵蛋白)\s*(?:\(Ferritin\)|（Ferritin）)?\s*([＞>＜<≧≥≦≤=＝~至\-])\s*([0-9\.,]+)\s*(ug/L|μg/L|ng/mL)?', 'Ferritin', 'μg/L'),
            (r'(?:肝臟鐵質)\s*(?:\([^\)]*\)|（[^）]*）)?\s*([＞>＜<≧≥≦≤=＝=~至\-])\s*([0-9\.]+)\s*(mg/g\s*dry\s*weight|mg/g)?', 'Liver_Iron_Content', 'mg/g dry weight'),
            (r'(?:血清鈉濃度|血清鈉|血鈉)\s*(低於|小於|高於|大於|[<≦≤<=≧≥>＝=~至\-])\s*([0-9\.]+)\s*(mEq/L|mmol/L)?', 'Serum_Sodium', 'mEq/L'),
            (r'(?:微量殘留病灶|MRD)\s*(?:\(MRD\)|（MRD）)?\s*(?:為|呈)?\s*(陽性|\+|\-)', 'MRD', ''),
            (r'(?<!微量)(?<!尿)(?:血清白蛋白|白蛋白|Albumin)\s*(?:值)?\s*([<≦≤<=≧≥>＝=~至\-]|\b(?:大於|小於|高於|低於)\b)?\s*([0-9\.]+)\s*(g/dL|g/L)?', 'Albumin', 'g/dL'),
            (r'(CD33)\s*(?:抗原)?\s*(?:為|呈)?\s*(陽性|\+|\-)', 'CD33', ''),
            (r'(?:Claudin\s*(?:（CLDN）|\(CLDN\))?\s*18\.2|CLDN18\.2)\s*(?:為|呈|確定腫瘤為)?\s*(陽性|\+|\-)', 'CLDN18.2', '')
        ]

        extracted_biomarkers = []
        seen_spans = set()
        for pat, bio_name, def_unit in biomarker_patterns:
            for m in re.finditer(pat, full_text, re.IGNORECASE):
                span_key = (m.start(), m.end(), bio_name)
                if span_key in seen_spans:
                    continue
                seen_spans.add(span_key)

                # Filter non-None groups
                raw_groups = [g for g in m.groups() if g is not None]
                
                if bio_name in ['BCVA', 'IgE'] and len(raw_groups) >= 2:
                    op_norm = 'range'
                    val_norm = f"{raw_groups[0]}~{raw_groups[1]}"
                    unit_norm = raw_groups[2] if len(raw_groups) > 2 and raw_groups[2] else def_unit
                elif bio_name == 'ECOG':
                    op_norm = '='
                    val_norm = raw_groups[1].strip() if len(raw_groups) > 1 else raw_groups[0].strip()
                    unit_norm = 'Score'
                    for sym, norm_s in [('≦', '<='), ('≤', '<='), ('<=', '<='), ('≧', '>='), ('≥', '>='), ('>=', '>='), ('＝', '='), ('=', '=')]:
                        if val_norm.startswith(sym):
                            op_norm = norm_s
                            val_norm = val_norm[len(sym):].strip()
                            break
                elif bio_name == 'Calcium' and len(raw_groups) >= 3 and raw_groups[2] in ['以上', '以下']:
                    op_norm = '>=' if raw_groups[2] == '以上' else '<='
                    val_norm = raw_groups[0].strip()
                    unit_norm = raw_groups[1].strip() or def_unit
                elif bio_name == 'PTH-i' and len(raw_groups) >= 1:
                    op_norm = '>=' if len(raw_groups) > 1 and '以上' in raw_groups[1] else '>'
                    cn_num = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5'}.get(raw_groups[0].strip(), raw_groups[0].strip())
                    val_norm = cn_num
                    unit_norm = '倍'
                else:
                    if len(raw_groups) == 1:
                        op_raw = "="
                        val_raw = raw_groups[0].strip()
                        unit_raw = def_unit
                    elif len(raw_groups) == 2:
                        if raw_groups[0] in [">", "≧", "≥", "<", "≦", "≤", "=", "＝", "＞", "＜", "大於", "小於", "高於", "低於", "超過"]:
                            op_raw = raw_groups[0]
                            val_raw = raw_groups[1].strip()
                            unit_raw = def_unit
                        else:
                            op_raw = "="
                            val_raw = raw_groups[1].strip()
                            unit_raw = def_unit
                    elif len(raw_groups) == 3:
                        if raw_groups[0] in ["≧", "≥", ">=", "≦", "≤", "<=", ">", "<", "＝", "=", "＞", "＜", "~", "-", "至", "大於或等於", "大於等於", "小於或等於", "小於等於", "高於", "大於", "超過", "低於", "小於", "未滿", "均≧", "均≥", "以上", "以下"]:
                            op_raw = raw_groups[0]
                            val_raw = raw_groups[1].strip()
                            unit_raw = raw_groups[2].strip() or def_unit
                        else:
                            op_raw = raw_groups[1].strip()
                            val_raw = raw_groups[2].strip()
                            unit_raw = def_unit
                    elif len(raw_groups) >= 4:
                        op_raw = raw_groups[1].strip() if raw_groups[1] else "="
                        val_raw = raw_groups[2].strip().replace(',', '') if len(raw_groups) > 2 else ""
                        unit_raw = raw_groups[3].strip() if len(raw_groups) > 3 and raw_groups[3] else def_unit
                    else:
                        op_raw = "="
                        val_raw = m.group(0).strip()
                        unit_raw = def_unit
                    
                    # Normalize operator
                    op_norm = ">=" if op_raw in ["≧", "≥", ">=", "大於或等於", "大於等於", "均≧", "均≥", "以上"] else \
                              "<=" if op_raw in ["≦", "≤", "<=", "小於或等於", "小於等於", "以下"] else \
                              ">" if op_raw in [">", "＞", "大於", "高於", "超過", "需於超過", "須大於"] else \
                              "<" if op_raw in ["<", "＜", "小於", "低於", "未滿"] else \
                              "=" if op_raw in ["＝", "=", "陽性", "陰性", "+", "-"] else "range"
                    val_norm = val_raw
                    unit_norm = unit_raw or def_unit
                
                # Check for duration context near the match (e.g. 持續3個月以上, 治療至少6個月)
                surrounding = full_text[max(0, m.start()-50) : min(len(full_text), m.end()+80)]
                dur_match = re.search(r'(?:連續|持續|治療|追蹤|使用)?\s*([0-9一二三四五六七八九十百]+)\s*(?:個?月|週|周|年|天|日)(?:以上)?', surrounding)
                duration_str = dur_match.group(0).strip() if dur_match else None

                # Look up standard terminology bindings
                cw_info = self.crosswalk.get(bio_name, {})
                bindings = {}
                if cw_info.get("loinc", {}).get("code"):
                    bindings["loinc"] = cw_info["loinc"]["code"]
                if cw_info.get("snomed_ct", {}).get("concept_id"):
                    bindings["snomed_ct"] = str(cw_info["snomed_ct"]["concept_id"])
                if cw_info.get("snomed_ct", {}).get("procedure_id"):
                    bindings["snomed_procedure"] = str(cw_info["snomed_ct"]["procedure_id"])
                if cw_info.get("snomed_ct", {}).get("finding_id"):
                    bindings["snomed_finding"] = str(cw_info["snomed_ct"]["finding_id"])

                extracted_biomarkers.append({
                    "biomarker": bio_name,
                    "operator": op_norm,
                    "value": val_norm,
                    "unit": unit_norm or "",
                    "duration": duration_str,
                    "terminology_bindings": bindings,
                    "source_grounding": {
                        "start_char": m.start(),
                        "end_char": m.end(),
                        "snippet": full_text[m.start():m.end()]
                    }
                })

        # 3. Extract Prior Therapy / Step Therapy Requirements (前線用藥條件)
        step_therapy_rules = []
        step_patterns = [
            r'(?:經使用|曾使用|使用|接受)?(?:第一線|第二線|傳統|標準)?(?:治療藥物|藥物)?(?:最大耐受劑量)?(?:治療|使用)?(?:至少|連續)?\s*[0-9一二三四五六七八九十]+\s*(?:個?月|週|周|年)?\s*(?:治療)?(?:效果不佳|無效|失敗|無法耐受|產生耐藥性|不耐受)',
            r'(?:第一線|二線|第2線|第3線|第三線)(?:用藥|治療|治療失敗)',
            r'(?:須先經|需先經|應先使用).{2,40}(?:無效|失敗|無法耐受)'
        ]
        for spat in step_patterns:
            for m in re.finditer(spat, full_text):
                step_snippet = full_text[m.start():m.end()].strip()
                if len(step_snippet) > 4:
                    step_therapy_rules.append({
                        "requirement": step_snippet,
                        "source_grounding": {
                            "start_char": m.start(),
                            "end_char": m.end(),
                            "snippet": step_snippet
                        }
                    })

        # 4. Extract Stopping Rules (停藥/不予給付條件)
        stopping_rules = []
        stop_patterns = [
            r'(?:若|如|當)?.{0,30}(?:應即停藥|應停止給付|不再給付|停止使用|不得繼續使用|停藥標準).{0,50}',
            r'疾病惡化(?:時)?應(?:即)?停藥',
            r'(?:發生|出現).{2,20}(?:不耐受|嚴重不良反應).{0,20}(?:應停藥|停止給付)'
        ]
        for stpat in stop_patterns:
            for m in re.finditer(stpat, full_text):
                stop_snippet = full_text[m.start():m.end()].strip()
                if len(stop_snippet) > 6 and stop_snippet not in [s["condition"] for s in stopping_rules]:
                    stopping_rules.append({
                        "condition": stop_snippet,
                        "source_grounding": {
                            "start_char": m.start(),
                            "end_char": m.end(),
                            "snippet": stop_snippet
                        }
                    })

        # 5. Extract Evaluation Intervals (評估與續用週期)
        eval_intervals = []
        eval_patterns = [
            r'(?:每|每隔|每經過)\s*[0-9一二三四五六七八九十]+\s*(?:個?月|週|周|年)\s*(?:需|應|須)?(?:重新評估|再次評估|進行評估|確認療效|評估一次)',
            r'(?:每次申請|每次核准)?(?:之?給付|使用)?(?:期限|療程)?(?:最長|以)?\s*[0-9一二三四五六七八九十]+\s*(?:個?月|週|周|年|天|日)(?:為限|為期)?'
        ]
        for epat in eval_patterns:
            for m in re.finditer(epat, full_text):
                eval_snippet = full_text[m.start():m.end()].strip()
                if len(eval_snippet) > 4:
                    eval_intervals.append({
                        "frequency": eval_snippet,
                        "source_grounding": {
                            "start_char": m.start(),
                            "end_char": m.end(),
                            "snippet": eval_snippet
                        }
                    })

        # 6. Synthesize Clinical Summary (High-quality, readable synthesis)
        clinical_summary = self._generate_clean_clinical_summary(
            section_number, section_title, full_text, known_indications, extracted_biomarkers, prior_auth
        )

        # 7. Assemble Structured Clinical Rules Group
        clinical_rules = []
        if known_indications:
            for ind in known_indications:
                ind_rules = {
                    "indication": ind,
                    "biomarkers": [b for b in extracted_biomarkers],
                    "prior_authorization": prior_auth,
                    "step_therapy": [s["requirement"] for s in step_therapy_rules],
                    "stopping_rules": [s["condition"] for s in stopping_rules],
                    "evaluation_frequency": [e["frequency"] for e in eval_intervals]
                }
                clinical_rules.append(ind_rules)
        else:
            clinical_rules.append({
                "indication": section_title,
                "biomarkers": extracted_biomarkers,
                "prior_authorization": prior_auth,
                "step_therapy": [s["requirement"] for s in step_therapy_rules],
                "stopping_rules": [s["condition"] for s in stopping_rules],
                "evaluation_frequency": [e["frequency"] for e in eval_intervals]
            })

        result = {
            "summary": clinical_summary,
            "clinical_rules": clinical_rules,
            "structured_biomarkers": extracted_biomarkers,
            "prior_authorization_required": prior_auth,
            "prior_authorization_grounding": prior_auth_span,
            "step_therapy": [s["requirement"] for s in step_therapy_rules],
            "stopping_rules": [s["condition"] for s in stopping_rules],
            "evaluation_intervals": [e["frequency"] for e in eval_intervals]
        }

        # Cache result
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return result

    def _generate_clean_clinical_summary(self, section_number: str, section_title: str, full_text: str,
                                        known_indications: List[str], biomarkers: List[Dict[str, Any]], prior_auth: bool) -> str:
        """
        Synthesizes a crisp, professional 1-3 sentence clinical summary of the payment rules.
        """
        # Clean title
        clean_title = re.sub(r'^\d+(\.\d+)*\s*', '', section_title)
        clean_title = re.sub(r'（[^）]*\d+[^）]*）|\([^)]*\d+[^)]*\)', '', clean_title).strip()
        
        parts = []
        
        # Indications summary
        if known_indications:
            ind_names = "、".join([i.split(' (')[0] for i in known_indications[:3]])
            parts.append(f"適用於【{ind_names}】之健保給付。")
        else:
            parts.append(f"規範【{clean_title}】之健保給付條件。")

        # Criteria highlight
        criteria_highlights = []
        if biomarkers:
            bio_strs = []
            for b in biomarkers[:3]:
                bio_strs.append(f"{b['biomarker']} {b['operator']} {b['value']}{b['unit']}")
            criteria_highlights.append(f"臨床檢驗需符合 {', '.join(bio_strs)}")

        if prior_auth:
            criteria_highlights.append("使用前須經事前審查核准")

        if criteria_highlights:
            parts.append("主要條件包含：" + "；".join(criteria_highlights) + "。")
        else:
            # Fallback to concise first sentences of text if no special criteria found
            first_sent = full_text.split('。')[0].replace('\n', ' ').strip()
            first_sent = re.sub(r'【.*?】', '', first_sent).strip()
            if len(first_sent) > 15 and len(first_sent) < 180:
                parts.append(f"規範重點：{first_sent}。")

        return " ".join(parts)

if __name__ == "__main__":
    extractor = LangExtractEngine()
    sample_text = (
        "2.16. Dapagliflozin(如Forxiga)、empagliflozin (如Jardiance 10mg)：(109/12/1、110/6/1、111/5/1)\n"
        "1.門診治療慢性心衰竭（NYHA II-IV），左心室射出分率 LVEF≦40%，且使用標準治療無效者。\n"
        "2.慢性腎臟病 eGFR 25-75 mL/min/1.73m2 且尿液 ACR≧200 mg/g。\n"
        "3.使用本藥品需先經事前審查核准後始得使用，每次核准期限為6個月。若eGFR下降至<15時應停藥。"
    )
    res = extractor.extract_section_rules("2.16.", "Dapagliflozin", sample_text, ["Heart Failure", "CKD"])
    print("=== Extracted Result ===")
    print(json.dumps(res, ensure_ascii=False, indent=2))
