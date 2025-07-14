"""
Debug Console

Main debug console window with tabs for various debugging functions.
"""

import logging
import sys
from datetime import datetime
from typing import List

from PyQt6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QComboBox,
    QLabel,
    QScrollArea,
    QTreeWidget,
    QTreeWidgetItem,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QCloseEvent


class LogHandler(logging.Handler):
    """Custom log handler that emits signals for GUI updates."""

    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def emit(self, record):
        """Emit log record through signal."""
        try:
            msg = self.format(record)
            self.signal.emit(record.levelno, msg, record)
        except Exception:
            pass


class DebugConsole(QMainWindow):
    """Main debug console window."""

    # Signals
    log_message_received = pyqtSignal(int, str, object)  # level, message, record

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.logger = logging.getLogger(__name__)

        # Console state
        self.log_messages = []
        self.max_log_lines = 1000
        self.current_log_level = logging.INFO

        # Setup UI
        self._setup_ui()
        self._setup_logging()

        # Timer for periodic updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_monitoring_tab)
        self.update_timer.start(2000)  # Update every 2 seconds

    def _setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("Widget Automation Tool - Debug Console")
        self.setGeometry(100, 100, 800, 600)

        # Central widget with tabs
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Create tabs
        self._create_console_tab()
        self._create_settings_tab()
        self._create_monitoring_tab()
        self._create_debug_tab()

        # Status bar
        self.statusBar().showMessage("Debug Console Ready")

    def _create_console_tab(self):
        """Create the console tab."""
        console_widget = QWidget()
        layout = QVBoxLayout(console_widget)

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
        self.close_btn.clicked.connect(self.hide)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

        self.tab_widget.addTab(console_widget, "Console")

    def _create_settings_tab(self):
        """Create the settings tab."""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)

        # Settings will be populated here
        settings_text = QTextEdit()
        settings_text.setPlainText("Settings configuration will be implemented here...")
        settings_text.setReadOnly(True)
        layout.addWidget(settings_text)

        self.tab_widget.addTab(settings_widget, "Settings")

    def _create_monitoring_tab(self):
        """Create the monitoring tab."""
        monitoring_widget = QWidget()
        layout = QVBoxLayout(monitoring_widget)

        # Process information
        self.process_table = QTableWidget(0, 3)
        self.process_table.setHorizontalHeaderLabels(["Property", "Value", "Status"])
        header = self.process_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(QLabel("Process Monitoring:"))
        layout.addWidget(self.process_table)

        # Application state
        self.state_info = QTextEdit()
        self.state_info.setMaximumHeight(100)
        self.state_info.setReadOnly(True)
        layout.addWidget(QLabel("Application State:"))
        layout.addWidget(self.state_info)

        self.tab_widget.addTab(monitoring_widget, "Monitoring")

    def _create_debug_tab(self):
        """Create the debug tab."""
        debug_widget = QWidget()
        layout = QVBoxLayout(debug_widget)

        # Component status
        self.component_tree = QTreeWidget()
        self.component_tree.setHeaderLabels(["Component", "Status", "Details"])
        layout.addWidget(QLabel("Component Status:"))
        layout.addWidget(self.component_tree)

        # Debug actions
        debug_actions_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_debug_info)
        debug_actions_layout.addWidget(refresh_btn)

        test_btn = QPushButton("Run Tests")
        test_btn.clicked.connect(self._run_debug_tests)
        debug_actions_layout.addWidget(test_btn)

        debug_actions_layout.addStretch()
        layout.addLayout(debug_actions_layout)

        self.tab_widget.addTab(debug_widget, "Debug")

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
            from PyQt6.QtWidgets import QApplication

            # Get all visible log text
            log_text = self.log_display.toPlainText()

            # Copy to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(log_text)

            self.statusBar().showMessage("Logs copied to clipboard", 2000)

        except Exception as e:
            self.logger.error(f"Failed to copy logs: {e}")

    def _clear_logs(self):
        """Clear the log display."""
        self.log_display.clear()
        self.log_messages.clear()
        self.statusBar().showMessage("Logs cleared", 2000)

    def _update_monitoring_tab(self):
        """Update the monitoring tab with current information."""
        try:
            # Update process table
            self._update_process_table()

            # Update state info
            self._update_state_info()

        except Exception as e:
            self.logger.error(f"Error updating monitoring tab: {e}")

    def _update_process_table(self):
        """Update the process monitoring table."""
        if hasattr(self.app, "process_monitor") and self.app.process_monitor:
            target_info = self.app.process_monitor.get_current_target_info()

            # Clear and rebuild table
            self.process_table.setRowCount(0)

            data = [
                (
                    "Target Process",
                    self.app.process_monitor.target_process_name,
                    "Found" if target_info else "Not Found",
                ),
                (
                    "Monitoring",
                    "Enabled" if self.app.process_monitor.is_monitoring else "Disabled",
                    "Active" if self.app.process_monitor.is_monitoring else "Inactive",
                ),
            ]

            if target_info:
                data.extend(
                    [
                        ("Process ID", str(target_info["pid"]), "Connected"),
                        ("Window Handle", str(target_info["hwnd"]), "Attached"),
                    ]
                )

            for i, (prop, value, status) in enumerate(data):
                self.process_table.insertRow(i)
                self.process_table.setItem(i, 0, QTableWidgetItem(prop))
                self.process_table.setItem(i, 1, QTableWidgetItem(value))
                self.process_table.setItem(i, 2, QTableWidgetItem(status))

    def _update_state_info(self):
        """Update the application state information."""
        if hasattr(self.app, "get_state"):
            state = self.app.get_state()
            state_text = f"Current State: {state.value.title()}\n"
            state_text += f"Last Updated: {datetime.now().strftime('%H:%M:%S')}\n"

            # Add component status
            components = [
                "system_tray",
                "process_monitor",
                "overlay_window",
                "debug_console",
            ]
            for comp_name in components:
                comp = getattr(self.app, comp_name, None)
                status = "✓ Active" if comp else "✗ Inactive"
                state_text += f"{comp_name.replace('_', ' ').title()}: {status}\n"

            self.state_info.setPlainText(state_text)

    def _refresh_debug_info(self):
        """Refresh debug information."""
        self.component_tree.clear()

        try:
            # App component
            app_item = QTreeWidgetItem(
                ["Application", "Running", f"State: {self.app.get_state().value}"]
            )
            self.component_tree.addTopLevelItem(app_item)

            # System tray
            tray_status = (
                "Active"
                if self.app.system_tray and self.app.system_tray.tray_icon
                else "Inactive"
            )
            tray_item = QTreeWidgetItem(
                ["System Tray", tray_status, "Context menu available"]
            )
            app_item.addChild(tray_item)

            # Process monitor
            monitor_status = (
                "Monitoring"
                if self.app.process_monitor and self.app.process_monitor.is_monitoring
                else "Stopped"
            )
            monitor_item = QTreeWidgetItem(
                ["Process Monitor", monitor_status, "Target: WidgetInc.exe"]
            )
            app_item.addChild(monitor_item)

            # Overlay
            overlay_status = "Hidden"
            if self.app.overlay_window:
                overlay_status = (
                    "Visible" if self.app.overlay_window.isVisible() else "Hidden"
                )
            overlay_item = QTreeWidgetItem(
                ["Overlay", overlay_status, "Window overlay"]
            )
            app_item.addChild(overlay_item)

            # Debug console
            console_item = QTreeWidgetItem(
                ["Debug Console", "Active", f"Logs: {len(self.log_messages)}"]
            )
            app_item.addChild(console_item)

            # Expand all
            self.component_tree.expandAll()

        except Exception as e:
            error_item = QTreeWidgetItem(["Error", "Failed", str(e)])
            self.component_tree.addTopLevelItem(error_item)

    def _run_debug_tests(self):
        """Run debug tests."""
        self.logger.info("Running debug tests from console...")

        try:
            # Test state changes
            original_state = self.app.get_state()

            # Test each state
            from core.application import ApplicationState

            test_states = [
                ApplicationState.WAITING,
                ApplicationState.ACTIVE,
                ApplicationState.INACTIVE,
                ApplicationState.ERROR,
            ]

            for state in test_states:
                self.app.set_state(state)
                self.logger.info(f"Test: Set state to {state.value}")

            # Restore original state
            self.app.set_state(original_state)

            self.logger.info("Debug tests completed")

        except Exception as e:
            self.logger.error(f"Debug test failed: {e}")

    def closeEvent(self, event: QCloseEvent):
        """Handle close event - minimize to tray instead of closing."""
        event.ignore()
        self.hide()
        self.statusBar().showMessage("Console minimized to system tray", 2000)
