@echo off
REM Debug mode with console output
cd /d "%~dp0"
echo Starting Widget Automation Overlay (Debug Mode)...
".venv\Scripts\python.exe" src\main.py
pause
