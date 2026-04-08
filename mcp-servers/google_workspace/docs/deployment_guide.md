# 🚀 Deployment Guide: Google Workspace MCP Server

This doc covers how to set up the **Google Workspace MCP Server** in a local development environment and how to deploy it as a secure, containerized service on **Google Cloud Run**.

---

## 🛠️ Local Environment Setup

### 1. Prerequisites
- **Python 3.12** or higher.
- **`credentials.json`**: From your [Google Cloud Console](https://console.cloud.google.com/apis/credentials).

### 2. Installation
```bash
cd mcp-servers/google_workspace

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Running the Server

#### Development (Local FS based):
```bash
# Set transport to streamable-http (standard for ADK agents)
export MCP_TRANSPORT=streamable-http
export TOKEN_BACKEND=local
python server.py
```

#### Verification:
Access the health check at `http://localhost:8080/health`.

---

## 🌩️ Google Cloud Run Deployment

### 1. Build Container Image
```bash
# Build the image using the provided Dockerfile
docker build -t gcr.io/[PROJECT_ID]/google-workspace-mcp .
```

### 2. Deploy to Cloud Run
```bash
# Push the image to Container Registry
gcloud auth configure-docker
docker push gcr.io/[PROJECT_ID]/google-workspace-mcp

# Deploy the service
gcloud run deploy google-workspace-mcp \
  --image gcr.io/[PROJECT_ID]/google-workspace-mcp \
  --region asia-south1 \
  --set-env-vars TOKEN_BACKEND=firestore,GCP_PROJECT=[PROJECT_ID] \
  --allow-unauthenticated
```

> [!NOTE]
> **Base URL Auto-Detection**: Once deployed, the server will correctly detect its own Cloud Run URL (e.g. `https://my-mcp-abc123.run.app`) for OAuth redirects.

---

## 🔐 OAuth & Redirect URI

After deployment, take your **Cloud Run URL** and add it to the **Authorized redirect URIs** section in your Google Cloud Console:

1. Go to **APIs & Services** > **Credentials**.
2. Select your **OAuth 2.0 Client ID**.
3. Add the following URI:
   `https://[YOUR-SERVICE-URL]/auth/callback`

---

> [!CAUTION]
> **Production Security**: For a real-world deployment, consider using `--no-allow-unauthenticated` on Cloud Run and protecting your service with **Identity-Aware Proxy (IAP)** to ensure only authorized entities can call your MCP tools.

> [!TIP]
> **Firestore Permissions**: Ensure your Cloud Run service account has the `roles/datastore.user` IAM role so it can read/write tokens to Cloud Firestore.
