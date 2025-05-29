import os
import logging
from flask import Flask, request, jsonify
from generate_assessment import generate_assessment_report

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["GET", "HEAD"])
def health_check():
    return "📄 DOCX Generator API is live", 200

@app.route("/generate_assessment", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON payload"}), 400

        required_keys = ["session_id", "score_summary", "recommendations"]
        missing = [key for key in required_keys if key not in data]
        if missing:
            return jsonify({"error": f"Missing required keys: {', '.join(missing)}"}), 400

        result = generate_assessment_report(data)
        return jsonify(result), 200
    except Exception as e:
        logging.exception("Unhandled exception in /generate_assessment")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
