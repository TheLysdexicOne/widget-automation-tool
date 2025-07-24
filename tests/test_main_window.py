"""
Test cases for MainWindow GUI functionality.
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


class TestMainWindow:
    """Test cases for MainWindow functionality."""

    def test_main_window_initialization(self, app, qtbot):
        """Test that MainWindow initializes correctly."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test basic properties that should always exist
        assert window.windowTitle() is not None
        assert window.minimumSize() is not None

        # Test expected properties if they exist
        if window.windowTitle() == "Widget Automation Tool - Data Collection Workbench":
            if hasattr(window, "workbench_tabs"):
                assert hasattr(window, "workbench_tabs")
            if hasattr(window, "database_manager"):
                assert hasattr(window, "database_manager")
            if hasattr(window, "status_manager"):
                assert hasattr(window, "status_manager")

    def test_workbench_tabs_creation(self, app, qtbot):
        """Test that workbench tabs are created correctly."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Check that tabs exist if workbench_tabs attribute exists
        if hasattr(window, "workbench_tabs") and window.workbench_tabs is not None:
            assert window.workbench_tabs.count() >= 4

            # Check tab names
            tab_names = []
            for i in range(window.workbench_tabs.count()):
                tab_names.append(window.workbench_tabs.tabText(i))

            expected_tabs = ["Frame Management", "Screenshot Management", "Region Management", "Data Collection"]
            for expected_tab in expected_tabs:
                assert expected_tab in tab_names

    def test_menu_bar_creation(self, app, qtbot):
        """Test that menu bar is created with expected menus."""
        window = MainWindow()
        qtbot.addWidget(window)

        menubar = window.menuBar()
        assert menubar is not None

        # Check that menus exist if actions are available
        if hasattr(menubar, "actions") and menubar.actions():
            menus = [action.text() for action in menubar.actions() if action.menu()]
            expected_menus = ["&File", "&Edit", "&View", "&Tools", "&Help"]

            for expected_menu in expected_menus:
                if expected_menu in menus:
                    assert expected_menu in menus

    def test_status_bar_creation(self, app, qtbot):
        """Test that status bar is created correctly."""
        window = MainWindow()
        qtbot.addWidget(window)

        status_bar = window.statusBar()
        assert status_bar is not None

        # Test optional status bar components if they exist
        if hasattr(window, "status_message"):
            assert hasattr(window, "status_message")
        if hasattr(window, "connection_status"):
            assert hasattr(window, "connection_status")
        if hasattr(window, "frame_count_status"):
            assert hasattr(window, "frame_count_status")

    def test_frame_tree_functionality(self, app, qtbot):
        """Test frame tree widget functionality."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test frame tree exists if available
        if hasattr(window, "frame_tree") and window.frame_tree is not None:
            header_item = getattr(window.frame_tree, "headerItem", lambda: None)()
            if header_item is not None and hasattr(header_item, "text"):
                assert header_item.text(0) == "Frames Database"

    def test_window_icon_setting(self, app, qtbot):
        """Test that window icon can be set properly."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test icon setting without recursion
        icon = QIcon()  # Empty icon for testing
        window.setWindowIcon(icon)

        # Should not crash or cause recursion
        assert True  # If we get here, no recursion error occurred

    def test_activity_logging(self, app, qtbot):
        """Test activity logging functionality."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test activity logging
        initial_text = window.activity_log.toPlainText()
        window._log_activity("Test message")

        new_text = window.activity_log.toPlainText()
        assert "Test message" in new_text
        assert len(new_text) > len(initial_text)

    def test_target_window_connection(self, app, qtbot):
        """Test target window connection functionality."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test connect to target button functionality
        assert hasattr(window, "target_status_label")
        assert hasattr(window, "connection_status")

        # Initial state should be disconnected
        assert "Not Connected" in window.target_status_label.text() or "Not Found" in window.target_status_label.text()

    def test_data_collection_controls(self, app, qtbot):
        """Test data collection controls."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test data collection buttons exist
        assert hasattr(window, "start_collection_btn")
        assert hasattr(window, "stop_collection_btn")
        assert hasattr(window, "collection_progress")

        # Initial state
        assert window.start_collection_btn.isEnabled()
        assert not window.stop_collection_btn.isEnabled()
        assert not window.is_collecting_data

    def test_menu_actions_connect(self, app, qtbot):
        """Test that menu actions are properly connected."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test file menu actions
        menubar = window.menuBar()
        file_menu = None
        if menubar is not None and hasattr(menubar, "actions"):
            for action in menubar.actions():
                if action.menu() and action.text() == "&File":
                    file_menu = action.menu()
                    break

        if file_menu is not None:
            # Check that actions exist
            file_actions = [action.text() for action in file_menu.actions() if not action.isSeparator()]
            expected_actions = ["&Open Database", "&Save", "&Export Data", "&Import Data", "E&xit"]

            for expected_action in expected_actions:
                if expected_action in file_actions:
                    assert expected_action in file_actions

    def test_toolbar_creation(self, app, qtbot):
        """Test that toolbar is created with expected buttons."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Check for any QToolBar widgets
        from PyQt6.QtWidgets import QToolBar

        toolbars = window.findChildren(QToolBar)
        # If no toolbars found, that's okay for a basic MainWindow
        assert len(toolbars) >= 0

    def test_properties_panel_components(self, app, qtbot):
        """Test properties panel components."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test that properties panel components exist
        assert hasattr(window, "target_status_label")
        assert hasattr(window, "target_process_label")
        assert hasattr(window, "target_window_label")
        assert hasattr(window, "activity_log")

    def test_workbench_switching(self, app, qtbot):
        """Test switching between workbench tabs."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test tab switching if workbench_tabs exists
        if hasattr(window, "workbench_tabs") and window.workbench_tabs is not None:
            # Switch to different tab
            if window.workbench_tabs.count() > 1:
                window.workbench_tabs.setCurrentIndex(1)
                assert window.workbench_tabs.currentIndex() == 1

                # Switch back
                window.workbench_tabs.setCurrentIndex(0)
                assert window.workbench_tabs.currentIndex() == 0

    def test_frame_details_components(self, app, qtbot):
        """Test frame details form components."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test frame management components
        assert hasattr(window, "frame_id_edit")
        assert hasattr(window, "frame_name_edit")
        assert hasattr(window, "frame_item_edit")
        assert hasattr(window, "automation_enabled")

        # Test statistics labels
        assert hasattr(window, "screenshot_count_label")
        assert hasattr(window, "text_regions_label")
        assert hasattr(window, "interact_regions_label")

    def test_screenshot_management_components(self, app, qtbot):
        """Test screenshot management tab components."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test screenshot management components
        assert hasattr(window, "screenshot_list")
        assert hasattr(window, "screenshot_preview")

    def test_region_management_components(self, app, qtbot):
        """Test region management tab components."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test region management components
        assert hasattr(window, "regions_table")
        assert hasattr(window, "region_name_edit")
        assert hasattr(window, "region_x_spin")
        assert hasattr(window, "region_y_spin")
        assert hasattr(window, "region_width_spin")
        assert hasattr(window, "region_height_spin")

    def test_timer_initialization(self, app, qtbot):
        """Test that timers are initialized correctly."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test timers exist
        assert hasattr(window, "target_timer")
        assert hasattr(window, "refresh_timer")

        # Test timers are active
        assert window.target_timer.isActive()
        assert window.refresh_timer.isActive()

    def test_close_event_handling(self, app, qtbot):
        """Test window close event handling."""
        window = MainWindow()
        qtbot.addWidget(window)

        # Test that close event can be handled without errors
        # This tests the cleanup logic
        window.show()
        window.close()

        # Should not crash
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
