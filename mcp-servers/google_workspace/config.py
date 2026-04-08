import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv(Path(__file__).parent / ".env")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/drive.readonly",
]

GCP_PROJECT = os.environ.get("GCP_PROJECT", "personal-ai-agent-492408")

# In the new structure, config is inside google_workspace/, so parent is mcp-servers/
# The credentials.json should be in the same folder as config.py.
CREDENTIALS_PATH = os.environ.get(
    "GOOGLE_OAUTH_CREDENTIALS",
    str(Path(__file__).parent / "credentials.json"),
)

# Base URL for OAuth redirects — auto-detected from incoming requests.
# Set BASE_URL env var to override (e.g. custom domain).
_BASE_URL_ENV = os.environ.get("BASE_URL", "")  # explicit override
_detected_base_url: str = ""  # cached from first HTTP request


def get_base_url(request=None) -> str:
    """
    Resolve the server's public base URL. Priority:
      1. BASE_URL env var (explicit override)
      2. Auto-detect from request Host header (works on Cloud Run)
      3. Previously detected URL (cached)
      4. Fallback to http://localhost:8080
    """
    global _detected_base_url

    # 1. Explicit env var always wins
    if _BASE_URL_ENV:
        return _BASE_URL_ENV.rstrip("/")

    # 2. Auto-detect from request headers
    if request is not None:
        # Cloud Run sets X-Forwarded-Proto and Host
        proto = request.headers.get("x-forwarded-proto", "http")
        host = request.headers.get("host", "")
        if host:
            detected = f"{proto}://{host}"
            _detected_base_url = detected  # cache for MCP tools
            return detected

    # 3. Use cached detection
    if _detected_base_url:
        return _detected_base_url

    # 4. Fallback
    return "http://localhost:8080"

# Token storage backend: "firestore" or "local"
TOKEN_BACKEND = os.environ.get("TOKEN_BACKEND", "local")
