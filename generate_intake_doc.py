from flask import Flask, request, jsonify
from docx import Document
import os
import shutil

app = Flask(__name__)

@app.route('/generate_intake', methods=['POST'])
def generate_intake():
    try:
        # Print raw request data
        raw = request.data.decode("utf-8")
        print("📦 RAW REQUEST BODY:")
        print(raw)

        # Attempt to parse JSON
        data = request.get_json(force=True)
        print("✅ Parsed JSON:")
        print(data)

        # Extract fields
        session_id = data.get('session_id')
        email = data.get('email')
        intake = data.get('intake_answers', {})
        files = data.get('files', [])

        if not session_id or not email or not intake:
            print("❌ Missing one or more required fields.")
            return jsonify({
                "error": "Missing required fields: session_id, email, or intake_answers"
            }), 400

        # Create folder path
        folder_path = os.path.join("temp_sessions", f"Temp_{session_id}")
        os.makedirs(folder_path, exist_ok=True)

        # Load and copy the template
        template_path = "intakeform.docx"
        output_file = os.path.join(folder_path, f"intake_{session_id}.docx")

        if not os.path.exists(template_path):
            print("❌ intakeform.docx template not found.")
            return jsonify({"error": "Missing intakeform.docx template."}), 500

        shutil.copy(template_path, output_file)

        doc = Document(output_file)

        # Populate selected programs
        doc.add_heading("Selected Programs", level=1)
        selected_categories = intake.get("selected_categories", [])
        selected_programs = intake.get("selected_programs", {})

        for category in selected_categories:
            doc.add_paragraph(category, style="ListBullet")
            for program in selected_programs.get(category, []):
                doc.add_paragraph(f"  - {program}", style="ListBullet2")

        # Add questions
        doc.add_heading("Transformation Questions", level=1)
        doc.add_paragraph(f"1. {intake.get('q1', '')}")
        doc.add_paragraph(f"2. {intake.get('q2', '')}")
        doc.add_paragraph(f"3. {intake.get('q3', '')}")
        doc.add_paragraph(f"4. {intake.get('q4', '')}")
        doc.add_paragraph(f"5. {intake.get('q5', '')}")

        # Add uploaded file info
        if files:
            doc.add_heading("Uploaded Files", level=1)
            for f in files:
                name = f.get('name', 'Unnamed File')
                url = f.get('url', '')
                file_type = f.get('type', 'unknown')
                doc.add_paragraph(f"{name} ({file_type})", style="ListBullet")
                doc.add_paragraph(f"URL: {url}", style="Normal")

        doc.save(output_file)

        file_url = f"https://docx-generator-api.onrender.com/files/Temp_{session_id}/intake_{session_id}.docx"
        print("✅ Intake document generated and saved successfully.")
        print(f"📄 File URL: {file_url}")

        return jsonify({
            "session_id": session_id,
            "file_name": f"intake_{session_id}.docx",
            "file_url": file_url
        })

    except Exception as e:
        print("❌ Exception occurred in /generate_intake:")
        print(str(e))
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
