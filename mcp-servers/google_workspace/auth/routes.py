import secrets
import logging
from starlette.responses import JSONResponse, RedirectResponse, HTMLResponse
from google_auth_oauthlib.flow import Flow

from config import get_base_url, SCOPES, CREDENTIALS_PATH
from auth.store import token_store

logger = logging.getLogger("workspace-mcp.routes")

# In-memory state store for OAuth flows (maps state → {user_id, code_verifier})
_oauth_states: dict[str, dict] = {}

async def start_auth(request):
    user_id = request.query_params.get("user_id")
    if not user_id:
        return JSONResponse(
            {"error": "user_id query parameter required"}, status_code=400
        )

    state = secrets.token_urlsafe(32)

    base = get_base_url(request)
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES,
        redirect_uri=f"{base}/auth/callback",
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    # Store both user_id and code_verifier for the callback
    _oauth_states[state] = {
        "user_id": user_id,
        "code_verifier": flow.code_verifier
    }
    logger.info(f"OAuth started for user {user_id}")
    return RedirectResponse(auth_url)

async def auth_callback(request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")

    if error:
        return HTMLResponse(
            f"<h2>❌ Authorization failed</h2><p>{error}</p>", status_code=400
        )

    if not state or state not in _oauth_states:
        return HTMLResponse(
            "<h2>❌ Invalid state</h2><p>Please restart the auth flow.</p>",
            status_code=400,
        )

    if not code:
        return HTMLResponse(
            "<h2>❌ Missing authorization code</h2>"
            "<p>Google did not return a <code>code</code> query parameter. "
            "Try starting sign-in again from your assistant.</p>",
            status_code=400,
        )

    state_data = _oauth_states.pop(state)
    user_id = state_data["user_id"]
    code_verifier = state_data["code_verifier"]

    base = get_base_url(request)
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES,
        redirect_uri=f"{base}/auth/callback",
    )
    try:
        flow.fetch_token(code=code, code_verifier=code_verifier)
        creds = flow.credentials
        token_store.save(user_id, creds)
    except Exception as e:
        logger.exception("OAuth callback failed for user %s", user_id)
        hint = ""
        err = str(e).lower()
        if "redirect_uri" in err or "redirect uri" in err:
            hint = (
                "<p><strong>Tip:</strong> Set <code>BASE_URL</code> in <code>.env</code> to the "
                "exact redirect origin you registered in Google Cloud Console (e.g. "
                "<code>http://localhost:8080</code>), and add both "
                "<code>http://localhost:8080/auth/callback</code> and "
                "<code>http://127.0.0.1:8080/auth/callback</code> as authorized redirect URIs "
                "if you open the app via either host.</p>"
            )
        return HTMLResponse(
            "<h2>❌ Could not finish sign-in</h2>"
            f"<p>{e}</p>{hint}"
            "<p style=\"color:#64748b\">Check server logs for the full traceback.</p>",
            status_code=400,
        )

    logger.info(f"OAuth completed for user {user_id}")

    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head><title>Authorization Successful</title></head>
    <body style="font-family: system-ui; display: flex; justify-content: center;
                  align-items: center; min-height: 100vh; margin: 0;
                  background: #0f172a; color: #e2e8f0;">
        <div style="text-align: center; max-width: 400px;">
            <div style="font-size: 64px;">✅</div>
            <h1>Authorized!</h1>
            <p>User <strong>{user_id}</strong> has been granted access to
               Google Calendar, Gmail, and Drive.</p>
            <p style="color: #94a3b8;">You can close this window and return
               to your AI assistant.</p>
        </div>
    </body>
    </html>
    """)

async def auth_status(request):
    user_id = request.path_params["user_id"]
    is_authorized = token_store.exists(user_id)
    result = {"user_id": user_id, "authorized": is_authorized}
    if not is_authorized:
        result["auth_url"] = f"{get_base_url(request)}/auth?user_id={user_id}"
    return JSONResponse(result)

def get_auth_routes():
    from starlette.routing import Route
    return [
        Route("/auth", start_auth),
        Route("/auth/callback", auth_callback),
        Route("/auth/status/{user_id}", auth_status),
    ]
