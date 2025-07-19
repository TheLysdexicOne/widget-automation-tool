@echo off
echo Starting Widget Automation Tool...
echo.

REM Change to project directory
cd /d "%~dp0"

REM Run with virtual environment
".venv\Scripts\python.exe" src\main.py %*

echo.
echo Application exited.

