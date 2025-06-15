import os
import re
import requests
from docx import Document
from pptx import Presentation
from pptx.util import Inches
from drive_utils import upload_to_drive

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DOCX = os.path.join(BASE_DIR, "templates", "IT_Current_Status_Assessment_Report_Template.docx")
TEMPLATE_PPTX = os.path.join(BASE_DIR, "templates", "IT_Current_Status_Executive_Report_Template.pptx")
OUTPUT_ROOT = os.path.join(BASE_DIR, "temp_sessions")


def _to_direct_drive_url(url: str) -> str:
    """Convert a Drive view link to a direct download URL."""
    match = re.search(r"/d/([A-Za-z0-9_-]+)", url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url


def generate_assessment_docs(*args, **kwargs) -> dict:
    """
    Generate a filled DOCX and PPTX based on templates, then upload to Drive.
    Supports both old positional signature:
      (session_id, score_summary, recommendations, key_findings, chart_paths)
    and new keyword-driven payloads:
      session_id, score_summary, recommendations, key_findings, chart_paths,
      hw_gap_url, sw_gap_url, email
    """
    # Build data dict from args or kwargs
    data = dict(kwargs)
    if args:
        data.setdefault("session_id", args[0] if len(args) > 0 else "")
        data.setdefault("score_summary", args[1] if len(args) > 1 else "")
        data.setdefault("recommendations", args[2] if len(args) > 2 else "")
        data.setdefault("key_findings", args[3] if len(args) > 3 else "")
        data.setdefault("chart_paths", args[4] if len(args) > 4 else {})

    session_id = data.get("session_id", "")
    score_summary = data.get("score_summary", "")
    recommendations = data.get("recommendations", "")
    key_findings = data.get("key_findings", "")
    chart_paths = data.get("chart_paths", {})
    hw_gap_url = data.get("hw_gap_url", "")
    sw_gap_url = data.get("sw_gap_url", "")
    email = data.get("email", "")

    print(f"[DEBUG] Entered generate_assessment_docs for session: {session_id}", flush=True)

    # Prepare output directory
    session_dir = os.path.join(OUTPUT_ROOT, session_id)
    os.makedirs(session_dir, exist_ok=True)

    # Download and save chart images
    local_charts = {}
    for name, url in chart_paths.items():
        try:
            dl_url = _to_direct_drive_url(url)
            print(f"[DEBUG] Fetching chart '{name}' from {dl_url}", flush=True)
            resp = requests.get(dl_url)
            resp.raise_for_status()
            chart_path = os.path.join(session_dir, f"{name}.png")
            with open(chart_path, "wb") as f:
                f.write(resp.content)
            local_charts[name] = chart_path
            print(f"[DEBUG] Saved chart to: {chart_path}", flush=True)
        except Exception as e:
            print(f"[ERROR] Failed to download chart '{name}': {e}", flush=True)

    # Define placeholder replacements
    placeholders = {
        "{{ session_id }}": session_id,
        "{{ email }}": email,
        "{{ content_1 }}": score_summary,
        "{{ content_2 }}": f"Hardware GAP details: {hw_gap_url}",
        "{{ content_3 }}": f"Software GAP details: {sw_gap_url}",
        "{{ content_16 }}": key_findings,
        "{{ content_19 }}": recommendations,
        # Populate slide placeholders in PPTX
        "{{ slide_executive_summary }}": score_summary,
        "{{ slide_hardware_analysis }}": f"Hardware GAP details: {hw_gap_url}",
        "{{ slide_software_analysis }}": f"Software GAP details: {sw_gap_url}",
        "{{ slide_business_impact_of_gaps }}": key_findings,
        "{{ slide_remediation_recommendations }}": recommendations,
    }

    # --------- DOCX Generation ---------
    doc = Document(TEMPLATE_DOCX)
    # Replace placeholders in paragraphs
    for para in doc.paragraphs:
        for key, val in placeholders.items():
            if key in para.text:
                para.text = para.text.replace(key, val)
    # Replace in tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for key, val in placeholders.items():
                    if key in cell.text:
                        cell.text = cell.text.replace(key, val)
    # Add charts to DOCX
    for chart_path in local_charts.values():
        doc.add_page_break()
        doc.add_picture(chart_path, width=Inches(6))
    # Save DOCX
    docx_filename = f"IT_Current_Status_Assessment_Report_{session_id}.docx"
    docx_out = os.path.join(session_dir, docx_filename)
    doc.save(docx_out)
    print(f"[DEBUG] Saved DOCX file to: {docx_out}", flush=True)

    # --------- PPTX Generation ---------
    prs = Presentation(TEMPLATE_PPTX)
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, 'text'):
                for key, val in placeholders.items():
                    if key in shape.text:
                        shape.text = shape.text.replace(key, val)
    # Append charts as new slides
    for chart_path in local_charts.values():
        slide = prs.slides.add_slide(prs.slide_layouts[5])
        slide.shapes.add_picture(chart_path, Inches(1), Inches(1), width=Inches(8))
    # Save PPTX
    pptx_filename = f"IT_Current_Status_Executive_Report_{session_id}.pptx"
    pptx_out = os.path.join(session_dir, pptx_filename)
    prs.save(pptx_out)
    print(f"[DEBUG] Saved PPTX file to: {pptx_out}", flush=True)

    # --------- Upload to Google Drive ---------
    docx_url = upload_to_drive(docx_out, docx_filename, session_id)
    print(f"[DEBUG] Uploaded DOCX to Drive: {docx_url}", flush=True)
    try:
        pptx_url = upload_to_drive(pptx_out, pptx_filename, session_id)
        print(f"[DEBUG] Uploaded PPTX to Drive: {pptx_url}", flush=True)
    except Exception as e:
        print(f"[ERROR] PPTX upload failed: {e}", flush=True)
        pptx_url = ""

    return {"docx_url": docx_url, "pptx_url": pptx_url}
