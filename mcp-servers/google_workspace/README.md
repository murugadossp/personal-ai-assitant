# 🔌 Google Workspace MCP Server

> A multi-user **Model Context Protocol (MCP)** server that provides AI agents with secure access to **Google Calendar**, **Gmail**, and **Google Drive** through a unified interface.

---

## 🚀 Quick Links

- [🏗️ **Design Doc**](docs/design_doc.md): Architecture & Data Flow 
- [🔐 **Multi-User Auth**](docs/multi_user_auth.md): OAuth, Tokens & Isolation
- [🛠️ **Tools Reference**](docs/tools_reference.md): Detailed API & Tool Specs
- [☁️ **Deployment Guide**](docs/deployment_guide.md): Local Setup & Cloud Run

---

## ✨ Features

- **Multi-Transport Support**: Works with `stdio` (local), `SSE`, and `Streamable HTTP` (agentic).
- **Secure Per-User Identity**: Isolate tokens for thousands of users using Local or Firestore backends.
- **Auto-Base URL Detection**: Deploy to Cloud Run with zero manual callback configuration.
- **Modular Plugin System**: Easily extend the server with new workspace tools.
- **Premium Documentation**: Detailed walkthroughs and interactive HTML guides included.

---

## 🛠️ Quick Start (Local)

```bash
# 📂 Navigate to folder
cd mcp-servers/google_workspace

# 📦 Start in modular mode
MCP_TRANSPORT=streamable-http .venv/bin/activate python server.py

# 🔗 Authorize your user
open http://localhost:8080/auth?user_id=testuser
```

---

## 📄 License & Project

This project is part of the **Personal AI Assistant** ecosystem for the Google GenAI APAC Edition 2026.

- [🌐 Root Documentation](../../index.html)
- [🤖 Personal AI Assistant](../../personal-ai-assistant/index.html)
