#!/usr/bin/env python3
"""
Widget Automation Tool - Standalone Tracker Application

Single-file tracker window with coordinate monitoring and process tracking.
All required utilities are included below. No external imports except PyQt6 and standard library.
"""

import argparse
import ctypes
import logging
import signal
import sys
from typing import Callable, Dict, Optional

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QFont

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtGui import QPainter, QPen


# --- Utility: Window Detection ---
def find_target_window(target_process: str) -> Optional[Dict]:
    """Find the target window and its geometry. Returns info dict or None."""
    try:
        import psutil
        import win32gui
        import win32process
    except ImportError:
        return None

    # Ultra-fast: enumerate windows, match by title, then get PID
    target_pids = []

    def enum_windows_callback(hwnd, _):
        try:
            title = win32gui.GetWindowText(hwnd)
            if "WidgetInc" in title and win32gui.IsWindowVisible(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid not in target_pids:
                    target_pids.append(pid)
        except Exception:
            pass
        return True

    win32gui.EnumWindows(enum_windows_callback, None)

    # Find first valid process
    for pid in target_pids:
        try:
            proc = psutil.Process(pid)
            if proc.is_running() and proc.name() == target_process:
                # Find window for this PID
                def enum_windows_proc(hwnd, windows):
                    try:
                        _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                        if window_pid == pid and win32gui.IsWindowVisible(hwnd):
                            title = win32gui.GetWindowText(hwnd)
                            if "WidgetInc" in title:
                                windows.append(hwnd)
                    except Exception:
                        pass
                    return True

                windows = []
                win32gui.EnumWindows(enum_windows_proc, windows)
                if windows:
                    hwnd = windows[0]
                    rect = win32gui.GetWindowRect(hwnd)
                    client_rect = win32gui.GetClientRect(hwnd)
                    client_left_top = win32gui.ClientToScreen(hwnd, (client_rect[0], client_rect[1]))
                    client_right_bottom = win32gui.ClientToScreen(hwnd, (client_rect[2], client_rect[3]))
                    client_x = client_left_top[0]
                    client_y = client_left_top[1]
                    client_w = client_right_bottom[0] - client_left_top[0]
                    client_h = client_right_bottom[1] - client_left_top[1]
                    title = win32gui.GetWindowText(hwnd)

                    # Calculate 3:2 aspect ratio frame area
                    target_ratio = 3.0 / 2.0
                    client_ratio = client_w / client_h if client_h else 1

                    if client_ratio > target_ratio:
                        # Client is wider than 3:2 - fit height, center width
                        frame_height = client_h
                        frame_width = int(frame_height * target_ratio)
                        px = client_x + (client_w - frame_width) // 2
                        py = client_y
                    else:
                        # Client is taller than 3:2 - fit width, center height
                        frame_width = client_w
                        frame_height = int(frame_width / target_ratio)
                        px = client_x
                        py = client_y + (client_h - frame_height) // 2

                    frame_area = {"x": px, "y": py, "width": frame_width, "height": frame_height}

                    return {
                        "pid": pid,
                        "window_info": {
                            "hwnd": hwnd,
                            "title": title,
                            "window_rect": rect,
                            "client_left": client_x,
                            "client_top": client_y,
                            "client_width": client_w,
                            "client_height": client_h,
                        },
                        "frame_area": frame_area,
                    }
        except Exception:
            continue
    return None


# --- Utility: Mouse Tracker ---
class MouseTracker(QObject):
    position_changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._window_xy_cb: Optional[Callable[[], Dict]] = None
        self._frame_xy_cb: Optional[Callable[[], Dict]] = None
        self._timer: Optional[QTimer] = None
        self.current_grid_xy = (0, 0)  # Store current grid coordinates

    def set_coordinate_callbacks(self, window_cb: Callable[[], Dict], frame_cb: Callable[[], Dict]):
        self._window_xy_cb = window_cb
        self._frame_xy_cb = frame_cb

    def start_tracking(self, interval_ms: int = 100):
        if self._timer is None:
            self._timer = QTimer()
            self._timer.timeout.connect(self._emit_position)
            self._timer.start(interval_ms)

    def _emit_position(self):
        pos_info = self._get_position_info()
        self.position_changed.emit(pos_info)

    def _get_position_info(self) -> Dict:
        # Get mouse position using ctypes
        try:

            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

            pt = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            screen_x, screen_y = pt.x, pt.y
        except Exception:
            screen_x, screen_y = 0, 0

        info = {"screen_x": screen_x, "screen_y": screen_y}

        # Window info
        if self._window_xy_cb:
            win_info = self._window_xy_cb()
            if win_info and "window_rect" in win_info:
                wx1, wy1, wx2, wy2 = win_info["window_rect"]
                if wx1 <= screen_x <= wx2 and wy1 <= screen_y <= wy2:
                    info["inside_window"] = True
                    info["window_x_percent"] = 100 * (screen_x - wx1) / max(1, wx2 - wx1)
                    info["window_y_percent"] = 100 * (screen_y - wy1) / max(1, wy2 - wy1)
                else:
                    info["inside_window"] = False

        # Frame info - calculate pixel size regardless of mouse position
        if self._frame_xy_cb:
            frame = self._frame_xy_cb()
            if frame:
                px, py, pw, ph = (
                    frame.get("x", 0),
                    frame.get("y", 0),
                    frame.get("width", 0),
                    frame.get("height", 0),
                )

                # Pixel art grid calculation (192x128 background pixels)
                grid_width = 192
                grid_height = 128

                # Calculate actual pixel size (pixels per background grid unit)
                pixel_size_x = pw / grid_width if grid_width else 0
                pixel_size_y = ph / grid_height if grid_height else 0
                pixel_size = min(pixel_size_x, pixel_size_y)  # Use smaller for square pixels

                # Always include pixel size when we have frame area
                info["pixel_size"] = pixel_size

                # Only calculate grid position and percentages if mouse is inside frame area
                if px <= screen_x <= px + pw and py <= screen_y <= py + ph:
                    info["inside_frame"] = True

                    # Calculate actual pixel coordinates within frame area
                    rel_x = screen_x - px
                    rel_y = screen_y - py
                    info["frame_x"] = rel_x
                    info["frame_y"] = rel_y

                    info["x_percent"] = 100 * rel_x / max(1, pw)
                    info["y_percent"] = 100 * rel_y / max(1, ph)

                    # Calculate grid position
                    grid_x = int(rel_x / pixel_size) if pixel_size > 0 else 0
                    grid_y = int(rel_y / pixel_size) if pixel_size > 0 else 0

                    # Clamp to grid bounds
                    grid_x = max(0, min(grid_width - 1, grid_x))
                    grid_y = max(0, min(grid_height - 1, grid_y))

                    # Store current grid coordinates
                    self.current_grid_xy = (grid_x, grid_y)

                    info["grid_position"] = {"x": grid_x, "y": grid_y}
                else:
                    info["inside_frame"] = False

        return info


# --- Grid Overlay Widget ---
class GridOverlay(QWidget):
    """Semi-transparent grid overlay for the frame area."""

    def __init__(self, frame_area: Dict):
        super().__init__()
        self.frame_area = frame_area
        self.grid_width = 192
        self.grid_height = 128
        self._setup_overlay()

    def _setup_overlay(self):
        """Setup the overlay window."""
        # Set window properties for overlay
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Position and size the overlay to match frame area
        px = self.frame_area.get("x", 0)
        py = self.frame_area.get("y", 0)
        pw = self.frame_area.get("width", 0)
        ph = self.frame_area.get("height", 0)

        self.setGeometry(px, py, pw, ph)

    def paintEvent(self, event):
        """Draw the grid overlay."""
        painter = QPainter(self)

        # Set up pen for grid lines (2px thick, semi-transparent white)
        pen = QPen(Qt.GlobalColor.white)
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.setOpacity(0.3)  # Semi-transparent

        # Calculate pixel size
        pw = self.frame_area.get("width", 0)
        ph = self.frame_area.get("height", 0)

        if pw > 0 and ph > 0:
            pixel_size_x = pw / self.grid_width
            pixel_size_y = ph / self.grid_height
            pixel_size = min(pixel_size_x, pixel_size_y)  # Square pixels

            # Draw vertical lines
            for i in range(self.grid_width + 1):
                x = i * pixel_size
                painter.drawLine(int(x), 0, int(x), ph)

            # Draw horizontal lines
            for i in range(self.grid_height + 1):
                y = i * pixel_size
                painter.drawLine(0, int(y), pw, int(y))


# --- Main Tracker Widget ---
class TrackerWidget(QWidget):
    """Simple tracker widget."""

    def __init__(self, target_process="WidgetInc.exe"):
        super().__init__()
        self.target_process = target_process
        self.logger = logging.getLogger(self.__class__.__name__)

        # State
        self.target_found = False
        self.target_hwnd = None
        self.coordinates = {}
        self.window_xy = {}
        self.frame_xy = {}
        self.grid_overlay = None  # Grid overlay widget

        # Mouse tracker
        self.mouse_tracker = MouseTracker()
        self.mouse_tracker.set_coordinate_callbacks(self._get_window_coords, self._get_frame_coords)
        self.mouse_tracker.position_changed.connect(self._on_mouse_position_changed)

        self._setup_window()
        self._setup_ui()
        self._start_monitoring()

        # Start mouse tracking
        self.mouse_tracker.start_tracking(100)  # Update every 100ms

        self.logger.info("Tracker widget initialized")

    def _setup_window(self):
        """Setup window properties."""
        self.setWindowTitle("Widget Automation Tracker")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setMinimumSize(400, 100)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Allow keyboard focus

        # Dark mode styling
        self.setStyleSheet(
            """
            QWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                background-color: transparent;
            }
        """
        )

        # Position in bottom-right corner
        screen = QApplication.primaryScreen()
        if screen is not None:
            rect = screen.availableGeometry() if hasattr(screen, "availableGeometry") else screen.geometry()
            self.move(rect.width() - self.width() - 50, rect.height() - self.height() - 50)
        else:
            self.move(50, 50)

    def _setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Title
        self.title_label = QLabel("Widget Tracker")  # <-- Make this an instance attribute
        self.title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            """
            QLabel {
                color: #ffffff;
                padding: 8px;
                background-color: #3d3d3d;
                border-radius: 4px;
                margin-bottom: 4px;
            }
        """
        )

        # Hotkey hint
        hotkey_label = QLabel("Ctrl+G to copy grid coordinates")
        hotkey_label.setFont(QFont("Arial", 8))
        hotkey_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hotkey_label.setStyleSheet(
            """
            QLabel {
                color: #888888;
                padding: 2px;
                background-color: transparent;
                font-style: italic;
            }
        """
        )

        # Status section
        status_layout = QHBoxLayout()

        self.status_label = QLabel("SEARCHING...")
        self.status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.status_label.setStyleSheet(
            """
            QLabel {
                color: #cccccc;
                padding: 4px;
                background-color: transparent;
            }
        """
        )

        # Status circle
        self.status_circle = QLabel()
        self.status_circle.setFixedSize(20, 20)
        self.status_circle.setStyleSheet(
            """
            QLabel {
                background-color: #FF8C00;
                border-radius: 10px;
                border: 2px solid #FFA500;
            }
        """
        )

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.status_circle)

        # Info area
        self.info_area = QTextEdit()
        self.info_area.setMaximumHeight(120)
        self.info_area.setFixedHeight(78)
        self.info_area.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px;
                font-family: 'Courier New', monospace;
                font-size: 9pt;
                selection-background-color: #0078d4;
            }
        """
        )
        self.info_area.setReadOnly(True)

        # Coordinates display
        self.coords_label = QLabel("No coordinates available")
        self.coords_label.setFont(QFont("Courier New", 9))
        self.coords_label.setMaximumHeight(65)
        self.coords_label.setStyleSheet(
            """
            QLabel {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                margin: 4px 0px;
                font-family: 'Courier New', monospace;
            }
        """
        )

        # Control buttons
        button_layout = QHBoxLayout()

        self.grid_button = QPushButton("Grid")
        self.grid_button.clicked.connect(self._show_grid)
        self.grid_button.setStyleSheet(
            """
            QPushButton {
                background-color: #0d7377;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #14a085;
            }
            QPushButton:pressed {
                background-color: #0a5d61;
            }
        """
        )

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        self.close_button.setStyleSheet(
            """
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f44336;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """
        )

        button_layout.addWidget(self.grid_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)

        # Mouse tracking display
        self.mouse_label = QLabel("Mouse: No data")
        self.mouse_label.setFont(QFont("Courier New", 9))
        self.mouse_label.setFixedHeight(100)
        self.mouse_label.setStyleSheet(
            """
            QLabel {
                background-color: #1e1e1e;
                color: #00ff88;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                margin: 4px 0px;
                font-family: 'Courier New', monospace;
            }
        """
        )

        # Add all widgets to layout
        layout.addWidget(self.title_label)
        layout.addWidget(hotkey_label)
        layout.addLayout(status_layout)
        layout.addWidget(self.info_area)
        layout.addWidget(self.coords_label)
        layout.addWidget(self.mouse_label)
        layout.addLayout(button_layout)

        # Standard context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        # Add grid action
        grid_action = QAction("Toggle Grid", self)
        grid_action.triggered.connect(self._show_grid)
        self.addAction(grid_action)

        # Add separator
        separator = QAction(self)
        separator.setSeparator(True)
        self.addAction(separator)

        # Add close action
        close_action = QAction("Close", self)
        close_action.triggered.connect(self.close)
        self.addAction(close_action)

    def _start_monitoring(self):
        """Start monitoring for target process."""
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._check_target)
        self.monitor_timer.start(2000)  # Check every 2 seconds

        # Initial check
        self._check_target()

    def _check_target(self):
        """Check for target process using shared utilities."""
        target_info = find_target_window(self.target_process)

        if target_info:
            # Target found - extract information
            pid = target_info["pid"]
            window_info = target_info["window_info"]
            frame_area = target_info["frame_area"]

            # Create info dict compatible with existing update logic
            found_info = {
                "pid": pid,
                "hwnd": window_info["hwnd"],
                "title": window_info["title"],
                "rect": window_info["window_rect"],
                "client_rect": (
                    0,
                    0,
                    window_info["client_width"],
                    window_info["client_height"],
                ),
                "window_info": window_info,
                "frame_area": frame_area,
            }

            self._update_status(True, found_info)
        else:
            # Target not found
            self._update_status(False, {})

    def _update_status(self, found: bool, target_info: dict):
        """Update status display."""
        if found:
            # Always update when target is found
            self.status_label.setText("TARGET FOUND")
            self.status_circle.setStyleSheet(
                """
                QLabel {
                    background-color: #4CAF50;
                    border-radius: 10px;
                    border: 2px solid #66BB6A;
                }
            """
            )

            # Update info area
            info_text = f"Process: {self.target_process}\n"
            info_text += f"PID: {target_info.get('pid', 'N/A')}\n"
            info_text += f"HWND: {target_info.get('hwnd', 'N/A')}\n"
            info_text += f"Title: {target_info.get('title', 'N/A')}"
            self.info_area.setPlainText(info_text)

            # Always update coordinates when found
            if "rect" in target_info and "client_rect" in target_info:
                rect = target_info["rect"]
                client_rect = target_info["client_rect"]

                coords_text = f"Window: {rect[0]}, {rect[1]}, {rect[2] - rect[0]}x{rect[3] - rect[1]}\n"
                coords_text += f"Client: {client_rect[2]}x{client_rect[3]}"

                if "frame_area" in target_info and target_info["frame_area"]:
                    frame = target_info["frame_area"]
                    coords_text += f"\nFrame: {frame['x']}, {frame['y']}, {frame['width']}x{frame['height']}"

                    # Always update tracker coordinates
                    self.window_xy = target_info["window_info"]
                    self.frame_xy = frame

                self.coords_label.setText(coords_text)

        elif self.target_found:
            # Only update UI when going from found to not found
            self.status_label.setText("SEARCHING...")
            self.status_circle.setStyleSheet(
                """
                QLabel {
                    background-color: #FFA500;
                    border-radius: 10px;
                    border: 2px solid #FF8C00;
                }
            """
            )
            self.info_area.setPlainText("No target process found")
            self.coords_label.setText("No coordinates available")
            self.window_xy = {}
            self.frame_xy = {}

        # Update status flag
        self.target_found = found

    def _get_window_coords(self) -> Dict:
        """Callback to provide window coordinates to mouse tracker."""
        return self.window_xy

    def _get_frame_coords(self) -> Dict:
        """Callback to provide frame coordinates to mouse tracker."""
        return self.frame_xy

    def _on_mouse_position_changed(self, position_info: Dict):
        """Handle mouse position updates from mouse tracker."""
        try:
            screen_x = position_info.get("screen_x", 0)
            screen_y = position_info.get("screen_y", 0)

            mouse_text = f"Screen: {screen_x}, {screen_y}\n"

            # Add window information if available
            if position_info.get("inside_window", False):
                window_x_percent = position_info.get("window_x_percent", 0)
                window_y_percent = position_info.get("window_y_percent", 0)
                mouse_text += f"Window: {window_x_percent:.4f}%, {window_y_percent:.4f}%\n"
            else:
                mouse_text += "Window: Outside\n"

            # Add frame area information if available
            if position_info.get("inside_frame", False):
                frame_x = position_info.get("frame_x", 0)
                frame_y = position_info.get("frame_y", 0)
                grid_pos = position_info.get("grid_position", {})
                pixel_size = position_info.get("pixel_size", 0)

                mouse_text += f"Frame: {frame_x}, {frame_y}\n"
                mouse_text += f"Grid: ({grid_pos.get('x', 0)}, {grid_pos.get('y', 0)})\n"
                mouse_text += f"Pixel: {pixel_size:.4f}px"
            else:
                pixel_size = position_info.get("pixel_size", 0)
                mouse_text += "Frame: Outside\n"
                mouse_text += "Grid: Outside\n"
                mouse_text += f"Pixel: {pixel_size:.4f}px"

            self.mouse_label.setText(mouse_text)

        except Exception as e:
            self.logger.error(f"Error updating mouse display: {e}")
            self.mouse_label.setText("Mouse: Error")

    def _show_grid(self):
        """Toggle grid overlay on the frame area."""
        if self.grid_overlay is not None:
            # Grid is currently shown - hide it
            self.grid_overlay.close()
            self.grid_overlay = None
            self.grid_button.setText("Grid")
            self.logger.info("Grid overlay hidden")
        else:
            # Grid is not shown - show it if we have frame area
            if self.frame_xy and self.target_found:
                self.grid_overlay = GridOverlay(self.frame_xy)
                self.grid_overlay.show()
                self.grid_button.setText("Hide Grid")
                self.logger.info("Grid overlay shown")
            else:
                self.logger.warning("Cannot show grid: no frame area available")

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_G and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Copy grid coordinates to clipboard (Ctrl+G)
            grid_x, grid_y = self.mouse_tracker.current_grid_xy
            grid_text = f"{grid_x}, {grid_y}"
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(grid_text)
                self.logger.info(f"Grid coordinates copied to clipboard: {grid_text}")
                # Also show a brief visual feedback in the window title
                original_title = self.windowTitle()
                self.setWindowTitle(f"Widget Tracker - Copied: {grid_text}")

                # Visual cue: turn title_label background green, then fade back
                self._show_title_copied_feedback()

                QTimer.singleShot(2000, lambda: self.setWindowTitle(original_title))
        else:
            super().keyPressEvent(event)

    def _show_title_copied_feedback(self):
        """Flash the title label green and fade back to normal."""
        # Set green background
        self.title_label.setStyleSheet(
            """
            QLabel {
                color: #ffffff;
                padding: 8px;
                background-color: #2ecc40;
                border-radius: 4px;
                margin-bottom: 4px;
            }
            """
        )
        # Fade back to normal after ~1 second
        QTimer.singleShot(1000, self._reset_title_label_style)

    def _reset_title_label_style(self):
        """Restore the title label's normal background."""
        self.title_label.setStyleSheet(
            """
            QLabel {
                color: #ffffff;
                padding: 8px;
                background-color: #3d3d3d;
                border-radius: 4px;
                margin-bottom: 4px;
            }
            """
        )

    def closeEvent(self, event):
        """Clean up when closing the tracker."""
        if self.grid_overlay is not None:
            self.grid_overlay.close()
            self.grid_overlay = None
        super().closeEvent(event)


# --- Logging and CLI ---
def setup_logging():
    """Setup basic logging for tracker."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Widget Automation Tracker")

    parser.add_argument(
        "--target",
        default="WidgetInc.exe",
        help="Target process name to track (default: WidgetInc.exe)",
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    logger = setup_logging()

    logger.info(f"Starting tracker for {args.target}")

    app = QApplication(sys.argv)

    tracker = TrackerWidget(args.target)
    tracker.show()

    # Signal handling
    def signal_handler(signum, frame):
        logger.info("Shutdown signal received")
        tracker.close()
        app.quit()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
