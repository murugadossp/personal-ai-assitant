#!/usr/bin/env bash
# Create or recreate .venv with Python 3.12 and install dependencies.
# Prefers uv (https://github.com/astral-sh/uv); falls back to pip + requirements.txt.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -d .venv ]]; then
  echo "Removing existing .venv ..."
  rm -rf .venv
fi

if command -v uv &>/dev/null; then
  echo "Using uv: $(command -v uv) — $(uv --version)"
  uv sync --python 3.12
else
  echo "uv not found. Install: https://docs.astral.sh/uv/getting-started/installation/"
  echo "Falling back to pip + requirements.txt (needs python3.12)."
  if ! command -v python3.12 &>/dev/null; then
    echo "error: python3.12 not found on PATH."
    echo "  macOS (Homebrew): brew install python@3.12"
    echo "  pyenv: pyenv install 3.12.8 && pyenv local 3.12.8"
    exit 1
  fi
  echo "Using: $(command -v python3.12) — $(python3.12 --version)"
  python3.12 -m venv .venv
  ./.venv/bin/python -m pip install -U pip
  ./.venv/bin/pip install -r requirements.txt
fi

echo ""
echo "OK. Activate before adk or FastAPI:"
echo "  source .venv/bin/activate"
echo "  which python adk   # should be under $ROOT/.venv/bin/"
echo "  adk web"
