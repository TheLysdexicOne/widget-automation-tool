@echo off
REM Test launcher script for Widget Automation Tool
REM This script automatically uses the virtual environment

echo Widget Automation Tool - Test Launcher
echo ========================================

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo Error: Virtual environment not found!
    echo Please run the following commands first:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

REM Run tests using virtual environment
echo Using virtual environment...
.venv\Scripts\python.exe tests\run_tests.py

pause
