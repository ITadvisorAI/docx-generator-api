
from flask import Flask, request, jsonify
from docx import Document
import os
import shutil

app = Flask(__name__)

@app.route('/generate_intake', methods=['POST'])
def generate_intake():
    data = request.get_json()
    session_id = data['session_id']
    intake = data['intake_answers']
    email = data['email']

    folder_path = os.path.join("temp_sessions", f"Temp_{session_id}")
    os.makedirs(folder_path, exist_ok=True)

    template_path = "intakeform.docx"
    output_file = os.path.join(folder_path, f"intake_{session_id}.docx")
    shutil.copy(template_path, output_file)

    doc = Document(output_file)
    doc.add_heading("Selected Programs", level=1)

    for category in intake["selected_categories"]:
        doc.add_paragraph(category, style="ListBullet")
        for program in intake["selected_programs"].get(category, []):
            doc.add_paragraph(f"  - {program}", style="ListBullet2")

    doc.add_heading("Transformation Questions", level=1)
    doc.add_paragraph(f"1. {intake['q1']}")
    doc.add_paragraph(f"2. {intake['q2']}")
    doc.add_paragraph(f"3. {intake['q3']}")
    doc.add_paragraph(f"4. {intake['q4']}")
    doc.add_paragraph(f"5. {intake['q5']}")

    doc.save(output_file)

    return jsonify({
        "session_id": session_id,
        "file_name": f"intake_{session_id}.docx",
        "file_url": f"https://yourdomain.com/files/Temp_{session_id}/intake_{session_id}.docx"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
