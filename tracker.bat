@echo off
REM Widget Automation Tool - Tracker Application Launcher
REM Launch the standalone tracker app

echo Starting Widget Automation Tracker...

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Launch tracker with Python
python -m src.tracker_app.tracker_app %*

pause
