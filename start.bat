@echo off
echo Starting Widget Automation Tool (Overlay Only)...
echo.

REM Change to project directory
cd /d "%~dp0"

REM Run with virtual environment - overlay only
".venv\Scripts\python.exe" src\main.py %*

echo.
echo Application exited.

