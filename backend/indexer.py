import os
import glob
import yaml
import re
from backend.atc_engine import ATCEngine
from backend.disease_engine import DiseaseEngine

class NHIIndexer:
    def __init__(self, data_dir="okf_data"):
        self.data_dir = data_dir
        self.atc_engine = ATCEngine()
        self.disease_engine = DiseaseEngine()
        self.regulations = []
        self.index = {}
        self.load_and_index()

    def load_and_index(self):
        self.regulations = []
        self.index = {
            "by_section": {},
            "by_keyword": {},
            "by_drug": {},
            "by_lab": {}
        }
        
        yaml_files = glob.glob(os.path.join(self.data_dir, "*.yaml"))
        for yf in yaml_files:
            try:
                with open(yf, "r", encoding="utf-8") as f:
                    content = yaml.safe_load(f)
                    if content and "regulations" in content:
                        for reg in content["regulations"]:
                            self._index_record(reg)
            except Exception as e:
                print(f"Error loading {yf}: {e}")

    def _index_record(self, reg):
        self.regulations.append(reg)
        reg_id = reg["regulation_id"]
        
        sec_num = reg.get("section_number", "")
        self.index["by_section"][sec_num] = reg_id
        
        full_text = reg.get("reference_annotations", {}).get("full_text", "") + " " + reg.get("section_title", "")
        tokens = set(re.findall(r'\w+', full_text.lower()))
        for t in tokens:
            if t not in self.index["by_keyword"]:
                self.index["by_keyword"][t] = set()
            self.index["by_keyword"][t].add(reg_id)
            
        labs = reg.get("conditions_of_payment", {}).get("laboratory_criteria", [])
        for lab in labs:
            l_key = lab.lower()
            if l_key not in self.index["by_lab"]:
                self.index["by_lab"][l_key] = set()
            self.index["by_lab"][l_key].add(reg_id)

    def search(self, query, chapter_filter=None, lab_filter=None):
        query_clean = query.strip()
        if not query_clean and not chapter_filter and not lab_filter:
            return self.regulations[:50]

        expanded_terms = set([query_clean.lower()])
        matched_class_names = set()
        matched_disease_names = set()
        
        # Smart Normalization for Lab Criteria & Acronyms
        norm_q = re.sub(r'[\s\-_]+', '', query_clean.lower())
        if norm_q in ['hbvdna', 'hbv', 'b型肝炎病毒量', '血清hbvdna']:
            expanded_terms.add('hbv dna')
            expanded_terms.add('hbv-dna')
            expanded_terms.add('hbvdna')
            expanded_terms.add('hbv')
            expanded_terms.add('b型肝炎')
        elif norm_q in ['hcvrna', 'hcv', 'c型肝炎病毒量']:
            expanded_terms.add('hcv rna')
            expanded_terms.add('hcv-rna')
            expanded_terms.add('hcvrna')
            expanded_terms.add('c型肝炎')

        # ATC Expansion
        atc_expansions = self.atc_engine.expand_query(query_clean)
        for exp in atc_expansions:
            expanded_terms.add(exp["atc_code"].lower())
            expanded_terms.add(exp["class_name_en"].lower())
            expanded_terms.add(exp["class_name_tc"].lower())
            matched_class_names.add(exp["class_name_tc"].lower())
            
            for alias in exp.get("aliases", []):
                expanded_terms.add(alias.lower())
                
            for ing in exp["ingredients"]:
                expanded_terms.add(ing["en"].lower())
                expanded_terms.add(ing["tc"].lower())
                brand_str = ing.get("brand", "")
                if brand_str:
                    for b in re.findall(r'[a-zA-Z0-9\-]+|[\u4e00-\u9fa5]+', brand_str):
                        if len(b) > 1:
                            expanded_terms.add(b.lower())

        # Disease Expansion
        disease_expansions = self.disease_engine.expand_query(query_clean)
        if norm_q == 'hbvdna':
            disease_expansions.extend(self.disease_engine.expand_query('hbv'))
            
        for de in disease_expansions:
            expanded_terms.add(de["english_name"].lower())
            matched_disease_names.add(de["english_name"].lower())
            for alias in de["aliases"]:
                expanded_terms.add(alias.lower())
            for tc in de["chinese_terms"]:
                expanded_terms.add(tc.lower())
                matched_disease_names.add(tc.lower())

        results = []
        for reg in self.regulations:
            if chapter_filter and chapter_filter not in reg["chapter"]:
                continue
                
            if lab_filter:
                reg_labs = [l.lower() for l in reg.get("conditions_of_payment", {}).get("laboratory_criteria", [])]
                if lab_filter.lower() not in reg_labs:
                    continue

            if not query_clean:
                results.append((reg, 1.0))
                continue

            full_text = (reg["section_title"] + " " + reg.get("reference_annotations", {}).get("full_text", "")).lower()
            reg_classes = [c.lower() for c in reg.get("medications", {}).get("drug_classes", [])]
            reg_ingredients = [i.lower() for i in reg.get("medications", {}).get("ingredients", [])]
            reg_indications = [ind.lower() for ind in reg.get("conditions_of_payment", {}).get("indications", [])]
            
            score = 0
            if query_clean.lower() == reg["section_number"].lower():
                score += 300

            for mdn in matched_disease_names:
                if any(mdn in ind for ind in reg_indications):
                    score += 150

            for mc in matched_class_names:
                if any(mc in rc or rc in mc for rc in reg_classes):
                    score += 100

            for term in expanded_terms:
                if term and len(term) > 1:
                    is_match = False
                    # For short English terms (<=4 chars like ppi, pud, gerd), require word boundary regex
                    if re.match(r'^[a-z0-9\-]{2,5}$', term) and term not in ['hbv', 'hcv', 'dna', 'rna']:
                        if re.search(r'\b' + re.escape(term) + r'\b', full_text):
                            is_match = True
                    else:
                        if term in full_text:
                            is_match = True

                    if is_match:
                        if term in reg["section_title"].lower():
                            score += 50
                        else:
                            score += 5
                    if any(term in ri for ri in reg_ingredients):
                        score += 30

            if score > 0:
                results.append((reg, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results]

if __name__ == "__main__":
    indexer = NHIIndexer()
    print(f"Total indexed regulations: {len(indexer.regulations)}")
