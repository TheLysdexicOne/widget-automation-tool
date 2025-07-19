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

        # Debouncing for close events
        self._closing = False
        self._last_close_time = 0

        # Setup UI
        self._setup_ui()

    def _setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("Widget Automation Tool - Debug Console")
        self.setGeometry(100, 100, 800, 600)

        # Set proper window flags for system tray behavior and focus
        from PyQt6.QtCore import Qt

        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )

        # Ensure window can receive focus properly
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        self.setAttribute(Qt.WidgetAttribute.WA_X11NetWmWindowTypeDialog, False)

        # Central widget with tabs
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # Create tabs
        self.console_tab = ConsoleTab(self.app, self)
        self.tab_widget.addTab(self.console_tab, "Console")

        self.settings_tab = SettingsTab(self.app, self)
        self.tab_widget.addTab(self.settings_tab, "Settings")

        self.monitoring_tab = MonitoringTab(self.app, self)
        self.tab_widget.addTab(self.monitoring_tab, "Monitoring")

        self.debug_tab = DebugTab(self.app, self)
        self.tab_widget.addTab(self.debug_tab, "Debug")

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
        """Handle close event - hide instead of closing (minimize to system tray)."""
        # Debounce close events to prevent multiple rapid close attempts
        import time

        current_time = time.time()
        if self._closing or (current_time - self._last_close_time) < 0.5:
            event.ignore()
            return

        self._closing = True
        self._last_close_time = current_time

        self.logger.info("Debug console close event - minimizing to system tray...")
        event.ignore()  # Don't actually close the window

        # Hide the console (minimize to tray)
        self.minimize_to_tray()

        # Reset closing flag after a short delay
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(500, lambda: setattr(self, "_closing", False))

    def minimize_to_tray(self):
        """Minimize the console to system tray."""
        if self._closing:
            return  # Already in process of closing

        try:
            self.logger.info("Minimizing debug console to system tray")
            self.hide()

            # Update system tray menu text if available
            if hasattr(self.app, "system_tray") and self.app.system_tray:
                self.app.system_tray._update_menu_actions()

        except Exception as e:
            self.logger.error(f"Error minimizing to tray: {e}")
            # Fallback: just hide the window
            super().hide()

    def showEvent(self, event):
        """Handle show event - restore from system tray."""
        self.logger.info("Debug console shown - restoring from system tray")
        super().showEvent(event)

        # Use a timer to ensure focus is set after the window is fully shown
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(100, self._ensure_focus)

        # Update system tray menu text if available
        if hasattr(self.app, "system_tray") and self.app.system_tray:
            self.app.system_tray._update_menu_actions()

        # Activate the current tab
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            self._on_tab_changed(current_index)

    def _ensure_focus(self):
        """Ensure the console window gets and keeps focus."""
        try:
            # Multiple attempts to ensure focus
            self.show()
            self.raise_()
            self.activateWindow()
            self.setFocus()

            # Force to front on Windows with more aggressive approach
            try:
                import win32gui
                import win32con

                hwnd = int(self.winId())

                # Get current foreground window
                current_fg = win32gui.GetForegroundWindow()

                # Try to set as foreground window
                win32gui.SetForegroundWindow(hwnd)

                # If that didn't work, try the more aggressive approach
                if win32gui.GetForegroundWindow() != hwnd:
                    # Temporarily set to topmost, then remove topmost
                    win32gui.SetWindowPos(
                        hwnd,
                        win32con.HWND_TOPMOST,
                        0,
                        0,
                        0,
                        0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
                    )
                    win32gui.SetWindowPos(
                        hwnd,
                        win32con.HWND_NOTOPMOST,
                        0,
                        0,
                        0,
                        0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
                    )

                    # Final attempt to set foreground
                    win32gui.SetForegroundWindow(hwnd)

                self.logger.debug(
                    f"Focus set - previous FG: {current_fg}, current FG: {win32gui.GetForegroundWindow()}"
                )

            except Exception as e:
                self.logger.debug(f"Could not use win32 to force window focus: {e}")

            # As a backup, try Qt focus methods again
            self.raise_()
            self.activateWindow()

        except Exception as e:
            self.logger.error(f"Error ensuring focus: {e}")

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
