@echo off
:: ============================================================================
::  Engineering Calculator Suite — First-time setup (Windows)
::  Run this ONCE after cloning the repo.
::  It creates a virtual environment, installs all dependencies, then launches
::  the app. After setup, use  run.bat  to start the app in future sessions.
:: ============================================================================

echo.
echo  =========================================================
echo   Engineering Calculator Suite — Setup
echo  =========================================================
echo.

:: Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python was not found on PATH.
    echo  Download Python 3.11+ from https://www.python.org/downloads/
    echo  Make sure to tick "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo  [1/3]  Creating virtual environment (.venv) ...
python -m venv .venv
if errorlevel 1 (
    echo  [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

echo  [2/3]  Installing dependencies ...
.venv\Scripts\pip install --upgrade pip --quiet
.venv\Scripts\pip install -r requirements.txt
if errorlevel 1 (
    echo  [ERROR] Dependency installation failed. Check the error above.
    pause
    exit /b 1
)

echo.
echo  [3/3]  Setup complete.  Launching app ...
echo.
.venv\Scripts\python main.py

pause
