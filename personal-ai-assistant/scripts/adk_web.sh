#!/usr/bin/env bash
# From repo root: run ADK web UI with the project venv (Python 3.12 + locked deps).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VENV_PY="$ROOT/.venv/bin/python"
VENV_ADK="$ROOT/.venv/bin/adk"

if [[ ! -x "$VENV_PY" ]]; then
  echo "error: no venv at $ROOT/.venv"
  echo "  run: ./scripts/bootstrap_venv.sh"
  exit 1
fi

if [[ ! -x "$VENV_ADK" ]]; then
  echo "error: adk not found in venv ($VENV_ADK)"
  echo "  run: ./scripts/bootstrap_venv.sh"
  exit 1
fi

# shellcheck source=/dev/null
source "$ROOT/.venv/bin/activate"

# ADK expects a directory whose *subfolders* are agents (each with agent.py + root_agent).
# Default project layout: app/agents/coordinator/agent.py (workspace is a sub-agent only)
AGENTS_DIR="${ADK_AGENTS_DIR:-$ROOT/app/agents}"
if [[ ! -d "$AGENTS_DIR" ]]; then
  echo "error: agents directory not found: $AGENTS_DIR"
  echo "  set ADK_AGENTS_DIR or restore app/agents/"
  exit 1
fi

echo "Using: $(command -v python) — $(python --version)"
echo "Using: $(command -v adk)"
echo "cwd: $ROOT"
echo "agents: $AGENTS_DIR"
echo ""

# Positional agents_dir must be last: adk web [options] <agents_dir>
exec adk web "$@" "$AGENTS_DIR"
