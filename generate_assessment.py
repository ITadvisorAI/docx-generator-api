import os
import traceback
from docx import Document
from docx.shared import Inches
from pptx import Presentation
from pptx.util import Inches

BASE_DIR = "temp_sessions"
PUBLIC_BASE_URL = "https://docx-generator-api.onrender.com/files"

def generate_docs(data):
    try:
        session_id = data.get("session_id")
        score_summary = data.get("score_summary")
        recommendations = data.get("recommendations")
        key_findings = data.get("key_findings", "")

        if not session_id or not score_summary or not recommendations:
            raise ValueError("Missing required fields: session_id, score_summary, or recommendations")

        folder_path = os.path.join(BASE_DIR, session_id)
        os.makedirs(folder_path, exist_ok=True)

        # === DOCX Generation ===
        docx_path = os.path.join(folder_path, "IT_Current_Status_Assessment_Report.docx")
        doc = Document()
        doc.add_heading("IT Infrastructure Assessment", 0)
        doc.add_paragraph(f"Session ID: {session_id}")
        doc.add_heading("Tier Distribution Summary", level=1)
        doc.add_paragraph(score_summary)
        doc.add_heading("Modernization Recommendations", level=1)
        doc.add_paragraph(recommendations)
        if key_findings:
            doc.add_heading("Key Executive Findings", level=1)
            doc.add_paragraph(key_findings)
        doc.save(docx_path)

        # === PPTX Generation ===
        pptx_path = os.path.join(folder_path, "IT_Current_Status_Executive_Report.pptx")
        ppt = Presentation()
        slide1 = ppt.slides.add_slide(ppt.slide_layouts[0])
        slide1.shapes.title.text = "Executive IT Summary"
        slide1.placeholders[1].text = f"Session ID: {session_id}"

        slide2 = ppt.slides.add_slide(ppt.slide_layouts[1])
        slide2.shapes.title.text = "Tier Summary"
        slide2.placeholders[1].text = score_summary

        slide3 = ppt.slides.add_slide(ppt.slide_layouts[1])
        slide3.shapes.title.text = "Recommendations"
        slide3.placeholders[1].text = recommendations

        if key_findings:
            slide4 = ppt.slides.add_slide(ppt.slide_layouts[1])
            slide4.shapes.title.text = "Key Findings"
            slide4.placeholders[1].text = key_findings

        ppt.save(pptx_path)

        # === Build public URLs ===
        docx_url = f"{PUBLIC_BASE_URL}/{session_id}/IT_Current_Status_Assessment_Report.docx"
        pptx_url = f"{PUBLIC_BASE_URL}/{session_id}/IT_Current_Status_Executive_Report.pptx"

        return {
            "docx_url": docx_url,
            "pptx_url": pptx_url
        }

    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}
