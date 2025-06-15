import os
import re
import requests
from docx import Document
from pptx import Presentation
from pptx.util import Inches

TEMPLATE_DOCX = os.path.join("templates", "IT_Current_Status_Assessment_Report_Template.docx")
TEMPLATE_PPTX = os.path.join("templates", "IT_Current_Status_Executive_Report_Template.pptx")
OUTPUT_DIR    = "temp_sessions"

def _to_direct_drive_url(url: str) -> str:
    """If this is a Google Drive 'view' link, convert to direct-download."""
    m = re.search(r"/d/([A-Za-z0-9_-]+)", url)
    if m:
        fid = m.group(1)
        return f"https://drive.google.com/uc?export=download&id={fid}"
    return url

def generate_assessment_docs(session_id, summary, recommendations, findings, chart_paths):
    print(f"[DEBUG] Entered generate_assessment_docs for session {session_id}", flush=True)
    out_dir = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(out_dir, exist_ok=True)

    # 1. Download & normalize chart images
    local_charts = {}
    for name, url in chart_paths.items():
        dl_url = _to_direct_drive_url(url)
        print(f"[DEBUG] Fetching chart '{name}' from {dl_url}", flush=True)
        r = requests.get(dl_url)
        r.raise_for_status()
        local_path = os.path.join(out_dir, f"{name}.png")
        with open(local_path, "wb") as f:
            f.write(r.content)
        print(f"[DEBUG] Saved chart to: {local_path}", flush=True)
        local_charts[name] = local_path

    # 2. Load templates
    docx = Document(TEMPLATE_DOCX)
    pptx = Presentation(TEMPLATE_PPTX)

    # 3. Fill placeholders
    replacements = {
        "{{ session_id }}":   session_id,
        "{{ content_1 }}":    summary,
        "{{ content_19 }}":   recommendations,
        "{{ content_16 }}":   findings,
    }
    for p in docx.paragraphs:
        for key, val in replacements.items():
            if key in p.text:
                p.text = p.text.replace(key, val)
    for table in docx.tables:
        for row in table.rows:
            for cell in row.cells:
                for key, val in replacements.items():
                    if key in cell.text:
                        cell.text = cell.text.replace(key, val)
    for slide in pptx.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for key, val in replacements.items():
                    if key in shape.text:
                        shape.text = shape.text.replace(key, val)

    # 4. Embed charts in DOCX
    for name, path in local_charts.items():
        docx.add_page_break()
        docx.add_picture(path, width=Inches(6))

    # 5. Embed charts in PPTX
    for name, path in local_charts.items():
        slide = pptx.slides.add_slide(pptx.slide_layouts[5])
        slide.shapes.add_picture(path, Inches(1), Inches(1), width=Inches(8))

    # 6. Save out
    docx_out = os.path.join(out_dir, f"IT_Current_Status_Assessment_Report_{session_id}.docx")
    pptx_out = os.path.join(out_dir, f"IT_Current_Status_Executive_Report_{session_id}.pptx")

    docx.save(docx_out)
    print(f"[DEBUG] Saved DOCX file to: {docx_out}", flush=True)

    pptx.save(pptx_out)
    print(f"[DEBUG] Saved PPTX file to: {pptx_out}", flush=True)

    # 7. Return URLs relative to the /files endpoint
    return {
        "docx_url": f"/files/{session_id}/{os.path.basename(docx_out)}",
        "pptx_url": f"/files/{session_id}/{os.path.basename(pptx_out)}"
    }
