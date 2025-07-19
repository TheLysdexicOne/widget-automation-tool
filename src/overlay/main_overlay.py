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
    QMenu,
    QApplication,
    QSystemTrayIcon,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect
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
    QKeySequence,
    QShortcut,
)

try:
    import win32gui
    import win32process
    import psutil
    import logging

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    import logging

    logging.warning("win32gui/psutil not available - some features may be limited")

from utility.grid_overlay import create_grid_overlay
from utility.status_manager import StatusManager, ApplicationState
from utility.qss_loader import get_main_stylesheet
from utility.window_utils import (
    find_target_window,
    is_window_valid,
    get_window_info,
)


class StatusIndicatorWidget(QWidget):
    """Custom widget for status circle and text display."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_state = ApplicationState.READY
        self.setFixedHeight(40)  # Slightly taller than buttons to fit circle and text
        self.setMinimumWidth(180)

        # Transparent background to blend with main overlay
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_state(self, state: ApplicationState):
        """Update the status state and trigger repaint."""
        if self.current_state != state:
            self.current_state = state
            self.update()

    def paintEvent(self, event: QPaintEvent):
        """Paint the status circle and text."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw status circle - fixed 24px diameter in right side
        circle_color = self._get_status_color()
        painter.setBrush(QBrush(circle_color))
        painter.setPen(QPen(circle_color.darker(120), 2))

        # Position circle on right side with margin
        circle_size = 24
        margin = 10
        circle_x = self.width() - circle_size - margin
        circle_y = (self.height() - circle_size) // 2  # Center vertically
        circle_rect = QRect(circle_x, circle_y, circle_size, circle_size)
        painter.drawEllipse(circle_rect)

        # Draw status text - left-aligned, inline with circle center
        painter.setPen(QPen(QColor(200, 200, 200), 1))  # Light gray text
        painter.setFont(
            QFont("Segoe UI", 14, QFont.Weight.Bold)
        )  # Slightly smaller for widget

        # Position text inline with circle center
        text_y = circle_y + (circle_size // 2)
        text_rect = QRect(10, text_y - 10, self.width() - circle_size - 30, 20)
        status_text = self.current_state.value.upper()
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            status_text,
        )

    def _get_status_color(self) -> QColor:
        """Get color based on current state."""
        if self.current_state == ApplicationState.ACTIVE:
            return QColor(0, 255, 0)  # Bright green - performing automation
        elif self.current_state == ApplicationState.READY:
            return QColor(
                144, 238, 144
            )  # Light green - recognizes screen, waiting for user
        elif self.current_state == ApplicationState.ATTENTION:
            return QColor(
                255, 165, 0
            )  # Orange - recognizes screen, no automation programmed
        elif self.current_state == ApplicationState.INACTIVE:
            return QColor(
                128, 128, 128
            )  # Gray - doesn't recognize screen, no automation available
        elif self.current_state == ApplicationState.ERROR:
            return QColor(255, 0, 0)  # Red - something wrong with application
        return QColor(128, 128, 128)

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse clicks - cycle through states when clicking status circle."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click is within status circle area
            circle_size = 24
            margin = 10
            circle_x = self.width() - circle_size - margin
            circle_y = (self.height() - circle_size) // 2
            circle_rect = QRect(circle_x, circle_y, circle_size, circle_size)

            if circle_rect.contains(event.pos()):
                # Notify parent to start reset animation instead of cycling states
                if hasattr(self.parent(), "_on_status_clicked"):
                    self.parent()._on_status_clicked(None)  # Parameter not used anymore
                return

        super().mousePressEvent(event)


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

        # Status manager for intelligent state detection
        self.status_manager = StatusManager()
        self.status_manager.state_changed.connect(self._on_status_manager_state_changed)

        # Initialize capabilities
        self.status_manager.update_capabilities(
            scene_recognition=False,  # Not implemented yet
            automation_logic=False,  # Not implemented yet
            target_window=False,  # Will be updated by monitoring
            win32_available=WIN32_AVAILABLE,
        )

        # Application state - managed by StatusManager
        self.current_state = self.status_manager.get_current_state()
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

        # Start initialization sequence (combines animation with actual status detection)
        self.status_manager.start_initialization_sequence()

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

        # Status indicator widget
        self.status_widget = StatusIndicatorWidget(self)
        layout.addWidget(self.status_widget)

        # Buttons section
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(5)

        # FRAMES button
        self.frames_button = QPushButton("FRAMES")
        self.frames_button.setObjectName(
            "frames_button"
        )  # Set object name for QSS targeting
        self.frames_button.setFixedHeight(30)
        self.frames_button.clicked.connect(self._on_frames_clicked)

        # TRACKER button
        self.tracker_button = QPushButton("TRACKER")
        self.tracker_button.setObjectName(
            "tracker_button"
        )  # Set object name for QSS targeting
        self.tracker_button.setFixedHeight(30)
        self.tracker_button.clicked.connect(self._on_tracker_clicked)

        # GRID button
        self.grid_button = QPushButton("GRID")
        self.grid_button.setObjectName(
            "grid_button"
        )  # Set object name for QSS targeting
        self.grid_button.setFixedHeight(30)
        self.grid_button.clicked.connect(self._on_grid_clicked)

        buttons_layout.addWidget(self.frames_button)
        buttons_layout.addWidget(self.tracker_button)
        buttons_layout.addWidget(self.grid_button)
        layout.addLayout(buttons_layout)

        # Add Alt+G shortcut to toggle grid overlay
        grid_shortcut = QShortcut(QKeySequence("Alt+G"), self)
        grid_shortcut.activated.connect(self._on_grid_clicked)

        # Load and apply QSS stylesheet
        stylesheet = get_main_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)

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
        """Create a menu with styling from QSS file."""
        menu = QMenu(parent)
        # Styling is handled by the QSS file loaded in _setup_widget
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
        """Check if target window exists and update position using shared utilities."""
        try:
            # Check current window validity first
            if self.target_hwnd and not is_window_valid(self.target_hwnd):
                self._on_target_lost()
                return

            # Use shared utility to find target window
            target_info = find_target_window(self.target_process)

            if target_info:
                hwnd = target_info["window_info"]["hwnd"]
                pid = target_info["pid"]

                # Check if this is a new window
                if self.target_hwnd != hwnd:
                    self._on_target_found(hwnd, pid)

                # Update position and coordinates using shared data
                self._update_position_from_shared_data(target_info)
            else:
                # Target not found
                if self.target_hwnd:
                    self._on_target_lost()

        except Exception as e:
            self.logger.error(f"Error checking target window: {e}")

    def _on_target_found(self, hwnd: int, pid: int):
        """Handle target window found."""
        self.target_hwnd = hwnd
        self.target_pid = pid
        # Update status manager with target window found
        self.status_manager.update_capabilities(target_window=True)
        self.target_found.emit(True)
        self.logger.info(f"Target window found - HWND: {hwnd}, PID: {pid}")

    def _on_target_lost(self):
        """Handle target window lost."""
        self.target_hwnd = None
        self.target_pid = None
        # Update status manager with target window lost
        self.status_manager.update_capabilities(target_window=False)
        self.target_found.emit(False)
        self.hide()  # Hide overlay when target is lost
        self.logger.info("Target window lost")

    def _on_status_manager_state_changed(self, new_state: ApplicationState):
        """Handle state changes from the status manager."""
        if self.current_state != new_state:
            old_state = self.current_state
            self.current_state = new_state
            self.state_changed.emit(new_state)
            # Update the status indicator widget
            if hasattr(self, "status_widget"):
                self.status_widget.set_state(new_state)
            self.logger.debug(
                f"UI updated for state change: {old_state.value} -> {new_state.value}"
            )

    def _on_status_clicked(self, new_state: ApplicationState):
        """Handle status circle clicked from status widget - start reset sequence."""
        self.logger.info("Status circle clicked - starting reset sequence")
        self.status_manager.start_reset_sequence()

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

    def _update_position_from_shared_data(self, target_info):
        """Update overlay position using shared target window data."""
        try:
            window_info = target_info["window_info"]
            playable_area = target_info["playable_area"]

            # Store window coordinates in the format expected by existing code
            self.window_coords = {
                "x": window_info["window_rect"][0],
                "y": window_info["window_rect"][1],
                "width": window_info["window_width"],
                "height": window_info["window_height"],
                "client_x": window_info["client_x"],
                "client_y": window_info["client_y"],
                "client_width": window_info["client_width"],
                "client_height": window_info["client_height"],
            }

            # Store playable coordinates
            if playable_area:
                self.playable_coords = playable_area
                self.logger.debug(f"Playable area: {self.playable_coords}")

            # Position overlay in top-right of client area
            overlay_x = (
                window_info["client_x"]
                + window_info["client_width"]
                - self.width()
                - 10
            )
            overlay_y = window_info["client_y"] + 40

            self.move(overlay_x, overlay_y)

            # Update grid overlay if it's visible
            if self.grid_visible and self.grid_overlay and playable_area:
                self.grid_overlay.update_playable_area(self.playable_coords)

            if not self.isVisible():
                self.show()

        except Exception as e:
            self.logger.error(f"Error updating position from shared data: {e}")

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
                # Screenshot successful - no need to change state temporarily

        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}")
            # Could trigger error state in status manager if needed

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
            # Launch tracker application from new location
            tracker_path = (
                Path(__file__).parent.parent / "tracker_app" / "tracker_app.py"
            )
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
