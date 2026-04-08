import json
import datetime
import logging
from pathlib import Path
from google.oauth2.credentials import Credentials

from config import GCP_PROJECT, TOKEN_BACKEND

logger = logging.getLogger("workspace-mcp.store")

class LocalTokenStore:
    """File-based token store for development."""

    def __init__(self):
        # The .tokens directory should be inside google_workspace/
        self._dir = Path(__file__).parent.parent / ".tokens"
        self._dir.mkdir(exist_ok=True)

    def get(self, user_id: str) -> Credentials | None:
        path = self._dir / f"{user_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        creds = Credentials(
            token=data.get("token"),
            refresh_token=data.get("refresh_token"),
            token_uri=data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=data.get("client_id"),
            client_secret=data.get("client_secret"),
            scopes=data.get("scopes"),
        )
        return creds

    def save(self, user_id: str, creds: Credentials):
        path = self._dir / f"{user_id}.json"
        path.write_text(json.dumps({
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes) if creds.scopes else [],
        }))

    def exists(self, user_id: str) -> bool:
        return (self._dir / f"{user_id}.json").exists()

    def delete(self, user_id: str):
        path = self._dir / f"{user_id}.json"
        if path.exists():
            path.unlink()


class FirestoreTokenStore:
    """Firestore-based token store for production."""

    def __init__(self):
        from google.cloud import firestore
        self._db = firestore.Client(project=GCP_PROJECT)
        self._collection = "mcp_user_tokens"

    def get(self, user_id: str) -> Credentials | None:
        doc = self._db.collection(self._collection).document(user_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        return Credentials(
            token=data.get("token"),
            refresh_token=data.get("refresh_token"),
            token_uri=data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=data.get("client_id"),
            client_secret=data.get("client_secret"),
            scopes=data.get("scopes"),
        )

    def save(self, user_id: str, creds: Credentials):
        self._db.collection(self._collection).document(user_id).set({
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes) if creds.scopes else [],
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        })

    def exists(self, user_id: str) -> bool:
        return self._db.collection(self._collection).document(user_id).get().exists

    def delete(self, user_id: str):
        self._db.collection(self._collection).document(user_id).delete()


def create_token_store():
    if TOKEN_BACKEND == "firestore":
        logger.info("Using Firestore token store")
        return FirestoreTokenStore()
    else:
        logger.info("Using local file token store")
        return LocalTokenStore()

# Global token store instance
token_store = create_token_store()
