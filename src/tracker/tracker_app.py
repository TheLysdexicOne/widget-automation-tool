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

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

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

try:
    import win32gui
    import win32process
    import psutil

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


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

        self._setup_window()
        self._setup_ui()
        self._start_monitoring()

        self.logger.info("Tracker widget initialized")

    def _setup_window(self):
        """Setup window properties."""
        self.setWindowTitle("Widget Automation Tracker")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(400, 300)

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

        # Add all widgets to layout
        layout.addWidget(title_label)
        layout.addLayout(status_layout)
        layout.addWidget(self.info_area)
        layout.addWidget(self.coords_label)
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
        """Check for target process."""
        found = False
        target_info = {}

        if WIN32_AVAILABLE:
            try:
                for proc in psutil.process_iter(["pid", "name"]):
                    if proc.info["name"] == self.target_process:
                        pid = proc.info["pid"]
                        hwnd = self._find_window_by_pid(pid)
                        if hwnd:
                            found = True
                            target_info = {
                                "pid": pid,
                                "hwnd": hwnd,
                                "title": win32gui.GetWindowText(hwnd),
                                "rect": win32gui.GetWindowRect(hwnd),
                                "client_rect": win32gui.GetClientRect(hwnd),
                            }
                            break
            except Exception as e:
                self.logger.error(f"Error checking target: {e}")

        self._update_status(found, target_info)

    def _find_window_by_pid(self, pid: int):
        """Find window handle by process ID."""

        def enum_windows_proc(hwnd, windows):
            try:
                _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                if window_pid == pid and win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if "WidgetInc" in title:
                        windows.append(hwnd)
            except:
                pass
            return True

        windows = []
        win32gui.EnumWindows(enum_windows_proc, windows)
        return windows[0] if windows else None

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
                info_text = f"Process: {self.target_process}\\n"
                info_text += f"PID: {target_info.get('pid', 'N/A')}\\n"
                info_text += f"HWND: {target_info.get('hwnd', 'N/A')}\\n"
                info_text += f"Title: {target_info.get('title', 'N/A')}"
                self.info_area.setPlainText(info_text)

                # Update coordinates
                if "rect" in target_info and "client_rect" in target_info:
                    rect = target_info["rect"]
                    client_rect = target_info["client_rect"]

                    coords_text = f"Window: {rect[0]}, {rect[1]}, {rect[2] - rect[0]}x{rect[3] - rect[1]}\\n"
                    coords_text += f"Client: {client_rect[2]}x{client_rect[3]}"
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

    def _refresh_target(self):
        """Manually refresh target search."""
        self.logger.info("Manual refresh requested")
        self._check_target()


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
