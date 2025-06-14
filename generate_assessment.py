import os
import requests
from docx import Document
from pptx import Presentation
from pptx.util import Inches

# Template paths
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

def generate_assessment_docs(session_id, summary, recommendations, findings, chart_paths):
    # Prepare output folder
    out_dir = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(out_dir, exist_ok=True)

    # 1. Download chart images
    local_charts = {}
    for name, url in chart_paths.items():
        resp = requests.get(url)
        resp.raise_for_status()
        local_path = os.path.join(out_dir, f"{name}.png")
        with open(local_path, "wb") as f:
            f.write(resp.content)
        local_charts[name] = local_path

    # 2. Load templates
    docx_template = Document(TEMPLATE_DOCX)
    pptx_template = Presentation(TEMPLATE_PPTX)

    # 3. Fill text placeholders
    replacements = {
        "{{ session_id }}": session_id,
        "{{ content_1 }}": summary,
        "{{ content_19 }}": recommendations,
        "{{ content_16 }}": findings
    }
    fill_docx_template(docx_template, replacements)
    fill_pptx_template(pptx_template, replacements)

    # 4. Embed charts into DOCX
    for name, path in local_charts.items():
        docx_template.add_page_break()
        docx_template.add_picture(path, width=Inches(6))

    # 5. Embed charts into PPTX
    for name, path in local_charts.items():
        slide = pptx_template.slides.add_slide(pptx_template.slide_layouts[5])
        slide.shapes.add_picture(path, Inches(1), Inches(1), width=Inches(8))

    # 6. Save outputs
    docx_out = os.path.join(out_dir, f"IT_Current_Status_Assessment_Report_{session_id}.docx")
    pptx_out = os.path.join(out_dir, f"IT_Current_Status_Executive_Report_{session_id}.pptx")
    docx_template.save(docx_out)
    pptx_template.save(pptx_out)

    # 7. Return service-relative URLs
    return {
        "docx_url": f"/files/{session_id}/IT_Current_Status_Assessment_Report_{session_id}.docx",
        "pptx_url": f"/files/{session_id}/IT_Current_Status_Executive_Report_{session_id}.pptx"
    }
