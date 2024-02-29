from langchain_community.tools.gmail.utils import get_gmail_credentials

GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/tasks',
    'https://mail.google.com/',
]

def authenticate_with_google():
    return get_gmail_credentials(scopes = GOOGLE_SCOPES)
