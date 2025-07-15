@echo off
REM Activate the virtual environment and launch the application
SET VENV_DIR=%~dp0.venv
IF NOT EXIST "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
)
CALL "%VENV_DIR%\Scripts\activate.bat"
ECHO Virtual environment activated.
ECHO You can now run your application commands.
cmd /k