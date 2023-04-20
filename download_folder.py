#!/usr/bin/env python3
import os
import io
import pickle
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaIoBaseDownload

# Replace with your folder ID
folder_id = '1YvFj33Bfum4YuBeqNNCYLfiBrD4tpzg7'

# Initialize the Drive API client
creds = None

if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', ['https://www.googleapis.com/auth/drive'])
        creds = flow.run_local_server(port=0)
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('drive', 'v3', credentials=creds)

# Define a function to download a file from Drive
def download_file(file_id, file_name):
    request = service.files().get_media(fileId=file_id)
    file = io.BytesIO()
    downloader = MediaIoBaseDownload(file, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(f'Download {int(status.progress() * 100)}.')
    file.seek(0)
    with open(file_name, 'wb') as f:
        f.write(file.read())

# Define a function to get all files in a folder
def get_files_in_folder(folder_id):
    results = []
    query = f"'{folder_id}' in parents and trashed = false"
    page_token = None
    while True:
        try:
            response = service.files().list(q=query,
                                            spaces='drive',
                                            fields='nextPageToken, files(id, name)',
                                            pageToken=page_token).execute()
            files = response.get('files', [])
            results.extend(files)
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        except HttpError as error:
            print(f'An error occurred: {error}')
            break
    return results

# Get all files in the folder
files = get_files_in_folder(folder_id)

# Download each file
for file in files:
    file_id = file['id']
    file_name = file['name']
    print(f'Downloading {file_name}...')
    download_file(file_id, file_name)

