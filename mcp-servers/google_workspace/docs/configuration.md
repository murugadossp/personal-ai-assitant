# ⚙️ Configuration Reference

This document lists all the environment variables and settings available for the **Google Workspace MCP Server**. These settings control how the server connects to Google APIs and how it stores user tokens.

---

## 🛠️ Global Configuration

| Variable | Default | Description |
| :--- | :--- | :--- |
| **`MCP_TRANSPORT`** | `streamable-http` | The transport method for MCP. Options: `stdio`, `sse`, `streamable-http`. |
| **`PORT`** | `8080` | The network port the ASGI server (Uvicorn) listens on. |
| **`BASE_URL`** | *(Detect)* | The public URL of the server. Automatically detected by headers on Cloud Run. |
| **`TOKEN_BACKEND`** | `local` | Storage engine for user tokens. Options: `local`, `firestore`. |
| **`GCP_PROJECT`** | `personal-ai-agent-492408` | The Google Cloud Project ID used for Firestore. |
| **`GOOGLE_OAUTH_CREDENTIALS`** | `./credentials.json` | Path to your Google OAuth client secret JSON file. |

---

## 🔐 Transport Details

### Streamable HTTP (Recommended)
This is the default for interacting with **Google ADK** agents. It allows for high-concurrency, asynchronous tool execution.
- **Port**: 8080 (standard)
- **Auto-Detection**: Works perfectly with `X-Forwarded-Proto` and `Host` headers.

### Stdio
Used for local IDE testing (Claude Desktop, Cursor). 
- **Command**: `mcp-servers/google_workspace/.venv/bin/python mcp-servers/google_workspace/server.py`

---

## 💾 Storage Details

### Local File Storage
Used for development. Tokens are stored as plain JSON files in the `.tokens/` directory within the server folder. 
> [!WARNING]
> **Do not commit** the `.tokens/` directory to version control.

### Firestore (Production)
Requires a valid GCP project and a Firestore database in Native mode.
- **Service Account**: Cloud Run usually provides this automatically.
- **Permissions**: Needs `Cloud Datastore User` (which includes Firestore) role.

---

> [!TIP]
> **Overriding BASE_URL**: If you choose to use a custom domain (e.g. `mcp.assistant.com`), you should explicitly set `BASE_URL=https://mcp.assistant.com` to ensure the OAuth redirect URI is generated correctly.
