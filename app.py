import os
from flask import Flask, request, jsonify, send_from_directory
from generate_assessment import generate_assessment_docs

app = Flask(__name__)

# Serve generated DOCX/PPTX files
@app.route("/files/<session_id>/<path:filename>")
def serve_generated_file(session_id, filename):
    directory = os.path.join("temp_sessions", session_id)
    return send_from_directory(directory, filename)

# Main generation endpoint
@app.route("/generate_assessment", methods=["POST"])
def generate_assessment_endpoint():
    print("[DEBUG] /generate_assessment called with payload:", request.get_json(), flush=True)
    try:
        data = request.get_json(force=True)
        session_id      = data["session_id"]
        score_summary   = data["score_summary"]
        recommendations = data["recommendations"]
        key_findings    = data["key_findings"]
        chart_paths     = data.get("chart_paths", {})

        # Generate the docs, now including charts
        result = generate_assessment_docs(
            session_id,
            score_summary,
            recommendations,
            key_findings,
            chart_paths
        )

        # Prefix URLs with this service's base URL
        base_url = os.getenv("DOCX_SERVICE_URL", f"{request.scheme}://{request.host}")
        result["docx_url"] = f"{base_url}{result['docx_url']}"
        result["pptx_url"] = f"{base_url}{result['pptx_url']}"

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health check
@app.route("/", methods=["HEAD", "GET"])
def health_check():
    return "✅ docx-generator-api is live", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10010))
    app.run(host="0.0.0.0", port=port)
