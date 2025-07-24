@echo off
echo Starting Widget Automation Tool (Debug: GUI + Overlay + Console Logging)...
echo.

REM Change to project directory  
cd /d "%~dp0"

REM Run with virtual environment in debug mode (shows GUI, overlay, and console logging)
".venv\Scripts\python.exe" src\main.py --debug

echo.
echo Application exited.
