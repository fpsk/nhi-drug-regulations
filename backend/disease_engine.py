import re
from backend.disease_data import DISEASE_DATABASE


class DiseaseEngine:
    def __init__(self):
        self.disease_db = DISEASE_DATABASE

    def expand_query(self, query):
        """Given a query in English or Chinese, return matching disease entries using word boundary and substring matching."""
        q_clean = query.strip().lower()
        if not q_clean:
            return []

        matched_keys = set()
        is_q_chinese = any(ord(c) > 127 for c in q_clean)

        for key, info in self.disease_db.items():
            terms_to_check = [info["en"]] + info["aliases"] + info["tc_terms"]
            for term in terms_to_check:
                t_clean = term.lower()
                is_t_chinese = any(ord(c) > 127 for c in t_clean)

                if is_q_chinese or is_t_chinese:
                    # For Chinese, require >= 2 chars or exact match to prevent single char clutter
                    if q_clean in t_clean or t_clean in q_clean:
                        if len(q_clean) >= 2 or q_clean == t_clean:
                            matched_keys.add(key)
                            break
                else:
                    # For English, use exact match for short queries or word boundary search
                    if len(q_clean) <= 2:
                        if q_clean == t_clean or any(q_clean == a.lower() for a in info["aliases"]):
                            matched_keys.add(key)
                            break
                    else:
                        if re.search(r'\b' + re.escape(q_clean) + r'\b', t_clean) or re.search(r'\b' + re.escape(t_clean) + r'\b', q_clean):
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
