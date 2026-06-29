import re

# Comprehensive Medical Disease & Condition Ontology for Taiwan NHI Regulations
# Ensures 100% bilingual translation across Oncology, Gastroenterology, Rheumatology,
# Neurology, Dermatology, Cardiology, Hematology, Endocrinology, and Clinical Nutrition / Vitamins.

DISEASE_DATABASE = {
    # Vitamin & Nutrient Deficiency Indications (維生素與營養缺乏症 - 附表三-A)
    "scurvy": {
        "en": "Scurvy (Vitamin C Deficiency)",
        "tc_terms": ["壞血病"],
        "aliases": ["scurvy", "vitamin c deficiency"]
    },
    "rickets": {
        "en": "Rickets / Osteomalacia (Vitamin D Deficiency)",
        "tc_terms": ["佝僂病", "骨軟化症", "尿毒症腎性骨質病變"],
        "aliases": ["rickets", "osteomalacia", "renal osteodystrophy"]
    },
    "night_blindness": {
        "en": "Night Blindness / Xerophthalmia (Vitamin A Deficiency)",
        "tc_terms": ["夜盲症", "眼球乾燥症", "角膜軟化症", "皮膚角化異常症"],
        "aliases": ["night blindness", "xerophthalmia", "keratomalacia"]
    },
    "pellagra": {
        "en": "Pellagra (Niacin / Vitamin B3 Deficiency)",
        "tc_terms": ["癩皮症"],
        "aliases": ["pellagra", "niacin deficiency"]
    },
    "megaloblastic_anemia": {
        "en": "Megaloblastic Anemia (Vitamin B12 / Folic Acid Deficiency)",
        "tc_terms": ["巨球性貧血", "巨大紅血球貧血症"],
        "aliases": ["megaloblastic anemia", "vitamin b12 deficiency", "folic acid deficiency"]
    },
    "beriberi_thiamine": {
        "en": "Thiamine Deficiency / Malabsorption Syndrome (Vitamin B1)",
        "tc_terms": ["維生素B1缺乏症", "營養吸收障礙症候群", "酒精戒斷症候群"],
        "aliases": ["thiamine deficiency", "beriberi", "malabsorption syndrome", "alcohol withdrawal syndrome"]
    },
    "angular_cheilitis": {
        "en": "Angular Cheilitis (Vitamin B2 Deficiency)",
        "tc_terms": ["口角炎"],
        "aliases": ["angular cheilitis", "vitamin b2 deficiency"]
    },

    # Hepatology & Gastroenterology (肝膽與腸胃)
    "hepatoprotectants": {
        "en": "Hepatoprotectants / Liver Protective Agents",
        "tc_terms": ["肝庇護劑", "保肝劑", "護肝劑", "水飛薊素", "水飛薊", "西利馬林", "利加隆", "熊去氧膽酸", "優思", "強體力蒙", "合寶麥斯"],
        "aliases": [
            "hepatoprotectant", "hepatoprotectants", "hepatoprotective agent", "hepatoprotective agents", 
            "liver protective agent", "liver protective agents", "hepatoprotective",
            "silymarin", "silybin", "legalon", "silygen", "hepalgen", "silybon", "silyrin", "silybest", "kewei",
            "ursodeoxycholic acid", "ursodiol", "udca", "urso",
            "ornithine", "aspartate", "hepa-merz", "hepaneed",
            "glycyrrhizin", "snmc", "minophagen"
        ]
    },
    "cirrhosis": {
        "en": "Liver Cirrhosis",
        "tc_terms": ["肝硬化", "代償性肝硬化", "失代償性肝硬化", "代償不全肝硬化"],
        "aliases": ["cirrhosis", "liver cirrhosis", "hepatic cirrhosis"]
    },
    "hepatitis": {
        "en": "Hepatitis B / Hepatitis C (HBV DNA / HCV RNA)",
        "tc_terms": ["肝炎", "慢性B型肝炎", "慢性C型肝炎", "B型肝炎", "C型肝炎", "急性肝炎", "肝炎發作", "B型肝炎病毒量", "血清HBV DNA"],
        "aliases": ["hepatitis", "hbv", "hcv", "hepatitis b", "hepatitis c", "hbvdna", "hbv dna", "hbv-dna", "hcvrna", "hcv rna", "hcv-rna"]
    },
    "liver_cancer": {
        "en": "Liver Cancer / Hepatocellular Carcinoma",
        "tc_terms": ["肝癌", "肝細胞癌"],
        "aliases": ["liver cancer", "hcc"]
    },
    "ulcerative_colitis": {
        "en": "Ulcerative Colitis (UC)",
        "tc_terms": ["潰瘍性結腸炎", "潰瘍性大腸炎"],
        "aliases": ["ulcerative colitis", "uc"]
    },
    "crohn_disease": {
        "en": "Crohn's Disease (CD)",
        "tc_terms": ["克隆氏症", "克羅恩病"],
        "aliases": ["crohn's disease", "crohns", "cd"]
    },
    "ibd": {
        "en": "Inflammatory Bowel Disease (IBD)",
        "tc_terms": ["發炎性腸道疾病", "炎症性腸病"],
        "aliases": ["inflammatory bowel disease", "ibd"]
    },
    "peptic_ulcer": {
        "en": "Peptic Ulcer Disease",
        "tc_terms": ["消化性潰瘍", "胃潰瘍", "十二指腸潰瘍"],
        "aliases": ["peptic ulcer", "pud", "gastric ulcer", "duodenal ulcer"]
    },
    "gerd": {
        "en": "Gastroesophageal Reflux Disease",
        "tc_terms": ["逆流性食道炎", "胃食道逆流症", "胃食道逆流"],
        "aliases": ["gerd", "reflux esophagitis", "reflux"]
    },

    # Oncology (癌症與腫瘤)
    "triple_negative_breast_cancer": {
        "en": "Triple-Negative Breast Cancer (TNBC)",
        "tc_terms": ["三陰性乳癌", "轉移性三陰性乳癌"],
        "aliases": ["triple negative breast cancer", "tnbc"]
    },
    "breast_cancer": {
        "en": "Breast Cancer",
        "tc_terms": ["乳癌", "乳腺癌", "轉移性乳癌"],
        "aliases": ["breast cancer"]
    },
    "lung_cancer": {
        "en": "Lung Cancer",
        "tc_terms": ["肺癌", "非小細胞肺癌", "小細胞肺癌", "肺腺癌"],
        "aliases": ["lung cancer", "nsclc", "sclc"]
    },
    "prostate_cancer": {
        "en": "Prostate Cancer",
        "tc_terms": ["前列腺癌", "攝護腺癌", "前列腺腺癌"],
        "aliases": ["prostate cancer"]
    },
    "ovarian_cancer": {
        "en": "Ovarian Cancer",
        "tc_terms": ["卵巢癌", "卵巢上皮癌", "輸卵管癌", "原發性腹膜癌"],
        "aliases": ["ovarian cancer"]
    },
    "gist": {
        "en": "Gastrointestinal Stromal Tumor (GIST)",
        "tc_terms": ["胃腸基質瘤", "胃腸道基質腫瘤"],
        "aliases": ["gastrointestinal stromal tumor", "gist"]
    },
    "nasopharyngeal_carcinoma": {
        "en": "Nasopharyngeal Carcinoma",
        "tc_terms": ["鼻咽癌"],
        "aliases": ["nasopharyngeal carcinoma", "npc"]
    },
    "head_neck_cancer": {
        "en": "Head and Neck Cancer",
        "tc_terms": ["頭頸部癌", "下咽癌", "喉癌", "口腔癌"],
        "aliases": ["head and neck cancer", "hnscc"]
    },
    "melanoma": {
        "en": "Melanoma",
        "tc_terms": ["黑色素瘤", "惡性黑色素瘤"],
        "aliases": ["melanoma"]
    },
    "neuroendocrine_tumor": {
        "en": "Neuroendocrine Tumor (NET)",
        "tc_terms": ["神經內分泌腫瘤", "胰臟神經內分泌腫瘤"],
        "aliases": ["neuroendocrine tumor", "net"]
    },
    "thyroid_cancer": {
        "en": "Thyroid Cancer",
        "tc_terms": ["甲狀腺癌", "分化型甲狀腺癌"],
        "aliases": ["thyroid cancer"]
    },
    "renal_cell_carcinoma": {
        "en": "Renal Cell Carcinoma (RCC)",
        "tc_terms": ["腎細胞癌", "轉移性腎細胞癌"],
        "aliases": ["renal cell carcinoma", "rcc"]
    },
    "urothelial_carcinoma": {
        "en": "Urothelial Carcinoma / Bladder Cancer",
        "tc_terms": ["尿路上皮癌", "膀胱癌"],
        "aliases": ["urothelial carcinoma", "bladder cancer"]
    },
    "colorectal_cancer": {
        "en": "Colorectal Cancer",
        "tc_terms": ["大腸直腸癌", "大腸癌", "直腸癌"],
        "aliases": ["colorectal cancer", "colon cancer"]
    },
    "pancreatic_cancer": {
        "en": "Pancreatic Cancer",
        "tc_terms": ["胰臟癌", "胰腺癌"],
        "aliases": ["pancreatic cancer"]
    },
    "multiple_myeloma": {
        "en": "Multiple Myeloma",
        "tc_terms": ["多發性骨髓瘤"],
        "aliases": ["multiple myeloma"]
    },
    "leukemia": {
        "en": "Leukemia",
        "tc_terms": ["白血病", "血癌", "急性骨髓性白血病", "慢性骨髓性白血病"],
        "aliases": ["leukemia", "aml", "cml", "all", "cll"]
    },
    "lymphoma": {
        "en": "Lymphoma",
        "tc_terms": ["淋巴腫瘤", "淋巴癌", "霍奇金淋巴瘤", "非霍奇金淋巴瘤"],
        "aliases": ["lymphoma"]
    },

    # Dermatology & Infections (皮膚與真菌感染)
    "onychomycosis": {
        "en": "Onychomycosis / Tinea Unguium",
        "tc_terms": ["足趾甲癬", "手指甲癬", "甲癬", "灰指甲", "灰趾甲", "甲真菌病"],
        "aliases": ["onychomycosis", "tinea unguium", "fungal nail infection", "nail fungus", "toenail fungus"]
    },
    "tinea": {
        "en": "Tinea (Ringworm / Dermatophytosis)",
        "tc_terms": ["體癬", "股癬", "頭癬", "手足癬", "皮真菌病"],
        "aliases": ["tinea", "ringworm", "tinea corporis", "tinea cruris", "tinea capitis", "tinea pedis"]
    },
    "fungal_infection": {
        "en": "Fungal Infection / Mycosis",
        "tc_terms": ["黴菌感染", "真菌感染", "念珠菌感染", "念珠性陰道炎", "汗斑"],
        "aliases": ["fungal infection", "mycosis", "candidiasis", "tinea versicolor"]
    },
    "hidradenitis_suppurativa": {
        "en": "Hidradenitis Suppurativa",
        "tc_terms": ["化膿性汗腺炎"],
        "aliases": ["hidradenitis suppurativa", "hs"]
    },
    "atopic_dermatitis": {
        "en": "Atopic Dermatitis",
        "tc_terms": ["異位性皮膚炎", "濕疹"],
        "aliases": ["atopic dermatitis", "eczema"]
    },
    "urticaria": {
        "en": "Chronic Urticaria",
        "tc_terms": ["蕁麻疹", "慢性特發性蕁麻疹", "慢性自發性蕁麻疹"],
        "aliases": ["urticaria", "hives"]
    },

    # Rheumatology & Immunology (風濕免疫)
    "gpp": {
        "en": "Generalized Pustular Psoriasis (GPP)",
        "tc_terms": ["全身型急性發作膿疱性乾癬", "膿疱性乾癬"],
        "aliases": ["generalized pustular psoriasis", "gpp"]
    },
    "psoriasis": {
        "en": "Psoriasis / Psoriatic Arthritis",
        "tc_terms": ["乾癬", "銀屑病", "乾癬性關節炎"],
        "aliases": ["psoriasis", "psoriatic arthritis"]
    },
    "sle": {
        "en": "Systemic Lupus Erythematosus",
        "tc_terms": ["紅斑性狼瘡", "系統性紅斑性狼瘡", "狼瘡"],
        "aliases": ["systemic lupus erythematosus", "sle", "lupus"]
    },
    "ra": {
        "en": "Rheumatoid Arthritis",
        "tc_terms": ["類風濕性關節炎"],
        "aliases": ["rheumatoid arthritis"]
    },
    "ankylosing_spondylitis": {
        "en": "Ankylosing Spondylitis",
        "tc_terms": ["僵直性脊椎炎"],
        "aliases": ["ankylosing spondylitis"]
    },
    "vasculitis": {
        "en": "Vasculitis / Dermatomyositis",
        "tc_terms": ["血管炎", "皮肌炎", "多發性肌炎", "硬皮症", "貝西氏症"],
        "aliases": ["vasculitis", "dermatomyositis", "polymyositis", "scleroderma", "behcet's disease"]
    },

    # Cardiology & Cardiovascular (心血管)
    "heart_failure": {
        "en": "Heart Failure",
        "tc_terms": ["心臟衰竭", "心力衰竭", "充血性心臟衰竭"],
        "aliases": ["heart failure", "chf"]
    },
    "stroke": {
        "en": "Stroke / Cerebrovascular Accident",
        "tc_terms": ["腦中風", "中風", "缺血性腦中風", "出血性腦中風", "腦血管疾病"],
        "aliases": ["stroke", "cva", "cerebrovascular accident"]
    },
    "myocardial_infarction": {
        "en": "Myocardial Infarction",
        "tc_terms": ["心肌梗塞", "急性心肌梗塞", "冠狀動脈疾病", "冠心病"],
        "aliases": ["myocardial infarction", "mi", "heart attack", "coronary artery disease", "cad"]
    },
    "atrial_fibrillation": {
        "en": "Atrial Fibrillation",
        "tc_terms": ["心房顫動", "心房纖維顫動", "房顫"],
        "aliases": ["atrial fibrillation", "af", "afib"]
    },
    "thrombosis": {
        "en": "Thrombosis / Pulmonary Embolism",
        "tc_terms": ["血栓", "深靜脈血栓", "肺栓塞", "靜脈血栓栓塞", "栓塞"],
        "aliases": ["thrombosis", "dvt", "pulmonary embolism", "pe", "embolism", "thromboembolism"]
    },
    "hypertension": {
        "en": "Hypertension",
        "tc_terms": ["高血壓", "原發性高血壓"],
        "aliases": ["hypertension", "htn", "high blood pressure"]
    },
    "hyperlipidemia": {
        "en": "Hyperlipidemia / Hypercholesterolemia",
        "tc_terms": ["高脂血症", "高膽固醇血症", "高三酸甘油酯血症", "血脂異常"],
        "aliases": ["hyperlipidemia", "hypercholesterolemia", "dyslipidemia"]
    },

    # Neurology & Psychiatry (神經與精神科)
    "migraine": {
        "en": "Migraine",
        "tc_terms": ["偏頭痛", "慢性偏頭痛"],
        "aliases": ["migraine"]
    },
    "myasthenia_gravis": {
        "en": "Myasthenia Gravis",
        "tc_terms": ["重症肌無力"],
        "aliases": ["myasthenia gravis", "mg"]
    },
    "multiple_sclerosis": {
        "en": "Multiple Sclerosis",
        "tc_terms": ["多發性硬化症"],
        "aliases": ["multiple sclerosis", "ms"]
    },
    "parkinson": {
        "en": "Parkinson's Disease",
        "tc_terms": ["帕金森氏症", "帕金森病", "巴金森氏症"],
        "aliases": ["parkinson's disease", "parkinsons"]
    },
    "alzheimer": {
        "en": "Alzheimer's Disease / Dementia",
        "tc_terms": ["阿茲海默症", "失智症", "老年痴呆症"],
        "aliases": ["alzheimer's disease", "dementia", "alzheimers"]
    },
    "epilepsy": {
        "en": "Epilepsy",
        "tc_terms": ["癲癇", "癲癇症"],
        "aliases": ["epilepsy", "seizure"]
    },
    "schizophrenia": {
        "en": "Schizophrenia",
        "tc_terms": ["思覺失調症", "精神分裂症"],
        "aliases": ["schizophrenia"]
    },
    "bipolar": {
        "en": "Bipolar Disorder",
        "tc_terms": ["雙相情緒障礙症", "躁鬱症"],
        "aliases": ["bipolar disorder", "bipolar"]
    },
    "depression": {
        "en": "Major Depressive Disorder",
        "tc_terms": ["憂鬱症", "重度憂鬱症"],
        "aliases": ["depression", "mdd"]
    },

    # Respiratory & Nephrology & Endocrinology (呼吸、腎臟與內分泌)
    "asthma": {
        "en": "Asthma",
        "tc_terms": ["氣喘", "哮喘"],
        "aliases": ["asthma"]
    },
    "copd": {
        "en": "Chronic Obstructive Pulmonary Disease",
        "tc_terms": ["慢性阻塞性肺病", "肺氣腫", "慢性支氣管炎"],
        "aliases": ["chronic obstructive pulmonary disease", "copd"]
    },
    "ipf": {
        "en": "Idiopathic Pulmonary Fibrosis (IPF)",
        "tc_terms": ["特發性肺纖維化"],
        "aliases": ["idiopathic pulmonary fibrosis", "ipf"]
    },
    "ckd": {
        "en": "Chronic Kidney Disease",
        "tc_terms": ["慢性腎臟病", "慢性腎衰竭", "末期腎臟病", "透析"],
        "aliases": ["chronic kidney disease", "ckd", "esrd", "dialysis"]
    },
    "hypoparathyroidism": {
        "en": "Hypoparathyroidism",
        "tc_terms": ["副甲狀腺機能低下症", "副甲狀腺功能低下症", "甲狀旁腺功能減退症"],
        "aliases": ["hypoparathyroid"]
    },
    "hyperparathyroidism": {
        "en": "Hyperparathyroidism",
        "tc_terms": ["副甲狀腺機能亢進症", "副甲狀腺功能亢進症", "甲狀旁腺功能亢進症"],
        "aliases": ["hyperparathyroid"]
    },
    "diabetes": {
        "en": "Diabetes Mellitus",
        "tc_terms": ["糖尿病", "第一型糖尿病", "第二型糖尿病"],
        "aliases": ["diabetes mellitus", "t2dm", "t1dm"]
    },
    "osteoporosis": {
        "en": "Osteoporosis",
        "tc_terms": ["骨質疏鬆症", "骨質疏鬆"],
        "aliases": ["osteoporosis"]
    },
    "acromegaly": {
        "en": "Acromegaly",
        "tc_terms": ["肢端肥大症"],
        "aliases": ["acromegaly"]
    },
    "gout": {
        "en": "Gout / Hyperuricemia",
        "tc_terms": ["痛風", "痛風性關節炎", "高尿酸血症"],
        "aliases": ["gout", "hyperuricemia"]
    },
    "hemophilia": {
        "en": "Hemophilia",
        "tc_terms": ["血友病", "第八凝血因子", "第九凝血因子"],
        "aliases": ["hemophilia"]
    },
    "anemia": {
        "en": "Anemia",
        "tc_terms": ["貧血", "腎性貧血", "缺鐵性貧血"],
        "aliases": ["anemia"]
    },
    "itp": {
        "en": "Immune Thrombocytopenia (ITP)",
        "tc_terms": ["特發性血小板減少性紫斑症", "血小板減少症"],
        "aliases": ["immune thrombocytopenia", "itp"]
    }
}

