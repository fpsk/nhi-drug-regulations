import re
from backend.disease_data import DISEASE_DATABASE


class DiseaseEngine:
    ENGLISH_STOPWORDS = {
        "of", "the", "in", "on", "for", "with", "and", "or", "a", "an", "to", "by", "from", "at"
    }

    TOKEN_SYNONYMS = {
        "carcinoma": "cancer",
        "tumour": "tumor",
        "tumours": "tumors",
        "haemorrhage": "hemorrhage",
        "oesophageal": "esophageal",
        "oesophagus": "esophagus",
        "leukaemia": "leukemia",
        "paediatric": "pediatric",
        "pulmonary": "lung",
        "hepatic": "liver",
        "gastric": "stomach",
        "mammary": "breast",
    }

    NEGATED_TC_TERMS = {"小細胞肺癌", "鱗狀非小細胞肺癌", "何杰金氏淋巴瘤", "霍奇金淋巴瘤"}

    def __init__(self):
        self.disease_db = DISEASE_DATABASE

    @classmethod
    def _tokenize_english(cls, text, normalize_synonyms=False):
        tokens = [
            t for t in re.findall(r'[a-z0-9]+', text.lower())
            if t not in cls.ENGLISH_STOPWORDS
        ]
        if not normalize_synonyms:
            return set(tokens)
        return {cls.TOKEN_SYNONYMS.get(t, t) for t in tokens}

    @classmethod
    def _has_negation_conflict(cls, q_clean, t_clean, q_tokens=None, t_tokens=None):
        if "non" not in q_clean and "non" not in t_clean:
            return False
        q_negated = set(re.findall(r'\bnon[\s\-]+([a-z0-9]+)', q_clean))
        t_negated = set(re.findall(r'\bnon[\s\-]+([a-z0-9]+)', t_clean))
        if q_tokens is None:
            q_tokens = cls._tokenize_english(q_clean)
        if t_tokens is None:
            t_tokens = cls._tokenize_english(t_clean)
        for w in q_negated:
            if w in t_tokens and w not in t_negated:
                return True
        for w in t_negated:
            if w in q_tokens and w not in q_negated:
                return True
        return False

    @classmethod
    def matches_chinese_term(cls, tc_term, text):
        if tc_term in cls.NEGATED_TC_TERMS:
            return bool(re.search(r'(?<!非)' + re.escape(tc_term), text))
        return tc_term in text

    def expand_query(self, query):
        """Given a query in English or Chinese, return matching disease entries using phrase, token-set, and substring matching."""
        q_clean = query.strip().lower()
        if not q_clean:
            return []

        matched_keys = set()
        is_q_chinese = any(ord(c) > 127 for c in q_clean)
        q_tokens_raw = self._tokenize_english(q_clean, normalize_synonyms=False) if not is_q_chinese else set()

        for key, info in self.disease_db.items():
            terms_to_check = [info["en"]] + info["aliases"] + info["tc_terms"]
            for term in terms_to_check:
                t_clean = term.lower()
                is_t_chinese = any(ord(c) > 127 for c in t_clean)

                if is_q_chinese or is_t_chinese:
                    if q_clean in t_clean or t_clean in q_clean:
                        if len(q_clean) >= 2 or q_clean == t_clean:
                            if q_clean in self.NEGATED_TC_TERMS and ("非" + q_clean) in t_clean:
                                continue
                            if t_clean in self.NEGATED_TC_TERMS and ("非" + t_clean) in q_clean:
                                continue
                            matched_keys.add(key)
                            break
                else:
                    if len(q_clean) <= 2:
                        if q_clean == t_clean or any(q_clean == a.lower() for a in info["aliases"]):
                            matched_keys.add(key)
                            break
                    else:
                        t_tokens_raw = self._tokenize_english(t_clean, normalize_synonyms=False)
                        if re.search(r'\b' + re.escape(q_clean) + r'\b', t_clean) or re.search(r'\b' + re.escape(t_clean) + r'\b', q_clean):
                            if self._has_negation_conflict(q_clean, t_clean, q_tokens_raw, t_tokens_raw):
                                continue
                            matched_keys.add(key)
                            break
                        # Order-independent token-set match (e.g. "adenocarcinoma of lung" <-> "lung adenocarcinoma")
                        if len(t_tokens_raw) >= 2 and len(q_tokens_raw) >= 2:
                            if not self._has_negation_conflict(q_clean, t_clean, q_tokens_raw, t_tokens_raw) and t_tokens_raw.issubset(q_tokens_raw):
                                matched_keys.add(key)
                                break

        # Fallback pass with medical synonym normalization (e.g., "carcinoma of the lung" -> "lung cancer")
        if not matched_keys and not is_q_chinese and len(q_tokens_raw) >= 2:
            q_tokens_norm = self._tokenize_english(q_clean, normalize_synonyms=True)
            for key, info in self.disease_db.items():
                for term in [info["en"]] + info["aliases"]:
                    t_clean = term.lower()
                    t_tokens_norm = self._tokenize_english(t_clean, normalize_synonyms=True)
                    if len(t_tokens_norm) >= 2 and not self._has_negation_conflict(q_clean, t_clean, q_tokens_norm, t_tokens_norm):
                        if t_tokens_norm.issubset(q_tokens_norm):
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
                if self.matches_chinese_term(tc, text):
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
    print("Expand query 'adenocarcinoma of lung':", engine.expand_query("adenocarcinoma of lung"))
