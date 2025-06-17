import os
import traceback
from flask import Flask, request, jsonify, send_from_directory
from generate_assessment import generate_assessment_docs

app = Flask(__name__)

@app.route("/healthz", methods=["GET"])
def health_check():
    """Simple keep-alive endpoint."""
    return "OK", 200

@app.route("/health", methods=["GET"])
def health_check_simple():
    return "OK", 200

# Serve generated DOCX/PPTX files
@app.route("/files/<session_id>/<path:filename>")
def serve_generated_file(session_id, filename):
    directory = os.path.join("temp_sessions", session_id)
    return send_from_directory(directory, filename)

# Main generation endpoint
@app.route("/generate_assessment", methods=["POST"])
def generate_assessment_endpoint():
    payload = request.get_json(force=True)
    print("[DEBUG] /generate_assessment called with payload:", payload, flush=True)
    try:
        # Forward all incoming fields to generator
        result = generate_assessment_docs(**payload)
        return jsonify(result), 200
    except Exception as e:
        print("[ERROR] /generate_assessment threw exception:", str(e), flush=True)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Health check at root
@app.route("/", methods=["HEAD", "GET"])
def health_check_root():
    return "✅ docx-generator-api is live", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10010))
    app.run(host="0.0.0.0", port=port)
