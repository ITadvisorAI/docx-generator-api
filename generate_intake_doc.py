from flask import Flask, request, jsonify, send_from_directory, abort
from docx import Document
import os
import shutil
from threading import Thread
import re
import requests

app = Flask(__name__)

# ✅ Sanitize session_id to make file paths safe
def sanitize_session_id(session_id):
    return re.sub(r"[^\w\-]", "_", session_id)


# ✅ Background thread for document generation
def process_intake_document(data):
    try:
        session_id = data.get('session_id')
        safe_session_id = sanitize_session_id(session_id)
        intake = data.get('intake_answers', {})
        files = data.get('files', [])

        print(f"🛠️ Processing DOCX for session: {session_id} → {safe_session_id}")

        folder_path = os.path.join("temp_sessions", f"Temp_{safe_session_id}")
        os.makedirs(folder_path, exist_ok=True)

        template_path = "intakeform.docx"
        output_file = os.path.join(folder_path, f"intake_{safe_session_id}.docx")

        if not os.path.exists(template_path):
            print("❌ intakeform.docx not found.")
            return

        shutil.copy(template_path, output_file)
        doc = Document(output_file)

        doc.add_heading("Selected Programs", level=1)
        selected_categories = intake.get("selected_categories", [])
        selected_programs = intake.get("selected_programs", {})

        for category in selected_categories:
            doc.add_paragraph(category, style="ListBullet")
            for program in selected_programs.get(category, []):
                doc.add_paragraph(f"  - {program}", style="ListBullet2")

        doc.add_heading("Transformation Questions", level=1)
        doc.add_paragraph(_
