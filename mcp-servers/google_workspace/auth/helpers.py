import logging
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from config import get_base_url
from auth.store import token_store

logger = logging.getLogger("workspace-mcp.helpers")

def get_credentials(user_id: str) -> Credentials:
    """
    Get valid credentials for a user.
    Raises ValueError if user hasn't authorized yet.
    """
    creds = token_store.get(user_id)

    if not creds or not creds.refresh_token:
        base = get_base_url()
        auth_url = f"{base}/auth?user_id={user_id}"
        raise ValueError(
            f"User '{user_id}' has not authorized Google Workspace access. "
            f"Please open this URL to authorize: {auth_url}"
        )

    if creds.expired:
        try:
            creds.refresh(Request())
            token_store.save(user_id, creds)
            logger.info(f"Refreshed token for user {user_id}")
        except Exception as e:
            token_store.delete(user_id)
            base = get_base_url()
            auth_url = f"{base}/auth?user_id={user_id}"
            raise ValueError(
                f"Token expired and refresh failed for user '{user_id}'. "
                f"Please re-authorize: {auth_url}"
            ) from e

    return creds

def calendar_service(user_id: str):
    return build("calendar", "v3", credentials=get_credentials(user_id))

def gmail_service(user_id: str):
    return build("gmail", "v1", credentials=get_credentials(user_id))

def drive_service(user_id: str):
    return build("drive", "v3", credentials=get_credentials(user_id))
