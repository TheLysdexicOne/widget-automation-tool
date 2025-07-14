@echo off
REM Widget Automation Tool Launcher
REM Activates virtual environment and launches the application

SET SCRIPT_DIR=%~dp0
SET VENV_DIR=%SCRIPT_DIR%.venv

REM Check if virtual environment exists
IF NOT EXIST "%VENV_DIR%" (
    echo Virtual environment not found at: %VENV_DIR%
    echo Please create the virtual environment first:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
CALL "%VENV_DIR%\Scripts\activate.bat"

REM Check if activation was successful
IF NOT DEFINED VIRTUAL_ENV (
    echo Failed to activate virtual environment
    pause
    exit /b 1
)

echo Virtual environment activated: %VIRTUAL_ENV%

REM Launch the application
echo Starting Widget Automation Tool...
python src\main.py %*

REM Deactivate virtual environment
deactivate

echo Application closed.
pause
