#!/usr/bin/env bash
# Minimal Cloud Run deploy: builds from Dockerfile, runs FastAPI (`/api/chat`).
# Next steps: ADK Web (`--with_ui`), Secret Manager for keys, remote MCP URL, AlloyDB, etc.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SERVICE_NAME="${SERVICE_NAME:-personal-ai-assistant}"
REGION="${CLOUD_RUN_REGION:-${GOOGLE_CLOUD_LOCATION:-us-central1}}"
PROJECT="${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT}"

# Optional: mount API key from Secret Manager (recommended) instead of plain env:
#   gcloud secrets create GOOGLE_API_KEY --data-file=...
#   --set-secrets "GOOGLE_API_KEY=GOOGLE_API_KEY:latest"
#
# Minimal demo (less secure): pass key at deploy time:
#   GOOGLE_API_KEY=... ./scripts/deploy_cloud_run_minimal.sh

ENV_VARS=(
  "GOOGLE_GENAI_USE_VERTEXAI=${GOOGLE_GENAI_USE_VERTEXAI:-False}"
  "ENABLE_ADK_WEB_UI=${ENABLE_ADK_WEB_UI:-true}"
)
if [[ -n "${GOOGLE_API_KEY:-}" ]]; then
  ENV_VARS+=("GOOGLE_API_KEY=${GOOGLE_API_KEY}")
fi
if [[ -n "${GOOGLE_CLOUD_LOCATION:-}" ]]; then
  ENV_VARS+=("GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION}")
fi
if [[ -n "${ASSISTANT_TIMEZONE:-}" ]]; then
  ENV_VARS+=("ASSISTANT_TIMEZONE=${ASSISTANT_TIMEZONE}")
fi
IFS=","; ENV_STRING="${ENV_VARS[*]}"; unset IFS

exec gcloud run deploy "$SERVICE_NAME" \
  --source "$ROOT" \
  --region "$REGION" \
  --project "$PROJECT" \
  --allow-unauthenticated \
  --timeout=300 \
  --memory=2Gi \
  --set-env-vars="$ENV_STRING" \
  "$@"
