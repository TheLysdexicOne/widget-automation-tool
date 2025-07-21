"""
Test configuration for pytest
"""

import pytest
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication

# Add the src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for testing Qt widgets."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit the app during tests as it may be needed for multiple tests
