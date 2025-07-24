@echo off
echo Starting Widget Automation Tool (GUI + Overlay)...
echo.

REM Change to project directory
cd /d "%~dp0"

REM Run with virtual environment in GUI mode (shows both GUI and overlay)
".venv\Scripts\python.exe" src\main.py --gui

echo.
echo Application exited.
