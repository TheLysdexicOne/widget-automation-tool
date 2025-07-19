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
from core.window_manager import WindowManager
from core.mouse_tracker import MouseTracker
from console.debug_console import DebugConsole
from overlay.overlay_window_original import OverlayWindowOriginal


class ApplicationState(Enum):
    """Application state enumeration."""

    ACTIVE = "active"  # performing automation
    READY = (
        "ready"  # tool recognizes screen/minigame and is waiting for user to activate
    )
    ATTENTION = (
        "attention"  # tool recognizes screen/minigame but no automation programmed
    )
    INACTIVE = "inactive"  # tool does not recognize current screen/minigame
    ERROR = "error"  # something wrong with application


class WidgetAutomationApp(QObject):
    """Main application class that coordinates all components."""

    # Signals
    state_changed = pyqtSignal(ApplicationState)
    target_process_found = pyqtSignal(bool)

    def __init__(self, debug_mode=False, target_process="WidgetInc.exe"):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.debug_mode = debug_mode
        self.target_process = target_process

        # Application state
        self._state = ApplicationState.INACTIVE

        # Components
        self.config_manager = None
        self.system_tray = None
        self.process_monitor = None
        self.window_manager = None
        self.mouse_tracker = None
        self.debug_console = None
        self.overlay_window = None

        # Current target window info
        self.current_target_hwnd = None
        self.current_target_window = None

        # Initialize components
        self._initialize_components()

    def _initialize_components(self):
        """Initialize all application components."""
        try:
            self.logger.info("Initializing application components...")

            # Configuration manager
            self.config_manager = ConfigManager()

            # Window manager (Core - handles all window operations)
            self.window_manager = WindowManager()

            # Mouse tracker (Core - handles mouse tracking)
            self.mouse_tracker = MouseTracker(self.window_manager)

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

            # Overlay window (original-style with screenshot functionality)
            try:
                self.overlay_window = OverlayWindowOriginal(self.window_manager, self)
                self.logger.info("Overlay window created successfully")
            except Exception as e:
                self.logger.error(f"Failed to create overlay window: {e}")
                self.overlay_window = None

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

        # Store target window information
        self.current_target_hwnd = hwnd
        try:
            import pygetwindow as gw

            windows = gw.getWindowsWithTitle("WidgetInc")
            if windows:
                self.current_target_window = windows[0]
        except Exception as e:
            self.logger.error(f"Error getting target window: {e}")
            self.current_target_window = None

        # Show and position overlay for the target window
        if self.overlay_window:
            self.overlay_window.position_overlay()
            self.overlay_window.show()

        # Update state - when target process is found, we don't know what screen it's on yet
        # So we start with INACTIVE (not recognized) until we can analyze the screen content
        if self._state in [ApplicationState.ERROR]:
            self.set_state(ApplicationState.INACTIVE)

    def _on_target_process_lost(self):
        """Handle target process lost."""
        self.logger.info("Target process lost")
        self.target_process_found.emit(False)

        # Clear target window information
        self.current_target_hwnd = None
        self.current_target_window = None

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
        """Show the debug console with proper focus."""
        if self.debug_console:
            self.debug_console.show()
            self.debug_console._ensure_focus()

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

            # Close debug console properly
            if self.debug_console:
                # Force close without event handling
                self.debug_console.setVisible(False)
                self.debug_console.cleanup()

            # Clean up system tray
            if self.system_tray:
                self.system_tray.cleanup()

            self.logger.info("Application shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

        # Force exit the application
        try:
            from PyQt6.QtWidgets import QApplication

            QApplication.quit()
        except:
            pass

        # Force exit as last resort
        import os

        os._exit(0)
