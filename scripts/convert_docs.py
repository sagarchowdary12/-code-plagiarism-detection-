import os
import re
from docx import Document
from docx.shared import Pt, RGBColor
from fpdf import FPDF
import markdown

# Paths
SOURCE_MD = "docs/MASTER_PROJECT_DOCUMENTATION.md"
OUTPUT_DOCX = "docs/MASTER_PROJECT_DOCUMENTATION.docx"
OUTPUT_PDF = "docs/MASTER_PROJECT_DOCUMENTATION.pdf"

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Plagiarism Detection Service v3.0.0 - Project Documentation', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def convert_to_docx(content):
    doc = Document()
    
    # Simple markdown parser for the purposes of this specialized report
    lines = content.splitlines()
    for line in lines:
        if line.startswith('# '):
            p = doc.add_heading(line[2:], level=0)
        elif line.startswith('## '):
            doc.add_heading(line[3:], level=1)
        elif line.startswith('### '):
            doc.add_heading(line[4:], level=2)
        elif line.startswith('* '):
            doc.add_paragraph(line[2:], style='List Bullet')
        elif line.startswith('1. ') or re.match(r'^\d+\.', line):
            text = re.sub(r'^\d+\.\s*', '', line)
            doc.add_paragraph(text, style='List Number')
        elif line.strip() == '---':
            doc.add_page_break() # Using horizontal rules as page breaks for a cleaner look
        elif line.startswith('```'):
            continue # Skip code block markers
        elif line.strip():
            # Handle some basic inline formatting
            p = doc.add_paragraph()
            text = line
            # Bold
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            p.add_run(text)
            
    doc.save(OUTPUT_DOCX)
    print(f"Successfully created {OUTPUT_DOCX}")

def convert_to_pdf(content):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    lines = content.splitlines()
    for line in lines:
        if line.startswith('# '):
            pdf.set_font("Arial", 'B', 18)
            pdf.cell(0, 15, line[2:].encode('latin-1', 'replace').decode('latin-1'), ln=True)
            pdf.ln(5)
        elif line.startswith('## '):
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, line[3:].encode('latin-1', 'replace').decode('latin-1'), ln=True)
            pdf.ln(2)
        elif line.startswith('### '):
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, line[4:].encode('latin-1', 'replace').decode('latin-1'), ln=True)
        elif line.strip() == '---':
            pdf.add_page()
        elif line.strip():
            pdf.set_font("Arial", size=11)
            # Remove bold markers for PDF (fpdf basic doesn't handle inline markdown easily)
            clean_line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
            pdf.multi_cell(0, 8, clean_line.encode('latin-1', 'replace').decode('latin-1'))
            pdf.ln(2)
            
    pdf.output(OUTPUT_PDF)
    print(f"Successfully created {OUTPUT_PDF}")

def main():
    if not os.path.exists(SOURCE_MD):
        print(f"Error: {SOURCE_MD} not found.")
        return

    with open(SOURCE_MD, "r", encoding="utf-8") as f:
        content = f.read()

    print("Converting to DOCX...")
    convert_to_docx(content)
    
    print("Converting to PDF...")
    convert_to_pdf(content)

if __name__ == "__main__":
    main()
