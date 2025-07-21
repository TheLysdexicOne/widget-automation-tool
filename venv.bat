@echo off
REM Activate the virtual environment and launch the application in Powershell
SET VENV_DIR=%~dp0.venv
IF NOT EXIST "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
)
REM Start Powershell and activate the venv
powershell -NoExit -Command "& '%VENV_DIR%\Scripts\Activate.ps1'"