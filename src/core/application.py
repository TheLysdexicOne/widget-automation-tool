"""
Core Application Module - Main Application Coordinator

This module contains the main application class that coordinates all components.
"""

import logging
import sys
from enum import Enum
from typing import Optional

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QAction

from core.system_tray import SystemTrayManager
from core.process_monitor import ProcessMonitor
from core.config_manager import ConfigManager
from console.debug_console import DebugConsole
from overlay.overlay_window import OverlayWindow


class ApplicationState(Enum):
    """Application state enumeration."""

    ACTIVE = "active"
    WAITING = "waiting"
    INACTIVE = "inactive"
    ERROR = "error"


class WidgetAutomationApp(QObject):
    """Main application class that coordinates all components."""

    # Signals
    state_changed = pyqtSignal(ApplicationState)
    target_process_found = pyqtSignal(bool)

    def __init__(
        self, debug_mode=False, test_mode=False, target_process="WidgetInc.exe"
    ):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.debug_mode = debug_mode
        self.test_mode = test_mode
        self.target_process = target_process

        # Application state
        self._state = ApplicationState.INACTIVE

        # Components
        self.config_manager = None
        self.system_tray = None
        self.process_monitor = None
        self.debug_console = None
        self.overlay_window = None

        # Initialize components
        self._initialize_components()

    def _initialize_components(self):
        """Initialize all application components."""
        try:
            self.logger.info("Initializing application components...")

            # Configuration manager
            self.config_manager = ConfigManager()

            # System tray
            self.system_tray = SystemTrayManager(self)

            # Process monitor
            self.process_monitor = ProcessMonitor(self, self.target_process)
            self.process_monitor.target_found.connect(self._on_target_process_found)
            self.process_monitor.target_lost.connect(self._on_target_process_lost)

            # Debug console (create but don't show unless debug mode)
            self.debug_console = DebugConsole(self)
            if self.debug_mode:
                self.debug_console.show()

            # Overlay window
            self.overlay_window = OverlayWindow(self)

            # Connect signals
            self.state_changed.connect(self._on_state_changed)

            # Start process monitoring
            self.process_monitor.start_monitoring()

            self.logger.info("All components initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            self.set_state(ApplicationState.ERROR)

    def _on_target_process_found(self, hwnd):
        """Handle target process found."""
        self.logger.info(f"Target process found with handle: {hwnd}")
        self.target_process_found.emit(True)

        # Attach overlay to the target window
        if self.overlay_window:
            self.overlay_window.attach_to_window(hwnd)

        # Update state if we were inactive
        if self._state == ApplicationState.INACTIVE:
            self.set_state(ApplicationState.WAITING)

    def _on_target_process_lost(self):
        """Handle target process lost."""
        self.logger.info("Target process lost")
        self.target_process_found.emit(False)

        # Hide overlay
        if self.overlay_window:
            self.overlay_window.hide()

        # Update state
        self.set_state(ApplicationState.INACTIVE)

    def _on_state_changed(self, new_state):
        """Handle application state changes."""
        self.logger.info(f"Application state changed to: {new_state.value}")

        # Update overlay color based on state
        if self.overlay_window:
            self.overlay_window.update_state_color(new_state)

    def set_state(self, state: ApplicationState):
        """Set the application state."""
        if self._state != state:
            old_state = self._state
            self._state = state
            self.logger.debug(f"State transition: {old_state.value} -> {state.value}")
            self.state_changed.emit(state)

    def get_state(self) -> ApplicationState:
        """Get the current application state."""
        return self._state

    def show_debug_console(self):
        """Show the debug console."""
        if self.debug_console:
            self.debug_console.show()
            self.debug_console.raise_()
            self.debug_console.activateWindow()

    def run_tests(self) -> int:
        """Run automated tests."""
        self.logger.info("Running automated tests...")

        # TODO: Implement actual test cases
        # For now, just simulate a test run

        try:
            # Test component initialization
            if not all(
                [
                    self.config_manager,
                    self.system_tray,
                    self.process_monitor,
                    self.debug_console,
                    self.overlay_window,
                ]
            ):
                self.logger.error("Component initialization test failed")
                return 1

            # Test state changes
            original_state = self.get_state()
            self.set_state(ApplicationState.WAITING)
            if self.get_state() != ApplicationState.WAITING:
                self.logger.error("State change test failed")
                return 1
            self.set_state(original_state)

            self.logger.info("All tests passed")
            return 0

        except Exception as e:
            self.logger.error(f"Test execution failed: {e}")
            return 1

    def shutdown(self):
        """Gracefully shutdown the application."""
        self.logger.info("Shutting down application...")

        try:
            # Stop process monitoring
            if self.process_monitor:
                self.process_monitor.stop_monitoring()

            # Hide overlay
            if self.overlay_window:
                self.overlay_window.hide()

            # Close debug console
            if self.debug_console:
                self.debug_console.close()

            # Clean up system tray
            if self.system_tray:
                self.system_tray.cleanup()

            self.logger.info("Application shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

        # Exit the application
        QApplication.quit()
