"""
Refactored Debug Console

Main debug console window that coordinates individual tab components.
"""

import logging
from PyQt6.QtWidgets import QMainWindow, QTabWidget
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QCloseEvent

from .tabs import ConsoleTab, SettingsTab, MonitoringTab, DebugTab


class DebugConsole(QMainWindow):
    """Main debug console window with modular tab architecture."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.logger = logging.getLogger(__name__)

        # Tab instances
        self.console_tab = None
        self.settings_tab = None
        self.monitoring_tab = None
        self.debug_tab = None

        # Setup UI
        self._setup_ui()

    def _setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("Widget Automation Tool - Debug Console")
        self.setGeometry(100, 100, 800, 600)

        # Central widget with tabs
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Create tabs
        self._create_tabs()

        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # Status bar
        self.statusBar().showMessage("Debug Console Ready")

    def _create_tabs(self):
        """Create all tabs."""
        # Console Tab
        self.console_tab = ConsoleTab(self.app, self)
        self.tab_widget.addTab(self.console_tab, "Console")

        # Settings Tab
        self.settings_tab = SettingsTab(self.app, self)
        self.tab_widget.addTab(self.settings_tab, "Settings")

        # Monitoring Tab
        self.monitoring_tab = MonitoringTab(self.app, self)
        self.tab_widget.addTab(self.monitoring_tab, "Monitoring")

        # Debug Tab
        self.debug_tab = DebugTab(self.app, self)
        self.tab_widget.addTab(self.debug_tab, "Debug")

    def _on_tab_changed(self, index):
        """Handle tab change events."""
        try:
            # Get the current tab
            current_tab = self.tab_widget.widget(index)

            # Notify current tab that it's been activated
            if hasattr(current_tab, "on_tab_activated"):
                current_tab.on_tab_activated()

            # Notify all other tabs that they've been deactivated
            for i in range(self.tab_widget.count()):
                if i != index:
                    tab = self.tab_widget.widget(i)
                    if hasattr(tab, "on_tab_deactivated"):
                        tab.on_tab_deactivated()

        except Exception as e:
            self.logger.error(f"Error handling tab change: {e}")

    def switch_to_tab(self, tab_name):
        """Switch to the specified tab."""
        tab_map = {
            "console": 0,
            "settings": 1,
            "monitoring": 2,
            "debug": 3,
        }

        if tab_name.lower() in tab_map:
            self.tab_widget.setCurrentIndex(tab_map[tab_name.lower()])
            self.logger.info(f"Switched to {tab_name} tab")
        else:
            self.logger.warning(f"Unknown tab: {tab_name}")

    def closeEvent(self, event: QCloseEvent):
        """Handle close event - hide instead of closing."""
        event.ignore()
        self.hide()

    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        # Activate the current tab
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            self._on_tab_changed(current_index)

    def cleanup(self):
        """Cleanup all tabs when console is destroyed."""
        try:
            # Cleanup all tabs
            for i in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(i)
                if hasattr(tab, "cleanup"):
                    tab.cleanup()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Destructor - ensure cleanup."""
        self.cleanup()
