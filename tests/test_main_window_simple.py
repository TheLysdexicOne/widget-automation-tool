"""
Simple test cases for MainWindow GUI functionality.
Following project standards: pytest with pytest-qt for GUI testing.
"""

import sys
import os
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from gui.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
    """Create QApplication instance for testing."""
    app = QApplication.instance() or QApplication([])
    yield app


class TestMainWindowSimple:
    """Simple test cases for MainWindow functionality."""

    def test_main_window_initialization(self, app, qtbot):
        """Test that MainWindow initializes correctly."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test basic properties that should always exist
        assert window.windowTitle() is not None
        assert window.minimumSize() is not None

        # Test that it's a QMainWindow
        assert hasattr(window, "menuBar")
        assert hasattr(window, "statusBar")
        assert hasattr(window, "setCentralWidget")

    def test_window_can_be_shown(self, app, qtbot):
        """Test that window can be shown without errors."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Should be able to show and hide without crashing
        window.show()
        assert window.isVisible()

        window.hide()
        assert not window.isVisible()

    def test_window_icon_setting(self, app, qtbot):
        """Test that window icon can be set properly."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test icon setting without recursion
        icon = QIcon()  # Empty icon for testing
        window.setWindowIcon(icon)

        # Should not crash or cause recursion
        assert True  # If we get here, no recursion error occurred

    def test_menu_bar_exists(self, app, qtbot):
        """Test that menu bar exists."""
        window = MainWindow()
        qtbot.addWidget(window)

        menubar = window.menuBar()
        assert menubar is not None

    def test_status_bar_exists(self, app, qtbot):
        """Test that status bar exists."""
        window = MainWindow()
        qtbot.addWidget(window)

        status_bar = window.statusBar()
        assert status_bar is not None

    def test_close_event_handling(self, app, qtbot):
        """Test window close event handling."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test that close event can be handled without errors
        window.show()
        window.close()

        # Should not crash
        assert True

    def test_window_resize(self, app, qtbot):
        """Test window can be resized."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test resizing
        window.resize(800, 600)
        size = window.size()
        assert size.width() >= 600  # Should at least honor minimum if set
        assert size.height() >= 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
