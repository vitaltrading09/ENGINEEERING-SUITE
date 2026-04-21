#!/usr/bin/env bash
# =============================================================================
#  Engineering Calculator Suite — Launch (Linux / macOS)
#  Run this after you have already run  ./setup.sh  once.
# =============================================================================

if [ ! -f ".venv/bin/python" ]; then
    echo " Virtual environment not found."
    echo " Please run  ./setup.sh  first to install dependencies."
    exit 1
fi

.venv/bin/python main.py
