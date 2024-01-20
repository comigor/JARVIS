import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from ..fuckio import async_add_executor_job
from const import ROOT_DIR

json_fname = 'jarvis-config/rooms.json'
CONFIG_FILE = 'jarvis-config/credentials.json'  # login credentials JSON file
STORE_PATH = './jarvis-config/store/'  # local directory


def get_full_file_path(relative_path: str) -> str:
    path = Path(ROOT_DIR).joinpath(relative_path)
    if not path.is_file() and not path.is_dir():
        path2 = Path(ROOT_DIR).parent.joinpath(relative_path)
        if not path2.is_file() and not path2.is_dir():
            raise Exception(f'Could not find file: {relative_path}. Tried {path} & {path2}')
        return str(path2)
    return str(path)


GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/tasks',
]

def _authenticate_with_google():
    # The file token.json stores the user's access and refresh tokens, and it is
    # created automatically when the authorization flow completes for the first time.
    token_path = get_full_file_path('jarvis-config/token.json')

    # If there are no (valid) credentials available, let the user log in.
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                get_full_file_path('jarvis-config/client_secret.json'),
                GOOGLE_SCOPES,
            )
            creds = flow.run_local_server(port=8035)
        
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return creds

async def authenticate_with_google():
    return await async_add_executor_job(_authenticate_with_google)
