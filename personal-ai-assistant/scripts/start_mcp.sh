#!/bin/bash
# Start the Google Calendar MCP server in HTTP/SSE mode
# This runs as a standalone service that agents connect to via HTTP
# Same config works in dev and prod — only the URL changes

export GOOGLE_OAUTH_CREDENTIALS="${GOOGLE_OAUTH_CREDENTIALS:-./mcp_config/google/calendar/gcp-oauth.keys.json}"

echo "🚀 Starting Google Calendar MCP server on http://localhost:3001/sse"
echo "   OAuth credentials: $GOOGLE_OAUTH_CREDENTIALS"
echo ""

npx -y @cocal/google-calendar-mcp --transport sse --port 3001
