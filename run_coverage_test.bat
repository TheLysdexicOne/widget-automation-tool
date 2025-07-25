@echo off
echo Running Comprehensive Coverage Test...
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install pytest-cov if not already installed
pip install pytest-cov

REM Run comprehensive coverage test
pytest tests/test_comprehensive_coverage.py --cov=src --cov-report=html --cov-report=term-missing -v --tb=short

echo.
echo Coverage report generated in htmlcov/index.html
echo.
pause
