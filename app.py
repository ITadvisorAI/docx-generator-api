from flask import Flask, request, jsonify, send_from_directory
import logging
import os
from generate_assessment import generate_docs

# === Flask App Initialization ===
app = Flask(__name__)
BASE_DIR = "temp_sessions"

# === Logging Configuration ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# === Health Check ===
@app.route("/", methods=["GET"])
def health_check():
    return "✅ DOCX Generator API is running", 200

# === POST /generate_assessment ===
@app.route("/generate_assessment", methods=["POST"])
def generate_assessment():
    try:
        data = request.get_json(force=True)
        logging.info("📥 Received request for /generate_assessment")
        result = generate_docs(data)
        return jsonify(result), 200
    except Exception as e:
        logging.exception("❌ Exception in /generate_assessment")
        return jsonify({"error": str(e)}), 500

# === GET /files/<filename> ===
@app.route("/files/<path:filename>", methods=["GET"])
def serve_file(filename):
    try:
        directory = os.path.join(BASE_DIR, os.path.dirname(filename))
        file_only = os.path.basename(filename)
        logging.info(f"📤 Serving file: {filename}")
        return send_from_directory(directory, file_only, as_attachment=False)
    except Exception as e:
        logging.exception(f"❌ File serve error for: {filename}")
        return jsonify({"error": str(e)}), 500

# === Entry Point ===
if __name__ == '__main__':
    os.makedirs(BASE_DIR, exist_ok=True)
    try:
        port = int(os.environ.get("PORT", 5000))
    except KeyError:
        raise RuntimeError("❌ PORT environment variable is not set. Required by Render.")
    
    logging.info(f"🚦 Starting DOCX Generator Server on port {port}...")
    app.run(debug=False, host="0.0.0.0", port=port)
