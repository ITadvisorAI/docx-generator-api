from flask import Flask, request, jsonify
import os
import logging
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from generate_assessment import generate_assessment_report

# === Flask App Initialization ===
app = Flask(__name__)
BASE_DIR = "temp_sessions"

# === Logging Configuration ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# === Google Drive Setup (from ENV) ===
drive_service = None
creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
if creds_json:
    try:
        service_account_info = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        drive_service = build('drive', 'v3', credentials=creds)
        logging.info("✅ Google Drive service initialized from ENV")
    except Exception as e:
        logging.warning(f"⚠️ Google Drive init failed: {e}")
        drive_service = None
else:
    logging.info("🔕 GOOGLE_SERVICE_ACCOUNT_JSON not provided")

# === Health Check ===
@app.route("/", methods=["GET"])
def health_check():
    return "✅ DOCX Generator API is running", 200

# === POST /generate_assessment ===
@app.route("/generate_assessment", methods=["POST"])
def generate_assessment():
    try:
        data = request.get_json(force=True)
        logging.info(f"📥 Received request: {json.dumps(data)}")

        if not data or not all(k in data for k in ("session_id", "score_summary", "recommendations")):
            return jsonify({"error": "Missing required fields"}), 400

        result = generate_assessment_report(data)
        logging.info("📤 Assessment report generated and returned")
        return jsonify(result), 200

    except Exception as e:
        logging.exception("❌ Failed to generate assessment")
        return jsonify({"error": str(e)}), 500

# === Entry Point ===
if __name__ == "__main__":
    os.makedirs(BASE_DIR, exist_ok=True)
    port = int(os.environ.get("PORT", 10000))
    logging.info(f"🚦 Starting DOCX Generator API on port {port}")
    app.run(debug=False, host="0.0.0.0", port=port)
