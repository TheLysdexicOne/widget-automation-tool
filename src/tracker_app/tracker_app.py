#!/usr/bin/env python3
"""
Widget Automation Tool - Tracker Application

Simple tracker window launched from the main overlay TRACKER button.
Provides basic tracking functionality and coordinate monitoring.
"""

import sys
import argparse
import logging
import signal
from pathlib import Path
from typing import Dict

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QScrollArea,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QColor, QBrush, QPen, QAction

# Import shared utilities
from utility.window_utils import find_target_window, is_window_valid
from utility.mouse_tracker import MouseTracker


class TrackerWidget(QWidget):
    """Simple tracker widget."""

    def __init__(self, target_process="WidgetInc.exe"):
        super().__init__()
        self.target_process = target_process
        self.logger = logging.getLogger(__name__)

        # State
        self.target_found = False
        self.target_hwnd = None
        self.coordinates = {}
        self.window_coords = {}
        self.playable_coords = {}

        # Mouse tracker
        self.mouse_tracker = MouseTracker()
        self.mouse_tracker.set_coordinate_callbacks(
            self._get_window_coords, self._get_playable_coords
        )
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
        self.setMinimumSize(400, 300)

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
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.width() - self.width() - 50, screen.height() - self.height() - 50
        )

    def _setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Title
        title_label = QLabel("Widget Tracker")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(
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

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._refresh_target)
        self.refresh_button.setStyleSheet(
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

        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)

        # Mouse tracking display
        self.mouse_label = QLabel("Mouse: No data")
        self.mouse_label.setFont(QFont("Courier New", 9))
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
        layout.addWidget(title_label)
        layout.addLayout(status_layout)
        layout.addWidget(self.info_area)
        layout.addWidget(self.coords_label)
        layout.addWidget(self.mouse_label)  # Add mouse tracking display
        layout.addLayout(button_layout)

        # Standard context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        # Add refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self._refresh_target)
        self.addAction(refresh_action)

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
            playable_area = target_info["playable_area"]

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
                "playable_area": playable_area,
            }

            self._update_status(True, found_info)
        else:
            # Target not found
            self._update_status(False, {})

    def _update_status(self, found: bool, target_info: dict):
        """Update status display."""
        if found != self.target_found:
            self.target_found = found

            if found:
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

                # Update coordinates - include playable area if available
                if "rect" in target_info and "client_rect" in target_info:
                    rect = target_info["rect"]
                    client_rect = target_info["client_rect"]

                    coords_text = f"Window: {rect[0]}, {rect[1]}, {rect[2] - rect[0]}x{rect[3] - rect[1]}\n"
                    coords_text += f"Client: {client_rect[2]}x{client_rect[3]}"

                    # Add playable area if available
                    if "playable_area" in target_info and target_info["playable_area"]:
                        playable = target_info["playable_area"]
                        coords_text += f"\nPlayable: {playable['x']}, {playable['y']}, {playable['width']}x{playable['height']}"

                        # Update tracker state for mouse tracker
                        self.window_coords = target_info["window_info"]
                        self.playable_coords = playable

                    self.coords_label.setText(coords_text)

            else:
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
                self.window_coords = {}
                self.playable_coords = {}

    def _refresh_target(self):
        """Manually refresh target search."""
        self.logger.info("Manual refresh requested")
        self._check_target()

    def _get_window_coords(self) -> Dict:
        """Callback to provide window coordinates to mouse tracker."""
        return self.window_coords

    def _get_playable_coords(self) -> Dict:
        """Callback to provide playable coordinates to mouse tracker."""
        return self.playable_coords

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
                mouse_text += (
                    f"Window: {window_x_percent:.1f}%, {window_y_percent:.1f}%\n"
                )
            else:
                mouse_text += "Window: Outside\n"

            # Add playable area information if available
            if position_info.get("inside_playable", False):
                x_percent = position_info.get("x_percent", 0)
                y_percent = position_info.get("y_percent", 0)
                grid_pos = position_info.get("grid_position", {})
                pixel_size = position_info.get("pixel_size", 0)

                mouse_text += f"Playable: {x_percent:.1f}%, {y_percent:.1f}%\n"
                mouse_text += (
                    f"Grid: ({grid_pos.get('x', 0)}, {grid_pos.get('y', 0)})\n"
                )
                mouse_text += f"Pixel: {pixel_size:.2f}px"
            else:
                mouse_text += "Playable: Outside"

            self.mouse_label.setText(mouse_text)

        except Exception as e:
            self.logger.error(f"Error updating mouse display: {e}")
            self.mouse_label.setText("Mouse: Error")


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
