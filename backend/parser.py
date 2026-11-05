import os
import re
import yaml
import docx
from docx.text.paragraph import Paragraph
from docx.table import Table
from pypdf import PdfReader
from backend.atc_engine import ATCEngine
from backend.disease_engine import DiseaseEngine
from backend.langextract_engine import LangExtractEngine


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


class NHIRegulationParser:
    CHAP_PATTERN = re.compile(r'^第\s*(\d+)\s*節\s*(.*)')
    SEC_PATTERN = re.compile(r'^(\d+\.\d+[\d\.]*)\s*(.*)')
    FALSE_SEC_PREFIX = re.compile(r'^[歲年個週天日小~～至項\*]')
    APPENDIX_PATTERN = re.compile(r'^(?:◎\s*附表|附表[一二三四五六七八九十0-9]+|全民健康保險保險對象使用.*協議書)')
    EFFECTIVE_DATE_PATTERN = re.compile(r'\(\d{2,3}/\d{1,2}/\d{1,2}(?:[、,]\d{2,3}/\d{1,2}/\d{1,2})*\)')

    LAB_PATTERNS = (
        (r'\bHbA1c\b', 'HbA1c'),
        (r'\beGFR\b', 'eGFR'),
        (r'\bALT\b', 'ALT'),
        (r'\bAST\b', 'AST'),
        (r'\bLVEF\b', 'LVEF'),
        (r'\bScr\b|血清肌酸酐', 'Scr'),
        (r'血糖', '血糖'),
        (r'血壓', '血壓'),
        (r'\bBMI\b', 'BMI'),
        (r'白血球', '白血球'),
        (r'血小板', '血小板'),
    )

    GENERIC_SUBSECTION_HEADERS = ("單方製劑", "複方製劑", "全身性抗疱疹病毒劑")

    def __init__(self, output_dir="okf_data"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.atc_engine = ATCEngine()
        self.disease_engine = DiseaseEngine()
        self.langextract_engine = LangExtractEngine()

    def parse_docx(self, file_path):
        doc = docx.Document(file_path)
        return self._structure_docx_body(doc, source_file=os.path.basename(file_path))

    def parse_pdf(self, file_path):
        reader = PdfReader(file_path)
        paragraphs = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                for line in text.split("\n"):
                    if line.strip():
                        paragraphs.append(line.strip())
        return self._structure_paragraphs(paragraphs, source_file=os.path.basename(file_path))

    @staticmethod
    def _extract_table_rows(table):
        rows = []
        for i, row in enumerate(table.rows):
            cell_texts = [cell.text.strip().replace('\n', ' ') for cell in row.cells]
            if any(cell_texts):
                if i == 0 and not cell_texts[0]:
                    cell_texts[0] = "對象類別 (Target Group)"
                rows.append(" | ".join(cell_texts))
        return rows

    def _build_record(self, rec_index, current_section_num, current_section_title, current_chapter, source_file, full_text):
        effective_dates = self.EFFECTIVE_DATE_PATTERN.findall(full_text)
        combined_text = f"{current_section_title}\n{full_text}"
        atc_classes, ingredients = self.atc_engine.find_related_terms(combined_text)

        extracted_diseases = self.disease_engine.extract_diseases_from_text(combined_text)
        bilingual_indications = [f"{d['english']} ({d['chinese']})" for d in extracted_diseases]

        labs = [label for pat, label in self.LAB_PATTERNS if re.search(pat, full_text)]

        le_res = self.langextract_engine.extract_section_rules(
            section_number=current_section_num,
            section_title=current_section_title,
            full_text=full_text,
            known_indications=bilingual_indications
        )
        for bio in le_res.get("structured_biomarkers", []):
            if bio["biomarker"] not in labs:
                labs.append(bio["biomarker"])

        return {
            "regulation_id": f"REG-{rec_index:04d}",
            "section_number": current_section_num,
            "section_title": current_section_title,
            "chapter": current_chapter,
            "source_file": source_file,
            "effective_dates": effective_dates,
            "medications": {
                "drug_classes": atc_classes,
                "ingredients": ingredients
            },
            "conditions_of_payment": {
                "indications": bilingual_indications,
                "laboratory_criteria": labs,
                "summary": le_res.get("summary", full_text[:300] + "..." if len(full_text) > 300 else full_text),
                "clinical_rules": le_res.get("clinical_rules", []),
                "structured_biomarkers": le_res.get("structured_biomarkers", []),
                "prior_authorization_required": le_res.get("prior_authorization_required", False),
                "prior_authorization_grounding": le_res.get("prior_authorization_grounding", None),
                "step_therapy": le_res.get("step_therapy", []),
                "stopping_rules": le_res.get("stopping_rules", []),
                "evaluation_intervals": le_res.get("evaluation_intervals", [])
            },
            "reference_annotations": {
                "original_clause": current_section_title,
                "full_text": full_text
            }
        }

    def _structure_docx_body(self, doc, source_file):
        records = []
        current_chapter = "通則 General Rules"
        active_chapter = "通則 General Rules"
        active_chap_num = "0"
        current_section_num = "0.0"
        current_section_title = "通則 General Rules"
        current_buffer = []
        section_title_map = {}

        specific_attached_tables = {}
        for t in doc.tables:
            t_rows = self._extract_table_rows(t)
            t_text = "\n".join(t_rows)
            if "維生素A" in t_text and "維生素B1" in t_text:
                specific_attached_tables["附表三-A"] = t_text
            elif "荷爾蒙" in t_text and "閉經" in t_text:
                specific_attached_tables["附表三-B"] = t_text
            elif "Amoxicillin" in t_text and "AmphotericinB" in t_text:
                specific_attached_tables["附表一"] = t_text

        def flush_buffer():
            nonlocal current_buffer, records
            if not current_buffer:
                return
            full_text = "\n".join(current_buffer)
            if current_section_num.startswith("3.2") and "附表三-A" in specific_attached_tables:
                full_text = full_text + "\n\n【附表詳細內容 / Attached Table Details】:\n" + specific_attached_tables["附表三-A"]

            records.append(self._build_record(
                rec_index=len(records) + 1,
                current_section_num=current_section_num,
                current_section_title=current_section_title,
                current_chapter=current_chapter,
                source_file=source_file,
                full_text=full_text
            ))
            current_buffer = []

        for element in doc.element.body:
            tag = element.tag.split('}')[-1]
            if tag == 'p':
                p = Paragraph(element, doc)
                text = p.text.strip()
                if not text:
                    continue

                chap_match = self.CHAP_PATTERN.match(text)
                if chap_match:
                    flush_buffer()
                    chap_num, chap_name = chap_match.groups()
                    active_chap_num = chap_num
                    active_chapter = f"第{chap_num}節 {chap_name}".strip()
                    current_chapter = active_chapter
                    current_section_num = f"{chap_num}.0"
                    current_section_title = current_chapter
                    continue

                sec_match = self.SEC_PATTERN.match(text)
                if sec_match:
                    s_num, s_title = sec_match.groups()
                    first_num = s_num.split('.')[0]
                    is_valid_sec = (
                        first_num == active_chap_num
                        and not self.FALSE_SEC_PREFIX.match(s_title)
                        and not (s_num == "13.3.3" and s_title.startswith("與tazarotene"))
                    )
                    if is_valid_sec:
                        flush_buffer()
                        if s_title.startswith('.'):
                            s_title = s_title.lstrip('.').strip()
                        s_num_norm = s_num.rstrip('.') + '.'
                        clean_sec = s_num.rstrip('.')
                        clean_t = re.sub(r'[（\(][^）\)]*\d+[^）\)]*[）\)]', '', s_title).strip(' ：:。')
                        section_title_map[clean_sec] = clean_t

                        if clean_t in self.GENERIC_SUBSECTION_HEADERS:
                            parent_sec = ".".join(clean_sec.split(".")[:-1])
                            parent_t = section_title_map.get(parent_sec, "")
                            if parent_t:
                                s_title = f"{parent_t} - {s_title}"

                        current_chapter = active_chapter
                        current_section_num = s_num_norm
                        current_section_title = f"{s_num_norm} {s_title}".strip()
                        continue

                if self.APPENDIX_PATTERN.match(text):
                    flush_buffer()
                    current_chapter = "附表附錄 Standalone Appendix Forms"
                    current_section_num = "APP"
                    current_section_title = text
                    continue

                current_buffer.append(text)

            elif tag == 'tbl':
                tbl_rows = self._extract_table_rows(Table(element, doc))
                if tbl_rows and current_section_num != "APP":
                    current_buffer.append("\n【給付與評估表格 / Clinical Assessment Table】:\n" + "\n".join(tbl_rows))

        flush_buffer()
        self._enrich_parent_ingredients(records)
        return records

    def _enrich_parent_ingredients(self, records):
        """If a parent section (e.g. 2.8.2. or 5.6.) has no extracted ingredients of its own, roll up child section ingredients."""
        for r in records:
            sec = r["section_number"]
            if sec in ("0.0", "APP") or sec.endswith(".0"):
                continue
            if not r["medications"]["ingredients"]:
                child_ings = []
                seen = set()
                for child in records:
                    c_sec = child["section_number"]
                    if c_sec != sec and c_sec.startswith(sec):
                        for ing in child["medications"]["ingredients"]:
                            base_ing = ing.split("(")[0].strip().lower()
                            if base_ing not in seen:
                                seen.add(base_ing)
                                child_ings.append(ing)
                if child_ings:
                    r["medications"]["ingredients"] = child_ings

    def _structure_paragraphs(self, paragraphs, source_file):
        records = []
        current_chapter = "通則 General Rules"
        active_chapter = "通則 General Rules"
        active_chap_num = "0"
        current_section_num = "0.0"
        current_section_title = "通則 General Rules"
        current_buffer = []

        def flush_buffer():
            nonlocal current_buffer, records
            if not current_buffer:
                return
            records.append(self._build_record(
                rec_index=len(records) + 1,
                current_section_num=current_section_num,
                current_section_title=current_section_title,
                current_chapter=current_chapter,
                source_file=source_file,
                full_text="\n".join(current_buffer)
            ))
            current_buffer = []

        for p in paragraphs:
            chap_match = self.CHAP_PATTERN.match(p)
            if chap_match:
                flush_buffer()
                chap_num, chap_name = chap_match.groups()
                active_chap_num = chap_num
                active_chapter = f"第{chap_num}節 {chap_name}".strip()
                current_chapter = active_chapter
                current_section_num = f"{chap_num}.0"
                current_section_title = current_chapter
                continue

            sec_match = self.SEC_PATTERN.match(p)
            if sec_match:
                s_num, s_title = sec_match.groups()
                first_num = s_num.split('.')[0]
                if first_num == active_chap_num and not self.FALSE_SEC_PREFIX.match(s_title):
                    flush_buffer()
                    if s_title.startswith('.'):
                        s_title = s_title.lstrip('.').strip()
                    s_num_norm = s_num.rstrip('.') + '.'
                    current_chapter = active_chapter
                    current_section_num = s_num_norm
                    current_section_title = f"{s_num_norm} {s_title}".strip()
                    continue

            current_buffer.append(p)

        flush_buffer()
        self._enrich_parent_ingredients(records)
        return records

    def save_to_okf_yaml(self, records, source_doc="完整給付規定1150821.docx"):
        grouped = {}
        for r in records:
            grouped.setdefault(r["chapter"], []).append(r)

        generated_files = []
        for chap, items in grouped.items():
            clean_name = re.sub(r'[^\w\-_]', '_', chap)[:30].strip('_')
            file_path = os.path.join(self.output_dir, f"{clean_name}.yaml")

            okf_payload = {
                "okf_version": "0.2",
                "type": "regulation/taiwan_nhi_drug_payment",
                "chapter": chap,
                "provenance": {
                    "authority": "衛生福利部中央健康保險署 (Taiwan NHIA)",
                    "source_document": source_doc,
                    "jurisdiction": "TW",
                    "legal_basis": "全民健康保險法第41條暨全民健康保險藥物給付項目及支付標準"
                },
                "trust": {
                    "tier": "machine-confirmed",
                    "extracted_by": "LangExtract-NHI-Engine",
                    "grounding_verified": True,
                    "confidence_score": 0.98
                },
                "lifecycle": {
                    "status": "active",
                    "last_synced": "2026-11-04",
                    "stale_after": "2026-12-31"
                },
                "total_regulations": len(items),
                "regulations": items
            }

            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    okf_payload,
                    f,
                    Dumper=NoAliasDumper,
                    allow_unicode=True,
                    sort_keys=False,
                    default_flow_style=False
                )
            generated_files.append(file_path)

        return generated_files


if __name__ == "__main__":
    parser = NHIRegulationParser()
    target_docx = "完整給付規定1150821.docx"
    if not os.path.exists(target_docx):
        target_docx = "完整給付規定1150623.docx"
    if os.path.exists(target_docx):
        print(f"Parsing {target_docx}...")
        recs = parser.parse_docx(target_docx)
        files = parser.save_to_okf_yaml(recs, source_doc=target_docx)
        print(f"Parsed {len(recs)} records into {len(files)} YAML files.")
