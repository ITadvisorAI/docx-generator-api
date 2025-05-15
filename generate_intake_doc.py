from flask import Flask, request, jsonify, send_from_directory, abort
from docx import Document
import os
import shutil
from threading import Thread
import re

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
        doc.add_paragraph(f"1. {intake.get('q1', '')}")
        doc.add_paragraph(f"2. {intake.get('q2', '')}")
        doc.add_paragraph(f"3. {intake.get('q3', '')}")
        doc.add_paragraph(f"4. {intake.get('q4', '')}")
        doc.add_paragraph(f"5. {intake.get('q5', '')}")

        if files:
            doc.add_heading("Uploaded Files", level=1)
            for f in files:
                doc.add_paragraph(f"{f.get('name', 'Unknown')} ({f.get('type', '')})", style="ListBullet")
                doc.add_paragraph(f"URL: {f.get('url', '')}", style="Normal")

        doc.save(output_file)
        print(f"✅ DOCX saved: {output_file}")

    except Exception as e:
        print("❌ Error in background processing:")
        print(str(e))


@app.route('/generate_intake', methods=['POST'])
def generate_intake():
    try:
        raw = request.data.decode("utf-8")
        print("📦 RAW REQUEST:")
        print(raw)

        data = request.get_json(force=True)
        print("✅ Parsed JSON:")
        print(data)

        session_id = data.get('session_id')
        safe_session_id = sanitize_session_id(session_id)
        email = data.get('email')
        intake = data.get('intake_answers', {})

        if not session_id or not email or not intake:
            return jsonify({
                "error": "Missing session_id, email, or intake_answers"
            }), 400

        # Start DOCX generation thread
        Thread(target=process_intake_document, args=(data,)).start()

        return jsonify({
            "status": "processing",
            "session_id": session_id,
            "file_name": f"intake_{safe_session_id}.docx",
            "file_url": f"https://docx-generator-api.onrender.com/files/Temp_{safe_session_id}/intake_{safe_session_id}.docx"
        }), 202

    except Exception as e:
        print("❌ Exception in /generate_intake:")
        print(str(e))
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# ✅ Route to serve files from temp_sessions
@app.route('/files/<path:filename>', methods=['GET'])
def serve_generated_file(filename):
    try:
        directory = os.path.join(os.getcwd(), 'temp_sessions')
        full_path = os.path.join(directory, filename)

        if not os.path.exists(full_path):
            print(f"❌ Not found: {full_path}")
            abort(404)

        print(f"📤 Serving file: {full_path}")
        return send_from_directory(directory, filename, as_attachment=False)

    except Exception as e:
        print(f"❌ Error in /files: {str(e)}")
        abort(500)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
