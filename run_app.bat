@echo off
echo Widget Automation Tool - Main Application
echo ========================================

REM Check for debug parameter
if "%1"=="--debug" (
    echo Starting in DEBUG mode with GUI...
    call .venv\Scripts\activate
    python src\main.py --debug
) else (
    echo Starting in NORMAL mode with system tray...
    call .venv\Scripts\activate
    python src\main.py
)