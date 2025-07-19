"""
Main Overlay Widget - Primary Application

This is the main application widget that provides:
- Status circle and text
- FRAMES button (screenshot functionality)
- TRACKER button (launch standalone tracker)
- GRID button (playable area border toggle)
- Right-click menu with Close
- Window tracking and playable area calculations
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMenu,
    QApplication,
    QSystemTrayIcon,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QColor,
    QFont,
    QPaintEvent,
    QMouseEvent,
    QContextMenuEvent,
    QIcon,
    QPixmap,
    QAction,
)

try:
    import win32gui
    import win32process
    import psutil

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    logging.warning("win32gui/psutil not available - some features may be limited")

from utility.grid_overlay import create_grid_overlay


class ApplicationState(Enum):
    """Simple application states."""

    ACTIVE = "active"  # Target found and ready
    INACTIVE = "inactive"  # No target found
    ERROR = "error"  # Something wrong


class MainOverlayWidget(QWidget):
    """Main overlay widget - the primary application interface."""

    # Signals
    target_found = pyqtSignal(bool)
    state_changed = pyqtSignal(ApplicationState)

    def __init__(self, target_process="WidgetInc.exe", debug_mode=False):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.target_process = target_process
        self.debug_mode = debug_mode

        # Application state
        self.current_state = ApplicationState.INACTIVE
        self.target_hwnd = None
        self.target_pid = None

        # Cached coordinates
        self.window_coords = {}
        self.playable_coords = {}

        # Grid overlay state
        self.grid_visible = False
        self.grid_overlay = None

        # Timers
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._check_target_window)

        # System tray
        self.tray_icon = None

        # Setup the widget
        self._setup_widget()
        self._setup_system_tray()
        self._setup_grid_overlay()
        self._start_monitoring()

        self.logger.info("Main overlay widget initialized")

    def __del__(self):
        """Destructor to ensure proper cleanup."""
        try:
            if hasattr(self, "monitor_timer") and self.monitor_timer:
                self.monitor_timer.stop()
            if hasattr(self, "tray_icon") and self.tray_icon:
                self.tray_icon.hide()
        except:
            pass  # Ignore errors during destruction

    def _setup_widget(self):
        """Setup the main overlay widget."""
        # Window properties
        self.setWindowTitle("Widget Automation Tool")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(200)
        self.setMinimumSize(200, 120)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Status section
        status_layout = QHBoxLayout()

        # Status text
        self.status_label = QLabel("INACTIVE")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.status_label.setStyleSheet(
            """
            QLabel {
                color: #cccccc;
                background: transparent;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """
        )

        status_layout.addWidget(self.status_label)
        layout.addLayout(status_layout)

        # Buttons section
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(5)

        # FRAMES button
        self.frames_button = QPushButton("FRAMES")
        self.frames_button.setFixedHeight(30)
        self.frames_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2a2a2a;
                color: #cccccc;
                border: 1px solid #505050;
                border-radius: 3px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #606060;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
                border: 1px solid #404040;
            }
        """
        )
        self.frames_button.clicked.connect(self._on_frames_clicked)

        # TRACKER button
        self.tracker_button = QPushButton("TRACKER")
        self.tracker_button.setFixedHeight(30)
        self.tracker_button.setStyleSheet(
            """
            QPushButton {
                background-color: #1a3a5a;
                color: #cccccc;
                border: 1px solid #3a5a7a;
                border-radius: 3px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #2a4a6a;
                color: #ffffff;
                border: 1px solid #4a6a8a;
            }
            QPushButton:pressed {
                background-color: #0a2a4a;
                border: 1px solid #2a4a6a;
            }
        """
        )
        self.tracker_button.clicked.connect(self._on_tracker_clicked)

        # GRID button
        self.grid_button = QPushButton("GRID")
        self.grid_button.setFixedHeight(30)
        self.grid_button.setStyleSheet(
            """
            QPushButton {
                background-color: #5a1a1a;
                color: #cccccc;
                border: 1px solid #7a3a3a;
                border-radius: 3px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #6a2a2a;
                color: #ffffff;
                border: 1px solid #8a4a4a;
            }
            QPushButton:pressed {
                background-color: #4a0a0a;
                border: 1px solid #6a2a2a;
            }
        """
        )
        self.grid_button.clicked.connect(self._on_grid_clicked)

        buttons_layout.addWidget(self.frames_button)
        buttons_layout.addWidget(self.tracker_button)
        buttons_layout.addWidget(self.grid_button)
        layout.addLayout(buttons_layout)

        # Standard context menu with enhanced styling
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        # Add restart action to context menu
        restart_action = QAction("Restart", self)
        restart_action.triggered.connect(self.restart)
        self.addAction(restart_action)

        # Add separator
        separator = QAction(self)
        separator.setSeparator(True)
        self.addAction(separator)

        # Add close action to context menu
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.shutdown)
        self.addAction(exit_action)

    def _setup_system_tray(self):
        """Setup system tray icon for emergency close."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.logger.warning("System tray not available")
            return

        self.tray_icon = QSystemTrayIcon(self)

        # Create simple icon
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(70, 130, 180))
        self.tray_icon.setIcon(QIcon(pixmap))

        # Create tray menu with enhanced native Windows styling
        tray_menu = self._create_styled_menu()
        self._populate_menu(tray_menu)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("Widget Automation Tool")
        self.tray_icon.show()

        self.logger.debug("System tray icon created")

    def _setup_grid_overlay(self):
        """Setup the grid overlay widget."""
        try:
            self.grid_overlay = create_grid_overlay()
            self.logger.debug("Grid overlay initialized")
        except Exception as e:
            self.logger.error(f"Failed to setup grid overlay: {e}")
            self.grid_overlay = None

    def _create_styled_menu(self, parent=None):
        """Create a menu with native Windows styling and industrial touches."""
        menu = QMenu(parent)

        # Apply native Windows-style menu styling with subtle industrial touches
        menu.setStyleSheet(
            """
            QMenu {
                background-color: #f0f0f0;
                border: 1px solid #a0a0a0;
                border-radius: 2px;
                padding: 2px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 9pt;
            }
            QMenu::item {
                background-color: transparent;
                padding: 6px 24px 6px 8px;
                margin: 0px;
                color: #2d2d30;
                border: 1px solid transparent;
            }
            QMenu::item:selected {
                background-color: #316ac5;
                color: white;
                border-radius: 1px;
            }
            QMenu::item:disabled {
                color: #999999;
            }
            QMenu::separator {
                height: 1px;
                background-color: #d4d4d4;
                margin: 2px 0px;
            }
        """
        )

        return menu

    def _populate_menu(self, menu):
        """Populate menu with standard actions."""
        # Add restart action
        restart_action = QAction("Restart", menu)
        restart_action.triggered.connect(self.restart)
        menu.addAction(restart_action)

        # Add separator
        menu.addSeparator()

        # Add exit action
        exit_action = QAction("Exit", menu)
        exit_action.triggered.connect(self.shutdown)
        menu.addAction(exit_action)

        return menu

    def contextMenuEvent(self, event: QContextMenuEvent):
        """Override context menu event to apply custom styling."""
        try:
            # Create styled menu using shared method
            menu = self._create_styled_menu(self)
            self._populate_menu(menu)

            # Show the menu at the event position
            menu.exec(event.globalPos())

        except Exception as e:
            self.logger.error(f"Error showing context menu: {e}")
            # Fallback to default behavior
            super().contextMenuEvent(event)

    def _start_monitoring(self):
        """Start monitoring for the target window."""
        self.monitor_timer.start(1000)  # Check every second
        self.logger.info(f"Started monitoring for {self.target_process}")

    def _check_target_window(self):
        """Check if target window exists and update position."""
        try:
            # Find target process
            target_found = False
            for proc in psutil.process_iter(["pid", "name"]):
                if proc.info["name"] == self.target_process:
                    pid = proc.info["pid"]
                    hwnd = self._find_window_by_pid(pid)
                    if hwnd and self._is_window_valid(hwnd):
                        if self.target_hwnd != hwnd:
                            self._on_target_found(hwnd, pid)
                        target_found = True
                        self._update_position()
                        break

            if not target_found and self.target_hwnd:
                self._on_target_lost()

        except Exception as e:
            self.logger.error(f"Error checking target window: {e}")

    def _find_window_by_pid(self, pid: int) -> Optional[int]:
        """Find window handle by process ID."""
        if not WIN32_AVAILABLE:
            return None

        def enum_windows_proc(hwnd, windows):
            _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
            if window_pid == pid and win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "WidgetInc" in title:
                    windows.append(hwnd)
            return True

        windows = []
        win32gui.EnumWindows(enum_windows_proc, windows)
        return windows[0] if windows else None

    def _is_window_valid(self, hwnd: int) -> bool:
        """Check if window handle is still valid."""
        if not WIN32_AVAILABLE:
            return False
        try:
            return win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd)
        except:
            return False

    def _on_target_found(self, hwnd: int, pid: int):
        """Handle target window found."""
        self.target_hwnd = hwnd
        self.target_pid = pid
        self._set_state(ApplicationState.ACTIVE)
        self.target_found.emit(True)
        self.logger.info(f"Target window found - HWND: {hwnd}, PID: {pid}")

    def _on_target_lost(self):
        """Handle target window lost."""
        self.target_hwnd = None
        self.target_pid = None
        self._set_state(ApplicationState.INACTIVE)
        self.target_found.emit(False)
        self.hide()  # Hide overlay when target is lost
        self.logger.info("Target window lost")

    def _set_state(self, state: ApplicationState):
        """Set application state and update UI."""
        if self.current_state != state:
            old_state = self.current_state
            self.current_state = state
            self.state_changed.emit(state)
            self._update_status_display()
            self.logger.info(f"State changed: {old_state.value} -> {state.value}")

    def _update_status_display(self):
        """Update the status label and trigger repaint for status circle."""
        self.status_label.setText(self.current_state.value.upper())
        self.update()  # Trigger repaint

    def _update_position(self):
        """Update overlay position relative to target window's client area."""
        if not self.target_hwnd or not WIN32_AVAILABLE:
            return

        try:
            # Get window and client coordinates
            window_rect = win32gui.GetWindowRect(self.target_hwnd)
            client_rect = win32gui.GetClientRect(self.target_hwnd)
            client_top_left = win32gui.ClientToScreen(self.target_hwnd, (0, 0))

            # Store window coordinates
            self.window_coords = {
                "x": window_rect[0],
                "y": window_rect[1],
                "width": window_rect[2] - window_rect[0],
                "height": window_rect[3] - window_rect[1],
                "client_x": client_top_left[0],
                "client_y": client_top_left[1],
                "client_width": client_rect[2],
                "client_height": client_rect[3],
            }

            # Calculate playable area (3:2 aspect ratio, centered)
            self._calculate_playable_area()

            # Position overlay in top-right of client area
            overlay_x = (
                client_top_left[0]
                + self.window_coords["client_width"]
                - self.width()
                - 10
            )
            overlay_y = client_top_left[1] + 40

            self.move(overlay_x, overlay_y)

            if not self.isVisible():
                self.show()

        except Exception as e:
            self.logger.error(f"Error updating position: {e}")

    def _calculate_playable_area(self):
        """Calculate the playable area coordinates centered in client area."""
        if not self.window_coords:
            return

        client_x = self.window_coords["client_x"]
        client_y = self.window_coords["client_y"]
        client_width = self.window_coords["client_width"]
        client_height = self.window_coords["client_height"]

        # Calculate 3:2 aspect ratio area centered in client
        target_ratio = 3.0 / 2.0
        client_ratio = client_width / client_height if client_height else 1

        if client_ratio > target_ratio:
            # Black bars on sides
            playable_height = client_height
            playable_width = int(playable_height * target_ratio)
        else:
            # Black bars on top/bottom
            playable_width = client_width
            playable_height = int(playable_width / target_ratio)

        # Center the playable area in the client area
        playable_x = client_x + (client_width - playable_width) // 2
        playable_y = client_y + (client_height - playable_height) // 2

        self.playable_coords = {
            "x": playable_x,
            "y": playable_y,
            "width": playable_width,
            "height": playable_height,
        }

        # Update grid overlay if it's visible
        if self.grid_visible and self.grid_overlay:
            self.grid_overlay.update_playable_area(self.playable_coords)

        self.logger.debug(f"Playable area: {self.playable_coords}")

    def paintEvent(self, event: QPaintEvent):
        """Paint the overlay with industrial dark mode styling."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background with industrial dark theme
        bg_color = QColor(20, 20, 20, 240)  # Very dark background
        painter.fillRect(self.rect(), bg_color)

        # Draw border with subtle highlight
        border_color = QColor(80, 80, 80, 200)
        painter.setPen(QPen(border_color, 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

        # Draw inner border for depth
        inner_border = QColor(60, 60, 60, 150)
        painter.setPen(QPen(inner_border, 1))
        painter.drawRect(self.rect().adjusted(1, 1, -2, -2))

        # Draw status circle
        circle_color = self._get_status_color()
        painter.setBrush(QBrush(circle_color))
        painter.setPen(QPen(circle_color.darker(120), 2))

        circle_rect = self.rect().adjusted(160, 10, -10, -80)
        painter.drawEllipse(circle_rect)

    def _get_status_color(self) -> QColor:
        """Get color based on current state."""
        if self.current_state == ApplicationState.ACTIVE:
            return QColor(0, 255, 0)  # Green
        elif self.current_state == ApplicationState.INACTIVE:
            return QColor(128, 128, 128)  # Gray
        elif self.current_state == ApplicationState.ERROR:
            return QColor(255, 0, 0)  # Red
        return QColor(128, 128, 128)

    def _on_frames_clicked(self):
        """Handle FRAMES button click - screenshot functionality."""
        self.logger.info("FRAMES button clicked")
        try:
            if not self.target_hwnd:
                self.logger.warning("No target window for screenshot")
                return

            # Create output directory
            output_dir = Path(__file__).parent.parent.parent / "analysis_output"
            output_dir.mkdir(exist_ok=True)

            # Take screenshot of target window
            screenshot_path = self._capture_window_screenshot(output_dir)

            if screenshot_path:
                self.logger.info(f"Screenshot saved: {screenshot_path}")
                # Change state temporarily to show action completed
                old_state = self.current_state
                self._set_state(ApplicationState.ACTIVE)
                QTimer.singleShot(1000, lambda: self._set_state(old_state))

        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}")
            self._set_state(ApplicationState.ERROR)

    def _capture_window_screenshot(self, output_dir: Path) -> Optional[Path]:
        """Capture screenshot of the target window."""
        if not self.target_hwnd or not WIN32_AVAILABLE:
            return None

        try:
            import time
            from PIL import Image, ImageGrab

            # Get window rectangle
            window_rect = win32gui.GetWindowRect(self.target_hwnd)
            x, y, x2, y2 = window_rect
            width = x2 - x
            height = y2 - y

            # Create timestamp for filename
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            screenshot_path = output_dir / f"screenshot_{timestamp}.png"

            # Take screenshot using PIL
            screenshot = ImageGrab.grab(bbox=(x, y, x2, y2))
            screenshot.save(screenshot_path)

            return screenshot_path

        except ImportError:
            self.logger.error("PIL not available for screenshots")
            return None
        except Exception as e:
            self.logger.error(f"Screenshot capture failed: {e}")
            return None

    def _on_tracker_clicked(self):
        """Handle TRACKER button click - launch standalone tracker."""
        self.logger.info("TRACKER button clicked")
        try:
            # Launch tracker application
            tracker_path = Path(__file__).parent.parent / "tracker" / "tracker_app.py"
            if tracker_path.exists():
                subprocess.Popen(
                    [
                        sys.executable,
                        str(tracker_path),
                        f"--target={self.target_process}",
                    ]
                )
                self.logger.info("Launched tracker application")
            else:
                self.logger.error(f"Tracker application not found at: {tracker_path}")
        except Exception as e:
            self.logger.error(f"Error launching tracker: {e}")

    def _on_grid_clicked(self):
        """Handle GRID button click - toggle playable area border."""
        self.logger.info("GRID button clicked")
        try:
            if not self.grid_overlay:
                self.logger.warning("Grid overlay not available")
                return

            self.grid_visible = not self.grid_visible

            if self.grid_visible:
                if self.playable_coords:
                    self.grid_overlay.update_playable_area(self.playable_coords)
                    self.grid_overlay.show_grid()
                    self.logger.info("Grid overlay shown")
                else:
                    self.logger.warning(
                        "No playable area coordinates available for grid"
                    )
                    self.grid_visible = False
            else:
                self.grid_overlay.hide_grid()
                self.logger.info("Grid overlay hidden")

        except Exception as e:
            self.logger.error(f"Error toggling grid: {e}")
            self.grid_visible = False

    def restart(self):
        """Restart the application."""
        self.logger.info("Restarting application...")

        try:
            # Stop monitoring and cleanup
            if hasattr(self, "monitor_timer") and self.monitor_timer:
                self.monitor_timer.stop()
                self.monitor_timer.timeout.disconnect()

            if hasattr(self, "tray_icon") and self.tray_icon:
                self.tray_icon.hide()
                self.tray_icon.setContextMenu(None)

            self.hide()

            # Launch new instance
            import sys
            import subprocess
            import os

            # Get the main script path
            main_script = Path(__file__).parent.parent / "main.py"

            # Build command arguments
            args = [sys.executable, str(main_script)]
            if self.debug_mode:
                args.append("--debug")
            args.extend(["--target", self.target_process])

            # Start new process
            subprocess.Popen(args, cwd=main_script.parent.parent)
            self.logger.info("New instance launched, shutting down current instance")

            # Use QTimer.singleShot for cleaner shutdown
            from PyQt6.QtCore import QTimer

            QTimer.singleShot(100, lambda: [QApplication.quit(), os._exit(0)])

        except Exception as e:
            self.logger.error(f"Error during restart: {e}")
            # If restart fails, just continue running

    def shutdown(self):
        """Gracefully shutdown the application."""
        self.logger.info("Shutting down overlay application...")

        try:
            # Stop timer first
            if hasattr(self, "monitor_timer") and self.monitor_timer:
                self.monitor_timer.stop()
                self.monitor_timer.timeout.disconnect()
                self.monitor_timer = None

            # Clean up tray icon
            if hasattr(self, "tray_icon") and self.tray_icon:
                self.tray_icon.hide()
                self.tray_icon.setContextMenu(None)
                self.tray_icon = None

            # Clean up grid overlay
            if hasattr(self, "grid_overlay") and self.grid_overlay:
                self.grid_overlay.hide()
                self.grid_overlay = None
                self.grid_visible = False

            # Disconnect any remaining signals
            try:
                self.target_found.disconnect()
                self.state_changed.disconnect()
            except:
                pass  # Ignore if already disconnected

            # Hide the widget
            self.hide()

            # Clear references
            self.target_hwnd = None
            self.target_pid = None
            self.window_coords = {}
            self.playable_coords = {}

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

        # Use QTimer.singleShot to defer the quit call
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(100, QApplication.quit)

    def get_current_coordinates(self) -> Dict[str, Any]:
        """Get current window and playable area coordinates."""
        return {
            "window": self.window_coords,
            "playable_area": self.playable_coords,
            "state": self.current_state.value,
        }
