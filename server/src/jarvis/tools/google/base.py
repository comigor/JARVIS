from langchain_community.tools.gmail.utils import get_gmail_credentials
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/tasks",
    "https://mail.google.com/",
]


def authenticate_with_google():
    return get_gmail_credentials(scopes=GOOGLE_SCOPES)


def refresh_google_token():
    creds = Credentials.from_authorized_user_file("token.json", GOOGLE_SCOPES)
    creds.refresh(Request())
    with open("token.json", "w") as token:
        token.write(creds.to_json())
