"""
Main Overlay Widget - Primary Application

Provides status display and control buttons for widget automation.
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMenu, QApplication, QSystemTrayIcon
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QPainter,
    QPen,
    QColor,
    QPaintEvent,
    QContextMenuEvent,
    QIcon,
    QPixmap,
    QAction,
    QKeySequence,
    QShortcut,
    QFont,
)

try:
    import win32gui

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    logging.getLogger(__name__).warning("win32gui not available - some features limited")

from utility.grid_overlay import create_grid_overlay
from utility.status_manager import StatusManager, ApplicationState
from utility.qss_loader import get_main_stylesheet
from utility.window_utils import find_target_window, is_window_valid
from frames import FramesManager


def get_status_color(state: ApplicationState) -> QColor:
    """Centralized state-to-color mapping utility."""
    color_map = {
        ApplicationState.ACTIVE: QColor(0, 255, 0),  # Bright green - performing automation
        ApplicationState.READY: QColor(144, 238, 144),  # Light green - ready, waiting for user
        ApplicationState.ATTENTION: QColor(255, 165, 0),  # Orange - no automation programmed
        ApplicationState.INACTIVE: QColor(128, 128, 128),  # Gray - no automation available
        ApplicationState.ERROR: QColor(255, 0, 0),  # Red - application error
    }
    return color_map.get(state, QColor(128, 128, 128))


class MainOverlayWidget(QWidget):
    def get_current_frame_data(self):
        """Return the currently selected frame data from frames_manager, or None if unavailable."""
        if self.frames_manager and hasattr(self.frames_manager, "selected_frame"):
            return self.frames_manager.selected_frame
        return None

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

        # Initialize capabilities first
        self.status_manager.update_capabilities(
            scene_recognition=False,  # Not implemented yet
            automation_logic=False,  # Not implemented yet
            target_window=False,  # Will be updated by monitoring
            win32_available=WIN32_AVAILABLE,
        )

        # Application state - managed by StatusManager
        self.current_state = self.status_manager.get_current_state()

        # Connect signal AFTER state is initialized
        self.status_manager.state_changed.connect(self._on_status_manager_state_changed)
        self.target_hwnd = None

        # Window dragging state
        self.dragging = False
        self.drag_start_position = None
        self.is_draggable = False
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

        # Frames management system
        self.frames_manager = None

        # Setup the widget
        self._setup_widget()
        self._setup_system_tray()
        self._setup_grid_overlay()
        self._setup_frames_system()
        self._start_monitoring()

        # Initialize state detection
        self.status_manager.force_state_detection()

        self.logger.info("Main overlay widget initialized")

    def _create_button(self, text: str, object_name: str, callback) -> QPushButton:
        """Helper method to create styled buttons with consistent properties."""
        button = QPushButton(text)
        button.setObjectName(object_name)
        button.setFixedHeight(30)
        button.clicked.connect(callback)
        return button

    def _add_context_actions(self):
        """Helper method to add context menu actions."""
        # Add restart action
        restart_action = QAction("Restart", self)
        restart_action.triggered.connect(self.restart)
        self.addAction(restart_action)

        # Add separator
        separator = QAction(self)
        separator.setSeparator(True)
        self.addAction(separator)

        # Add close action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.shutdown)
        self.addAction(exit_action)

    def __del__(self):
        """Destructor to ensure proper cleanup."""
        try:
            if hasattr(self, "monitor_timer") and self.monitor_timer:
                self.monitor_timer.stop()
            if hasattr(self, "tray_icon") and self.tray_icon:
                self.tray_icon.hide()
        except Exception:
            pass  # Ignore errors during destruction

    def _setup_widget(self):
        """Setup the main overlay widget."""
        # Window properties
        self.setWindowTitle("Widget Automation Tool")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(180)
        self.setMinimumSize(180, 120)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # --- Status Row: Indicator + Text ---
        from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy

        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(8)

        self.status_label = QLabel()
        self.status_label.setObjectName("status_text_label")
        self.status_label.setText(self.current_state.value.upper())
        self.status_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: rgb(200,200,200);")
        self.status_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        status_row.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.status_button = QPushButton()
        self.status_button.setObjectName("status_indicator_button")
        self.status_button.setFixedSize(24, 24)
        self.status_button.setEnabled(True)  # purely decorative
        status_row.addWidget(self.status_button, alignment=Qt.AlignmentFlag.AlignVCenter)
        self._update_status_button_style()

        layout.addLayout(status_row)

        # Buttons section
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(5)

        # Create buttons using helper method
        self.frames_button = self._create_button("FRAMES", "frames_button", self._on_frames_clicked)
        self.screenshots_button = self._create_button("SCREENSHOTS", "screenshots_button", self._on_screenshots_clicked)
        self.tracker_button = self._create_button("TRACKER", "tracker_button", self._on_tracker_clicked)
        self.grid_button = self._create_button("GRID", "grid_button", self._on_grid_clicked)

        buttons_layout.addWidget(self.frames_button)
        buttons_layout.addWidget(self.screenshots_button)
        buttons_layout.addWidget(self.tracker_button)
        buttons_layout.addWidget(self.grid_button)
        layout.addLayout(buttons_layout)

    def _on_screenshots_clicked(self):
        """Handle SCREENSHOTS button click - show screenshot manager dialog for current frame."""
        try:
            from overlay.screenshot_manager import ScreenshotManagerDialog

            # You may need to implement get_current_frame_data() to retrieve the current frame context
            frame_data = self.get_current_frame_data() if hasattr(self, "get_current_frame_data") else None
            if not frame_data:
                self.logger.warning("No frame selected for screenshots.")
                return
            # Pass the frames_manager or DB manager as needed
            dialog = ScreenshotManagerDialog(frame_data, self.frames_manager, self)
            dialog.exec()
        except Exception as e:
            self.logger.error(f"Error showing screenshot manager dialog: {e}")

        # Add Alt+G shortcut to toggle grid overlay
        grid_shortcut = QShortcut(QKeySequence("Alt+G"), self)
        grid_shortcut.activated.connect(self._on_grid_clicked)

        # Load and apply QSS stylesheet
        stylesheet = get_main_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)

        # Standard context menu with enhanced styling
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self._add_context_actions()

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

        # Create tray menu
        tray_menu = self._create_standard_menu()
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

    def _setup_frames_system(self):
        """Setup the frames management system."""
        try:
            # Initialize frames manager (project root is calculated internally)
            self.frames_manager = FramesManager(self)

            self.logger.debug("Frames management system initialized")
        except Exception as e:
            self.logger.error(f"Failed to setup frames system: {e}")
            self.frames_manager = None

    def _create_standard_menu(self, parent=None):
        """Create a standardized menu with common actions."""
        menu = QMenu(parent)
        self._add_menu_actions(menu)
        return menu

    def _add_menu_actions(self, menu: QMenu):
        """Helper method to add standard menu actions to any menu."""
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

    def contextMenuEvent(self, event: QContextMenuEvent):
        """Override context menu event to apply custom styling."""
        try:
            # Create standardized menu
            menu = self._create_standard_menu(self)
            menu.exec(event.globalPos())

        except Exception as e:
            self.logger.error(f"Error showing context menu: {e}")
            # Fallback to default behavior
            super().contextMenuEvent(event)

    def _set_monitoring_speed(self, fast_mode: bool, reason: str):
        """Centralized monitoring speed control."""
        if not self.monitor_timer:
            return

        target_interval = 100 if fast_mode else 500
        current_interval = self.monitor_timer.interval()

        if current_interval != target_interval:
            self.monitor_timer.setInterval(target_interval)
            mode = "fast (100ms)" if fast_mode else "slow (500ms)"
            self.logger.debug(f"Monitoring set to {mode} - {reason}")

    def _start_monitoring(self):
        """Start monitoring for the target window."""
        # Start with fast polling for initial detection
        if self.monitor_timer:
            self.monitor_timer.start(100)  # Check every 100ms initially
        self.logger.info(f"Started monitoring for {self.target_process}")

        # Perform immediate check to avoid delay in positioning
        QTimer.singleShot(0, self._check_target_window)  # Immediate check
        QTimer.singleShot(50, self._check_target_window)  # Quick follow-up

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

                # Slow down monitoring once target is stable
                self._set_monitoring_speed(fast_mode=False, reason="target window stable")

            else:
                # Target not found - speed up monitoring if it was slowed down
                if self.target_hwnd:
                    self._on_target_lost()

                # Speed up monitoring when no target (for faster detection)
                self._set_monitoring_speed(fast_mode=True, reason="searching for target")

        except Exception as e:
            self.logger.error(f"Error checking target window: {e}")

    def _on_target_found(self, hwnd: int, pid: int):
        """Handle target window found."""
        self.target_hwnd = hwnd
        self.target_pid = pid
        # Disable dragging when target is found
        self.is_draggable = False
        # Update status manager with target window found
        self.status_manager.update_capabilities(target_window=True)
        self.target_found.emit(True)
        self.logger.info(f"Target window found - HWND: {hwnd}, PID: {pid}")

    def _on_target_lost(self):
        """Handle target window lost."""
        self.target_hwnd = None
        self.target_pid = None
        # Center the widget on the current window and enable dragging
        self._center_on_screen()
        self.is_draggable = True
        self.show()  # Show overlay when target is lost so user can drag it
        # Update status manager with target window lost
        self.status_manager.update_capabilities(target_window=False)
        self.target_found.emit(False)

        # Speed up monitoring to quickly detect when target returns
        self._set_monitoring_speed(fast_mode=True, reason="target lost, searching")

        self.logger.info("Target window lost")

    def _on_status_manager_state_changed(self, new_state: ApplicationState):
        """Handle state changes from the status manager."""
        if self.current_state != new_state:
            old_state = self.current_state
            self.current_state = new_state
            self.state_changed.emit(new_state)
            self._update_status_button_style()
            self.status_label.setText(self.current_state.value.upper())
            self.update()
            self.logger.debug(f"UI updated for state change: {old_state.value} -> {new_state.value}")

    def _update_status_button_style(self):
        """Update the status indicator button's color and tooltip based on state."""
        color = get_status_color(self.current_state)
        # Style: circular, flat, colored background, no border
        qss = f"""
            QPushButton#status_indicator_button {{
                background-color: rgba({color.red()}, {color.green()}, {color.blue()}, 255);
                border: 2px solid rgba({color.darker(120).red()}, {color.darker(120).green()}, {color.darker(120).blue()}, 255);
                border-radius: 12px;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
                padding: 0px;
            }}
        """
        self.status_button.setStyleSheet(qss)
        self.status_button.setToolTip(self.current_state.value.capitalize())

    def _on_status_clicked(self, new_state: ApplicationState):
        """Handle status circle clicked from status widget - force state detection."""
        self.logger.info("Status circle clicked - forcing state detection")
        self.status_manager.force_state_detection()

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

            # Position overlay in top-right of client area
            overlay_x = window_info["client_x"] + window_info["client_width"] - self.width() - 10
            overlay_y = window_info["client_y"] + 40

            self.move(overlay_x, overlay_y)

            # Update grid overlay if it's visible
            if self.grid_visible and self.grid_overlay and playable_area:
                self.grid_overlay.update_playable_area(self.playable_coords)

            if not self.isVisible():
                self.show()

        except Exception as e:
            self.logger.error(f"Error updating position from shared data: {e}")

    def mousePressEvent(self, event):
        """Handle mouse press for dragging when target is lost."""
        if self.is_draggable and event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start_position = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging when target is lost."""
        if self.dragging and self.is_draggable:
            delta = event.globalPosition().toPoint() - self.drag_start_position
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.drag_start_position = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release to stop dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
        super().mouseReleaseEvent(event)

    def _center_on_screen(self):
        """Center the widget on the current screen."""
        try:
            # Get the screen geometry
            screen = QApplication.primaryScreen()
            if screen:
                screen_geometry = screen.geometry()
                # Center the widget
                x = (screen_geometry.width() - self.width()) // 2
                y = (screen_geometry.height() - self.height()) // 2
                self.move(x, y)
                self.logger.debug(f"Centered widget at ({x}, {y})")
            else:
                # Fallback to a reasonable position
                self.move(100, 100)
                self.logger.warning("Could not get screen geometry, using fallback position")
        except Exception as e:
            self.logger.error(f"Error centering widget: {e}")
            # Fallback to a reasonable position
            self.move(100, 100)

    def paintEvent(self, event: QPaintEvent):
        """Paint the overlay background and border with industrial dark mode styling."""
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
        """Handle FRAMES button click - show frames dialog."""
        self.logger.info("FRAMES button clicked")
        try:
            if not self.target_hwnd:
                self.logger.warning("No target window for frames functionality")
                return

            if not self.frames_manager:
                self.logger.error("Frames system not initialized")
                return

            # Show the frames dialog directly
            self.frames_manager.show_frames_dialog()

        except Exception as e:
            self.logger.error(f"Error showing frames dialog: {e}")

    def _capture_window_screenshot(self, output_dir: Path) -> Optional[Path]:
        """Capture screenshot of the target window."""
        if not self.target_hwnd or not WIN32_AVAILABLE:
            return None

        try:
            from time import strftime
            from PIL import ImageGrab

            # Get window rectangle
            window_rect = win32gui.GetWindowRect(self.target_hwnd)
            x, y, x2, y2 = window_rect

            # Create timestamp for filename
            timestamp = strftime("%Y%m%d_%H%M%S")
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
            tracker_path = Path(__file__).parent.parent / "tracker_app" / "tracker_app.py"
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
                    self.logger.warning("No playable area coordinates available for grid")
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
            except Exception:
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
