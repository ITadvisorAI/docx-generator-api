import os
from docx import Document
from pptx import Presentation
from pptx.util import Inches, Pt

TEMPLATE_DOCX = "IT_Current_Status_Assessment_Report_Template.docx"
TEMPLATE_PPTX = "IT_Current_Status_Executive_Report_Template.pptx"
OUTPUT_DIR = "temp_sessions"

def fill_docx_template(doc: Document, replacements: dict):
    for para in doc.paragraphs:
        for key, val in replacements.items():
            if key in para.text:
                para.text = para.text.replace(key, val)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for key, val in replacements.items():
                    if key in cell.text:
                        cell.text = cell.text.replace(key, val)

def fill_pptx_template(prs: Presentation, replacements: dict):
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for key, val in replacements.items():
                    if key in shape.text:
                        shape.text = shape.text.replace(key, val)

def generate_assessment_docs(session_id, summary, recommendations, findings):
    docx_template = Document(TEMPLATE_DOCX)
    pptx_template = Presentation(TEMPLATE_PPTX)

    replacements = {
        "{{ session_id }}": session_id,
        "{{ email }}": "user@example.com",
        "{{ content_1 }}": summary,
        "{{ content_19 }}": recommendations,
        "{{ content_16 }}": findings
    }

    fill_docx_template(docx_template, replacements)
    fill_pptx_template(pptx_template, replacements)

    output_path = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(output_path, exist_ok=True)

    docx_out = os.path.join(output_path, f"IT_Current_Status_Assessment_Report_{session_id}.docx")
    pptx_out = os.path.join(output_path, f"IT_Current_Status_Executive_Report_{session_id}.pptx")

    docx_template.save(docx_out)
    pptx_template.save(pptx_out)

    return {
        "docx_url": f"/files/{session_id}/IT_Current_Status_Assessment_Report_{session_id}.docx",
        "pptx_url": f"/files/{session_id}/IT_Current_Status_Executive_Report_{session_id}.pptx"
    }
