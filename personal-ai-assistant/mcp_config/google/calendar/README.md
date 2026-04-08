# Google Calendar MCP Server

## Overview

| Property | Value |
|---|---|
| **Package** | `@cocal/google-calendar-mcp` |
| **Transport** | SSE (HTTP) |
| **Default Port** | `3001` |
| **Endpoint** | `http://localhost:3001/sse` |
| **Auth** | Google OAuth 2.0 (Desktop App) |

## Capabilities

Once connected, the MCP server exposes tools to:

- 📅 **List** calendar events (today, this week, date range)
- ➕ **Create** new events with title, time, attendees
- ✏️ **Update** existing events (reschedule, rename)
- ❌ **Delete** events
- 🔍 **Search** events by keyword
- 📋 **Check availability** across calendars

## Prerequisites

### 1. Google Cloud Project Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Navigate to **APIs & Services → Library**
4. Search for and **enable** the **Google Calendar API**

### 2. OAuth 2.0 Credentials

1. Go to **APIs & Services → Credentials**
2. Click **Create Credentials → OAuth client ID**
3. Select **Desktop app** as application type
4. Name it (e.g., `personal-assistant-calendar`)
5. Click **Create**
6. **Download the JSON** file
7. Save it as `gcp-oauth.keys.json` in this folder:
   ```
   mcp_config/google/calendar/gcp-oauth.keys.json
   ```

### 3. OAuth Consent Screen

1. Go to **APIs & Services → OAuth consent screen**
2. Choose **External** user type
3. Fill in the required app info
4. Under **Test users**, add your Google email address
5. Save

## Configuration

### mcp_settings.json Entry

This server is registered in the project root `mcp_settings.json`:

```json
{
  "mcpServers": {
    "google-calendar": {
      "transport": "sse",
      "url": "http://localhost:3001/sse"
    }
  }
}
```

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_OAUTH_CREDENTIALS` | ✅ | Path to `gcp-oauth.keys.json` |
| `GOOGLE_CALENDAR_MCP_TOKEN_PATH` | ❌ | Custom path for cached OAuth tokens (default: `~/.config/google-calendar-mcp/tokens.json`) |

## Running

### Local Development

```bash
# From project root
GOOGLE_OAUTH_CREDENTIALS=./mcp_config/google/calendar/gcp-oauth.keys.json \
  npx -y @cocal/google-calendar-mcp --transport sse --port 3001
```

Or use the convenience script:
```bash
./scripts/start_mcp.sh
```

### First Run — OAuth Flow

On the first run, the server will:
1. Print a URL in the terminal
2. Open your browser to Google's OAuth consent page
3. You authorize the app
4. Tokens are cached locally — subsequent runs skip this step

### Production Deployment

Deploy the MCP server as a standalone Cloud Run service, then update `mcp_settings.json`:

```json
{
  "mcpServers": {
    "google-calendar": {
      "transport": "sse",
      "url": "https://calendar-mcp-xxxxx.run.app/sse"
    }
  }
}
```

## File Structure

```
mcp_config/google/calendar/
├── README.md                  # This file
├── gcp-oauth.keys.json        # OAuth credentials (⚠️ DO NOT COMMIT)
└── sample.env                 # Sample environment variables
```

## Security

> ⚠️ **Never commit `gcp-oauth.keys.json` to version control.**

Make sure your `.gitignore` includes:
```
mcp_config/**/gcp-oauth.keys.json
*.keys.json
```
