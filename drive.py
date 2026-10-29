import io
import os

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

load_dotenv()
SCOPES = ["https://www.googleapis.com/auth/drive"]
FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")


def _service():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds.valid:
        creds.refresh(Request())
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return build("drive", "v3", credentials=creds)


def upload_receipt(file_bytes, filename, mime_type):
    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime_type)
    meta = {"name": filename, "parents": [FOLDER_ID]}
    result = (
        _service()
        .files()
        .create(body=meta, media_body=media, fields="id, webViewLink")
        .execute()
    )
    return result["webViewLink"]