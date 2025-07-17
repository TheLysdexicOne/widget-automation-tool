"""
Monitoring tab for debug console - displays real-time system information.
"""

from PyQt6.QtWidgets import (
    QVBoxLayout,
    QScrollArea,
    QWidget,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
)
from PyQt6.QtCore import Qt, QTimer

from .base_tab import BaseTab


class MonitoringTab(BaseTab):
    """Monitoring tab for real-time system information."""

    def _setup_ui(self):
        """Setup the monitoring tab UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)  # Space between sections
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Set dark background for the main container
        self.setStyleSheet("background-color: #1A1A1A;")

        # Process Monitoring Section
        process_title = QLabel("Process Monitoring")
        process_title.setStyleSheet(
            "font-weight: bold; font-size: 11px; color: #E0E0E0; margin-bottom: 2px; background-color: #2D2D2D; padding: 2px 4px;"
        )
        main_layout.addWidget(process_title)

        self.process_monitoring_table = QTableWidget(
            4, 3
        )  # Pre-set 4 rows for our processes
        self.process_monitoring_table.setHorizontalHeaderLabels(
            ["Process", "Status", "Details"]
        )
        self.process_monitoring_table.setMaximumHeight(150)
        self.process_monitoring_table.setAlternatingRowColors(True)
        header = self.process_monitoring_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(0, 120)  # Process name column
        header.resizeSection(1, 80)  # Status column

        self.process_monitoring_table.setStyleSheet(
            """
            QTableWidget {
                background-color: #2D2D2D;
                alternate-background-color: #363636;
                color: #E0E0E0;
                gridline-color: #505050;
                border: 1px solid #404040;
            }
            QTableWidget::item {
                border-bottom: 1px solid #505050;
                padding: 3px;
            }
            QHeaderView::section {
                background-color: #404040;
                color: #E0E0E0;
                border: 1px solid #505050;
                padding: 3px;
                font-weight: bold;
            }
            """
        )
        main_layout.addWidget(self.process_monitoring_table)

        # Coordinates Monitoring Section
        coordinates_title = QLabel("Coordinates Monitoring")
        coordinates_title.setStyleSheet(
            "font-weight: bold; font-size: 11px; color: #E0E0E0; margin-bottom: 2px; background-color: #2D2D2D; padding: 2px 4px;"
        )
        main_layout.addWidget(coordinates_title)

        self.coordinates_table = QTableWidget(2, 4)  # Pre-set 2 rows for components
        self.coordinates_table.setHorizontalHeaderLabels(
            ["Component", "X", "Y", "Size"]
        )
        self.coordinates_table.setMaximumHeight(100)
        self.coordinates_table.setAlternatingRowColors(True)
        header = self.coordinates_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(0, 100)  # Component name
        header.resizeSection(1, 60)  # X coordinate
        header.resizeSection(2, 60)  # Y coordinate

        self.coordinates_table.setStyleSheet(
            """
            QTableWidget {
                background-color: #2D2D2D;
                alternate-background-color: #363636;
                color: #E0E0E0;
                gridline-color: #505050;
                border: 1px solid #404040;
            }
            QTableWidget::item {
                border-bottom: 1px solid #505050;
                padding: 3px;
            }
            QHeaderView::section {
                background-color: #404040;
                color: #E0E0E0;
                border: 1px solid #505050;
                padding: 3px;
                font-weight: bold;
            }
            """
        )
        main_layout.addWidget(self.coordinates_table)

        # Mouse Tracking Section
        mouse_title = QLabel("Mouse Tracking")
        mouse_title.setStyleSheet(
            "font-weight: bold; font-size: 11px; color: #E0E0E0; margin-bottom: 2px; background-color: #2D2D2D; padding: 2px 4px;"
        )
        main_layout.addWidget(mouse_title)

        self.mouse_tracking_table = QTableWidget(3, 2)  # Pre-set 3 rows for metrics
        self.mouse_tracking_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.mouse_tracking_table.setMaximumHeight(100)
        self.mouse_tracking_table.setAlternatingRowColors(True)
        header = self.mouse_tracking_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(0, 100)  # Metric name

        self.mouse_tracking_table.setStyleSheet(
            """
            QTableWidget {
                background-color: #2D2D2D;
                alternate-background-color: #363636;
                color: #E0E0E0;
                gridline-color: #505050;
                border: 1px solid #404040;
            }
            QTableWidget::item {
                border-bottom: 1px solid #505050;
                padding: 3px;
            }
            QHeaderView::section {
                background-color: #404040;
                color: #E0E0E0;
                border: 1px solid #505050;
                padding: 3px;
                font-weight: bold;
            }
            """
        )
        main_layout.addWidget(self.mouse_tracking_table)

        # Add stretch to push everything to the top
        main_layout.addStretch()

    def _setup_updates(self):
        """Setup periodic updates for monitoring data."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_monitoring_data)
        self.update_timer.start(2000)  # Update every 2 seconds

    def _update_monitoring_data(self):
        """Update all monitoring cards with current information."""
        try:
            # Update process monitoring card
            self._update_process_monitoring_card()

            # Update coordinates monitoring card
            self._update_coordinates_card()

            # Update mouse tracking card
            self._update_mouse_tracking_card()

        except Exception as e:
            self.logger.error(f"Error updating monitoring data: {e}")

    def _update_process_monitoring_card(self):
        """Update the process monitoring card."""
        try:
            # Define the processes we're monitoring (fixed rows)
            processes_to_monitor = [
                ("WidgetInc.exe", self._get_widgetinc_status()),
                ("Widget Core", self._get_widget_core_status()),
                ("Widget Console", self._get_widget_console_status()),
                ("Widget Overlay", self._get_widget_overlay_status()),
            ]

            # Update each row with current data
            for i, (process_name, status_info) in enumerate(processes_to_monitor):
                # Set process name (only needs to be set once, but safe to repeat)
                if not self.process_monitoring_table.item(i, 0):
                    self.process_monitoring_table.setItem(
                        i, 0, QTableWidgetItem(process_name)
                    )

                # Update status
                status_item = self.process_monitoring_table.item(i, 1)
                if not status_item:
                    status_item = QTableWidgetItem()
                    self.process_monitoring_table.setItem(i, 1, status_item)
                status_item.setText(status_info["status"])

                # Update details
                details_item = self.process_monitoring_table.item(i, 2)
                if not details_item:
                    details_item = QTableWidgetItem()
                    self.process_monitoring_table.setItem(i, 2, details_item)
                details_item.setText(status_info["details"])

        except Exception as e:
            self.logger.error(f"Error updating process monitoring card: {e}")

    def _update_coordinates_card(self):
        """Update the coordinates monitoring card."""
        try:
            # Define the components we're monitoring (fixed rows)
            coordinates_to_monitor = [
                ("WidgetInc.exe", self._get_widgetinc_coordinates()),
                ("Overlay", self._get_overlay_coordinates()),
            ]

            # Update each row with current data
            for i, (component_name, coord_info) in enumerate(coordinates_to_monitor):
                # Set component name (only needs to be set once, but safe to repeat)
                if not self.coordinates_table.item(i, 0):
                    self.coordinates_table.setItem(
                        i, 0, QTableWidgetItem(component_name)
                    )

                # Update X coordinate
                x_item = self.coordinates_table.item(i, 1)
                if not x_item:
                    x_item = QTableWidgetItem()
                    self.coordinates_table.setItem(i, 1, x_item)
                x_item.setText(str(coord_info["x"]))

                # Update Y coordinate
                y_item = self.coordinates_table.item(i, 2)
                if not y_item:
                    y_item = QTableWidgetItem()
                    self.coordinates_table.setItem(i, 2, y_item)
                y_item.setText(str(coord_info["y"]))

                # Update size
                size_item = self.coordinates_table.item(i, 3)
                if not size_item:
                    size_item = QTableWidgetItem()
                    self.coordinates_table.setItem(i, 3, size_item)
                size_item.setText(f"{coord_info['width']}x{coord_info['height']}")

        except Exception as e:
            self.logger.error(f"Error updating coordinates card: {e}")

    def _update_mouse_tracking_card(self):
        """Update the mouse tracking card."""
        try:
            # Define the metrics we're monitoring (fixed rows)
            metrics_to_monitor = [
                ("Current Position", self._get_current_mouse_position()),
                ("Click Count", self._get_click_count()),
                ("Last Action", self._get_last_action()),
            ]

            # Update each row with current data
            for i, (metric_name, metric_value) in enumerate(metrics_to_monitor):
                # Set metric name (only needs to be set once, but safe to repeat)
                if not self.mouse_tracking_table.item(i, 0):
                    self.mouse_tracking_table.setItem(
                        i, 0, QTableWidgetItem(metric_name)
                    )

                # Update value
                value_item = self.mouse_tracking_table.item(i, 1)
                if not value_item:
                    value_item = QTableWidgetItem()
                    self.mouse_tracking_table.setItem(i, 1, value_item)
                value_item.setText(str(metric_value))

        except Exception as e:
            self.logger.error(f"Error updating mouse tracking card: {e}")

    def _get_widgetinc_status(self):
        """Get WidgetInc.exe status information."""
        try:
            # Check if WidgetInc.exe is running
            import psutil

            for proc in psutil.process_iter(["pid", "name"]):
                if proc.info["name"] == "WidgetInc.exe":
                    return {
                        "status": "Running",
                        "details": f"PID: {proc.info['pid']}",
                    }
            return {
                "status": "Not Running",
                "details": "Process not found",
            }
        except Exception as e:
            return {
                "status": "Error",
                "details": f"Check failed: {str(e)[:30]}...",
            }

    def _get_widget_core_status(self):
        """Get Widget Core status information."""
        try:
            # Check if core components are initialized
            from ..console.debug_console import DebugConsole

            if hasattr(DebugConsole, "is_initialized") and DebugConsole.is_initialized:
                return {
                    "status": "Active",
                    "details": "Core initialized",
                }
            return {
                "status": "Inactive",
                "details": "Core not initialized",
            }
        except Exception as e:
            return {
                "status": "Error",
                "details": f"Check failed: {str(e)[:30]}...",
            }

    def _get_widget_console_status(self):
        """Get Widget Console status information."""
        try:
            # This console itself is running if we can execute this
            return {
                "status": "Running",
                "details": "Console active",
            }
        except Exception as e:
            return {
                "status": "Error",
                "details": f"Check failed: {str(e)[:30]}...",
            }

    def _get_widget_overlay_status(self):
        """Get Widget Overlay status information."""
        try:
            # Check if overlay is active
            # This would need to be implemented based on your overlay system
            return {
                "status": "Unknown",
                "details": "Status check not implemented",
            }
        except Exception as e:
            return {
                "status": "Error",
                "details": f"Check failed: {str(e)[:30]}...",
            }

    def _get_widgetinc_coordinates(self):
        """Get WidgetInc.exe window coordinates."""
        try:
            # Get window coordinates - this would need to be implemented
            # based on your window detection system
            return {
                "x": 100,
                "y": 100,
                "width": 800,
                "height": 600,
            }
        except Exception as e:
            return {
                "x": 0,
                "y": 0,
                "width": 0,
                "height": 0,
            }

    def _get_overlay_coordinates(self):
        """Get overlay window coordinates."""
        try:
            # Get overlay coordinates - this would need to be implemented
            # based on your overlay system
            return {
                "x": 0,
                "y": 0,
                "width": 1920,
                "height": 1080,
            }
        except Exception as e:
            return {
                "x": 0,
                "y": 0,
                "width": 0,
                "height": 0,
            }

    def _get_current_mouse_position(self):
        """Get current mouse position."""
        try:
            import pyautogui

            pos = pyautogui.position()
            return f"({pos.x}, {pos.y})"
        except Exception as e:
            return "Unknown"

    def _get_click_count(self):
        """Get click count - this would need to be implemented."""
        try:
            # This would need to be implemented based on your tracking system
            return 0
        except Exception as e:
            return 0

    def _get_last_action(self):
        """Get last action - this would need to be implemented."""
        try:
            # This would need to be implemented based on your action tracking system
            return "None"
        except Exception as e:
            return "Unknown"
