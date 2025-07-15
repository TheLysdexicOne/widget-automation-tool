@echo off
REM Test Runner Script
REM Starts the main application and then runs standalone tests

echo Starting Widget Automation Tool...

REM Start the main application in the background
start "Widget Automation Tool" /B .\start_debug.bat

REM Give the application time to start
echo Waiting for application to initialize...
timeout /t 5 /nobreak > nul

REM Run the standalone test
echo Running standalone test...
python standalone_test_runner.py overlay_expansion

REM Store test result
set TEST_RESULT=%ERRORLEVEL%

REM Clean up - kill any python processes running the application
echo Cleaning up...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Widget Automation Tool*" 2>nul

echo Test completed with result: %TEST_RESULT%
exit /b %TEST_RESULT%
