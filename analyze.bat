@echo off
REM Frame Border Analysis Tool Launcher
REM Activates virtual environment and launches the frame analyzer

echo Starting Frame Border Analysis Tool...
echo.

REM Change to project directory
cd /d "%~dp0"

REM Activate virtual environment
call venv.bat

REM Launch the analyzer
python src/analyze/frame_analyzer.py

pause
