import os
import re
import yaml
from backend.disease_engine import DISEASE_DATABASE

def mine_nhi_vocabulary(data_dir="okf_data"):
    """Scans all parsed OKF YAML datasets to extract potential disease & clinical condition terms."""
    all_texts = []
    yaml_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.yaml')]
    
    for yf in yaml_files:
        with open(yf, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data and 'regulations' in data:
                for r in data['regulations']:
                    text = r['section_title'] + " " + r['reference_annotations']['full_text']
                    all_texts.append(text)
                    
    full_corpus = "\n".join(all_texts)
    
    # Extract terms matching common Chinese medical suffixes
    disease_patterns = r'[\u4e00-\u9fa5]{2,8}(?:症|病|炎|瘤|癌|衰竭|感染|血症|障礙|不全|突變|綜合征|症候群)'
    candidates = set(re.findall(disease_patterns, full_corpus))
    
    # Filter out already indexed Chinese terms
    already_indexed = set()
    for info in DISEASE_DATABASE.values():
        for tc in info['tc_terms']:
            already_indexed.add(tc)
            
    unmapped = [c for c in candidates if c not in already_indexed and not any(ai in c for ai in ['發作', '治療', '使用', '檢查', '診斷', '申請'])]
    
    return sorted(unmapped)

if __name__ == "__main__":
    unmapped_terms = mine_nhi_vocabulary()
    print(f"Total candidate medical terms found in NHI corpus: {len(unmapped_terms)}")
    print("Sample unmapped terms:", unmapped_terms[:30])
