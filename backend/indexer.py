import os
import glob
import yaml
import re
from backend.atc_engine import ATCEngine
from backend.disease_engine import DiseaseEngine

try:
    from yaml import CSafeLoader as YamlLoader
except ImportError:
    from yaml import SafeLoader as YamlLoader


class NHIIndexer:
    STOPWORDS = {
        'for', 'how', 'long', 'the', 'could', 'should', 'would', 'be', 'used', 'use', 'using',
        'with', 'about', 'and', 'or', 'but', 'a', 'an', 'at', 'by', 'from', 'to', 'in', 'on',
        'this', 'that', 'these', 'those', 'can', 'will', 'what', 'why', 'where', 'when', 'who',
        'which', 'have', 'has', 'had', 'been', 'is', 'are', 'was', 'were', 'does', 'did', 'do',
        'patient', 'patients', 'non', 'of', 'last', 'before'
    }

    BIOMARKER_QUERY_ALIASES = {
        'egfr': 'eGFR',
        'hba1c': 'HbA1c',
        'a1c': 'HbA1c',
        'lvef': 'LVEF',
        'alt': 'ALT',
        'ast': 'AST',
        'scr': 'Scr',
        'creatinine': 'Scr',
        'bmi': 'BMI',
        'pdl1': 'PD-L1',
        'pd-l1': 'PD-L1',
        'her2': 'HER2',
        'das28': 'DAS28',
        'pasi': 'PASI',
        'edss': 'EDSS',
        'mmse': 'MMSE',
        'cdr': 'CDR',
        'ldlc': 'LDL-C',
        'ldl-c': 'LDL-C',
        'ldl': 'LDL-C',
        'psa': 'PSA',
        'afp': 'AFP',
        'ige': 'IgE',
        'anc': 'ANC',
        'hb': 'Hb',
        'bnp': 'BNP/NT-proBNP',
        'nt-probnp': 'BNP/NT-proBNP',
        'dexa': 'DEXA/BMD',
        'bmd': 'DEXA/BMD',
        't-score': 'DEXA/BMD',
        'uacr': 'UACR',
        'upcr': 'UPCR',
        'fev1': 'FEV1',
        'nihss': 'NIHSS',
        'ecog': 'ECOG',
        'child-pugh': 'Child-Pugh',
        'basdai': 'BASDAI',
        'easi': 'EASI',
    }

    def __init__(self, data_dir="okf_data"):
        self.data_dir = data_dir
        self.atc_engine = ATCEngine()
        self.disease_engine = DiseaseEngine()
        self.regulations = []
        self.index = {}
        self._compiled_word_regex = {}
        self.load_and_index()

    def _get_word_regex(self, term):
        pat = self._compiled_word_regex.get(term)
        if pat is None:
            pat = re.compile(r'\b' + re.escape(term) + r'\b')
            self._compiled_word_regex[term] = pat
        return pat

    LAB_FILTER_GROUP_MAP = {
        "bnp/nt-probnp": {"nt-probnp", "bnp", "probnp"},
        "uacr": {"uacr", "upcr"},
        "alt": {"alt", "ast", "gpt", "got"},
        "braf": {"braf", "ras", "kras", "nras", "ros1"},
        "psa": {"psa", "afp"},
        "pasi": {"pasi", "easi"},
        "mmse": {"mmse", "cdr"},
        "dexa/bmd": {"t-score", "bmd", "dexa"},
        "hbv dna": {"hbv dna", "hbsag", "hbeag"},
        "hcv rna": {"hcv rna", "anti-hcv"},
        "hb": {"hb", "hemoglobin", "血色素", "血紅素"},
        "anc": {"anc", "wbc", "白血球"},
        "platelet": {"platelet", "血小板"},
    }

    def load_and_index(self):
        self.regulations = []
        self.index = {
            "by_section": {},
            "by_keyword": {},
            "by_lab": {}
        }

        yaml_files = sorted(glob.glob(os.path.join(self.data_dir, "*.yaml")))
        for yf in yaml_files:
            try:
                with open(yf, "r", encoding="utf-8") as f:
                    content = yaml.load(f, Loader=YamlLoader)
                    if content and "regulations" in content:
                        for reg in content["regulations"]:
                            self._index_record(reg)
            except Exception as e:
                print(f"Error loading {yf}: {e}")

    def _index_record(self, reg):
        title_str = reg.get("section_title", "")
        body_str = reg.get("reference_annotations", {}).get("full_text", "")
        full_text = f"{title_str} {body_str}"
        full_text_lower = full_text.lower()
        title_lower = title_str.lower()

        reg["norm_full_text"] = re.sub(r'[\s\-_/]+', '', full_text_lower)
        reg["_title_lower"] = title_lower
        reg["_full_text_lower"] = full_text_lower
        reg["_classes_lower"] = [c.lower() for c in reg.get("medications", {}).get("drug_classes", [])]
        reg["_ingredients_lower"] = [i.lower() for i in reg.get("medications", {}).get("ingredients", [])]
        reg["_indications_lower"] = [ind.lower() for ind in reg.get("conditions_of_payment", {}).get("indications", [])]
        lab_tokens = {l.lower() for l in reg.get("conditions_of_payment", {}).get("laboratory_criteria", [])}
        for b in reg.get("conditions_of_payment", {}).get("structured_biomarkers", []):
            bio_name = b.get("biomarker", "").lower()
            if bio_name:
                lab_tokens.add(bio_name)
        reg["_lab_tokens_lower"] = lab_tokens

        self.regulations.append(reg)
        reg_id = reg["regulation_id"]

        sec_num = reg.get("section_number", "")
        self.index["by_section"][sec_num] = reg_id

        tokens = set(re.findall(r'\w+', full_text_lower))
        for t in tokens:
            self.index["by_keyword"].setdefault(t, set()).add(reg_id)

        labs = reg.get("conditions_of_payment", {}).get("laboratory_criteria", [])
        for lab in labs:
            l_key = lab.lower()
            self.index["by_lab"].setdefault(l_key, set()).add(reg_id)

        for bio in reg.get("conditions_of_payment", {}).get("structured_biomarkers", []):
            b_name = bio.get("biomarker", "").lower()
            if b_name:
                self.index["by_lab"].setdefault(b_name, set()).add(reg_id)
                for tok in b_name.split():
                    self.index["by_keyword"].setdefault(tok, set()).add(reg_id)

    def _parse_biomarker_constraint(self, raw_query):
        """Parse queries like 'eGFR < 30', 'HbA1c >= 8.0', 'PD-L1 >= 50%' into structured filter constraints."""
        if not raw_query:
            return None
        m = re.search(
            r'\b([A-Za-z][A-Za-z0-9\-/]{1,12})\s*(>=|<=|>|<|=|≧|≦|≥|≤)\s*(\d+(?:\.\d+)?)\s*(%|mg/dL|g/dL|mL/min|IU/mL|U/L|mmHg|分|倍)?',
            raw_query,
            flags=re.IGNORECASE
        )
        if not m:
            return None
        raw_bio, raw_op, raw_val, _ = m.groups()
        canon_bio = self.BIOMARKER_QUERY_ALIASES.get(raw_bio.lower())
        if not canon_bio:
            return None
        op_map = {'≧': '>=', '≥': '>=', '≦': '<=', '≤': '<='}
        norm_op = op_map.get(raw_op, raw_op)
        try:
            num_val = float(raw_val)
        except ValueError:
            num_val = None
        return {
            "biomarker": canon_bio,
            "operator": norm_op,
            "value_str": raw_val,
            "value_num": num_val
        }

    def search(self, query, chapter_filter=None, lab_filter=None, disease_query=None):
        query_clean = query.strip() if query else ""
        original_query = query_clean
        disease_query_clean = disease_query.strip() if disease_query else ""

        # Smart compound query parsing for single search bar: e.g. "statins, hyperlipidemia"
        if query_clean and not disease_query_clean:
            parts = [p.strip() for p in re.split(r'[,，;；]+', query_clean) if p.strip()]
            if len(parts) > 1:
                query_clean = parts[0]
                disease_query_clean = parts[1]

        if not query_clean and not disease_query_clean and not chapter_filter and not lab_filter:
            return self.regulations[:50]

        is_pure_section_query = bool(re.match(r'^\d+(\.\d+)+\.?$', query_clean)) and not disease_query_clean

        # Disambiguate renal eGFR vs oncology EGFR
        renal_egfr_intent = False
        oncology_egfr_intent = False
        if 'egfr' in original_query.lower():
            if 'eGFR' in original_query or re.search(r'egfr\s*(?:[><=≧≦≥≤]|\d)|腎|ckd|ml/min|dapagliflozin|empagliflozin', original_query, re.I):
                renal_egfr_intent = True
            elif 'EGFR' in original_query or re.search(r'突變|mutation|exon|tki|lung|肺癌|t790m|l858r', original_query, re.I):
                oncology_egfr_intent = True

        parsed_bio_constraint = self._parse_biomarker_constraint(original_query)

        direct_terms = set()
        expanded_terms = set()
        exact_target_terms = set()
        matched_class_names = set()
        matched_disease_names = set()
        matched_ingredients = set()

        for q_part in [original_query, query_clean, disease_query_clean]:
            if not q_part:
                continue
            q_part_lower = q_part.lower()
            direct_terms.add(q_part_lower)
            expanded_terms.add(q_part_lower)
            exact_target_terms.add(q_part_lower)

            # Do not split section numbers (e.g., "9.138") on dots into noisy integer tokens
            if re.match(r'^\d+(\.\d+)+\.?$', q_part_lower):
                continue

            # Preserve section numbers inside multi-word queries before splitting
            sec_tokens = re.findall(r'\b\d+(?:\.\d+)+\.?\b', q_part_lower)
            for st in sec_tokens:
                exact_target_terms.add(st.strip('.'))

            if parsed_bio_constraint and q_part == original_query:
                canon_b = parsed_bio_constraint["biomarker"].lower()
                direct_terms.add(canon_b)
                expanded_terms.add(canon_b)
                continue

            sub_tokens = re.split(r'[\s,，。;；?？!！_/><=≧≦≥≤%]+', q_part_lower)
            if len(sub_tokens) > 1:
                for token in sub_tokens:
                    t_clean = token.strip('.-')
                    if parsed_bio_constraint and t_clean == parsed_bio_constraint["value_str"]:
                        continue
                    if len(t_clean) > 1 and t_clean not in self.STOPWORDS and not t_clean.isdigit():
                        direct_terms.add(t_clean)
                        expanded_terms.add(t_clean)

        # Universal Alphanumeric Normalization for Lab Criteria & Medical Acronyms
        for q_part in [original_query, query_clean, disease_query_clean]:
            if not q_part:
                continue
            norm_q = re.sub(r'[\s\-_/]+', '', q_part.lower())
            if norm_q in ['hbvdna', 'hbv', 'b型肝炎病毒量', '血清hbvdna']:
                direct_terms.update(['hbv dna', 'hbv-dna', 'hbvdna', 'hbv', 'b型肝炎'])
            elif norm_q in ['hcvrna', 'hcv', 'c型肝炎病毒量']:
                direct_terms.update(['hcv rna', 'hcv-rna', 'hcvrna', 'c型肝炎'])

            if 'gene' in norm_q or 'genetic' in norm_q:
                direct_terms.add('基因')
                expanded_terms.add('基因')
            if 'test' in norm_q or 'detect' in norm_q or 'check' in norm_q or 'report' in norm_q:
                direct_terms.update(['檢測', '檢查', '報告'])
                expanded_terms.update(['檢測', '檢查', '報告'])

        # ATC Expansion (run on drug/primary query unless it's a pure section number or biomarker constraint)
        atc_expansions = []
        if query_clean and not is_pure_section_query and not parsed_bio_constraint:
            atc_expansions = self.atc_engine.expand_query(query_clean)
            q_clean_low = query_clean.lower()
            for exp in atc_expansions:
                expanded_terms.add(exp["atc_code"].lower())
                expanded_terms.add(exp["class_code"].lower())
                expanded_terms.add(exp["class_name_en"].lower())
                expanded_terms.add(exp["class_name_tc"].lower())
                matched_class_names.add(exp["class_name_tc"].lower())

                for alias in exp.get("aliases", []):
                    if alias and len(alias) > 1:
                        expanded_terms.add(alias.lower())

                ing_en = exp.get("ingredient_en", "").lower()
                ing_tc = exp.get("ingredient_tc", "").lower()
                brand_en = exp.get("brand_en", "").lower()
                brand_tc = [b.lower() for b in exp.get("brand_tc", [])]

                if ing_en:
                    matched_ingredients.add(ing_en)
                    direct_terms.add(ing_en)
                if ing_tc:
                    matched_ingredients.add(ing_tc)
                    direct_terms.add(ing_tc)

                is_matching_specific = (
                    q_clean_low in ing_en or
                    q_clean_low in ing_tc or
                    (brand_en and q_clean_low in brand_en) or
                    any(q_clean_low in b for b in brand_tc) or
                    q_clean_low == exp["atc_code"].lower()
                )

                if is_matching_specific:
                    if ing_en:
                        exact_target_terms.add(ing_en)
                    if ing_tc:
                        exact_target_terms.add(ing_tc)
                    if brand_en:
                        for b_part in brand_en.split(','):
                            b_p = b_part.strip()
                            if b_p:
                                exact_target_terms.add(b_p)
                    for b in brand_tc:
                        exact_target_terms.add(b)

        # Disease Expansion
        disease_expansions = []
        if not is_pure_section_query:
            for q_segment in [original_query, query_clean, disease_query_clean]:
                if q_segment:
                    disease_expansions.extend(self.disease_engine.expand_query(q_segment))
                    norm_disease_q = re.sub(r'[\s\-_/]+', '', q_segment.lower())
                    if norm_disease_q in ['hbvdna', 'hbvdna量']:
                        disease_expansions.extend(self.disease_engine.expand_query('hbv'))

        seen_disease_keys = set()
        for de in disease_expansions:
            if de["disease_key"] not in seen_disease_keys:
                seen_disease_keys.add(de["disease_key"])
                expanded_terms.add(de["english_name"].lower())
                matched_disease_names.add(de["english_name"].lower())
                for alias in de["aliases"]:
                    expanded_terms.add(alias.lower())
                for tc in de["chinese_terms"]:
                    expanded_terms.add(tc.lower())
                    matched_disease_names.add(tc.lower())

        primary_regulations = set([exp["primary_regulation"] for exp in atc_expansions if exp.get("primary_regulation")])

        def check_match(term, text):
            if re.match(r'^[a-z0-9\-]+$', term):
                return bool(self._get_word_regex(term).search(text))
            return term in text

        results = []
        lab_filter_lower = lab_filter.lower() if lab_filter else None
        lab_filter_targets = self.LAB_FILTER_GROUP_MAP.get(lab_filter_lower, {lab_filter_lower}) if lab_filter_lower else None

        for reg in self.regulations:
            if chapter_filter and chapter_filter not in reg["chapter"]:
                continue

            if lab_filter_lower:
                if lab_filter_lower == "prior_auth":
                    if not reg.get("conditions_of_payment", {}).get("prior_authorization_required"):
                        continue
                else:
                    if not (reg["_lab_tokens_lower"] & lab_filter_targets):
                        continue

            if not query_clean and not disease_query_clean:
                results.append((reg, 1.0))
                continue

            title_lower = reg["_title_lower"]
            full_text = reg["_full_text_lower"]
            norm_full_text = reg["norm_full_text"]
            reg_classes = reg["_classes_lower"]
            reg_ingredients = reg["_ingredients_lower"]
            reg_indications = reg["_indications_lower"]
            sec_clean = reg["section_number"].strip('.').lower()

            score = 0

            # If pure section query (e.g. "9.138" or "9.124."), only return exact or subsection matches!
            if is_pure_section_query:
                q_sec = query_clean.strip('.').lower()
                if sec_clean == q_sec:
                    results.append((reg, 10000))
                elif sec_clean.startswith(q_sec + '.'):
                    results.append((reg, 5000))
                continue

            # Exact section number check (from full query)
            if query_clean and query_clean.lower().strip('.') == sec_clean:
                score += 5000

            # Direct section number token matching boost
            for term in exact_target_terms:
                if re.match(r'^\d+(\.\d+)+\.?$', term):
                    term_clean = term.strip('.')
                    if sec_clean == term_clean:
                        score += 5000
                    elif sec_clean.startswith(term_clean + '.'):
                        score += 3000

            # Primary regulation mapping boost
            for pr in primary_regulations:
                pr_clean = pr.strip('.').lower()
                if sec_clean == pr_clean or sec_clean.startswith(pr_clean + '.'):
                    score += 1500
                    break

            # Priority boost for exact isolated brand/molecule matches in title or text
            for et in exact_target_terms:
                if et and len(et) > 1:
                    if check_match(et, title_lower):
                        score += 1800
                    elif check_match(et, full_text):
                        score += 500

            for dt in direct_terms:
                if dt and len(dt) > 1:
                    if check_match(dt, title_lower):
                        score += 100
                    elif check_match(dt, full_text):
                        score += 40

            for mdn in matched_disease_names:
                if any(mdn in ind for ind in reg_indications):
                    score += 100

            for mc in matched_class_names:
                if any(mc in rc or rc in mc for rc in reg_classes):
                    score += 50

            for dt in direct_terms:
                if dt and len(dt) > 1:
                    if any(dt in ing for ing in reg_ingredients):
                        score += 1000
                        break

            for dt in direct_terms:
                if dt and len(dt) > 1:
                    if any(dt in cls for cls in reg_classes):
                        score += 800
                        break

            for q_part in [query_clean, disease_query_clean]:
                if not q_part:
                    continue
                norm_q = re.sub(r'[\s\-_/]+', '', q_part.lower())
                if len(norm_q) >= 3 and norm_q in norm_full_text:
                    score += 40

            # Match on prior authorization intent
            if any(pa_kw in direct_terms for pa_kw in ['事前審查', '事前核准', '專案申請', '事前申請']):
                if reg.get("conditions_of_payment", {}).get("prior_authorization_required"):
                    score += 600

            # Structured biomarker & quantitative constraint scoring
            struct_bios = reg.get("conditions_of_payment", {}).get("structured_biomarkers", [])
            bio_names_exact = {b.get("biomarker", "") for b in struct_bios}

            if renal_egfr_intent:
                if "eGFR" in bio_names_exact or "腎絲球過濾率" in full_text or "慢性腎臟病" in full_text:
                    score += 900
                elif "EGFR" in bio_names_exact and "egfr" not in [b.get("biomarker", "") for b in struct_bios]:
                    score -= 400
            elif oncology_egfr_intent:
                if "EGFR" in bio_names_exact:
                    score += 900

            if parsed_bio_constraint:
                target_bio = parsed_bio_constraint["biomarker"]
                target_val = parsed_bio_constraint["value_num"]
                target_str = parsed_bio_constraint["value_str"]
                matched_bio_in_reg = False
                for b in struct_bios:
                    if b.get("biomarker", "").lower() == target_bio.lower():
                        # Exact case check for eGFR vs EGFR
                        if target_bio == "eGFR" and b.get("biomarker") != "eGFR":
                            continue
                        matched_bio_in_reg = True
                        score += 1200
                        b_val_str = str(b.get("value", ""))
                        if target_str in b_val_str:
                            score += 900
                        elif target_val is not None:
                            nums = [float(x) for x in re.findall(r'\d+(?:\.\d+)?', b_val_str)]
                            if len(nums) == 2 and nums[0] <= target_val <= nums[1]:
                                score += 600
                            elif len(nums) == 1 and abs(nums[0] - target_val) <= 15:
                                score += 350
                if not matched_bio_in_reg and not disease_query_clean:
                    continue

            for bio in struct_bios:
                b_name = bio.get("biomarker", "").lower()
                b_val = str(bio.get("value", "")).lower()
                if b_name and any(b_name in dt for dt in direct_terms):
                    score += 80
                if b_val and any(b_val == dt for dt in direct_terms):
                    score += 60

            for term in expanded_terms:
                if term and len(term) > 1:
                    if check_match(term, full_text):
                        if check_match(term, title_lower):
                            score += 30
                        else:
                            score += 5

            if score > 0:
                results.append((reg, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results]


if __name__ == "__main__":
    indexer = NHIIndexer()
    print(f"Total indexed regulations: {len(indexer.regulations)}")
