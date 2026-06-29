import os
import re
import yaml
import docx
from docx.text.paragraph import Paragraph
from docx.table import Table
from pypdf import PdfReader
from backend.atc_engine import ATCEngine
from backend.disease_engine import DiseaseEngine

class NHIRegulationParser:
    def __init__(self, output_dir="okf_data"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.atc_engine = ATCEngine()
        self.disease_engine = DiseaseEngine()

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

    def _structure_docx_body(self, doc, source_file):
        records = []
        current_chapter = "通則 General Rules"
        current_section_num = "0.0"
        current_section_title = "通則 General Rules"
        current_buffer = []

        chap_pattern = re.compile(r'^第\s*(\d+)\s*節\s*(.*)')
        sec_pattern = re.compile(r'^(\d+\.\d+[\d\.]*)\s*(.*)')
        appendix_pattern = re.compile(r'^(?:◎\s*附表|附表[一二三四五六七八九十0-9]+|全民健康保險保險對象使用.*協議書)')

        # Dictionary of specific attached appendix tables
        specific_attached_tables = {}
        for t in doc.tables:
            t_rows = []
            for i, row in enumerate(t.rows):
                cell_texts = [cell.text.strip().replace('\n', ' ') for cell in row.cells]
                if any(cell_texts):
                    if i == 0 and not cell_texts[0]:
                        cell_texts[0] = "對象類別 (Target Group)"
                    t_rows.append(" | ".join(cell_texts))
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
            
            # Check if this specific section references any specific attached table
            if current_section_num.startswith("3.2") and "附表三-A" in specific_attached_tables:
                full_text = full_text + "\n\n【附表詳細內容 / Attached Table Details】:\n" + specific_attached_tables["附表三-A"]

            effective_dates = re.findall(r'\(\d{2,3}/\d{1,2}/\d{1,2}(?:[、,]\d{2,3}/\d{1,2}/\d{1,2})*\)', full_text)
            atc_classes, ingredients = self.atc_engine.find_related_terms(full_text)
            
            # Extract diseases / indications
            extracted_diseases = self.disease_engine.extract_diseases_from_text(full_text)
            bilingual_indications = [f"{d['english']} ({d['chinese']})" for d in extracted_diseases]

            # Precise lab criteria extraction
            labs = []
            lab_patterns = [
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
                (r'血小板', '血小板')
            ]
            for pat, label in lab_patterns:
                if re.search(pat, full_text):
                    labs.append(label)

            record = {
                "regulation_id": f"REG-{len(records)+1:04d}",
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
                    "summary": full_text[:300] + "..." if len(full_text) > 300 else full_text
                },
                "reference_annotations": {
                    "original_clause": current_section_title,
                    "full_text": full_text
                }
            }
            records.append(record)
            current_buffer = []

        for element in doc.element.body:
            tag = element.tag.split('}')[-1]
            if tag == 'p':
                p = Paragraph(element, doc)
                text = p.text.strip()
                if not text:
                    continue
                    
                chap_match = chap_pattern.match(text)
                if chap_match:
                    flush_buffer()
                    chap_num, chap_name = chap_match.groups()
                    current_chapter = f"第{chap_num}節 {chap_name}".strip()
                    current_section_num = f"{chap_num}.0"
                    current_section_title = current_chapter
                    continue

                sec_match = sec_pattern.match(text)
                if sec_match:
                    flush_buffer()
                    s_num, s_title = sec_match.groups()
                    current_section_num = s_num
                    current_section_title = f"{s_num} {s_title}".strip()
                    continue

                if appendix_pattern.match(text):
                    flush_buffer()
                    current_chapter = "附表附錄 Standalone Appendix Forms"
                    current_section_num = "APP"
                    current_section_title = text
                    continue

                current_buffer.append(text)

            elif tag == 'tbl':
                tbl = Table(element, doc)
                tbl_rows = []
                for i, row in enumerate(tbl.rows):
                    cell_texts = [cell.text.strip().replace('\n', ' ') for cell in row.cells]
                    if any(cell_texts):
                        if i == 0 and not cell_texts[0]:
                            cell_texts[0] = "對象類別 (Target Group)"
                        tbl_rows.append(" | ".join(cell_texts))
                if tbl_rows:
                    tbl_formatted = "\n【給付與評估表格 / Clinical Assessment Table】:\n" + "\n".join(tbl_rows)
                    if current_section_num != "APP":
                        current_buffer.append(tbl_formatted)

        flush_buffer()
        return records

    def _structure_paragraphs(self, paragraphs, source_file):
        records = []
        current_chapter = "通則 General Rules"
        current_section_num = "0.0"
        current_section_title = "通則 General Rules"
        current_buffer = []

        chap_pattern = re.compile(r'^第\s*(\d+)\s*節\s*(.*)')
        sec_pattern = re.compile(r'^(\d+\.\d+[\d\.]*)\s*(.*)')

        def flush_buffer():
            nonlocal current_buffer, records
            if not current_buffer:
                return
            full_text = "\n".join(current_buffer)
            effective_dates = re.findall(r'\(\d{2,3}/\d{1,2}/\d{1,2}(?:[、,]\d{2,3}/\d{1,2}/\d{1,2})*\)', full_text)
            atc_classes, ingredients = self.atc_engine.find_related_terms(full_text)
            extracted_diseases = self.disease_engine.extract_diseases_from_text(full_text)
            bilingual_indications = [f"{d['english']} ({d['chinese']})" for d in extracted_diseases]

            labs = []
            lab_patterns = [
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
                (r'血小板', '血小板')
            ]
            for pat, label in lab_patterns:
                if re.search(pat, full_text):
                    labs.append(label)

            record = {
                "regulation_id": f"REG-{len(records)+1:04d}",
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
                    "summary": full_text[:300] + "..." if len(full_text) > 300 else full_text
                },
                "reference_annotations": {
                    "original_clause": current_section_title,
                    "full_text": full_text
                }
            }
            records.append(record)
            current_buffer = []

        for p in paragraphs:
            chap_match = chap_pattern.match(p)
            if chap_match:
                flush_buffer()
                chap_num, chap_name = chap_match.groups()
                current_chapter = f"第{chap_num}節 {chap_name}".strip()
                current_section_num = f"{chap_num}.0"
                current_section_title = current_chapter
                continue

            sec_match = sec_pattern.match(p)
            if sec_match:
                flush_buffer()
                s_num, s_title = sec_match.groups()
                current_section_num = s_num
                current_section_title = f"{s_num} {s_title}".strip()
                continue

            current_buffer.append(p)

        flush_buffer()
        return records

    def save_to_okf_yaml(self, records):
        grouped = {}
        for r in records:
            chap = r["chapter"]
            if chap not in grouped:
                grouped[chap] = []
            grouped[chap].append(r)

        generated_files = []
        for chap, items in grouped.items():
            clean_name = re.sub(r'[^\w\-_]', '_', chap)[:30].strip('_')
            file_name = f"{clean_name}.yaml"
            file_path = os.path.join(self.output_dir, file_name)
            
            okf_payload = {
                "okf_version": "1.0",
                "schema_type": "Taiwan_NHI_Drug_Regulation",
                "chapter": chap,
                "total_regulations": len(items),
                "regulations": items
            }
            
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(okf_payload, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
            generated_files.append(file_path)

        return generated_files

if __name__ == "__main__":
    parser = NHIRegulationParser()
    if os.path.exists("完整給付規定1150623.docx"):
        print("Parsing docx...")
        recs = parser.parse_docx("完整給付規定1150623.docx")
        files = parser.save_to_okf_yaml(recs)
        print(f"Parsed {len(recs)} records into {len(files)} YAML files.")
