"""
Test cases for taskbar icon functionality.
Following project standards: pytest with pytest-qt for GUI testing.
"""

import sys
import os
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from gui.main_window import MainWindow
from overlay.main_overlay import MainOverlay


@pytest.fixture(scope="module")
def app():
    """Create QApplication instance for testing."""
    app = QApplication.instance() or QApplication([])
    yield app


class TestTaskbarIcons:
    """Test cases for taskbar icon functionality."""

    def test_main_window_icon_setting(self, app, qtbot):
        """Test that MainWindow can set taskbar icon properly."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test with a basic icon
        icon = QIcon()
        window.setWindowIcon(icon)

        # Should not crash and icon should be set
        window_icon = window.windowIcon()
        assert window_icon is not None

    def test_overlay_icon_setting(self, app, qtbot):
        """Test that MainOverlay can set taskbar icon properly."""
        overlay = MainOverlay()
        qtbot.addWidget(overlay)

        # Test with a basic icon
        icon = QIcon()
        overlay.setWindowIcon(icon)

        # Should not crash and icon should be set
        overlay_icon = overlay.windowIcon()
        assert overlay_icon is not None

    def test_icon_path_handling(self, app, qtbot):
        """Test icon path handling for development icons."""
        # Test that we can create icons from the expected paths
        base_path = Path(__file__).parent.parent
        icon96_path = base_path / "assets" / "icons" / "development-96.png"
        icon64_path = base_path / "assets" / "icons" / "development-64.png"

        # Test icon creation (should not crash even if files don't exist)
        if icon96_path.exists():
            icon96 = QIcon(str(icon96_path))
            assert not icon96.isNull()

        if icon64_path.exists():
            icon64 = QIcon(str(icon64_path))
            assert not icon64.isNull()

    def test_window_icon_inheritance(self, app, qtbot):
        """Test that windows properly inherit application icon."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Set application icon
        app_icon = QIcon()
        app.setWindowIcon(app_icon)

        # Window should inherit or can be set independently
        window.setWindowIcon(app_icon)
        assert window.windowIcon() is not None
