import os
from flask import Flask, request, jsonify, send_from_directory
from generate_assessment import generate_assessment_docs

app = Flask(__name__)

# Directory where generated reports are stored
temp_dir = os.path.join(os.getcwd(), 'temp_sessions')

@app.route('/files/<session_id>/<path:filename>')
def serve_generated_file(session_id, filename):
    """Serve generated report files."""
    directory = os.path.join(temp_dir, session_id)
    return send_from_directory(directory, filename)

@app.route("/generate_assessment", methods=["POST"])
def generate_assessment():
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        score_summary = data.get("score_summary")
        recommendations = data.get("recommendations")
        key_findings = data.get("key_findings")

        result = generate_assessment_docs(
            session_id,
            score_summary,
            recommendations,
            key_findings
        )

        # Prefix URLs with this service's base URL
        base_url = os.getenv("DOCX_SERVICE_URL", "https://docx-generator-api.onrender.com")
        docx_path = result["docx_url"].lstrip('/')
        pptx_path = result["pptx_url"].lstrip('/')
        result["docx_url"] = f"{base_url}/files/{docx_path}"
        result["pptx_url"] = f"{base_url}/files/{pptx_path}"

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["HEAD", "GET"])
def health_check():
    return "✅ docx-generator-api is live"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10010))
    app.run(host="0.0.0.0", port=port)
