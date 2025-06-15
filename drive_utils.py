import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Service account credentials file: use env var or default path
SERVICE_ACCOUNT_FILE = os.environ.get(
    "GOOGLE_APPLICATION_CREDENTIALS", "/etc/secrets/service_account.json"
)
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def _get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def _ensure_folder(service, folder_name: str) -> str:
    """
    Ensure a folder with the given name exists in Drive; create it if missing.
    Returns the folder ID.
    """
    query = (
        f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'"
        " and trashed = false"
    )
    resp = service.files().list(q=query, spaces="drive", fields="files(id,name)").execute()
    files = resp.get("files", [])
    if files:
        return files[0]["id"]
    metadata = {"name": folder_name, "mimeType": "application/vnd.google-apps.folder"}
    folder = service.files().create(body=metadata, fields="id").execute()
    return folder.get("id")


def upload_to_drive(file_path: str, file_name: str, session_folder_name: str) -> str:
    """
    Upload a file to a Drive folder named session_folder_name.
    Creates the folder if it doesn't exist. Returns the file's webViewLink.
    """
    service = _get_drive_service()
    # Ensure session folder exists
    folder_id = _ensure_folder(service, session_folder_name)

    # Determine MIME type based on extension
    _, ext = os.path.splitext(file_name.lower())
    mime_types = {
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".pdf": "application/pdf",
    }
    mime_type = mime_types.get(ext, "application/octet-stream")

    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
    file_metadata = {"name": file_name, "parents": [folder_id]}
    uploaded = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id, webViewLink")
        .execute()
    )

    # Make the file publicly viewable
    service.permissions().create(
        fileId=uploaded.get("id"),
        body={"type": "anyone", "role": "reader"},
        fields="id",
    ).execute()

    return uploaded.get("webViewLink")
