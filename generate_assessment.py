import os
from docx import Document
from pptx import Presentation
from pptx.util import Inches
import logging

BASE_DIR = "temp_sessions"

def generate_docs(data):
    session_id = data.get("session_id")
    score_summary = data.get("score_summary")
    recommendations = data.get("recommendations")
    key_findings = data.get("key_findings", "")

    if not session_id or not score_summary or not recommendations:
        raise ValueError("Missing required fields in request")

    logging.info(f"🧾 Generating reports for session: {session_id}")
    folder_name = session_id
    folder_path = os.path.join(BASE_DIR, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    docx_path = os.path.join(folder_path, "IT_Current_Status_Assessment_Report.docx")
    pptx_path = os.path.join(folder_path, "IT_Current_Status_Executive_Report.pptx")

    # === DOCX Generation ===
    doc = Document()
    doc.add_heading("IT Current Status Assessment", 0)
    doc.add_paragraph(f"Session ID: {session_id}")
    doc.add_paragraph("Score Summary:")
    doc.add_paragraph(score_summary)
    doc.add_paragraph("Recommendations:")
    doc.add_paragraph(recommendations)
    if key_findings:
        doc.add_paragraph("Key Findings:")
        doc.add_paragraph(key_findings)
    doc.save(docx_path)
    logging.info(f"📄 DOCX created: {docx_path}")

    # === PPTX Generation ===
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    title, content = slide.shapes.title, slide.placeholders[1]
    title.text = "IT Executive Summary"
    content.text = f"Score Summary:\n{score_summary}\n\nRecommendations:\n{recommendations}"
    if key_findings:
        slide2 = prs.slides.add_slide(prs.slide_layouts[1])
        slide2.shapes.title.text = "Key Findings"
        slide2.placeholders[1].text = key_findings
    prs.save(pptx_path)
    logging.info(f"📊 PPTX created: {pptx_path}")

    # Return public URLs
    public_base = f"https://docx-generator-api.onrender.com/files/{folder_name}"
    return {
        "docx_url": f"{public_base}/IT_Current_Status_Assessment_Report.docx",
        "pptx_url": f"{public_base}/IT_Current_Status_Executive_Report.pptx"
    }
