---
name: nhi-regulation-query
description: Parse Taiwan NHI drug regulations (.docx/.pdf), convert clauses into Google OKF compatible YAML datasets, build ATC taxonomy cross-search indices (Taiwan Traditional Chinese + INN English names), and operate the NHI query engine web app.
---

# Taiwan NHI Drug Regulation Knowledge & Query Engine Skill

This skill provides comprehensive workflows for parsing, structuring, updating, and searching Taiwan National Health Insurance (NHI) drug payment regulations ("全民健康保險藥品給付規定").

## Key Capabilities

1. **Document Ingestion & Google OKF YAML Conversion**:
   - Parses official NHI regulation files in Word (`.docx`) or PDF (`.pdf`) format.
   - Extracts chapter hierarchy (Chapters 1–15 and General Rules), section numbers, medication lists, effective revision dates, and clinical/laboratory constraints.
   - Outputs standardized Google Open Knowledge Format (OKF) YAML files into `okf_data/`.

2. **ATC Taxonomy & Taiwan Drug Dictionary Engine**:
   - Enforces strict use of **Taiwan Traditional Chinese drug names** (繁體中文藥物名稱, e.g., 恩格列淨, 達格列淨, 派姆單抗) alongside **International Standard English INN ingredient names** (e.g., Empagliflozin, Dapagliflozin, Pembrolizumab).
   - Resolves WHO ATC classification codes (e.g., `A10BK` for SGLT2 inhibitors, `A10BJ` for GLP-1 receptor agonists, `L01FF` for PD-1/PD-L1 inhibitors).
   - Enables bidirectional cross-query expansion: Searching by drug class returns all member ingredients, and searching by ingredient returns class-level regulations.

3. **Multi-Attribute Inverted Indexing & Web Application**:
   - Indexes regulation records by section number, laboratory thresholds (`eGFR`, `HbA1c`, `ALT`, `LVEF`), clinical diagnoses, and drug terms.
   - Serves a modern interactive web application featuring payment condition summaries, reference annotations, and live document drag-and-drop update drawer.

---

## Command Workflows

### 1. Reparse Regulations and Rebuild OKF YAML Datasets
To parse a newly released regulation document (e.g., `完整給付規定.docx` or `.pdf`):
```bash
python3 -m backend.parser
```
*Output*: Generates 16 structured YAML datasets in `okf_data/` categorized by section.

### 2. Run Inverted Index & Query Tests
To execute command-line search and query expansion tests:
```bash
python3 -m backend.indexer
```

### 3. Launch Web Application Server
To launch the query web service:
```bash
PORT=5001 python3 -m backend.server
```
Access the web dashboard at `http://localhost:5001`.

---

## Schema Overview: Google OKF YAML Format
Each regulation entry in `okf_data/*.yaml` adheres to the following structure:
```yaml
regulation_id: REG-0042
section_number: 2.5.1
section_title: 2.5.1. SGLT2 inhibitors (如 empagliflozin、dapagliflozin)
chapter: 第2節 心臟血管及腎臟藥物 Cardiovascular-renal drugs
effective_dates:
  - (109/12/1)
medications:
  drug_classes:
    - SGLT2抑制劑 (鈉-葡萄糖共同輸送轉運蛋白2抑制劑)
  ingredients:
    - Empagliflozin (恩格列淨)
conditions_of_payment:
  laboratory_criteria:
    - HbA1c
    - eGFR
  summary: 門診二甲雙胍 (Metformin) 治療效果不佳，且 eGFR >= 30 mL/min/1.73m2 時得合併使用...
reference_annotations:
  original_clause: 2.5.1. SGLT2 inhibitors
  full_text: 完整法規條文內文...
```
