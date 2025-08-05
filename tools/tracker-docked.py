#!/usr/bin/env python3
"""
Widget Automation Tool - Standalone Tracker Application

Single-file tracker window with coordinate monitoring and process tracking.
All required utilities are included below. No external imports except PyQt6 and standard library.
"""

import argparse
import ctypes
import logging
import os
import pyautogui
import pyperclip
import signal
import subprocess
import sys
from typing import Callable, Dict, Optional

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QFont

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


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

                    # Refine frame borders using PyAutoGUI for better accuracy
                    refined_frame = _refine_frame_borders_pyautogui(frame_area)
                    refinement_applied = False
                    if refined_frame and refined_frame != frame_area:
                        frame_area = refined_frame
                        refinement_applied = True

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
                        "refinement_applied": refinement_applied,
                    }
        except Exception:
            continue
    return None


def _refine_frame_borders_pyautogui(frame_area: Dict) -> Optional[Dict]:
    """
    Refine frame borders using PyAutoGUI pixel checking.
    Adjusts left and right borders by ±1 or ±2 pixels to achieve exactly 2054 pixel width.
    """
    if not frame_area:
        return None

    x = frame_area.get("x", 0)
    y = frame_area.get("y", 0)
    width = frame_area.get("width", 0)
    height = frame_area.get("height", 0)

    # Only refine if width is close to target (within ±10 pixels)
    target_width = 2054
    if abs(width - target_width) > 10:
        return None

    try:
        # Use middle Y coordinate for validation (with buffer for overlay)
        validation_y = y + height // 2

        # Check if we need adjustment
        width_diff = target_width - width

        if width_diff == 0:
            return frame_area  # Already perfect

        # For the specific case where width=2053 and we need 2054,
        # PIL analysis shows the correct answer is to expand right (keep x, increase width)
        if width == 2053 and target_width == 2054:
            return {"x": x, "y": y, "width": target_width, "height": height}

        # Try adjustments: ±1 or ±2 pixels on left/right borders
        adjustments = []

        if abs(width_diff) <= 4:  # Can be fixed with ±2 pixel adjustments
            if width_diff > 0:  # Need to increase width
                # Try expanding right first (preserves X position), then left, then both
                adjustments = [
                    (0, width_diff),  # Expand right only (preserves X)
                    (-width_diff, 0),  # Expand left only
                    (-width_diff // 2, width_diff // 2 + width_diff % 2),  # Expand both
                ]
            else:  # Need to decrease width
                width_diff = abs(width_diff)
                # Try contracting right first (preserves X position), then left, then both
                adjustments = [
                    (0, -width_diff),  # Contract right only (preserves X)
                    (width_diff, 0),  # Contract left only
                    (width_diff // 2, -(width_diff // 2 + width_diff % 2)),  # Contract both
                ]

        # Test each adjustment
        for i, (left_adj, right_adj) in enumerate(adjustments):
            new_x = x + left_adj
            new_width = width - left_adj + right_adj

            if new_width == target_width:
                # Validate borders using pixel checking
                left_x = new_x - 1
                right_x = new_x + new_width

                # Check if we can safely sample these pixels (multi-monitor aware)
                if left_x >= -3840 and right_x < 7680:  # Wide multi-monitor bounds
                    try:
                        # Sample pixels to validate border
                        left_pixel = pyautogui.pixel(left_x, validation_y)
                        right_pixel = pyautogui.pixel(right_x, validation_y)

                        # Basic validation: borders should be different from typical game content
                        # (This is a simple heuristic - could be improved)
                        if left_pixel != right_pixel:  # Different colors suggest border area
                            return {"x": new_x, "y": y, "width": new_width, "height": height}
                    except Exception:
                        continue  # Try next adjustment

        # If no adjustment worked, return original
        return frame_area

    except Exception:
        # If any error occurs, return original frame area
        return frame_area


# --- Coordinate System Manager ---
class CoordinateSystem:
    """Simple coordinate system for frame area management."""

    def __init__(self):
        self.frame_area = None

    def update_frame_area(self, frame_area: Dict):
        """Update frame area."""
        self.frame_area = frame_area

    def is_inside_frame(self, screen_x: int, screen_y: int) -> bool:
        """Check if screen coordinates are inside the frame area."""
        if not self.frame_area:
            return False

        px = self.frame_area.get("x", 0)
        py = self.frame_area.get("y", 0)
        pw = self.frame_area.get("width", 0)
        ph = self.frame_area.get("height", 0)

        return px <= screen_x <= px + pw and py <= screen_y <= py + ph


# --- Utility: Mouse Tracker ---
class MouseTracker(QObject):
    position_changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._window_xy_cb: Optional[Callable[[], Dict]] = None
        self._frame_xy_cb: Optional[Callable[[], Dict]] = None
        self._timer: Optional[QTimer] = None
        self.coord_system = CoordinateSystem()  # Coordinate system
        self.last_position_info = {}  # Store last position info

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
        self.last_position_info = pos_info  # Store for clipboard access
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

        # Frame info
        if self._frame_xy_cb:
            frame = self._frame_xy_cb()
            if frame:
                # Update coordinate system with current frame
                self.coord_system.update_frame_area(frame)

                # Only calculate percentages if mouse is inside frame area
                if self.coord_system.is_inside_frame(screen_x, screen_y):
                    info["inside_frame"] = True

                    # Calculate actual pixel coordinates within frame area
                    px = frame.get("x", 0)
                    py = frame.get("y", 0)
                    pw = frame.get("width", 0)
                    ph = frame.get("height", 0)

                    rel_x = screen_x - px
                    rel_y = screen_y - py
                    info["frame_x"] = rel_x
                    info["frame_y"] = rel_y

                    info["x_percent"] = 100 * rel_x / max(1, pw)
                    info["y_percent"] = 100 * rel_y / max(1, ph)
                else:
                    info["inside_frame"] = False

        return info


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
        self.frozen = False  # Add freeze state

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
        self.setMinimumSize(300, 100)
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

        # Position in center of screen
        screen = QApplication.primaryScreen()
        if screen is not None:
            rect = screen.availableGeometry() if hasattr(screen, "availableGeometry") else screen.geometry()
            self.move((rect.width() - self.width()) // 2, (rect.height() - self.height()) // 2)
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
        hotkey_label = QLabel("Ctrl+F to freeze coordinates")
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

        # Coordinates table
        self.coords_table = QTableWidget(3, 2)
        self.coords_table.setHorizontalHeaderLabels(["Top-Left", "Dimensions"])
        self.coords_table.setVerticalHeaderLabels(["Screen", "Window", "Frame"])

        # Set table properties
        self.coords_table.setFixedHeight(120)
        self.coords_table.setAlternatingRowColors(True)
        # Fix type issues with header resize modes
        h_header = self.coords_table.horizontalHeader()
        if h_header:
            h_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        v_header = self.coords_table.verticalHeader()
        if v_header:
            v_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.coords_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)  # Disable selection

        # Style the coordinates table
        self.coords_table.setStyleSheet(
            """
            QTableWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                gridline-color: #555;
                font-family: 'Courier New', monospace;
                font-size: 9pt;
            }
            QTableWidget::item {
                padding: 4px;
                border: none;
            }
            QHeaderView::section {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555;
                padding: 4px;
                font-weight: bold;
            }
        """
        )

        # Initialize coordinates table with default values
        self._init_coords_table()

        # Control buttons
        button_layout = QHBoxLayout()

        self.restart_button = QPushButton("RESTART")
        self.restart_button.clicked.connect(self._restart_application)
        self.restart_button.setStyleSheet(
            """
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2196f3;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """
        )

        self.close_button = QPushButton("CLOSE")
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

        button_layout.addStretch()
        button_layout.addWidget(self.restart_button)
        button_layout.addWidget(self.close_button)

        # Mouse tracking table
        self.mouse_table = QTableWidget(4, 2)
        self.mouse_table.setHorizontalHeaderLabels(["Actuals", "Percents"])
        self.mouse_table.setVerticalHeaderLabels(["Screen", "Window", "Frame", "Color"])

        # Set table properties
        self.mouse_table.setFixedHeight(140)
        self.mouse_table.setAlternatingRowColors(True)
        # Fix type issues with header resize modes
        h_header = self.mouse_table.horizontalHeader()
        if h_header:
            h_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        v_header = self.mouse_table.verticalHeader()
        if v_header:
            v_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.mouse_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )  # Enable single cell selection for copying
        self.mouse_table.cellClicked.connect(self.on_cell_clicked)  # Connect click handler

        # Style the table
        self.mouse_table.setStyleSheet(
            """
            QTableWidget {
                background-color: #1e1e1e;
                color: #00ff88;
                border: 1px solid #555;
                border-radius: 4px;
                gridline-color: #555;
                font-family: 'Courier New', monospace;
                font-size: 9pt;
            }
            QTableWidget::item {
                padding: 4px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #1e1e1e;
                color: #ff0000;
            }
            QHeaderView::section {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555;
                padding: 4px;
                font-weight: bold;
            }
        """
        )

        # Initialize table with default values
        self._init_mouse_table()

        # Add all widgets to layout
        layout.addWidget(self.title_label)
        layout.addWidget(hotkey_label)
        layout.addLayout(status_layout)
        layout.addWidget(self.coords_table)
        layout.addWidget(self.mouse_table)
        layout.addLayout(button_layout)

        # Standard context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        # Add close action
        close_action = QAction("Close", self)
        close_action.triggered.connect(self.close)
        self.addAction(close_action)

    def _init_coords_table(self):
        """Initialize the coordinates table with default values."""
        # Screen row
        self.coords_table.setItem(0, 0, QTableWidgetItem("N/A"))
        self.coords_table.setItem(0, 1, QTableWidgetItem("N/A"))

        # Window row
        self.coords_table.setItem(1, 0, QTableWidgetItem("N/A"))
        self.coords_table.setItem(1, 1, QTableWidgetItem("N/A"))

        # Frame row
        self.coords_table.setItem(2, 0, QTableWidgetItem("N/A"))
        self.coords_table.setItem(2, 1, QTableWidgetItem("N/A"))

    def _init_mouse_table(self):
        """Initialize the mouse tracking table with default values."""
        # Screen row
        self.mouse_table.setItem(0, 0, QTableWidgetItem("0, 0"))
        self.mouse_table.setItem(0, 1, QTableWidgetItem("N/A"))

        # Window row
        self.mouse_table.setItem(1, 0, QTableWidgetItem("Outside"))
        self.mouse_table.setItem(1, 1, QTableWidgetItem("N/A"))

        # Frame row
        self.mouse_table.setItem(2, 0, QTableWidgetItem("Outside"))
        self.mouse_table.setItem(2, 1, QTableWidgetItem("N/A"))

        # Color row
        self.mouse_table.setItem(3, 0, QTableWidgetItem("#000000"))
        self.mouse_table.setItem(3, 1, QTableWidgetItem("0, 0, 0"))

    def on_cell_clicked(self, row: int, column: int) -> None:
        """Handle cell clicks to copy values to clipboard."""
        item = self.mouse_table.item(row, column)
        if item is None:
            return

        text = item.text()
        if text == "N/A" or text == "Outside":
            return

        copied_text = ""
        # For percentage values, extract and format with 6 decimal precision
        if column == 1 and "%" in text:  # Percents column
            # Extract percentages from text like "25.50%, 75.20%"
            percentages = []
            parts = text.replace("%", "").split(", ")
            for part in parts:
                try:
                    value = float(part)
                    percentages.append(f"{value / 100:.6f}")  # Convert to decimal with 6 precision
                except ValueError:
                    continue
            if percentages:
                copied_text = ", ".join(percentages)
                pyperclip.copy(copied_text)
        else:
            # Copy actual values as-is
            copied_text = text
            pyperclip.copy(text)

        # Show visual feedback that something was copied
        if copied_text:
            self.logger.info(f"Copied to clipboard: {copied_text}")
            self._show_copy_feedback(copied_text)

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
                "refinement_applied": target_info.get("refinement_applied", False),
            }

            self._update_status(True, found_info)
        else:
            # Target not found
            self._update_status(False, {})

    def _update_status(self, found: bool, target_info: dict):
        """Update status display."""
        if found:
            # Update status with process name and PID
            pid = target_info.get("pid", "unknown")
            self.status_label.setText(f"{self.target_process} (PID: {pid})")
            self.status_circle.setStyleSheet(
                """
                QLabel {
                    background-color: #4CAF50;
                    border-radius: 10px;
                    border: 2px solid #66BB6A;
                }
            """
            )

            # Always update coordinates when found
            if "rect" in target_info and "client_rect" in target_info:
                rect = target_info["rect"]

                # Update Screen row - using primary screen info
                screen = QApplication.primaryScreen()
                if screen:
                    screen_rect = screen.geometry()
                    self.coords_table.setItem(0, 0, QTableWidgetItem(f"{screen_rect.x()}, {screen_rect.y()}"))
                    self.coords_table.setItem(0, 1, QTableWidgetItem(f"{screen_rect.width()}x{screen_rect.height()}"))
                else:
                    self.coords_table.setItem(0, 0, QTableWidgetItem("0, 0"))
                    self.coords_table.setItem(0, 1, QTableWidgetItem("N/A"))

                # Update Window row
                window_width = rect[2] - rect[0]
                window_height = rect[3] - rect[1]
                self.coords_table.setItem(1, 0, QTableWidgetItem(f"{rect[0]}, {rect[1]}"))
                self.coords_table.setItem(1, 1, QTableWidgetItem(f"{window_width}x{window_height}"))

                # Update Frame row
                if "frame_area" in target_info and target_info["frame_area"]:
                    frame = target_info["frame_area"]
                    self.coords_table.setItem(2, 0, QTableWidgetItem(f"{frame['x']}, {frame['y']}"))
                    self.coords_table.setItem(2, 1, QTableWidgetItem(f"{frame['width']}x{frame['height']}"))

                    # Always update tracker coordinates
                    self.window_xy = target_info["window_info"]
                    self.frame_xy = frame
                else:
                    self.coords_table.setItem(2, 0, QTableWidgetItem("N/A"))
                    self.coords_table.setItem(2, 1, QTableWidgetItem("N/A"))

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
            # Reset coordinates table to N/A
            for row in range(3):
                self.coords_table.setItem(row, 0, QTableWidgetItem("N/A"))
                self.coords_table.setItem(row, 1, QTableWidgetItem("N/A"))
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
        # Skip updates if frozen
        if self.frozen:
            return

        try:
            screen_x = position_info.get("screen_x", 0)
            screen_y = position_info.get("screen_y", 0)

            # Get color at current mouse position
            try:
                color = pyautogui.pixel(screen_x, screen_y)
                hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                rgb_color = f"{color[0]}, {color[1]}, {color[2]}"
            except Exception:
                hex_color = "#000000"
                rgb_color = "0, 0, 0"

            # Update Screen row
            self.mouse_table.setItem(0, 0, QTableWidgetItem(f"{screen_x}, {screen_y}"))
            self.mouse_table.setItem(0, 1, QTableWidgetItem("N/A"))

            # Update Window row
            if position_info.get("inside_window", False):
                window_x_percent = position_info.get("window_x_percent", 0)
                window_y_percent = position_info.get("window_y_percent", 0)
                self.mouse_table.setItem(1, 0, QTableWidgetItem(f"{screen_x}, {screen_y}"))
                self.mouse_table.setItem(1, 1, QTableWidgetItem(f"{window_x_percent:.2f}%, {window_y_percent:.2f}%"))
            else:
                self.mouse_table.setItem(1, 0, QTableWidgetItem("Outside"))
                self.mouse_table.setItem(1, 1, QTableWidgetItem("N/A"))

            # Update Frame row
            if position_info.get("inside_window", False):
                # Inside window - check if also inside frame
                if position_info.get("inside_frame", False):
                    frame_x = position_info.get("frame_x", 0)
                    frame_y = position_info.get("frame_y", 0)
                    x_percent = position_info.get("x_percent", 0)
                    y_percent = position_info.get("y_percent", 0)
                    self.mouse_table.setItem(2, 0, QTableWidgetItem(f"{frame_x}, {frame_y}"))
                    self.mouse_table.setItem(2, 1, QTableWidgetItem(f"{x_percent:.2f}%, {y_percent:.2f}%"))
                else:
                    # Inside window but outside frame - show clamped coordinates with frame percentages
                    if self.frame_xy:
                        # Calculate frame-relative coordinates even when outside frame bounds
                        frame_x_raw = screen_x - self.frame_xy.get("x", 0)
                        frame_y_raw = screen_y - self.frame_xy.get("y", 0)
                        frame_width = self.frame_xy.get("width", 1)
                        frame_height = self.frame_xy.get("height", 1)

                        # Clamp coordinates to frame bounds
                        frame_x = max(0, min(frame_x_raw, frame_width))
                        frame_y = max(0, min(frame_y_raw, frame_height))

                        # Clamp percentages to 0-100%
                        x_percent = max(0.0, min(100.0, 100 * frame_x_raw / max(1, frame_width)))
                        y_percent = max(0.0, min(100.0, 100 * frame_y_raw / max(1, frame_height)))

                        self.mouse_table.setItem(2, 0, QTableWidgetItem(f"{frame_x}, {frame_y}"))
                        self.mouse_table.setItem(2, 1, QTableWidgetItem(f"{x_percent:.2f}%, {y_percent:.2f}%"))
                    else:
                        self.mouse_table.setItem(2, 0, QTableWidgetItem("N/A"))
                        self.mouse_table.setItem(2, 1, QTableWidgetItem("N/A"))
            else:
                # Outside window - show "Outside" for frame
                self.mouse_table.setItem(2, 0, QTableWidgetItem("Outside"))
                self.mouse_table.setItem(2, 1, QTableWidgetItem("N/A"))

            # Update Color row
            self.mouse_table.setItem(3, 0, QTableWidgetItem(hex_color))
            self.mouse_table.setItem(3, 1, QTableWidgetItem(rgb_color))

        except Exception as e:
            self.logger.error(f"Error updating mouse display: {e}")
            # Reset table to error state
            for row in range(4):  # Updated to 4 rows
                self.mouse_table.setItem(row, 0, QTableWidgetItem("Error"))
                self.mouse_table.setItem(row, 1, QTableWidgetItem("Error"))

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_F and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Toggle freeze state (Ctrl+F)
            self.frozen = not self.frozen
            freeze_status = "FROZEN" if self.frozen else "TRACKING"

            # Update freeze status display
            freeze_item = QTableWidgetItem(freeze_status)
            if self.frozen:
                freeze_item.setBackground(Qt.GlobalColor.darkRed)
            else:
                freeze_item.setBackground(Qt.GlobalColor.darkGreen)

            # This will be shown in the Color row for now since we removed the separate freeze row
            # We'll update the status through visual styling instead

            self.logger.info(f"Coordinate tracking {'frozen' if self.frozen else 'resumed'}")

            # Visual feedback in title
            original_title = self.windowTitle()
            self.setWindowTitle(f"Widget Tracker - {freeze_status}")
            QTimer.singleShot(1500, lambda: self.setWindowTitle(original_title))
        else:
            super().keyPressEvent(event)

    def _show_copy_feedback(self, copied_text: str):
        """Show visual feedback that text was copied to clipboard."""
        # Flash the title label green with copied text
        original_title = self.windowTitle()
        original_text = self.title_label.text()

        # Update title and label to show what was copied
        self.setWindowTitle(f"Widget Tracker - Copied: {copied_text}")
        self.title_label.setText(f"Copied: {copied_text}")

        # Call the existing green flash method
        self._show_title_copied_feedback()

        # Restore original text and title after 2 seconds
        QTimer.singleShot(2000, lambda: self.setWindowTitle(original_title))
        QTimer.singleShot(2000, lambda: self.title_label.setText(original_text))

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
        # Fade back to normal after 2 seconds to match the text duration
        QTimer.singleShot(2000, self._reset_title_label_style)

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

    def _restart_application(self):
        """Restart the tracker application."""
        try:
            self.logger.info("Restarting tracker application...")

            # Get the current executable path
            if getattr(sys, "frozen", False):
                # Running as compiled exe
                executable = sys.executable
                args = [executable] + sys.argv[1:]  # Include command line arguments
            else:
                # Running as Python script
                executable = sys.executable
                args = [executable, __file__] + sys.argv[1:]  # Include script file and arguments

            # Close current application
            self.close()

            # Start new instance
            subprocess.Popen(args, cwd=os.getcwd())

            # Exit current process
            QApplication.quit()

        except Exception as e:
            self.logger.error(f"Failed to restart application: {e}")

    def closeEvent(self, event):
        """Clean up when closing the tracker."""
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
