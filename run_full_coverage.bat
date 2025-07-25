@echo off
echo Running Full Test Suite with Coverage Analysis...
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install pytest-cov if not already installed
pip install pytest-cov

REM Run all tests with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing --cov-report=xml -v --tb=short

echo.
echo Coverage reports generated:
echo - HTML: htmlcov/index.html
echo - XML: coverage.xml
echo - Terminal output above
echo.
pause
