import os
import sys
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_to_drive(file_path, folder_id, credentials_json):
    print(f"Loading credentials...")
    try:
        creds_dict = json.loads(credentials_json)
        creds = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        )
    except Exception as e:
        print(f"Error loading credentials: {e}")
        sys.exit(1)

    print("Building Drive API service...")
    service = build('drive', 'v3', credentials=creds)

    file_name = os.path.basename(file_path)
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }

    print(f"Preparing to upload {file_name} to folder {folder_id}...")
    media = MediaFileUpload(file_path, mimetype='application/zip', resumable=True)

    try:
        # pylint: disable=no-member
        # To avoid the "Service Accounts do not have storage quota" error when uploading
        # to a folder owned by a regular user, use the `supportsAllDrives=True` parameter
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True
        ).execute()
        
        print(f"Success! File ID: {file.get('id')}")
    except Exception as e:
        print(f"An error occurred during upload: {e}")
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python upload_to_drive.py <file_path> <folder_id>")
        sys.exit(1)

    file_to_upload = sys.argv[1]
    drive_folder_id = sys.argv[2]
    
    gdrive_creds = os.environ.get("GDRIVE_CREDENTIALS")
    
    if not gdrive_creds:
        print("Error: GDRIVE_CREDENTIALS environment variable is not set.")
        sys.exit(1)
        
    upload_to_drive(file_to_upload, drive_folder_id, gdrive_creds)
