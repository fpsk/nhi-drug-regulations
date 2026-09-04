import os
import re
import sys
import json
import argparse
import dotenv
from pathlib import Path

# Load API keys from .env and ensure project root in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
dotenv.load_dotenv(BASE_DIR / '.env')
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

import langextract as lx
from langextract.core import data
from backend.indexer import NHIIndexer

def make_extraction(text, cls, sub):
    start = text.find(sub)
    if start != -1:
        end = start + len(sub)
        return data.Extraction(
            extraction_class=cls, 
            extraction_text=sub, 
            char_interval=data.CharInterval(start_pos=start, end_pos=end)
        )
    return data.Extraction(extraction_class=cls, extraction_text=sub)

_t0 = """9.80. Osimertinib (如Tagrisso)：(109/4/1、109/6/1、109/10/1、111/4/1、113/10/1、115/8/1)
1.限單獨使用於具有EGFR T790M突變之局部晚期或轉移性非小細胞肺癌之成年患者。
2.病患需經EGFR T790M突變檢測為陽性，且先前曾接受過第一代或第二代EGFR-TKI治療後疾病惡化者。
3.每日至多給付1粒，給付期間至疾病進展或出現無法耐受之毒性為止。"""

_t1 = """2.16. SGLT2抑制劑（如Forxiga、Jardiance）：
限用於第二型糖尿病病患且符合下列條件之一：
1.經使用metformin單一藥物治療3個月以上，HbA1c仍>=8.5%者。
2.合併有心血管疾病或心臟衰竭病史者。
3.病患之eGFR需大於等於45 mL/min/1.73m2。"""

# Clinical Few-Shot Examples for Taiwan NHI Drug Regulations
EXAMPLES = [
    data.ExampleData(
        text=_t0,
        extractions=[
            make_extraction(_t0, "drug_name", "Osimertinib"),
            make_extraction(_t0, "brand_name", "Tagrisso"),
            make_extraction(_t0, "indication", "局部晚期或轉移性非小細胞肺癌"),
            make_extraction(_t0, "biomarker", "EGFR T790M突變"),
            make_extraction(_t0, "prior_therapy", "先前曾接受過第一代或第二代EGFR-TKI治療後疾病惡化者"),
            make_extraction(_t0, "dosage_limit", "每日至多給付1粒")
        ]
    ),
    data.ExampleData(
        text=_t1,
        extractions=[
            make_extraction(_t1, "drug_class", "SGLT2抑制劑"),
            make_extraction(_t1, "brand_name", "Forxiga"),
            make_extraction(_t1, "brand_name", "Jardiance"),
            make_extraction(_t1, "indication", "第二型糖尿病"),
            make_extraction(_t1, "prior_therapy", "經使用metformin單一藥物治療3個月以上"),
            make_extraction(_t1, "laboratory_criteria", "HbA1c仍>=8.5%"),
            make_extraction(_t1, "comorbidity", "心血管疾病或心臟衰竭病史"),
            make_extraction(_t1, "laboratory_criteria", "eGFR需大於等於45 mL/min/1.73m2")
        ]
    )
]

PROMPT_DESCRIPTION = """Extract structured clinical and administrative payment conditions from Taiwan National Health Insurance (NHI) drug payment regulations (全民健康保險藥品給付規定).
Identify:
- drug_name / drug_class: The active pharmaceutical ingredient or therapeutic class.
- brand_name: Commercial brand names (e.g. 如 Tagrisso, Pulmivex).
- indication: Target approved clinical disease or disease stage.
- biomarker: Required molecular, genetic, or immunohistochemical biomarkers (e.g., EGFR T790M, FLT3, PD-L1).
- prior_therapy: Required previous treatments, lines of therapy, or drug trial durations.
- laboratory_criteria: Numerical or qualitative laboratory test thresholds (e.g., eGFR, HbA1c, LDL-C, LVEF, ALT).
- dosage_limit: Restrictions on daily pill counts, treatment courses, or renewal durations.
"""

def extract_section_criteria(section_text, model_id="gemini-2.5-flash"):
    res = lx.extract(
        section_text,
        prompt_description=PROMPT_DESCRIPTION,
        examples=EXAMPLES,
        model_id=model_id,
        show_progress=False
    )
    doc = res if hasattr(res, 'extractions') else res[0]
    
    extracted_items = []
    for e in doc.extractions:
        extracted_items.append({
            "class": e.extraction_class,
            "text": e.extraction_text,
            "char_interval": [e.char_interval.start_pos, e.char_interval.end_pos] if e.char_interval else None
        })
    return doc, extracted_items

def main():
    parser = argparse.ArgumentParser(description="Extract structured criteria from NHI regulation clauses using LangExtract")
    parser.add_argument("--query", "-q", type=str, help="Search query to find target regulation (e.g. pulmivex, repatha, fitusiran)")
    parser.add_argument("--section", "-s", type=str, help="Specific section number (e.g. 9.138, 2.6.4.1)")
    parser.add_argument("--model", "-m", type=str, default="gemini-2.5-flash", help="Gemini model ID")
    parser.add_argument("--visualize", "-v", action="store_true", help="Generate interactive HTML visualization")
    args = parser.parse_args()

    indexer = NHIIndexer()
    target_reg = None

    if args.section:
        for r in indexer.regulations:
            if r["section_number"].strip('.') == args.section.strip('.'):
                target_reg = r
                break
    elif args.query:
        hits = indexer.search(args.query)
        if hits:
            target_reg = hits[0]

    if not target_reg:
        print("No matching regulation found. Please provide a valid --query or --section.")
        sys.exit(1)

    print(f"=== Selected Regulation: {target_reg['section_number']} ===")
    print(f"Title: {target_reg['section_title']}")
    full_text = target_reg.get("reference_annotations", {}).get("full_text", "") or target_reg.get("conditions_of_payment", {}).get("summary", "")
    print(f"Clause length: {len(full_text)} characters\n")

    print(f"Running LangExtract using {args.model}...")
    doc, items = extract_section_criteria(full_text, model_id=args.model)

    print(f"\n[LangExtract Result] Extracted {len(items)} structured entities:")
    for item in items:
        span_str = f" [chars {item['char_interval']}]" if item['char_interval'] else ""
        print(f"  • {item['class']:<20}: {repr(item['text'])}{span_str}")

    if args.visualize:
        html = lx.visualize(doc)
        sec_clean = target_reg['section_number'].replace('.', '_').strip('_')
        out_path = f"scratch/{sec_clean}_langextract.html"
        os.makedirs("scratch", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html if isinstance(html, str) else str(html))
        print(f"\nSaved interactive visualizer to: {out_path}")

if __name__ == "__main__":
    main()
