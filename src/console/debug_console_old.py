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
    QFrame,
    QGridLayout,
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

    def switch_to_tab(self, tab_name):
        """Switch to the specified tab."""
        tab_map = {
            "console": 0,
            "settings": 1,
            "monitoring": 2,
            "debug": 3,
        }

        if tab_name.lower() in tab_map:
            self.tab_widget.setCurrentIndex(tab_map[tab_name.lower()])
            self.logger.info(f"Switched to {tab_name} tab")
        else:
            self.logger.warning(f"Unknown tab: {tab_name}")

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
        """Create the monitoring tab with card-based layout."""
        monitoring_widget = QWidget()
        main_layout = QVBoxLayout(monitoring_widget)

        # Create a scroll area for the cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Container for cards
        cards_container = QWidget()
        cards_layout = QGridLayout(cards_container)
        cards_layout.setSpacing(15)  # Space between cards

        # Row 1: Process Monitoring Card
        process_card = self._create_card(
            "Process Monitoring", "Monitor running processes"
        )
        self.process_monitoring_table = QTableWidget(0, 3)
        self.process_monitoring_table.setHorizontalHeaderLabels(
            ["Process", "Status", "Details"]
        )
        self.process_monitoring_table.setMaximumHeight(120)
        header = self.process_monitoring_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        process_card.layout().addWidget(self.process_monitoring_table)
        cards_layout.addWidget(process_card, 0, 0, 1, 2)  # Span 2 columns

        # Row 2: Coordinates Monitoring Card
        coordinates_card = self._create_card(
            "Coordinates Monitoring", "Track window positions"
        )
        self.coordinates_table = QTableWidget(0, 4)
        self.coordinates_table.setHorizontalHeaderLabels(
            ["Component", "X", "Y", "Size"]
        )
        self.coordinates_table.setMaximumHeight(120)
        header = self.coordinates_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        coordinates_card.layout().addWidget(self.coordinates_table)
        cards_layout.addWidget(coordinates_card, 1, 0)

        # Row 2: Mouse Tracking Card
        mouse_card = self._create_card("Mouse Tracking", "Real-time mouse position")
        self.mouse_tracking_table = QTableWidget(0, 2)
        self.mouse_tracking_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.mouse_tracking_table.setMaximumHeight(120)
        header = self.mouse_tracking_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        mouse_card.layout().addWidget(self.mouse_tracking_table)
        cards_layout.addWidget(mouse_card, 1, 1)

        # Set up scroll area
        scroll_area.setWidget(cards_container)
        main_layout.addWidget(scroll_area)

        self.tab_widget.addTab(monitoring_widget, "Monitoring")

    def _create_card(self, title, subtitle):
        """Create a card widget with title and subtitle."""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setStyleSheet(
            """
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                padding: 10px;
            }
        """
        )

        layout = QVBoxLayout(card)
        layout.setSpacing(5)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet("font-size: 12px; color: #666;")
        layout.addWidget(subtitle_label)

        return card

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
            # Update process monitoring card
            self._update_process_monitoring_card()

            # Update coordinates monitoring card
            self._update_coordinates_card()

            # Update mouse tracking card
            self._update_mouse_tracking_card()

        except Exception as e:
            self.logger.error(f"Error updating monitoring tab: {e}")

    def _update_process_monitoring_card(self):
        """Update the process monitoring card."""
        try:
            self.process_monitoring_table.setRowCount(0)

            # Add processes to monitor
            processes_to_monitor = [
                ("WidgetInc.exe", self._get_widgetinc_status()),
                ("Widget Core", self._get_widget_core_status()),
                ("Widget Console", self._get_widget_console_status()),
                ("Widget Overlay", self._get_widget_overlay_status()),
            ]

            for i, (process_name, status_info) in enumerate(processes_to_monitor):
                self.process_monitoring_table.insertRow(i)
                self.process_monitoring_table.setItem(
                    i, 0, QTableWidgetItem(process_name)
                )
                self.process_monitoring_table.setItem(
                    i, 1, QTableWidgetItem(status_info["status"])
                )
                self.process_monitoring_table.setItem(
                    i, 2, QTableWidgetItem(status_info["details"])
                )

        except Exception as e:
            self.logger.error(f"Error updating process monitoring card: {e}")

    def _update_coordinates_card(self):
        """Update the coordinates monitoring card."""
        try:
            self.coordinates_table.setRowCount(0)

            # Add coordinates to monitor
            coordinates_to_monitor = [
                ("WidgetInc.exe", self._get_widgetinc_coordinates()),
                ("Overlay", self._get_overlay_coordinates()),
            ]

            for i, (component, coord_info) in enumerate(coordinates_to_monitor):
                self.coordinates_table.insertRow(i)
                self.coordinates_table.setItem(i, 0, QTableWidgetItem(component))
                self.coordinates_table.setItem(
                    i, 1, QTableWidgetItem(str(coord_info["x"]))
                )
                self.coordinates_table.setItem(
                    i, 2, QTableWidgetItem(str(coord_info["y"]))
                )
                self.coordinates_table.setItem(
                    i, 3, QTableWidgetItem(coord_info["size"])
                )

        except Exception as e:
            self.logger.error(f"Error updating coordinates card: {e}")

    def _update_mouse_tracking_card(self):
        """Update the mouse tracking card."""
        try:
            self.mouse_tracking_table.setRowCount(0)

            # Get mouse tracking data
            mouse_data = self._get_mouse_tracking_data()

            tracking_metrics = [
                ("Actual", mouse_data["actual"]),
                ("Percentage", mouse_data["percentage"]),
                ("Playable %", mouse_data["playable_percentage"]),
            ]

            for i, (metric, value) in enumerate(tracking_metrics):
                self.mouse_tracking_table.insertRow(i)
                self.mouse_tracking_table.setItem(i, 0, QTableWidgetItem(metric))
                self.mouse_tracking_table.setItem(i, 1, QTableWidgetItem(value))

        except Exception as e:
            self.logger.error(f"Error updating mouse tracking card: {e}")

    def _get_widgetinc_status(self):
        """Get WidgetInc.exe status information."""
        try:
            if hasattr(self.app, "process_monitor") and self.app.process_monitor:
                target_info = self.app.process_monitor.get_current_target_info()
                if target_info:
                    return {
                        "status": "Running",
                        "details": f"PID: {target_info['pid']}, HWND: {target_info['hwnd']}",
                    }
                else:
                    return {"status": "Not Found", "details": "Process not detected"}
            else:
                return {
                    "status": "Monitor Disabled",
                    "details": "Process monitor not available",
                }
        except Exception as e:
            return {"status": "Error", "details": f"Error: {str(e)}"}

    def _get_widget_core_status(self):
        """Get Widget Core status information."""
        try:
            if hasattr(self.app, "get_state"):
                state = self.app.get_state()
                return {
                    "status": "Active",
                    "details": f"State: {state.value if hasattr(state, 'value') else str(state)}",
                }
            else:
                return {"status": "Unknown", "details": "Core state not available"}
        except Exception as e:
            return {"status": "Error", "details": f"Error: {str(e)}"}

    def _get_widget_console_status(self):
        """Get Widget Console status information."""
        try:
            return {
                "status": "Active",
                "details": f"Tabs: {self.tab_widget.count()}, Logs: {len(self.log_messages)}",
            }
        except Exception as e:
            return {"status": "Error", "details": f"Error: {str(e)}"}

    def _get_widget_overlay_status(self):
        """Get Widget Overlay status information."""
        try:
            if hasattr(self.app, "overlay_window") and self.app.overlay_window:
                overlay = self.app.overlay_window
                visibility = "Visible" if overlay.isVisible() else "Hidden"
                pin_status = "Pinned" if overlay.is_pinned else "Unpinned"
                return {
                    "status": visibility,
                    "details": f"{pin_status}, Expanded: {overlay.is_expanded}",
                }
            else:
                return {"status": "Not Available", "details": "Overlay not initialized"}
        except Exception as e:
            return {"status": "Error", "details": f"Error: {str(e)}"}

    def _get_widgetinc_coordinates(self):
        """Get WidgetInc.exe coordinates information."""
        try:
            if hasattr(self.app, "process_monitor") and self.app.process_monitor:
                target_info = self.app.process_monitor.get_current_target_info()
                if target_info and "hwnd" in target_info:
                    import win32gui

                    # Get client rectangle and convert to screen coordinates
                    client_rect = win32gui.GetClientRect(target_info["hwnd"])
                    client_screen_pos = win32gui.ClientToScreen(
                        target_info["hwnd"], (0, 0)
                    )
                    client_width = client_rect[2]
                    client_height = client_rect[3]

                    return {
                        "x": client_screen_pos[0],
                        "y": client_screen_pos[1],
                        "size": f"{client_width}×{client_height}",
                    }
                else:
                    return {"x": "N/A", "y": "N/A", "size": "N/A"}
            else:
                return {"x": "N/A", "y": "N/A", "size": "N/A"}
        except Exception as e:
            return {"x": "Error", "y": "Error", "size": f"Error: {str(e)}"}

    def _get_overlay_coordinates(self):
        """Get Overlay coordinates information."""
        try:
            if hasattr(self.app, "overlay_window") and self.app.overlay_window:
                overlay = self.app.overlay_window
                if overlay.isVisible():
                    geometry = overlay.geometry()
                    return {
                        "x": geometry.x(),
                        "y": geometry.y(),
                        "size": f"{geometry.width()}×{geometry.height()}",
                    }
                else:
                    return {"x": "Hidden", "y": "Hidden", "size": "Hidden"}
            else:
                return {"x": "N/A", "y": "N/A", "size": "N/A"}
        except Exception as e:
            return {"x": "Error", "y": "Error", "size": f"Error: {str(e)}"}

    def _get_mouse_tracking_data(self):
        """Get mouse tracking data."""
        try:
            import win32api

            # Get mouse position
            mouse_pos = win32api.GetCursorPos()
            mouse_x, mouse_y = mouse_pos

            # Calculate percentages relative to window if available
            window_percent_x = "N/A"
            window_percent_y = "N/A"
            playable_percent_x = "N/A"
            playable_percent_y = "N/A"

            if hasattr(self.app, "process_monitor") and self.app.process_monitor:
                target_info = self.app.process_monitor.get_current_target_info()
                if target_info and "hwnd" in target_info:
                    try:
                        import win32gui

                        # Get client rectangle
                        client_rect = win32gui.GetClientRect(target_info["hwnd"])
                        client_screen_pos = win32gui.ClientToScreen(
                            target_info["hwnd"], (0, 0)
                        )
                        client_width = client_rect[2]
                        client_height = client_rect[3]

                        if client_width > 0 and client_height > 0:
                            rel_x = mouse_x - client_screen_pos[0]
                            rel_y = mouse_y - client_screen_pos[1]

                            if (
                                0 <= rel_x <= client_width
                                and 0 <= rel_y <= client_height
                            ):
                                window_percent_x = (
                                    f"{(rel_x / client_width * 100):.1f}%"
                                )
                                window_percent_y = (
                                    f"{(rel_y / client_height * 100):.1f}%"
                                )

                        # Calculate playable area percentage (3:2 ratio centered)
                        if client_width > 0 and client_height > 0:
                            # Calculate 3:2 ratio playable area
                            target_ratio = 3.0 / 2.0
                            current_ratio = client_width / client_height

                            if current_ratio > target_ratio:
                                # Window is wider than 3:2, playable area is height-limited
                                playable_height = client_height
                                playable_width = playable_height * target_ratio
                                playable_x = (client_width - playable_width) / 2
                                playable_y = 0
                            else:
                                # Window is taller than 3:2, playable area is width-limited
                                playable_width = client_width
                                playable_height = playable_width / target_ratio
                                playable_x = 0
                                playable_y = (client_height - playable_height) / 2

                            # Calculate relative position within playable area
                            rel_playable_x = mouse_x - client_screen_pos[0] - playable_x
                            rel_playable_y = mouse_y - client_screen_pos[1] - playable_y

                            if (
                                0 <= rel_playable_x <= playable_width
                                and 0 <= rel_playable_y <= playable_height
                            ):
                                playable_percent_x = (
                                    f"{(rel_playable_x / playable_width * 100):.1f}%"
                                )
                                playable_percent_y = (
                                    f"{(rel_playable_y / playable_height * 100):.1f}%"
                                )
                            else:
                                playable_percent_x = "Outside"
                                playable_percent_y = "Outside"
                    except Exception:
                        pass

            return {
                "actual": f"{mouse_x}, {mouse_y}",
                "percentage": f"{window_percent_x}, {window_percent_y}",
                "playable_percentage": f"{playable_percent_x}, {playable_percent_y}",
            }
        except Exception as e:
            return {
                "actual": "Error",
                "percentage": "Error",
                "playable_percentage": f"Error: {str(e)}",
            }

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
