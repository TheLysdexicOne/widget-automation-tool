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
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect
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

        # Window position information (like AHK Window Spy)
        self.window_info_table = QTableWidget(0, 2)
        self.window_info_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.window_info_table.setMaximumHeight(200)
        header = self.window_info_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(QLabel("Window Information (AHK Style):"))
        layout.addWidget(self.window_info_table)

        # Overlay information
        self.overlay_info_table = QTableWidget(0, 2)
        self.overlay_info_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.overlay_info_table.setMaximumHeight(150)
        header = self.overlay_info_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(QLabel("Overlay Information:"))
        layout.addWidget(self.overlay_info_table)

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

            # Update window information
            self._update_window_info_table()

            # Update overlay information
            self._update_overlay_info_table()

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

    def _update_window_info_table(self):
        """Update the window information table with AHK Window Spy style data."""
        try:
            # Clear table
            self.window_info_table.setRowCount(0)

            # Get target window info from process monitor
            if hasattr(self.app, "process_monitor") and self.app.process_monitor:
                target_info = self.app.process_monitor.get_current_target_info()

                if target_info and "hwnd" in target_info:
                    # Get detailed window information using pygetwindow
                    import pygetwindow as gw

                    target_window = None

                    # Find the window object
                    for window in gw.getAllWindows():
                        if (
                            hasattr(window, "_hWnd")
                            and window._hWnd == target_info["hwnd"]
                        ):
                            target_window = window
                            break

                    if target_window:
                        # Get window rect information
                        try:
                            # Screen coordinates (full window including frame)
                            screen_data = [
                                ("Window Title", target_window.title),
                                ("--- SCREEN (Full Window) ---", ""),
                                ("Screen X", str(target_window.left)),
                                ("Screen Y", str(target_window.top)),
                                ("Screen Width", str(target_window.width)),
                                ("Screen Height", str(target_window.height)),
                                (
                                    "Screen Right",
                                    str(target_window.left + target_window.width),
                                ),
                                (
                                    "Screen Bottom",
                                    str(target_window.top + target_window.height),
                                ),
                            ]  # Try to get client area using Windows API
                            try:
                                import win32gui

                                # import win32api  # Not needed for this functionality

                                # Get client rectangle
                                client_rect = win32gui.GetClientRect(
                                    target_info["hwnd"]
                                )
                                client_left, client_top, client_right, client_bottom = (
                                    client_rect
                                )

                                # Convert client coordinates to screen coordinates
                                client_screen_pos = win32gui.ClientToScreen(
                                    target_info["hwnd"], (0, 0)
                                )
                                client_screen_x, client_screen_y = client_screen_pos

                                client_data = [
                                    ("--- CLIENT (Content Area) ---", ""),
                                    ("Client X", str(client_screen_x)),
                                    ("Client Y", str(client_screen_y)),
                                    ("Client Width", str(client_right - client_left)),
                                    ("Client Height", str(client_bottom - client_top)),
                                    (
                                        "Client Right",
                                        str(
                                            client_screen_x
                                            + (client_right - client_left)
                                        ),
                                    ),
                                    (
                                        "Client Bottom",
                                        str(
                                            client_screen_y
                                            + (client_bottom - client_top)
                                        ),
                                    ),
                                ]

                                # Calculate frame differences
                                frame_data = [
                                    ("--- FRAME DIFFERENCES ---", ""),
                                    (
                                        "Title Bar Height",
                                        str(client_screen_y - target_window.top),
                                    ),
                                    (
                                        "Left Border Width",
                                        str(client_screen_x - target_window.left),
                                    ),
                                    (
                                        "Right Border Width",
                                        str(
                                            (target_window.left + target_window.width)
                                            - (
                                                client_screen_x
                                                + (client_right - client_left)
                                            )
                                        ),
                                    ),
                                    (
                                        "Bottom Border Height",
                                        str(
                                            (target_window.top + target_window.height)
                                            - (
                                                client_screen_y
                                                + (client_bottom - client_top)
                                            )
                                        ),
                                    ),
                                ]

                                data = screen_data + client_data + frame_data

                            except (ImportError, Exception) as e:
                                # Fallback if win32gui is not available or fails
                                data = screen_data + [
                                    ("--- CLIENT INFO ---", ""),
                                    ("Client Info", f"win32gui error: {e}"),
                                    (
                                        "Note",
                                        "Install pywin32 for detailed client area info",
                                    ),
                                ]

                        except Exception as e:
                            data = [("Error", f"Failed to get window info: {e}")]

                    else:
                        data = [("Window Status", "Window object not found")]

                else:
                    data = [("Target Status", "No target window attached")]
            else:
                data = [("Monitor Status", "Process monitor not available")]

            # Populate table
            for i, (prop, value) in enumerate(data):
                self.window_info_table.insertRow(i)
                self.window_info_table.setItem(i, 0, QTableWidgetItem(prop))
                self.window_info_table.setItem(i, 1, QTableWidgetItem(str(value)))

        except Exception as e:
            self.logger.error(f"Error updating window info table: {e}")

    def _update_overlay_info_table(self):
        """Update the overlay information table."""
        try:  # Clear table
            self.overlay_info_table.setRowCount(0)

            # Get overlay info
            if hasattr(self.app, "overlay_window") and self.app.overlay_window:
                overlay = self.app.overlay_window

                # Check if overlay has missing import
                try:
                    import logging

                    logger = logging.getLogger(__name__)
                except ImportError:
                    pass

                # Get overlay geometry
                geometry = overlay.geometry()

                data = [
                    ("Overlay Visible", "Yes" if overlay.isVisible() else "No"),
                    ("--- OVERLAY POSITION ---", ""),
                    ("Overlay X", str(geometry.x())),
                    ("Overlay Y", str(geometry.y())),
                    ("Overlay Width", str(geometry.width())),
                    ("Overlay Height", str(geometry.height())),
                    ("Overlay Right", str(geometry.x() + geometry.width())),
                    ("Overlay Bottom", str(geometry.y() + geometry.height())),
                    ("--- OVERLAY STATE ---", ""),
                    ("Is Expanded", "Yes" if overlay.is_expanded else "No"),
                    ("Is Pinned", "Yes" if overlay.is_pinned else "No"),
                    ("Current Size", f"{geometry.width()}x{geometry.height()}"),
                    (
                        "Original Size",
                        f"{overlay.original_size[0]}x{overlay.original_size[1]}",
                    ),
                    (
                        "Expanded Size",
                        f"{overlay.expanded_size[0]}x{overlay.expanded_size[1]}",
                    ),
                    ("--- OVERLAY CONFIG ---", ""),
                    ("Circle Diameter", str(overlay.circle_diameter)),
                    ("Box Size", str(overlay.box_size)),
                    ("Offset X", str(overlay.offset_x)),
                    ("Offset Y", str(overlay.offset_y)),
                    ("Current Color", str(overlay.current_color.name())),
                ]

                # Add target window relationship if available
                if overlay.target_window:
                    target_geometry = QRect(
                        overlay.target_window.left,
                        overlay.target_window.top,
                        overlay.target_window.width,
                        overlay.target_window.height,
                    )

                    data.extend(
                        [
                            ("--- TARGET RELATIONSHIP ---", ""),
                            ("Target Window", overlay.target_window.title),
                            ("Target X", str(target_geometry.x())),
                            ("Target Y", str(target_geometry.y())),
                            ("Target Width", str(target_geometry.width())),
                            ("Target Height", str(target_geometry.height())),
                            ("--- POSITIONING CALC ---", ""),
                            ("Relative X", str(geometry.x() - target_geometry.x())),
                            ("Relative Y", str(geometry.y() - target_geometry.y())),
                            (
                                "Distance from Right",
                                str(target_geometry.right() - geometry.right()),
                            ),
                            (
                                "Distance from Bottom",
                                str(target_geometry.bottom() - geometry.bottom()),
                            ),
                        ]
                    )

            else:
                data = [("Overlay Status", "Overlay window not available")]

            # Populate table
            for i, (prop, value) in enumerate(data):
                self.overlay_info_table.insertRow(i)
                self.overlay_info_table.setItem(i, 0, QTableWidgetItem(prop))
                self.overlay_info_table.setItem(i, 1, QTableWidgetItem(str(value)))

        except Exception as e:
            self.logger.error(f"Error updating overlay info table: {e}")

    def _update_state_info(self):
        """Update the application state information."""
        try:
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

                for component_name in components:
                    if hasattr(self.app, component_name):
                        component = getattr(self.app, component_name)
                        if component:
                            if component_name == "system_tray":
                                status = (
                                    "Active"
                                    if hasattr(component, "tray_icon")
                                    and component.tray_icon
                                    else "Inactive"
                                )
                            elif component_name == "process_monitor":
                                status = (
                                    "Monitoring"
                                    if component.is_monitoring
                                    else "Stopped"
                                )
                            elif component_name == "overlay_window":
                                status = (
                                    "Visible" if component.isVisible() else "Hidden"
                                )
                            elif component_name == "debug_console":
                                status = "Active"
                            else:
                                status = "Unknown"

                            state_text += f"{component_name.replace('_', ' ').title()}: {status}\n"
                        else:
                            state_text += f"{component_name.replace('_', ' ').title()}: Not Initialized\n"
                    else:
                        state_text += (
                            f"{component_name.replace('_', ' ').title()}: Missing\n"
                        )

                self.state_info.setPlainText(state_text)
            else:
                self.state_info.setPlainText("Application state not available")

        except Exception as e:
            self.logger.error(f"Error updating state info: {e}")
            self.state_info.setPlainText(f"Error getting state info: {e}")

    def _refresh_debug_info(self):
        """Refresh the debug information in the debug tab."""
        try:
            # Clear the component tree
            self.component_tree.clear()

            # Create root items for each component
            components = {
                "Application": self.app,
                "System Tray": getattr(self.app, "system_tray", None),
                "Process Monitor": getattr(self.app, "process_monitor", None),
                "Overlay Window": getattr(self.app, "overlay_window", None),
                "Debug Console": self,
            }

            for component_name, component in components.items():
                item = QTreeWidgetItem(self.component_tree)
                item.setText(0, component_name)

                if component is None:
                    item.setText(1, "Not Available")
                    item.setText(2, "Component not initialized")
                else:
                    item.setText(1, "Available")

                    # Add specific details for each component
                    if component_name == "Application":
                        if hasattr(component, "get_state"):
                            state = component.get_state()
                            item.setText(2, f"State: {state.value.title()}")
                        else:
                            item.setText(2, "State management not available")

                    elif component_name == "System Tray":
                        if hasattr(component, "tray_icon") and component.tray_icon:
                            item.setText(1, "Active")
                            item.setText(2, "System tray icon visible")
                        else:
                            item.setText(1, "Inactive")
                            item.setText(2, "System tray icon not created")

                    elif component_name == "Process Monitor":
                        if hasattr(component, "is_monitoring"):
                            if component.is_monitoring:
                                item.setText(1, "Monitoring")
                                target_info = component.get_current_target_info()
                                if target_info:
                                    item.setText(
                                        2, f"Target found: PID {target_info['pid']}"
                                    )
                                else:
                                    item.setText(2, "Monitoring but target not found")
                            else:
                                item.setText(1, "Stopped")
                                item.setText(2, "Not monitoring")
                        else:
                            item.setText(2, "Monitor interface not available")

                    elif component_name == "Overlay Window":
                        if hasattr(component, "isVisible"):
                            if component.isVisible():
                                item.setText(1, "Visible")
                                geometry = component.geometry()
                                item.setText(
                                    2,
                                    f"Position: {geometry.x()},{geometry.y()} Size: {geometry.width()}x{geometry.height()}",
                                )
                            else:
                                item.setText(1, "Hidden")
                                item.setText(2, "Window created but not visible")
                        else:
                            item.setText(2, "Window interface not available")

                    elif component_name == "Debug Console":
                        item.setText(1, "Active")
                        item.setText(
                            2,
                            f"Tabs: {self.tab_widget.count()}, Logs: {len(self.log_messages)}",
                        )

            # Expand all items
            self.component_tree.expandAll()

            self.statusBar().showMessage("Debug information refreshed", 2000)

        except Exception as e:
            self.logger.error(f"Error refreshing debug info: {e}")
            self.statusBar().showMessage(f"Error refreshing debug info: {e}", 5000)

    def _run_debug_tests(self):
        """Run debug tests to validate component functionality."""
        try:
            self.logger.info("Starting debug tests...")

            test_results = []

            # Test 1: Application state
            try:
                if hasattr(self.app, "get_state"):
                    state = self.app.get_state()
                    test_results.append(
                        ("Application State", "PASS", f"Current state: {state.value}")
                    )
                else:
                    test_results.append(
                        ("Application State", "FAIL", "No get_state method")
                    )
            except Exception as e:
                test_results.append(("Application State", "ERROR", str(e)))

            # Test 2: System Tray
            try:
                if hasattr(self.app, "system_tray") and self.app.system_tray:
                    if (
                        hasattr(self.app.system_tray, "tray_icon")
                        and self.app.system_tray.tray_icon
                    ):
                        test_results.append(("System Tray", "PASS", "Tray icon active"))
                    else:
                        test_results.append(
                            ("System Tray", "FAIL", "Tray icon not found")
                        )
                else:
                    test_results.append(
                        ("System Tray", "FAIL", "System tray not initialized")
                    )
            except Exception as e:
                test_results.append(("System Tray", "ERROR", str(e)))

            # Test 3: Process Monitor
            try:
                if hasattr(self.app, "process_monitor") and self.app.process_monitor:
                    if self.app.process_monitor.is_monitoring:
                        target_info = self.app.process_monitor.get_current_target_info()
                        if target_info:
                            test_results.append(
                                (
                                    "Process Monitor",
                                    "PASS",
                                    f"Target found: PID {target_info['pid']}",
                                )
                            )
                        else:
                            test_results.append(
                                (
                                    "Process Monitor",
                                    "WARNING",
                                    "Monitoring but no target found",
                                )
                            )
                    else:
                        test_results.append(
                            ("Process Monitor", "WARNING", "Not currently monitoring")
                        )
                else:
                    test_results.append(
                        ("Process Monitor", "FAIL", "Process monitor not initialized")
                    )
            except Exception as e:
                test_results.append(("Process Monitor", "ERROR", str(e)))

            # Test 4: Overlay Window
            try:
                if hasattr(self.app, "overlay_window") and self.app.overlay_window:
                    if self.app.overlay_window.isVisible():
                        test_results.append(
                            ("Overlay Window", "PASS", "Window visible")
                        )
                    else:
                        test_results.append(
                            ("Overlay Window", "WARNING", "Window hidden")
                        )
                else:
                    test_results.append(
                        ("Overlay Window", "FAIL", "Overlay window not initialized")
                    )
            except Exception as e:
                test_results.append(("Overlay Window", "ERROR", str(e)))

            # Test 5: Debug Console (self-test)
            try:
                tab_count = self.tab_widget.count()
                log_count = len(self.log_messages)
                test_results.append(
                    ("Debug Console", "PASS", f"Tabs: {tab_count}, Logs: {log_count}")
                )
            except Exception as e:
                test_results.append(("Debug Console", "ERROR", str(e)))

            # Log test results
            for test_name, result, details in test_results:
                if result == "PASS":
                    self.logger.info(f"TEST {test_name}: {result} - {details}")
                elif result == "WARNING":
                    self.logger.warning(f"TEST {test_name}: {result} - {details}")
                elif result == "FAIL":
                    self.logger.error(f"TEST {test_name}: {result} - {details}")
                elif result == "ERROR":
                    self.logger.error(f"TEST {test_name}: {result} - {details}")

            # Summary
            pass_count = sum(1 for _, result, _ in test_results if result == "PASS")
            total_count = len(test_results)

            self.logger.info(
                f"Debug tests completed: {pass_count}/{total_count} passed"
            )
            self.statusBar().showMessage(
                f"Debug tests completed: {pass_count}/{total_count} passed", 5000
            )

        except Exception as e:
            self.logger.error(f"Error running debug tests: {e}")
            self.statusBar().showMessage(f"Error running debug tests: {e}", 5000)

    def closeEvent(self, event: QCloseEvent):
        """Handle close event - hide instead of closing."""
        event.ignore()
        self.hide()

    def showEvent(self, event):
        """Handle show event - refresh debug info when shown."""
        super().showEvent(event)
        # Refresh debug info when console is shown
        QTimer.singleShot(100, self._refresh_debug_info)
