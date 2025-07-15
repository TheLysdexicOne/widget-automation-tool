@echo off
REM Widget Automation Tool Debug Launcher
REM Launches the application in debug mode
REM Usage: start_debug.bat

SET SCRIPT_DIR=%~dp0
SET VENV_DIR=%SCRIPT_DIR%.venv

REM Parse command line arguments for passthrough
SET EXTRA_ARGS=%*

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

REM Launch the application in debug mode
IF "%EXTRA_ARGS%"=="" (
    echo Starting Widget Automation Tool in DEBUG mode...
    python src\main.py --debug
) ELSE (
    echo Starting Widget Automation Tool in DEBUG mode with args: %EXTRA_ARGS%
    python src\main.py --debug %EXTRA_ARGS%
)

REM Deactivate virtual environment
deactivate

echo Application closed.
pause
