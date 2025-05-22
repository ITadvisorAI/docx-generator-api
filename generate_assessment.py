import os
import traceback
import requests
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Inches
from pptx import Presentation
from pptx.util import Inches
from openpyxl import load_workbook
from collections import Counter

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

REQUIRED_FILE_TYPES = {"asset_inventory", "gap_working"}
TEMPLATES = {
    "hw": "templates/HWGapAnalysis.xlsx",
    "sw": "templates/SWGapAnalysis.xlsx",
    "docx": "templates/IT_Current_Status_Assesment_Template.docx",
    "pptx": "templates/IT_Infrastructure_Assessment_Report.pptx"
}
GENERATE_API_URL = "https://docx-generator-api.onrender.com/generate_assessment"
NEXT_API_URL = "https://market-gap-analysis.onrender.com/start_market_gap"
SERVICE_ACCOUNT_FILE = "/etc/secrets/service_account.json"

# === Google Drive Setup ===
SCOPES = ['https://www.googleapis.com/auth/drive']
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)
drive_service = build('drive', 'v3', credentials=creds)

def get_drive_folder_id(session_id):
    query = f"name = '{session_id}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    response = drive_service.files().list(q=query, fields="files(id)").execute()
    folders = response.get("files", [])
    if not folders:
        raise FileNotFoundError(f"No folder found in Google Drive for session ID: {session_id}")
    return folders[0]['id']

def upload_to_drive(file_path, folder_id):
    file_name = os.path.basename(file_path)
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, resumable=True)
    uploaded = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
    print(f"✅ Uploaded to Google Drive: {uploaded['webViewLink']}")
    return uploaded['webViewLink']

def generate_tier_chart(ws, output_path):
    tier_col_idx = None
    headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
    for idx, h in enumerate(headers):
        if h and "tier" in str(h).lower():
            tier_col_idx = idx
            break
    if tier_col_idx is None:
        print("⚠️ Tier column not found.")
        return False

    tiers = [str(row[tier_col_idx]).strip() for row in ws.iter_rows(min_row=2, values_only=True) if row[tier_col_idx]]
    if not tiers:
        print("⚠️ No tier values found.")
        return False

    counts = Counter(tiers)
    plt.figure(figsize=(6, 4))
    plt.bar(counts.keys(), counts.values(), color='skyblue')
    plt.title("Tier Distribution")
    plt.xlabel("Tier")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"✅ Tier chart saved to: {output_path}")
    return True

def call_generate_api(session_id, score_summary, recommendations, key_findings):
    payload = {
        "session_id": session_id,
        "score_summary": score_summary,
        "recommendations": recommendations,
        "key_findings": key_findings or ""
    }
    print(f"📤 Calling generate_assessment API: {GENERATE_API_URL}")
    try:
        response = requests.post(GENERATE_API_URL, json=payload)
        response.raise_for_status()
        print(f"✅ Generate API responded: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"🔴 Error calling generate_assessment: {e}")
        traceback.print_exc()
        return {}

def process_assessment(session_id, email, files, webhook, session_folder):
    try:
        print(f"🔧 Starting assessment for session: {session_id}")
        os.makedirs(session_folder, exist_ok=True)

        folder_name = session_id if session_id.startswith("Temp_") else f"Temp_{session_id}"
        folder_id = get_drive_folder_id(folder_name)

        file_dict = {f['type']: f for f in files if f.get('type') in REQUIRED_FILE_TYPES}
        missing = REQUIRED_FILE_TYPES - file_dict.keys()
        if missing:
            raise ValueError(f"Missing required file types: {', '.join(missing)}")

        for key, path in TEMPLATES.items():
            if not os.path.exists(path):
                raise FileNotFoundError(f"Missing template: {path}")

        for f in files:
            file_path = os.path.join(session_folder, f['file_name'])
            response = requests.get(f['file_url'])
            with open(file_path, 'wb') as local_file:
                local_file.write(response.content)

        hw_output = os.path.join(session_folder, f"HWGapAnalysis_{session_id}.xlsx")
        sw_output = os.path.join(session_folder, f"SWGapAnalysis_{session_id}.xlsx")
        docx_output = os.path.join(session_folder, "IT_Current_Status_Assessment_Report.docx")
        pptx_output = os.path.join(session_folder, "IT_Current_Status_Executive_Report.pptx")
        chart_path = os.path.join(session_folder, "tier_distribution.png")

        # Generate HW and SW GAP XLSX
        wb = load_workbook(TEMPLATES["hw"])
        ws = wb["GAP_Working"] if "GAP_Working" in wb.sheetnames else wb.active
        generate_tier_chart(ws, chart_path)
        wb.save(hw_output)

        wb = load_workbook(TEMPLATES["sw"])
        wb.save(sw_output)

        # Generate DOCX and PPTX from remote API
        gen_result = call_generate_api(session_id,
                                       "Excellent: 20%, Advanced: 40%, Standard: 30%, Obsolete: 10%",
                                       "Decommission Tier 1 servers and move Tier 2 apps to cloud.",
                                       "Critical workloads are on obsolete hardware.")

        if 'docx_url' in gen_result:
            response = requests.get(gen_result['docx_url'])
            with open(docx_output, 'wb') as f:
                f.write(response.content)

        if 'pptx_url' in gen_result:
            response = requests.get(gen_result['pptx_url'])
            with open(pptx_output, 'wb') as f:
                f.write(response.content)

        # Upload all files to Drive
        files_to_send = {
            os.path.basename(hw_output): upload_to_drive(hw_output, folder_id),
            os.path.basename(sw_output): upload_to_drive(sw_output, folder_id),
            os.path.basename(docx_output): upload_to_drive(docx_output, folder_id),
            os.path.basename(pptx_output): upload_to_drive(pptx_output, folder_id)
        }

        # Trigger GPT3
        print("📤 Sending result to GPT3 (market_gap_analysis)...")
        payload = {
            "session_id": session_id,
            "email": email
        }
        for i, (name, url) in enumerate(files_to_send.items(), start=1):
            payload[f"file_{i}_name"] = name
            payload[f"file_{i}_url"] = url

        response = requests.post(NEXT_API_URL, json=payload)
        print(f"➡️ GPT3 Response: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"💥 Unhandled error in process_assessment: {e}")
        traceback.print_exc()
