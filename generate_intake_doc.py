from flask import Flask, request, jsonify, send_from_directory, abort
from docx import Document
import os
import shutil
from threading import Thread
import re
import requests
import traceback

app = Flask(__name__)

# ✅ Sanitize session_id to make file paths safe
def sanitize_session_id(session_id):
    return re.sub(r"[^\w\-]", "_", session_id)

# ✅ Background thread for document generation
def process_intake_document(data):
    try:
        print("🚀 Thread started: processing intake document")

        session_id = data.get('session_id')
        if not session_id:
            print("❌ Missing session_id in data.")
            return

        safe_session_id = sanitize_session_id(session_id)
        intake = data.get('intake_answers', {})
        files = data.get('files', [])

        print(f"🛠️ Generating DOCX for session: {session_id} → {safe_session_id}")

        folder_path = os.path.join("temp_sessions", f"Temp_{safe_session_id}")
        os.makedirs(folder_path, exist_ok=True)
        print(f"📁 Folder created or exists: {folder_path}")

        # Resolve absolute path to template
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(script_dir, "intakeform.docx")
        output_file = os.path.join(folder_path, f"intake_{safe_session_id}.docx")

        print(f"🔍 Looking for template at: {template_path}")
        if not os.path.exists(template_path):
            print(f"❌ Template file missing: {template_path}")
            return

        shutil.copy(template_path, output_file)
        print(f"📄 Template copied to: {output_file}")

        doc = Document(output_file)

        doc.add_heading("Selected Programs", level=1)
        selected_categories = intake.get("selected_categories", [])
        selected_programs = intake.get("selected_programs", {})

        for category in selected_categories:
            doc.add_paragraph(category, style="ListBullet")
            programs = selected_programs.get(category, [])
            if not programs:
                doc.add_paragraph("  - No specific programs selected", style="ListBullet2")
            else:
                for program in programs:
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
        print(f"✅ DOCX successfully saved: {output_file}")
        print(f"🔗 Public URL: /files/Temp_{safe_session_id}/intake_{safe_session_id}.docx")

    except Exception as e:
        print("❌ Exception in process_intake_document:")
        traceback.print_exc()

# ✅ Intake DOCX Generator Route
@app.route('/generate_intake', methods=['POST'])
def generate_intake():
    try:
        print("📥 /generate_intake endpoint called")

        raw = request.data.decode("utf-8")
        print("📦 RAW REQUEST:")
        print(raw)

        data = request.get_json(force=True)
        print("✅ Parsed JSON:")
        print(data)

        session_id = data.get('session_id')
        email = data.get('email')
        intake = data.get('intake_answers', {})

        if not session_id or not email or not intake:
            print("❌ Missing required fields in request.")
            return jsonify({
                "error": "Missing session_id, email, or intake_answers"
            }), 400

        print("🧵 Launching background thread...")
        Thread(target=process_intake_document, args=(data,)).start()
        print("✅ Background thread launched")

        safe_session_id = sanitize_session_id(session_id)
        return jsonify({
            "status": "processing",
            "session_id": session_id,
            "file_name": f"intake_{safe_session_id}.docx",
            "file_url": f"https://docx-generator-api.onrender.com/files/Temp_{safe_session_id}/intake_{safe_session_id}.docx"
        }), 202

    except Exception as e:
        print("❌ Exception in /generate_intake:")
        traceback.print_exc()
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# ✅ Route to serve generated DOCX files
@app.route('/files/<path:filename>', methods=['GET'])
def serve_generated_file(filename):
    try:
        directory = os.path.join(os.getcwd(), 'temp_sessions')
        full_path = os.path.join(directory, filename)

        if not os.path.isfile(full_path):
            print(f"❌ File not found: {full_path}")
            abort(404)

        print(f"📤 Serving file: {full_path}")
        return send_from_directory(directory, filename, as_attachment=False)

    except Exception as e:
        print(f"❌ Exception in /files route:")
        traceback.print_exc()
        abort(500)

# ✅ Proxy route to forward email to Make.com webhook
@app.route('/start_session', methods=['POST'])
def start_session():
    try:
        data = request.get_json(force=True)
        print("📩 Received session start request:")
        print(data)

        make_webhook = 'https://hook.us2.make.com/1ivi9q9x6l253tikb557hemgtl7n2bv9'
        r = requests.post(make_webhook, json=data)

        if r.status_code == 200:
            print("✅ Session initiated via Make.com")
            return jsonify({"message": "Session started"}), 200
        else:
            print(f"❌ Failed to POST to Make.com: {r.status_code}")
            return jsonify({"error": "Make webhook failed", "status": r.status_code}), r.status_code

    except Exception as e:
        print("❌ Exception in /start_session:")
        traceback.print_exc()
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# ✅ Health check endpoint
@app.route('/healthz', methods=['GET'])
def health_check():
    return "ok", 200

# ✅ Run app (Render will assign dynamic port via $PORT env var)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
