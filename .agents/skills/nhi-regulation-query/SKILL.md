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
