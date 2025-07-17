"""
Monitoring tab for debug console - displays real-time system information.

Following separation of duties: Console (user display) only shows information
provided by Core components. Does NOT perform window operations itself.
"""

import logging
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
)
from PyQt6.QtCore import Qt, QTimer

from .base_tab import BaseTab


class MonitoringTab(BaseTab):
    """Monitoring tab for real-time system information."""

    def __init__(self, app, parent=None):
        super().__init__(app, parent)
        
        # Connect to Core components for data
        self.window_manager = app.window_manager if hasattr(app, 'window_manager') else None
        self.mouse_tracker = app.mouse_tracker if hasattr(app, 'mouse_tracker') else None
        
        # Connect to Core signals
        if self.window_manager:
            self.window_manager.coordinates_updated.connect(self._on_coordinates_updated)
        if self.mouse_tracker:
            self.mouse_tracker.position_changed.connect(self._on_mouse_moved)
        
        # Data storage
        self.current_coordinates = {}
        self.current_mouse_data = {}
        
        self._setup_updates()

    def _setup_ui(self):
        """Setup the monitoring tab UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Apply dark industrial styling
        self.setStyleSheet("""
            QWidget {
                background-color: #1A1A1A;
                color: #E0E0E0;
            }
            QLabel {
                color: #E0E0E0;
                font-weight: bold;
                font-size: 14px;
                padding: 5px;
            }
            QTableWidget {
                background-color: #2D2D2D;
                border: 1px solid #363636;
                border-radius: 4px;
                gridline-color: #363636;
                selection-background-color: #4A4A4A;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #363636;
            }
            QHeaderView::section {
                background-color: #363636;
                color: #E0E0E0;
                padding: 8px;
                border: 1px solid #4A4A4A;
                font-weight: bold;
            }
        """)

        # Process Monitoring Section
        process_label = QLabel("Process Monitoring")
        main_layout.addWidget(process_label)

        self.process_monitoring_table = QTableWidget(4, 4)
        self.process_monitoring_table.setHorizontalHeaderLabels(
            ["Process", "Status", "PID", "HWND"]
        )
        self.process_monitoring_table.setMaximumHeight(150)
        self.process_monitoring_table.setAlternatingRowColors(True)
        
        # Set column widths
        header = self.process_monitoring_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(0, 100)  # Process name
        header.resizeSection(1, 70)   # Status
        header.resizeSection(2, 60)   # PID
        
        main_layout.addWidget(self.process_monitoring_table)

        # Add visual separator
        separator1 = QWidget()
        separator1.setFixedHeight(1)
        separator1.setStyleSheet("background-color: #363636; margin: 10px 0;")
        main_layout.addWidget(separator1)

        # Coordinates Monitoring Section
        coordinates_label = QLabel("Coordinates Monitoring")
        main_layout.addWidget(coordinates_label)

        self.coordinates_table = QTableWidget(3, 4)
        self.coordinates_table.setHorizontalHeaderLabels(
            ["Component", "X", "Y", "Size"]
        )
        self.coordinates_table.setMaximumHeight(120)
        self.coordinates_table.setAlternatingRowColors(True)
        
        # Set column widths
        header = self.coordinates_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(0, 100)  # Component
        header.resizeSection(1, 70)   # X
        header.resizeSection(2, 70)   # Y
        
        main_layout.addWidget(self.coordinates_table)

        # Add visual separator
        separator2 = QWidget()
        separator2.setFixedHeight(1)
        separator2.setStyleSheet("background-color: #363636; margin: 10px 0;")
        main_layout.addWidget(separator2)

        # Mouse Tracking Section
        mouse_label = QLabel("Mouse Tracking")
        main_layout.addWidget(mouse_label)

        self.mouse_tracking_table = QTableWidget(3, 2)
        self.mouse_tracking_table.setHorizontalHeaderLabels(
            ["Metric", "Value"]
        )
        self.mouse_tracking_table.setMaximumHeight(120)
        self.mouse_tracking_table.setAlternatingRowColors(True)
        
        # Set column widths
        header = self.mouse_tracking_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(0, 120)  # Metric
        
        main_layout.addWidget(self.mouse_tracking_table)

        # Initialize table data
        self._initialize_tables()

    def _initialize_tables(self):
        """Initialize table data with placeholder values."""
        # Process monitoring table
        processes = [
            ("WidgetInc.exe", "N/A", "N/A", "N/A"),
            ("Widget Core", "N/A", "N/A", "N/A"),
            ("Widget Console", "N/A", "N/A", "N/A"),
            ("Widget Overlay", "N/A", "N/A", "N/A"),
        ]
        
        for i, (process, status, pid, hwnd) in enumerate(processes):
            self.process_monitoring_table.setItem(i, 0, QTableWidgetItem(process))
            self.process_monitoring_table.setItem(i, 1, QTableWidgetItem(status))
            self.process_monitoring_table.setItem(i, 2, QTableWidgetItem(pid))
            self.process_monitoring_table.setItem(i, 3, QTableWidgetItem(hwnd))

        # Coordinates table
        components = [
            ("WidgetInc.exe", "N/A", "N/A", "N/A"),
            ("Playable Area", "N/A", "N/A", "N/A"),
            ("Overlay", "N/A", "N/A", "N/A"),
        ]
        
        for i, (component, x, y, size) in enumerate(components):
            self.coordinates_table.setItem(i, 0, QTableWidgetItem(component))
            self.coordinates_table.setItem(i, 1, QTableWidgetItem(x))
            self.coordinates_table.setItem(i, 2, QTableWidgetItem(y))
            self.coordinates_table.setItem(i, 3, QTableWidgetItem(size))

        # Mouse tracking table
        metrics = [
            ("Exact Coordinates", "N/A"),
            ("% Inside WidgetInc", "N/A"),
            ("% Inside Playable", "N/A"),
        ]
        
        for i, (metric, value) in enumerate(metrics):
            self.mouse_tracking_table.setItem(i, 0, QTableWidgetItem(metric))
            self.mouse_tracking_table.setItem(i, 1, QTableWidgetItem(value))

    def _setup_updates(self):
        """Setup update timers."""
        # Update display every 2 seconds
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(2000)  # 2 seconds

    def _on_coordinates_updated(self, coordinates_data):
        """Handle coordinates update from Core."""
        self.current_coordinates = coordinates_data
        
    def _on_mouse_moved(self, position):
        """Handle mouse movement from Core."""
        # Get mouse data from Core
        if self.mouse_tracker:
            mouse_stats = self.mouse_tracker.get_stats()
            self.current_mouse_data = mouse_stats

    def _update_display(self):
        """Update the display with current data."""
        try:
            self._update_process_monitoring()
            self._update_coordinates_monitoring()
            self._update_mouse_tracking()
        except Exception as e:
            self.logger.error(f"Error updating display: {e}")

    def _update_process_monitoring(self):
        """Update process monitoring table."""
        try:
            # Get data from Core window manager
            if self.window_manager:
                widget_info = self.window_manager.get_widgetinc_info()
                
                # Update WidgetInc.exe row
                self.process_monitoring_table.item(0, 1).setText(widget_info.get("status", "N/A"))
                self.process_monitoring_table.item(0, 2).setText(str(widget_info.get("pid", "N/A")))
                self.process_monitoring_table.item(0, 3).setText(str(widget_info.get("hwnd", "N/A")))
                
                # Update other components based on app state
                self.process_monitoring_table.item(1, 1).setText("Running" if hasattr(self.app, 'window_manager') else "N/A")
                self.process_monitoring_table.item(2, 1).setText("Running" if hasattr(self.app, 'debug_console') else "N/A")
                self.process_monitoring_table.item(3, 1).setText("Running" if hasattr(self.app, 'overlay_window') else "N/A")
                
        except Exception as e:
            self.logger.error(f"Error updating process monitoring: {e}")

    def _update_coordinates_monitoring(self):
        """Update coordinates monitoring table."""
        try:
            if not self.current_coordinates:
                return
                
            # Widget window coordinates
            widget_info = self.current_coordinates.get("widget_window", {})
            if widget_info:
                coords = widget_info.get("coordinates", {})
                self.coordinates_table.item(0, 1).setText(str(coords.get("x", "N/A")))
                self.coordinates_table.item(0, 2).setText(str(coords.get("y", "N/A")))
                self.coordinates_table.item(0, 3).setText(f"{coords.get('width', 0)}x{coords.get('height', 0)}")
            
            # Playable area coordinates
            playable_info = self.current_coordinates.get("playable_area", {})
            if playable_info:
                self.coordinates_table.item(1, 1).setText(str(playable_info.get("x", "N/A")))
                self.coordinates_table.item(1, 2).setText(str(playable_info.get("y", "N/A")))
                self.coordinates_table.item(1, 3).setText(f"{playable_info.get('width', 0)}x{playable_info.get('height', 0)}")
            
            # Overlay coordinates (would need overlay to report this)
            if hasattr(self.app, 'overlay_window') and self.app.overlay_window:
                overlay_rect = self.app.overlay_window.geometry()
                self.coordinates_table.item(2, 1).setText(str(overlay_rect.x()))
                self.coordinates_table.item(2, 2).setText(str(overlay_rect.y()))
                self.coordinates_table.item(2, 3).setText(f"{overlay_rect.width()}x{overlay_rect.height()}")
                
        except Exception as e:
            self.logger.error(f"Error updating coordinates monitoring: {e}")

    def _update_mouse_tracking(self):
        """Update mouse tracking table."""
        try:
            if not self.current_mouse_data:
                return
                
            # Update mouse position
            self.mouse_tracking_table.item(0, 1).setText(self.current_mouse_data.get("current_position", "N/A"))
            
            # Get additional mouse data from window manager
            if self.window_manager and self.mouse_tracker:
                mouse_pos = self.mouse_tracker.get_current_position()
                coords = self.window_manager.get_all_coordinates()
                
                if coords:
                    # Calculate widget percentage
                    widget_coords = coords.get("widget_window", {}).get("coordinates", {})
                    if widget_coords.get("width", 0) > 0:
                        if (widget_coords["x"] <= mouse_pos[0] <= widget_coords["x"] + widget_coords["width"] and
                            widget_coords["y"] <= mouse_pos[1] <= widget_coords["y"] + widget_coords["height"]):
                            rel_x = mouse_pos[0] - widget_coords["x"]
                            rel_y = mouse_pos[1] - widget_coords["y"]
                            percent_x = (rel_x / widget_coords["width"]) * 100
                            percent_y = (rel_y / widget_coords["height"]) * 100
                            self.mouse_tracking_table.item(1, 1).setText(f"{percent_x:.1f}%, {percent_y:.1f}%")
                        else:
                            self.mouse_tracking_table.item(1, 1).setText("Outside")
                    
                    # Calculate playable percentage
                    playable_coords = coords.get("playable_area", {})
                    if playable_coords.get("width", 0) > 0:
                        if (playable_coords["x"] <= mouse_pos[0] <= playable_coords["x"] + playable_coords["width"] and
                            playable_coords["y"] <= mouse_pos[1] <= playable_coords["y"] + playable_coords["height"]):
                            rel_x = mouse_pos[0] - playable_coords["x"]
                            rel_y = mouse_pos[1] - playable_coords["y"]
                            percent_x = (rel_x / playable_coords["width"]) * 100
                            percent_y = (rel_y / playable_coords["height"]) * 100
                            bg_x = int((rel_x / playable_coords["width"]) * 192)
                            bg_y = int((rel_y / playable_coords["height"]) * 128)
                            self.mouse_tracking_table.item(2, 1).setText(f"{percent_x:.1f}%, {percent_y:.1f}% (BG:{bg_x},{bg_y})")
                        else:
                            self.mouse_tracking_table.item(2, 1).setText("Outside")
                            
        except Exception as e:
            self.logger.error(f"Error updating mouse tracking: {e}")

    def on_tab_activated(self):
        """Called when monitoring tab becomes active."""
        # Start timers when tab is activated
        if hasattr(self, 'update_timer'):
            self.update_timer.start(2000)

    def on_tab_deactivated(self):
        """Called when monitoring tab becomes inactive."""
        # Stop timers when tab is deactivated to save resources
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
