import os
import re
import sqlite3
from backend.who_atc_database import WHO_ATC_DATABASE
from backend.atc_data import (
    ATC_DATABASE,
    CLASS_REGULATION_MAPPING,
    CLASS_LEVEL_ENRICH_CODES,
)


class ATCEngine:
    GENERIC_BASE_STOPWORDS = {
        "sodium", "calcium", "potassium", "magnesium", "human", "extract",
        "solution", "water", "glucose", "vitamin", "compound", "normal",
        "sterile", "purified", "dried", "activated"
    }

    EXTRACTION_STOPWORDS = {
        "level", "stage", "class", "grade", "score", "type", "phase", "group", "table",
        "child-pugh", "nyha", "ecog", "era", "sglt2", "sglt-2", "nsaid", "nsaids", "dmard", "dmards",
        "immune", "factor", "recombinant", "human", "tablets", "injection", "solution", "capsules"
    }

    DOSAGE_FORM_TOKENS = (
        '膜衣錠', '糖衣錠', '緩釋錠', '持續錠', '咀嚼錠', '舌下錠', '錠',
        '軟膠囊', '硬膠囊', '持續性膠囊', '膠囊',
        '濃縮注射液', '乾粉注射劑', '注射液', '注射劑', '針劑',
        '點眼液', '點鼻液', '吸入劑', '噴霧劑', '乳膏', '軟膏', '凝膠', '藥膏',
        '毫克', '微克', '公克', '公絲', '公撮', '國際單位', '毫升'
    )

    def __init__(self):
        self.atc_db = ATC_DATABASE
        self.who_db = WHO_ATC_DATABASE
        self._expand_cache = {}
        self._fuzzy_vocab = None  # Lazy-initialized bucketed vocabulary from SQLite
        self._db_ingredients_map = None  # Lazy-initialized ingredient -> Chinese/ATC map

    def _ensure_vocab_loaded(self):
        """Load distinct English brand tokens and generic ingredients once into memory buckets by first character."""
        if self._fuzzy_vocab is not None:
            return
        self._fuzzy_vocab = {}
        self._db_ingredients_map = {}
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT english_name, ingredient, chinese_name, atc_code FROM nhi_drugs")
            for eng, ing, chi, atc in cursor.fetchall():
                if eng:
                    first = eng.split()[0].lower()
                    if len(first) >= 4 and first.isalpha():
                        self._fuzzy_vocab.setdefault(first[0], set()).add(('english_name', first))
                if ing:
                    ing_low = ing.strip().lower()
                    if len(ing_low) >= 4:
                        self._fuzzy_vocab.setdefault(ing_low[0], set()).add(('ingredient', ing_low))
                        if ing_low not in self._db_ingredients_map and atc:
                            self._db_ingredients_map[ing_low] = {
                                "en": ing.strip().title(),
                                "tc": self.clean_taiwan_brand(chi) if chi else "",
                                "atc": atc
                            }
                        ing_base = ing_low.split()[0]
                        if (
                            len(ing_base) >= 5
                            and ing_base.isalpha()
                            and ing_base not in self.GENERIC_BASE_STOPWORDS
                            and ing_base not in self._db_ingredients_map
                            and atc
                        ):
                            self._db_ingredients_map[ing_base] = {
                                "en": ing_base.title(),
                                "tc": self.clean_taiwan_brand(chi) if chi else "",
                                "atc": atc
                            }
            conn.close()
        except Exception:
            pass

    def parse_brand(self, brand_str):
        if not brand_str:
            return "", []
        match = re.match(r'^([^\(]+)\s*\((.*?)\)', brand_str)
        if match:
            brand_en = match.group(1).strip()
            parts = [p.strip() for p in match.group(2).split('/')]
            brand_tc = [p for p in parts if any(ord(c) > 127 for c in p)]
            if not brand_tc:
                brand_tc = [p for p in parts if p.lower() != brand_en.lower()]
            return brand_en, brand_tc
        return brand_str.strip(), []

    def levenshtein_distance(self, s1, s2):
        if abs(len(s1) - len(s2)) > 2:
            return 3
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        if len(s2) == 0:
            return len(s1)
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            min_in_row = current_row[0]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                val = insertions if insertions < deletions else deletions
                if substitutions < val:
                    val = substitutions
                current_row.append(val)
                if val < min_in_row:
                    min_in_row = val
            if min_in_row > 2:
                return 3
            previous_row = current_row
        return previous_row[-1]

    def is_fuzzy_match(self, q, target):
        q = q.lower()
        target = target.lower()
        if len(q) < 4 or len(target) < 4:
            return q == target
        if abs(len(q) - len(target)) > 2:
            return False

        if self.levenshtein_distance(q, target) <= 2:
            return True

        if abs(len(q) - len(target)) <= 1:
            s1, s2 = set(q), set(target)
            union = len(s1 | s2)
            if union > 0 and (len(s1 & s2) / union) >= 0.85:
                return True
        return False

    def clean_taiwan_brand(self, name):
        if not name:
            return ""
        parts = [p.strip() for p in re.split(r'[\"\'”’“‘]', name) if p.strip()]
        part = parts[-1] if parts else name
        part = re.sub(r'[\(（].*?[\)）]', '', part)
        for word in self.DOSAGE_FORM_TOKENS:
            part = part.replace(word, '')
        part = re.sub(r'[A-Za-z0-9\.\-\%\/\s\+\,\*\#\_]+', '', part)
        part = re.sub(r'[０-９ａ-ｚＡ-Ｚ％（）＆＋，。]+', '', part)
        return part.strip()

    def get_db_connection(self):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nhi_drugs.db')
        return sqlite3.connect(db_path)

    def expand_query(self, query):
        """Given a search query, return matching ATC classes and their associated ingredients with rich metadata and fast spelling tolerance."""
        q_clean = query.strip().lower()
        if not q_clean:
            return []

        if q_clean in self._expand_cache:
            return self._expand_cache[q_clean]

        # Skip ATC drug expansion for pure section numbers (e.g., "9.124", "2.16.")
        if re.match(r'^\d+(\.\d+)+\.?$', q_clean):
            self._expand_cache[q_clean] = []
            return []

        matched_expansions = []

        # Step 1: Check WHO ATC Database first for exact/curated 7-char ATC, ingredient, or brand matches
        for atc7, winfo in self.who_db.items():
            atc_code = winfo.get("atc7", atc7)
            class_code = winfo.get("atc5", atc_code[:5])
            brand_str = winfo.get("brand", "")
            en_name = winfo.get("en", "")
            tc_name = winfo.get("tc", "")

            match = (
                q_clean == atc_code.lower() or
                q_clean == class_code.lower() or
                (len(q_clean) >= 3 and q_clean in en_name.lower()) or
                (len(q_clean) >= 2 and q_clean in tc_name.lower()) or
                (len(q_clean) >= 3 and q_clean in brand_str.lower())
            )
            if match and not any(x.get("atc_code") == atc_code for x in matched_expansions):
                brand_en, brand_tc = self.parse_brand(brand_str)
                matched_expansions.append({
                    "atc_code": atc_code,
                    "class_code": class_code,
                    "class_name_en": winfo.get("class_en", "Therapeutic Class"),
                    "class_name_tc": winfo.get("class_tc", "治療類別"),
                    "ingredient_en": en_name,
                    "ingredient_tc": tc_name,
                    "brand_en": brand_en or en_name,
                    "brand_tc": brand_tc if brand_tc else [tc_name],
                    "is_brand": q_clean in brand_str.lower(),
                    "is_chinese": any(ord(c) > 127 for c in q_clean),
                    "searched_term": query,
                    "aliases": [atc_code.lower(), class_code.lower(), en_name.lower(), tc_name.lower()],
                    "primary_regulation": winfo.get("primary_regulation", "")
                })

        # Step 2: Check standard class database for alias/code matching (e.g., 'statins', 'sglt2')
        for code, info in self.atc_db.items():
            if q_clean == code.lower() or any(q_clean == alias.lower() for alias in info.get("aliases", [])):
                if not any(x.get("class_code") == code for x in matched_expansions):
                    primary_regulation = CLASS_REGULATION_MAPPING.get(code, "")
                    matched_expansions.append({
                        "atc_code": info["atc_code"],
                        "class_code": info["atc_code"],
                        "class_name_en": info["class_name_en"],
                        "class_name_tc": info["class_name_tc"],
                        "ingredient_en": "",
                        "ingredient_tc": "",
                        "brand_en": "",
                        "brand_tc": [],
                        "is_brand": False,
                        "is_chinese": any(ord(c) > 127 for c in q_clean),
                        "searched_term": query,
                        "aliases": info.get("aliases", []),
                        "primary_regulation": primary_regulation
                    })

        # Step 3: Substring/exact search in SQLite
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nhi_code, english_name, chinese_name, ingredient, atc_code, form, price
            FROM nhi_drugs
            WHERE nhi_code = ? 
               OR atc_code = ? 
               OR english_name LIKE ? 
               OR chinese_name LIKE ? 
               OR ingredient LIKE ?
            LIMIT 50
        """, (q_clean.upper(), q_clean.upper(), f"%{q_clean}%", f"%{q_clean}%", f"%{q_clean}%"))
        rows = cursor.fetchall()

        # Step 4: Fast bucketed fuzzy matching ONLY if no matches found yet and query is an English drug-like word
        if not rows and not matched_expansions and len(q_clean) >= 5 and re.match(r'^[a-z]+$', q_clean):
            self._ensure_vocab_loaded()
            bucket = self._fuzzy_vocab.get(q_clean[0], set())
            candidates = []
            for typ, cand in bucket:
                if abs(len(q_clean) - len(cand)) <= 2 and self.is_fuzzy_match(q_clean, cand):
                    candidates.append((typ, cand))
                    if len(candidates) >= 3:
                        break

            for typ, val in candidates:
                if typ == 'english_name':
                    cursor.execute("""
                        SELECT nhi_code, english_name, chinese_name, ingredient, atc_code, form, price
                        FROM nhi_drugs
                        WHERE english_name LIKE ?
                        LIMIT 10
                    """, (f"{val}%",))
                else:
                    cursor.execute("""
                        SELECT nhi_code, english_name, chinese_name, ingredient, atc_code, form, price
                        FROM nhi_drugs
                        WHERE ingredient = ?
                        LIMIT 10
                    """, (val.upper(),))
                rows.extend(cursor.fetchall())

        conn.close()

        # Step 5: Process SQLite rows into standardized expansions grouped by ATC
        atc_groups = {}
        for nhi_code, eng, chi, ing, atc, form, price in rows:
            if not atc:
                continue

            if atc not in atc_groups:
                atc_groups[atc] = {
                    "nhi_code": nhi_code,
                    "eng_name": eng,
                    "chi_name": chi,
                    "ingredient": ing,
                    "form": form,
                    "price": price,
                    "brands_en": set(),
                    "brands_tc": set()
                }

            brand_en, brand_tc = self.parse_brand(f"{eng} ({chi})")
            if brand_en:
                clean_eng = brand_en.split()[0].title()
                if clean_eng.replace('.', '').replace('-', '').isalnum():
                    atc_groups[atc]["brands_en"].add(clean_eng)

            clean_tc = self.clean_taiwan_brand(chi)
            if clean_tc:
                atc_groups[atc]["brands_tc"].add(clean_tc)
            elif brand_tc:
                for b in brand_tc:
                    atc_groups[atc]["brands_tc"].add(b)

        for atc, data in atc_groups.items():
            if any(x.get("atc_code") == atc for x in matched_expansions):
                continue
            class_code = atc[:5] if len(atc) >= 5 else atc

            class_info = self.atc_db.get(class_code, {})
            who_info = self.who_db.get(atc, {})
            class_name_en = who_info.get("class_en") or class_info.get("class_name_en", "Therapeutic Class")
            class_name_tc = who_info.get("class_tc") or class_info.get("class_name_tc", "治療類別")
            class_aliases = class_info.get("aliases", [])

            brand_en_list = sorted(list(data["brands_en"]))
            brand_tc_list = sorted(list(data["brands_tc"]))

            brand_en_str = ", ".join(brand_en_list) if brand_en_list else data["eng_name"].split()[0].title()
            primary_regulation = who_info.get("primary_regulation") or CLASS_REGULATION_MAPPING.get(class_code, "")

            matched_expansions.append({
                "atc_code": atc,
                "class_code": class_code,
                "class_name_en": class_name_en,
                "class_name_tc": class_name_tc,
                "ingredient_en": data["ingredient"].title(),
                "ingredient_tc": who_info.get("tc") or (data["chi_name"].split('膠囊')[0].split('膜衣錠')[0].strip() if data["chi_name"] else ""),
                "brand_en": brand_en_str,
                "brand_tc": brand_tc_list,
                "is_brand": q_clean in brand_en_str.lower() or any(q_clean in b.lower() for b in brand_tc_list),
                "is_chinese": any(ord(c) > 127 for c in q_clean),
                "searched_term": query,
                "aliases": class_aliases + [atc.lower(), data["ingredient"].lower()],
                "primary_regulation": primary_regulation
            })

        if len(self._expand_cache) >= 1024:
            self._expand_cache.clear()
        self._expand_cache[q_clean] = matched_expansions
        return matched_expansions

    def find_related_terms(self, text):
        """Find ATC classes and ingredients mentioned in text (including section title drug patterns)."""
        # Strip concomitant background medication clauses (e.g. antiplatelets/anticoagulants in 7.1. Clause 2.(5))
        cleaned_text = re.sub(r'而需使用[^。；]*?病人得以使用', '病人得以使用', text)
        text_lower = cleaned_text.lower()
        header_lower = cleaned_text[:300].lower()
        title_lower = cleaned_text.split('\n', 1)[0].lower()

        found_classes = set()
        primary_ingredients = set()
        secondary_ingredients = set()

        is_class_section_title = (
            not re.search(r'[a-z]{4,}', title_lower)
            or 'antipsychotics' in title_lower
            or 'ssri' in title_lower
            or 'nsaid' in title_lower
        )

        for code, info in self.atc_db.items():
            class_matched = False
            class_in_header = False
            for alias in info["aliases"]:
                alias_low = alias.lower()
                if re.match(r'^[a-z0-9\-\s]+$', alias_low):
                    pat = r'(?<![a-z0-9])' + re.escape(alias_low) + r'(?![a-z0-9])'
                    if re.search(pat, text_lower):
                        class_matched = True
                        if re.search(pat, header_lower):
                            class_in_header = True
                            break
                else:
                    if alias_low in text_lower:
                        class_matched = True
                        if alias_low in header_lower:
                            class_in_header = True
                            break
            if class_matched:
                found_classes.add(info["class_name_tc"])
                if is_class_section_title and class_in_header and code in CLASS_LEVEL_ENRICH_CODES:
                    for ing in info["ingredients"]:
                        primary_ingredients.add(f"{ing['en']} ({ing['tc']})")

            for ing in info["ingredients"]:
                en_low = ing["en"].lower()
                tc_low = ing["tc"].lower()
                if en_low in text_lower or tc_low in text_lower:
                    label = f"{ing['en']} ({ing['tc']})"
                    if en_low in title_lower or tc_low in title_lower:
                        primary_ingredients.add(label)
                    else:
                        secondary_ingredients.add(label)

        for code7, info7 in self.who_db.items():
            en_low = info7["en"].lower()
            tc_low = info7["tc"].lower()
            if en_low in text_lower or tc_low in text_lower:
                label = f"{info7['en']} ({info7['tc']})"
                if en_low in title_lower or tc_low in title_lower:
                    primary_ingredients.add(label)
                else:
                    secondary_ingredients.add(label)

        # Also extract explicit "GenericName (如BrandName)" patterns across title and body text
        for m in re.finditer(r'([A-Za-z][A-Za-z0-9\-\+\.\/\s]{2,45}?)\s*(?:注射劑|口服製劑|內服液劑|緩釋劑型|眼用製劑|外用製劑|栓劑|植入劑|凍晶注射劑|膠囊|錠劑)?\s*[（\(]\s*[:：]?如\s*[:：]?\s*([^）\)]+)[）\)]', cleaned_text):
            gen_name = m.group(1).strip()
            brand_name = m.group(2).strip().split('、')[0].split('，')[0].split(',')[0].split('；')[0].split(';')[0].strip()
            gen_name = re.sub(r'^(?:\d+(?:\.\d+)*\.?\s*)+', '', gen_name).strip()
            gen_name = re.sub(r'\s+\d+(?:\.\d+)?\s*(?:mg|mcg|ug|g|ml|iu|%)\b.*$', '', gen_name, flags=re.IGNORECASE).strip()
            all_existing = primary_ingredients | secondary_ingredients
            if len(gen_name) >= 3 and gen_name.lower() not in self.EXTRACTION_STOPWORDS and not any(gen_name.lower() in existing.lower() for existing in all_existing):
                label = f"{gen_name.title()} (如 {brand_name})"
                if m.start() <= len(title_lower):
                    primary_ingredients.add(label)
                else:
                    secondary_ingredients.add(label)

        # Match single-word generic ingredient names from NHI drug master DB (using ASCII boundary so Chinese-adjacent words match)
        self._ensure_vocab_loaded()
        if self._db_ingredients_map:
            for word in set(re.findall(r'[a-z]{5,}', text_lower)):
                if word in self._db_ingredients_map and word not in self.EXTRACTION_STOPWORDS:
                    all_existing = primary_ingredients | secondary_ingredients
                    if not any(word in existing.lower() for existing in all_existing):
                        if word in title_lower:
                            primary_ingredients.add(word.title())
                        else:
                            secondary_ingredients.add(word.title())

        ordered_ingredients = sorted(list(primary_ingredients)) + [
            x for x in sorted(list(secondary_ingredients)) if x not in primary_ingredients
        ]
        return sorted(list(found_classes)), ordered_ingredients


if __name__ == "__main__":
    engine = ATCEngine()
    print("Test Forteo expansion:", engine.expand_query("forteo"))
    print("Test Teriparatide expansion:", engine.expand_query("teriparatide"))