class DiseaseEngine:
    def __init__(self):
        self.disease_db = DISEASE_DATABASE

    def expand_query(self, query):
        """Given a query in English or Chinese, return matching disease entries using word boundary matching."""
        q_clean = query.strip().lower()
        matched_keys = set()

        for key, info in self.disease_db.items():
            terms_to_check = [info["en"]] + info["aliases"] + info["tc_terms"]
            for term in terms_to_check:
                t_clean = term.lower()
                if len(t_clean) <= 3:
                    if re.search(r'\b' + re.escape(t_clean) + r'\b', q_clean):
                        matched_keys.add(key)
                        break
                else:
                    if t_clean in q_clean or q_clean in t_clean:
                        matched_keys.add(key)
                        break

        results = []
        for key in matched_keys:
            info = self.disease_db[key]
            results.append({
                "disease_key": key,
                "english_name": info["en"],
                "chinese_terms": info["tc_terms"],
                "aliases": info["aliases"]
            })
        return results

    def extract_diseases_from_text(self, text):
        """Extract all mentioned diseases in text and return clean bilingual list."""
        found_diseases = []
        text_lower = text.lower()

        for key, info in self.disease_db.items():
            matched = False
            for tc in info["tc_terms"]:
                if tc in text:
                    matched = True
                    break
            if not matched:
                for alias in info["aliases"]:
                    if len(alias) >= 3 and re.search(r'\b' + re.escape(alias.lower()) + r'\b', text_lower):
                        matched = True
                        break

            if matched:
                found_diseases.append({
                    "english": info["en"],
                    "chinese": info["tc_terms"][0],
                    "all_tc_terms": info["tc_terms"]
                })

        return found_diseases

if __name__ == "__main__":
    engine = DiseaseEngine()
    print("Expand query 'scurvy':", engine.expand_query("scurvy"))
