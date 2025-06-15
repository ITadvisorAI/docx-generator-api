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
    Supports both positional signature and keyword-driven payloads.
    """
    # Merge args/kwargs into data dict
    data = dict(kwargs)
    if args:
        data.setdefault("session_id",      args[0] if len(args) > 0 else "")
        data.setdefault("score_summary",    args[1] if len(args) > 1 else "")
        data.setdefault("recommendations",  args[2] if len(args) > 2 else "")
        data.setdefault("key_findings",     args[3] if len(args) > 3 else "")
        data.setdefault("chart_paths",      args[4] if len(args) > 4 else {})

    # Extract common fields
    session_id     = data.get("session_id", "")
    print(f"[DEBUG] Entered generate_assessment_docs for session: {session_id}", flush=True)

    # Prepare output directory
    session_dir = os.path.join(OUTPUT_ROOT, session_id)
    os.makedirs(session_dir, exist_ok=True)

    # Download chart images
    local_charts = {}
    for name, url in data.get("chart_paths", {}).items():
        try:
            dl_url = _to_direct_drive_url(url)
            resp = requests.get(dl_url); resp.raise_for_status()
            chart_path = os.path.join(session_dir, f"{name}.png")
            with open(chart_path, "wb") as f:
                f.write(resp.content)
            local_charts[name] = chart_path
            print(f"[DEBUG] Saved chart {name} to {chart_path}", flush=True)
        except Exception as e:
            print(f"[ERROR] Failed to download chart '{name}': {e}", flush=True)

    # Build placeholder mapping dynamically
    placeholders = {}
    # Core and URL fields
    for field in ["session_id", "email", "goal", "score_summary", "recommendations", "key_findings", "hw_gap_url", "sw_gap_url"]:
        if field in data:
            placeholders[f"{{{{ {field} }}}}"] = str(data[field])
    # Content sections 1-20
    for i in range(1, 21):
        placeholders[f"{{{{ content_{i} }}}}"] = str(data.get(f"content_{i}", ""))
    # Appendices
    placeholders["{{ appendix_classification_matrix }}"] = str(data.get("appendix_classification_matrix", ""))
    placeholders["{{ appendix_data_sources }}"]        = str(data.get("appendix_data_sources", ""))
    # Slide placeholders
    slide_keys = [
        'executive_summary','it_landscape_overview','hardware_analysis','software_analysis',
        'tier_classification_summary','hardware_lifecycle_chart','software_licensing_review',
        'security_vulnerability_heatmap','performance_&_uptime_trends','system_reliability_overview',
        'scalability_insights','legacy_system_exposure','obsolete_platform_matrix',
        'cloud_migration_targets','strategic_it_alignment','business_impact_of_gaps',
        'cost_of_obsolescence','sustainability_&_green_it','remediation_recommendations',
        'roadmap_&_next_steps'
    ]
    for key in slide_keys:
        placeholders[f"{{{{ slide_{key} }}}}"] = str(data.get(f"slide_{key}", ""))

    # --------- DOCX Generation ---------
    doc = Document(TEMPLATE_DOCX)
    for para in doc.paragraphs:
        for ph, val in placeholders.items():
            if ph in para.text:
                para.text = para.text.replace(ph, val)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for ph, val in placeholders.items():
                    if ph in cell.text:
                        cell.text = cell.text.replace(ph, val)
    for chart_path in local_charts.values():
        doc.add_page_break()
        doc.add_picture(chart_path, width=Inches(6))
    docx_filename = f"IT_Current_Status_Assessment_Report_{session_id}.docx"
    docx_out = os.path.join(session_dir, docx_filename)
    doc.save(docx_out)
    print(f"[DEBUG] Saved DOCX to: {docx_out}", flush=True)

    # --------- PPTX Generation ---------
    prs = Presentation(TEMPLATE_PPTX)
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, 'text'):
                for ph, val in placeholders.items():
                    if ph in shape.text:
                        shape.text = shape.text.replace(ph, val)
    for chart_path in local_charts.values():
        sl = prs.slides.add_slide(prs.slide_layouts[5])
        sl.shapes.add_picture(chart_path, Inches(1), Inches(1), width=Inches(8))
    pptx_filename = f"IT_Current_Status_Executive_Report_{session_id}.pptx"
    pptx_out = os.path.join(session_dir, pptx_filename)
    prs.save(pptx_out)
    print(f"[DEBUG] Saved PPTX to: {pptx_out}", flush=True)

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
