@echo off
REM Widget Automation Tool Test Launcher (targets Notepad for testing)
REM Launches the application with Notepad as target for testing

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

REM Start Notepad for testing if not already running
tasklist /FI "IMAGENAME eq notepad.exe" 2>NUL | find /I /N "notepad.exe">NUL
if "%ERRORLEVEL%"=="1" (
    echo Starting Notepad for testing...
    start notepad
    timeout /t 2 /nobreak > nul
)

REM Launch the application targeting Notepad
echo Starting Widget Automation Tool targeting Notepad...
python src\main.py --target notepad.exe

REM Deactivate virtual environment
deactivate

echo Application closed.
pause
