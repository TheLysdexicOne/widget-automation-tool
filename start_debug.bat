@echo off
echo Starting Widget Automation Tool (Debug Mode)...
echo.

REM Change to project directory  
cd /d "%~dp0"

REM Run with virtual environment in debug mode
".venv\Scripts\python.exe" src\main.py --debug

echo.
echo Application exited.
pause
