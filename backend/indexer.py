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

    PRIOR_AUTH_KEYWORDS = ('事前審查', '事前核准', '專案申請', '事前申請')

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
            pat = re.compile(r'(?<![a-z0-9])' + re.escape(term) + r'(?![a-z0-9])')
            self._compiled_word_regex[term] = pat
        return pat

    def _matches_term(self, term, text):
        if re.match(r'^[a-z0-9\-]+$', term):
            return bool(self._get_word_regex(term).search(text))
        return term in text

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
        # Drop duplicate per-indication clinical_rules list from memory
        reg.get("conditions_of_payment", {}).pop("clinical_rules", None)

        title_str = reg.get("section_title", "")
        body_str = reg.get("reference_annotations", {}).get("full_text", "")
        full_text = f"{title_str} {body_str}"
        full_text_lower = full_text.lower()
        title_lower = title_str.lower()

        reg["norm_full_text"] = re.sub(r'[\s\-_/]+', '', full_text_lower)
        reg["_title_lower"] = title_lower
        reg["_body_lower"] = body_str.lower()
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

        for t in set(re.findall(r'\w+', full_text_lower)):
            self.index["by_keyword"].setdefault(t, set()).add(reg_id)

        for lab in reg.get("conditions_of_payment", {}).get("laboratory_criteria", []):
            self.index["by_lab"].setdefault(lab.lower(), set()).add(reg_id)

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
        q_str = query.strip() if query else ""
        d_str = disease_query.strip() if disease_query else ""
        combined_query = f"{q_str}, {d_str}".strip(", ") if (q_str and d_str) else (q_str or d_str)

        segments = [s.strip() for s in re.split(r'[,，;；]+', combined_query) if s.strip()] if combined_query else []

        if not segments and not chapter_filter and not lab_filter:
            return self.regulations[:50]

        lab_filter_lower = lab_filter.lower() if lab_filter else None
        lab_filter_targets = self.LAB_FILTER_GROUP_MAP.get(lab_filter_lower, {lab_filter_lower}) if lab_filter_lower else None

        candidate_regs = []
        for reg in self.regulations:
            if chapter_filter and chapter_filter not in reg["chapter"]:
                continue
            if lab_filter_lower:
                if lab_filter_lower == "prior_auth":
                    if not reg.get("conditions_of_payment", {}).get("prior_authorization_required"):
                        continue
                elif not (reg["_lab_tokens_lower"] & lab_filter_targets):
                    continue
            candidate_regs.append(reg)

        if not segments:
            return candidate_regs

        if len(segments) == 1:
            scored = self._score_single_segment(segments[0], candidate_regs, full_query_context=combined_query, is_multi_segment=False)
            scored.sort(key=lambda x: x[1], reverse=True)
            return [r[0] for r in scored]

        # Multi-segment comma-separated search: order-independent AND intersection across all segments
        score_map = {}
        current_candidates = candidate_regs
        for seg in segments:
            seg_scored = self._score_single_segment(seg, current_candidates, full_query_context=combined_query, is_multi_segment=True)
            if not seg_scored:
                return []
            next_candidates = []
            for reg, sc in seg_scored:
                rid = reg["regulation_id"]
                score_map[rid] = score_map.get(rid, 0) + sc
                next_candidates.append(reg)
            current_candidates = next_candidates

        current_candidates.sort(key=lambda r: score_map[r["regulation_id"]], reverse=True)
        return current_candidates

    def _expand_segment_context(self, seg_query, full_query_context=""):
        query_clean = seg_query.strip()
        original_query = full_query_context or query_clean
        is_pure_section_query = bool(re.match(r'^\d+(\.\d+)+\.?$', query_clean))

        renal_egfr_intent = False
        oncology_egfr_intent = False
        if 'egfr' in query_clean.lower():
            if 'eGFR' in query_clean or re.search(r'egfr\s*(?:[><=≧≦≥≤]|\d)|腎|ckd|心衰竭|心臟衰竭|ml/min|dapagliflozin|empagliflozin|forxiga|jardiance', original_query, re.I):
                renal_egfr_intent = True
            elif 'EGFR' in query_clean or re.search(r'突變|mutation|exon|tki|lung|肺癌|t790m|l858r', original_query, re.I):
                oncology_egfr_intent = True

        parsed_bio_constraint = self._parse_biomarker_constraint(query_clean)

        direct_terms = set()
        expanded_terms = set()
        exact_target_terms = set()
        matched_class_names = set()
        matched_disease_names = set()

        q_part_lower = query_clean.lower()
        direct_terms.add(q_part_lower)
        expanded_terms.add(q_part_lower)
        exact_target_terms.add(q_part_lower)

        if not is_pure_section_query:
            for st in re.findall(r'\b\d+(?:\.\d+)+\.?\b', q_part_lower):
                exact_target_terms.add(st.strip('.'))

            if parsed_bio_constraint:
                canon_b = parsed_bio_constraint["biomarker"].lower()
                direct_terms.add(canon_b)
                expanded_terms.add(canon_b)
            else:
                sub_tokens = re.split(r'[\s,，。;；?？!！_/><=≧≦≥≤%]+', q_part_lower)
                if len(sub_tokens) > 1:
                    for token in sub_tokens:
                        t_clean = token.strip('.-')
                        if len(t_clean) > 1 and t_clean not in self.STOPWORDS and not t_clean.isdigit():
                            direct_terms.add(t_clean)
                            expanded_terms.add(t_clean)

        norm_q = re.sub(r'[\s\-_/]+', '', q_part_lower)
        if norm_q in ['hbvdna', 'hbv', 'b型肝炎病毒量', '血清hbvdna']:
            direct_terms.update(['hbv dna', 'hbv-dna', 'hbvdna', 'hbv', 'b型肝炎'])
        elif norm_q in ['hcvrna', 'hcv', 'c型肝炎病毒量']:
            direct_terms.update(['hcv rna', 'hcv-rna', 'hcvrna', 'c型肝炎'])

        if 'gene' in norm_q or 'genetic' in norm_q:
            direct_terms.add('基因')
            expanded_terms.add('基因')
        if any(k in norm_q for k in ('test', 'detect', 'check', 'report')):
            direct_terms.update(['檢測', '檢查', '報告'])
            expanded_terms.update(['檢測', '檢查', '報告'])

        atc_expansions = []
        if query_clean and not is_pure_section_query and not parsed_bio_constraint:
            atc_expansions = self.atc_engine.expand_query(query_clean)
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
                    direct_terms.add(ing_en)
                if ing_tc:
                    direct_terms.add(ing_tc)

                is_matching_specific = (
                    q_part_lower in ing_en or
                    q_part_lower in ing_tc or
                    (brand_en and q_part_lower in brand_en) or
                    any(q_part_lower in b for b in brand_tc) or
                    q_part_lower == exp["atc_code"].lower()
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

        disease_expansions = []
        if not is_pure_section_query:
            disease_expansions.extend(self.disease_engine.expand_query(query_clean))
            if norm_q in ['hbvdna', 'hbvdna量']:
                disease_expansions.extend(self.disease_engine.expand_query('hbv'))

        seen_disease_keys = set()
        unique_disease_groups = []
        for de in disease_expansions:
            if de["disease_key"] not in seen_disease_keys:
                seen_disease_keys.add(de["disease_key"])
                expanded_terms.add(de["english_name"].lower())
                matched_disease_names.add(de["english_name"].lower())
                grp_terms = []
                for alias in de["aliases"]:
                    expanded_terms.add(alias.lower())
                    if len(alias) >= 3:
                        grp_terms.append(alias.lower())
                for tc in de["chinese_terms"]:
                    expanded_terms.add(tc.lower())
                    matched_disease_names.add(tc.lower())
                    grp_terms.append(tc.lower())
                if grp_terms:
                    unique_disease_groups.append(grp_terms)

        primary_regulations = {exp["primary_regulation"] for exp in atc_expansions if exp.get("primary_regulation")}

        return {
            "query_clean": query_clean,
            "norm_q": norm_q,
            "is_pure_section_query": is_pure_section_query,
            "renal_egfr_intent": renal_egfr_intent,
            "oncology_egfr_intent": oncology_egfr_intent,
            "parsed_bio_constraint": parsed_bio_constraint,
            "direct_terms": direct_terms,
            "expanded_terms": expanded_terms,
            "exact_target_terms": exact_target_terms,
            "matched_class_names": matched_class_names,
            "matched_disease_names": matched_disease_names,
            "unique_disease_groups": unique_disease_groups,
            "atc_expansions": atc_expansions,
            "primary_regulations": primary_regulations,
        }

    def _score_single_segment(self, seg_query, candidate_regs, full_query_context="", is_multi_segment=False):
        ctx = self._expand_segment_context(seg_query, full_query_context=full_query_context)
        min_score_threshold = 30 if (is_multi_segment and ctx["atc_expansions"] and not ctx["matched_disease_names"]) else 1
        results = []

        for reg in candidate_regs:
            title_lower = reg["_title_lower"]
            body_lower = reg["_body_lower"]
            full_text = reg["_full_text_lower"]
            norm_full_text = reg["norm_full_text"]
            reg_classes = reg["_classes_lower"]
            reg_ingredients = reg["_ingredients_lower"]
            reg_indications = reg["_indications_lower"]
            sec_clean = reg["section_number"].strip('.').lower()

            if ctx["is_pure_section_query"]:
                q_sec = ctx["query_clean"].strip('.').lower()
                if sec_clean == q_sec:
                    results.append((reg, 10000, 0))
                elif sec_clean.startswith(q_sec + '.'):
                    results.append((reg, 5000, 0))
                continue

            score = 0

            if ctx["query_clean"] and ctx["query_clean"].lower().strip('.') == sec_clean:
                score += 5000

            for term in ctx["exact_target_terms"]:
                if re.match(r'^\d+(\.\d+)+\.?$', term):
                    term_clean = term.strip('.')
                    if sec_clean == term_clean:
                        score += 5000
                    elif sec_clean.startswith(term_clean + '.'):
                        score += 3000

            for pr in ctx["primary_regulations"]:
                pr_clean = pr.strip('.').lower()
                if sec_clean == pr_clean or sec_clean.startswith(pr_clean + '.'):
                    score += 1500
                    break

            for et in ctx["exact_target_terms"]:
                if et and len(et) > 1:
                    if self._matches_term(et, title_lower):
                        score += 1800
                    elif self._matches_term(et, full_text):
                        score += 500

            for dt in ctx["direct_terms"]:
                if dt and len(dt) > 1:
                    if self._matches_term(dt, title_lower):
                        score += 100
                    elif self._matches_term(dt, full_text):
                        score += 40

            for mdn in ctx["matched_disease_names"]:
                if any(mdn in ind for ind in reg_indications):
                    score += 100
                if mdn in title_lower:
                    score += 350
                first_lines_lower = "\n".join(body_lower.split('\n', 2)[:2])
                if mdn in first_lines_lower:
                    score += 260
                occ = body_lower.count(mdn)
                if occ > 0:
                    score += min(occ, 8) * 35

            matched_disease_group_count = 0
            if ctx["unique_disease_groups"]:
                for grp in ctx["unique_disease_groups"]:
                    if any(self._matches_term(gt, full_text) for gt in grp):
                        matched_disease_group_count += 1
                if len(ctx["unique_disease_groups"]) >= 2 and matched_disease_group_count >= 2:
                    score += matched_disease_group_count * 700

            for mc in ctx["matched_class_names"]:
                if any(mc in rc or rc in mc for rc in reg_classes):
                    score += 50

            for dt in ctx["direct_terms"]:
                if dt and len(dt) > 1 and any(self._matches_term(dt, ing) for ing in reg_ingredients):
                    score += 1000
                    break

            for dt in ctx["direct_terms"]:
                if dt and len(dt) > 1 and any(self._matches_term(dt, cls) for cls in reg_classes):
                    score += 800
                    break

            if len(ctx["norm_q"]) >= 3 and ctx["norm_q"] in norm_full_text:
                score += 40

            if any(pa_kw in ctx["direct_terms"] for pa_kw in self.PRIOR_AUTH_KEYWORDS):
                if reg.get("conditions_of_payment", {}).get("prior_authorization_required"):
                    score += 600

            struct_bios = reg.get("conditions_of_payment", {}).get("structured_biomarkers", [])
            bio_names_exact = {b.get("biomarker", "") for b in struct_bios}

            if ctx["renal_egfr_intent"]:
                if "eGFR" in bio_names_exact or "腎絲球過濾率" in full_text or "慢性腎臟病" in full_text:
                    score += 900
                elif "EGFR" in bio_names_exact and "eGFR" not in bio_names_exact:
                    score -= 400
            elif ctx["oncology_egfr_intent"]:
                if "EGFR" in bio_names_exact:
                    score += 900

            parsed_bio = ctx["parsed_bio_constraint"]
            if parsed_bio:
                target_bio = parsed_bio["biomarker"]
                target_val = parsed_bio["value_num"]
                target_str = parsed_bio["value_str"]
                matched_bio_in_reg = False
                for b in struct_bios:
                    if b.get("biomarker", "").lower() == target_bio.lower():
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
                if not matched_bio_in_reg:
                    continue

            for bio in struct_bios:
                b_name = bio.get("biomarker", "").lower()
                b_val = str(bio.get("value", "")).lower()
                if b_name and any(b_name in dt for dt in ctx["direct_terms"]):
                    score += 80
                if b_val and any(b_val == dt for dt in ctx["direct_terms"]):
                    score += 60

            for term in ctx["expanded_terms"]:
                if term and len(term) > 1 and self._matches_term(term, full_text):
                    score += 30 if self._matches_term(term, title_lower) else 5

            if score >= min_score_threshold:
                results.append((reg, score, matched_disease_group_count))

        if len(ctx["unique_disease_groups"]) >= 2 and not ctx["atc_expansions"] and results:
            max_grp = max(r[2] for r in results)
            if max_grp >= 2:
                results = [r for r in results if r[2] >= 2]

        return [(r[0], r[1]) for r in results]

    def get_highlight_terms(self, query):
        """Return ordered bilingual (Chinese + English) highlight terms for all comma-separated query segments."""
        if not query or not query.strip():
            return []
        modifier_keys = {"metastatic_advanced", "prophylaxis_prevention"}
        primary_terms = []
        modifier_terms = []
        seen = set()

        def add_term(t, is_modifier=False):
            if not t:
                return
            t_clean = t.strip()
            if len(t_clean) < 2 or t_clean.lower() in self.STOPWORDS:
                return
            low = t_clean.lower()
            if low not in seen:
                seen.add(low)
                if is_modifier:
                    modifier_terms.append(t_clean)
                else:
                    primary_terms.append(t_clean)

        for seg in re.split(r'[,，;；]+', query):
            seg_clean = seg.strip()
            if not seg_clean or re.match(r'^\d+(\.\d+)+\.?$', seg_clean):
                continue

            for de in self.disease_engine.expand_query(seg_clean):
                if de["disease_key"] == "metastatic_advanced":
                    s_low = seg_clean.lower()
                    if "metastatic" in s_low or "轉移" in s_low:
                        add_term("轉移性", is_modifier=True)
                    if "locally advanced" in s_low or "局部晚期" in s_low:
                        add_term("局部晚期", is_modifier=True)
                    if "unresectable" in s_low or "無法切除" in s_low:
                        add_term("無法切除", is_modifier=True)
                        add_term("無法手術切除", is_modifier=True)
                    if "recurrent" in s_low or "relapsed" in s_low or "復發" in s_low:
                        add_term("復發性", is_modifier=True)
                    continue
                is_mod = de["disease_key"] in modifier_keys
                for tc in de["chinese_terms"]:
                    add_term(tc, is_modifier=is_mod)

            for exp in self.atc_engine.expand_query(seg_clean):
                ing_en = exp.get("ingredient_en", "")
                ing_tc = exp.get("ingredient_tc", "")
                brand_en = exp.get("brand_en", "")
                if ing_en:
                    add_term(ing_en)
                if ing_tc:
                    add_term(ing_tc)
                if brand_en:
                    for b in brand_en.split(','):
                        add_term(b.strip())
                for btc in exp.get("brand_tc", []):
                    add_term(btc)

            bio_c = self._parse_biomarker_constraint(seg_clean)
            if bio_c:
                add_term(bio_c["biomarker"])

            if any(ord(c) > 127 for c in seg_clean) or len(seg_clean.split()) <= 2:
                add_term(seg_clean)

        return primary_terms + modifier_terms


if __name__ == "__main__":
    indexer = NHIIndexer()
    print(f"Total indexed regulations: {len(indexer.regulations)}")
