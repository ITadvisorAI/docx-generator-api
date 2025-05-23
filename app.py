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
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# === Google Drive Credentials from ENV (Optional)
if os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"):
    try:
        service_account_info = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
        creds = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        drive_service = build('drive', 'v3', credentials=creds)
        logging.info("✅ Google Drive service initialized")
    except Exception as e:
        logging.warning(f"⚠️ Failed to initialize Google Drive: {e}")
else:
    logging.info("🔕 Google Drive not configured")

# === Health Check ===
@app.route("/", methods=["GET"])
def health_check():
    return "✅ DOCX Generator API is running", 200

# === POST /generate_assessment ===
@app.route("/generate_assessment", methods=["POST"])
def generate_assessment():
    try:
        data = request.get_json(force=True)
        logging.info("📥 Received POST /generate_assessment")
        result = generate_assessment_report(data)
        logging.info("📤 Assessment report generated and uploaded")
        return jsonify(result), 200
    except Exception as e:
        logging.exception("❌ Failed to generate assessment")
        return jsonify({"error": str(e)}), 500

# === Main Entry Point ===
if __name__ == "__main__":
    os.makedirs(BASE_DIR, exist_ok=True)
    port = int(os.environ.get("PORT", 10000))
    logging.info(f"🚦 Starting DOCX Generator API on port {port}...")
    app.run(debug=False, host="0.0.0.0", port=port)
