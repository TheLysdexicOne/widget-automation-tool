"""
Console tab for debug console - handles logging display and controls.
"""

import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QComboBox,
    QLabel,
    QApplication,
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor

from .base_tab import BaseTab
from ..components.log_handler import LogHandler


class ConsoleTab(BaseTab):
    """Console tab for displaying and managing log messages."""

    # Signals
    log_message_received = pyqtSignal(int, str, object)  # level, message, record

    def __init__(self, app, parent=None):
        # Console state
        self.log_messages = []
        self.max_log_lines = 1000
        self.current_log_level = logging.INFO
        self.log_handler = None

        super().__init__(app, parent)

        # Setup logging after UI is ready
        self._setup_logging()

    def _setup_ui(self):
        """Setup the console tab UI."""
        layout = QVBoxLayout(self)

        # Log level selector
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Log Level:"))

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        self.log_level_combo.currentTextChanged.connect(self._on_log_level_changed)
        level_layout.addWidget(self.log_level_combo)

        level_layout.addStretch()
        layout.addLayout(level_layout)

        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_display)

        # Bottom buttons
        button_layout = QHBoxLayout()

        self.copy_logs_btn = QPushButton("Copy Logs")
        self.copy_logs_btn.clicked.connect(self._copy_logs)
        button_layout.addWidget(self.copy_logs_btn)

        self.clear_logs_btn = QPushButton("Clear Logs")
        self.clear_logs_btn.clicked.connect(self._clear_logs)
        button_layout.addWidget(self.clear_logs_btn)

        button_layout.addStretch()

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self._close_console)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def _setup_logging(self):
        """Setup logging to capture log messages in the console."""
        # Create custom handler
        self.log_handler = LogHandler(self.log_message_received)
        self.log_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        # Add handler to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)

        # Connect signal
        self.log_message_received.connect(self._on_log_message)

    def _on_log_level_changed(self, level_text):
        """Handle log level change."""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
        }

        self.current_log_level = level_map.get(level_text, logging.INFO)
        if self.log_handler:
            self.log_handler.setLevel(self.current_log_level)

        # Refresh display
        self._refresh_log_display()

    def _on_log_message(self, level, message, record):
        """Handle new log message."""
        # Store message
        self.log_messages.append(
            {
                "level": level,
                "message": message,
                "record": record,
                "timestamp": datetime.now(),
            }
        )

        # Limit number of stored messages
        if len(self.log_messages) > self.max_log_lines:
            self.log_messages = self.log_messages[-self.max_log_lines :]

        # Update display if level is appropriate
        if level >= self.current_log_level:
            self._append_log_message(message)

    def _append_log_message(self, message):
        """Append a message to the log display."""
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(message + "\n")

        # Auto-scroll to bottom
        scrollbar = self.log_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _refresh_log_display(self):
        """Refresh the entire log display."""
        self.log_display.clear()

        for log_entry in self.log_messages:
            if log_entry["level"] >= self.current_log_level:
                self._append_log_message(log_entry["message"])

    def _copy_logs(self):
        """Copy logs to clipboard."""
        try:
            # Get all visible log text
            log_text = self.log_display.toPlainText()

            # Copy to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(log_text)

            # Notify parent if possible
            if hasattr(self.parent(), "statusBar"):
                self.parent().statusBar().showMessage("Logs copied to clipboard", 2000)
        except Exception as e:
            self.logger.error(f"Failed to copy logs: {e}")

    def _clear_logs(self):
        """Clear the log display."""
        self.log_display.clear()
        self.log_messages.clear()

        # Notify parent if possible
        if hasattr(self.parent(), "statusBar"):
            self.parent().statusBar().showMessage("Logs cleared", 2000)

    def _close_console(self):
        """Close the console window (minimize to system tray)."""
        # Debounce rapid close button clicks
        import time

        current_time = time.time()
        if hasattr(self, "_last_close_click"):
            if (current_time - self._last_close_click) < 0.5:  # 500ms debounce
                self.logger.debug("Close button click ignored (debouncing)")
                return
        self._last_close_click = current_time

        self.logger.info("Console close button clicked - minimizing to tray")

        # Use the debug console's minimize to tray method
        if self.debug_console and hasattr(self.debug_console, "minimize_to_tray"):
            self.debug_console.minimize_to_tray()
        elif self.debug_console and hasattr(self.debug_console, "hide"):
            self.debug_console.hide()
        else:
            self.logger.error(
                "No debug console reference available for close operation"
            )

    def cleanup(self):
        """Cleanup resources when tab is destroyed."""
        if self.log_handler:
            root_logger = logging.getLogger()
            root_logger.removeHandler(self.log_handler)
