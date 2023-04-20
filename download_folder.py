#!/usr/bin/env python3
import argparse
import os
import io
import pickle
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaIoBaseDownload


def get_args():
    parser = argparse.ArgumentParser(
        description='Download all files from a Google Drive folder.',
    )

    parser.add_argument(
        '--folder-id', '-folder-id', '--f', '-f',
        type=str,
        required=True,
        help='Folder ID of the Google Drive Folder (eg. 1YvFj33Bfum4YuBeqNNCYLfiBrD4tpzg7)'
    )

    parser.add_argument(
        '--output-path', '-output-path', '--o', '-o',
        type=str,
        required=True,
        help='Output path to save downloaded files (eg. /tmp)'
    )

    return parser.parse_args()


def download_file(file_id, file_name, output_path):
    request = service.files().get_media(fileId=file_id)
    file = io.BytesIO()
    downloader = MediaIoBaseDownload(file, request)
    done = False

    while done is False:
        status, done = downloader.next_chunk()
        print(f'Progress: {int(status.progress() * 100)}%')

    file.seek(0)

    with open(f'{output_path}/{file_name}', 'wb') as f:
        f.write(file.read())


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


if __name__ == '__main__':
    args = get_args()
    folder_id = args.folder_id
    output_path = args.output_path

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

    # Get all files in the folder
    files = get_files_in_folder(folder_id)

    # Download each file
    for file in files:
        file_id = file['id']
        file_name = file['name']
        print(f'Downloading {file_name} to {output_path}/{file_name}...')
        download_file(file_id, file_name, output_path)
