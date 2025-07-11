# Tests Directory

This directory contains all test files for the Widget Automation Tool.

## Test Categories

### GUI/Overlay Tests

- `test_overlay.py` - Full overlay test with WidgetInc integration
- `simple_overlay_test.py` - Standalone overlay test (no WidgetInc required)

### Unit Tests

- Future unit tests will be added here following the `test_*.py` naming convention

## Running Tests

### Test Runner (Recommended)

```bash
# From project root
python tests/run_tests.py
```

### Individual Tests

```bash
# Simple overlay test (standalone)
python tests/simple_overlay_test.py

# Full overlay test (requires WidgetInc)
python tests/test_overlay.py
```

### Using Virtual Environment

```bash
# Make sure to use the virtual environment
C:/Projects/Misc/widget-automation-tool/.venv/Scripts/python.exe tests/run_tests.py
```

## Test Structure

### GUI Tests

- Test the overlay GUI functionality
- Verify hover/click behaviors
- Test status updates and color changes
- Validate positioning and window management

### Unit Tests

- Test individual components in isolation
- Verify configuration loading
- Test mouse control functions
- Validate window detection logic

## Adding New Tests

1. Create new test files following the `test_*.py` naming convention
2. For GUI tests, add them to the `run_tests.py` menu
3. For unit tests, use the unittest framework
4. Update this README when adding new test categories
