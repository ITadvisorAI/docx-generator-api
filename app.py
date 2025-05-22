from flask import Flask, request, jsonify
from generate_assessment import generate_docs
import logging

# === Flask App Initialization ===
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["GET"])
def health_check():
    return "✅ DOCX Generator API is running", 200

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
