@echo off
echo Starting Widget Automation Tool - Overlay Expansion Test
echo ========================================================

:: Activate virtual environment
call venv.bat

:: Run the overlay expansion test
python src\main.py --debug --tests overlay_expansion

echo.
echo Test completed. Check the log output above for results.
pause
