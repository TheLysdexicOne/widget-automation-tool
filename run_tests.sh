#!/bin/bash
# Test launcher script for Widget Automation Tool (Linux/macOS)
# This script automatically uses the virtual environment

echo "Widget Automation Tool - Test Launcher"
echo "========================================"

# Check if virtual environment exists
if [ ! -f ".venv/bin/python" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run the following commands first:"
    echo "  python -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Run tests using virtual environment
echo "Using virtual environment..."
.venv/bin/python tests/run_tests.py
