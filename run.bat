@echo off
:: ============================================================================
::  Engineering Calculator Suite — Launch (Windows)
::  Run this after you have already run  setup.bat  once.
:: ============================================================================

:: Always run from the folder this .bat file lives in (fixes System32 issue)
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo  Virtual environment not found.
    echo  Please run  setup.bat  first to install dependencies.
    pause
    exit /b 1
)

.venv\Scripts\python main.py
