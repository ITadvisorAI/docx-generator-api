import os
from docx import Document
from pptx import Presentation
from pptx.util import Inches, Pt

# Point to templates in the templates/ folder
TEMPLATE_DOCX = os.path.join("templates", "IT_Current_Status_Assessment_Report_Template.docx")
TEMPLATE_PPTX = os.path.join("templates", "IT_Current_Status_Executive_Report_Template.pptx")
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
    # Prepare output folder
    out_dir = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(out_dir, exist_ok=True)

    # Load templates
    docx_template = Document(TEMPLATE_DOCX)
    pptx_template = Presentation(TEMPLATE_PPTX)

    # Replacement mapping
    replacements = {
        "{{ session_id }}": session_id,
        "{{ content_1 }}": summary,
        "{{ content_19 }}": recommendations,
        "{{ content_16 }}": findings
    }

    # Fill templates
    fill_docx_template(docx_template, replacements)
    fill_pptx_template(pptx_template, replacements)

    # Save outputs
    docx_out = f"{out_dir}/IT_Current_Status_Assessment_Report_{session_id}.docx"
    pptx_out = f"{out_dir}/IT_Current_Status_Executive_Report_{session_id}.pptx"
    docx_template.save(docx_out)
    pptx_template.save(pptx_out)

    return {
        # These URLs are served by the /files route in app.py
        "docx_url": f"/files/{session_id}/IT_Current_Status_Assessment_Report_{session_id}.docx",
        "pptx_url": f"/files/{session_id}/IT_Current_Status_Executive_Report_{session_id}.pptx"
    }
