#!/usr/bin/env bash
# =============================================================================
#  Engineering Calculator Suite — First-time setup (Linux / macOS)
#  Run this ONCE after cloning the repo.
#  After setup, use  ./run.sh  to start the app.
# =============================================================================

set -e

echo ""
echo " ========================================================="
echo "  Engineering Calculator Suite — Setup"
echo " ========================================================="
echo ""

# Check Python 3.11+
if ! command -v python3 &>/dev/null; then
    echo " [ERROR] python3 not found. Install Python 3.11+ then retry."
    exit 1
fi

echo " [1/3]  Creating virtual environment (.venv) ..."
python3 -m venv .venv

echo " [2/3]  Installing dependencies ..."
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt

echo ""
echo " [3/3]  Setup complete. Launching app ..."
echo ""
.venv/bin/python main.py
