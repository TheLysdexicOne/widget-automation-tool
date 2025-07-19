@echo off
REM Widget Automation Tool - Tracker Application Launcher (Debug Mode)
REM Launch the standalone tracker app with detailed logging

echo Starting Widget Automation Tracker (Debug Mode)...

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Launch tracker with Python in debug mode
python -m src.tracker_app.tracker_app %* --debug

pause
