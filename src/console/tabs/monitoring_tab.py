"""
Monitoring tab for debug console - displays real        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(0, 100)  # Process name column
        header.resizeSection(1, 70)   # Status column
        header.resizeSection(2, 60)   # PID column system information.
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

    def __init__(self, app, parent=None):
        super().__init__(app)
        self.widget_info_cache = {}
        self.cache_timeout = 5000  # Cache for 5 seconds
        self.last_cache_time = 0
        self._setup_updates()

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
            4, 4
        )  # Pre-set 4 rows for our processes
        self.process_monitoring_table.setHorizontalHeaderLabels(
            ["Process", "Status", "PID", "HWND"]
        )
        # Calculate proper height: header + 4 rows + padding
        row_height = 25  # Approximate row height
        header_height = 25  # Header height
        padding = 10  # Extra padding
        table_height = header_height + (4 * row_height) + padding + 19
        self.process_monitoring_table.setMinimumHeight(table_height)
        self.process_monitoring_table.setMaximumHeight(table_height)
        self.process_monitoring_table.setAlternatingRowColors(True)
        header = self.process_monitoring_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(0, 100)  # Process name column
        header.resizeSection(1, 70)  # Status column
        header.resizeSection(2, 60)  # PID column

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

        self.coordinates_table = QTableWidget(3, 4)  # Pre-set 3 rows for components
        self.coordinates_table.setHorizontalHeaderLabels(
            ["Component", "X", "Y", "Size"]
        )
        # Calculate proper height: header + 3 rows + padding
        row_height = 25  # Approximate row height
        header_height = 25  # Header height
        padding = 10  # Extra padding
        table_height = header_height + (3 * row_height) + padding + 14
        self.coordinates_table.setMinimumHeight(table_height)
        self.coordinates_table.setMaximumHeight(table_height)
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
        # Calculate proper height: header + 3 rows + padding
        row_height = 25  # Approximate row height
        header_height = 25  # Header height
        padding = 10  # Extra padding
        table_height = header_height + (3 * row_height) + padding + 14
        self.mouse_tracking_table.setMinimumHeight(table_height)
        self.mouse_tracking_table.setMaximumHeight(table_height)
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
        """Update monitoring data with caching to improve performance."""
        try:
            import time

            current_time = time.time() * 1000  # Convert to milliseconds

            # Only update expensive operations every 5 seconds
            if current_time - self.last_cache_time > self.cache_timeout:
                self._update_process_monitoring_card()
                self._update_coordinates_card()
                self.last_cache_time = current_time

            # Update mouse tracking every 2 seconds (lightweight)
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

                # Update PID
                pid_item = self.process_monitoring_table.item(i, 2)
                if not pid_item:
                    pid_item = QTableWidgetItem()
                    self.process_monitoring_table.setItem(i, 2, pid_item)
                pid_item.setText(str(status_info["pid"]))

                # Update HWND
                hwnd_item = self.process_monitoring_table.item(i, 3)
                if not hwnd_item:
                    hwnd_item = QTableWidgetItem()
                    self.process_monitoring_table.setItem(i, 3, hwnd_item)
                hwnd_item.setText(str(status_info["hwnd"]))

        except Exception as e:
            self.logger.error(f"Error updating process monitoring card: {e}")

    def _update_coordinates_card(self):
        """Update the coordinates monitoring card."""
        try:
            # Define the components we're monitoring (fixed rows)
            coordinates_to_monitor = [
                ("WidgetInc.exe", self._get_widgetinc_coordinates()),
                ("Playable Area", self._get_playable_area_coordinates()),
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
                # Update size - show more detailed info for playable area
                if component_name == "Playable Area":
                    playable_info = self._get_playable_area_info()
                    if playable_info:
                        size_text = f"{coord_info['width']}x{coord_info['height']} (BG:{playable_info['bg_pixel_width']:.1f}px)"
                    else:
                        size_text = f"{coord_info['width']}x{coord_info['height']}"
                else:
                    size_text = f"{coord_info['width']}x{coord_info['height']}"

                size_item.setText(size_text)

        except Exception as e:
            self.logger.error(f"Error updating coordinates card: {e}")

    def _update_mouse_tracking_card(self):
        """Update the mouse tracking card."""
        try:
            # Define the metrics we're monitoring (fixed rows)
            metrics_to_monitor = [
                ("Exact Coordinates", self._get_current_mouse_position()),
                ("% Inside WidgetInc", self._get_mouse_percentage_widget()),
                ("% Inside Playable", self._get_mouse_percentage_playable()),
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
            import win32gui
            import win32process

            for proc in psutil.process_iter(["pid", "name"]):
                if proc.info["name"] == "WidgetInc.exe":
                    pid = proc.info["pid"]
                    # Find window handle for this process
                    hwnd = self._find_window_by_pid(pid)
                    return {
                        "status": "Running",
                        "pid": pid,
                        "hwnd": hwnd if hwnd else "N/A",
                    }
            return {
                "status": "Not Running",
                "pid": "N/A",
                "hwnd": "N/A",
            }
        except Exception as e:
            return {
                "status": "Error",
                "pid": "N/A",
                "hwnd": "N/A",
            }

    def _get_widget_core_status(self):
        """Get Widget Core status information."""
        try:
            # Check if core components are initialized
            # This would need to be implemented based on your core system
            import os

            pid = os.getpid()  # Current process PID
            return {
                "status": "Active",
                "pid": pid,
                "hwnd": "N/A",
            }
        except Exception as e:
            return {
                "status": "Error",
                "pid": "N/A",
                "hwnd": "N/A",
            }

    def _get_widget_console_status(self):
        """Get Widget Console status information."""
        try:
            # This console itself is running if we can execute this
            import os

            pid = os.getpid()  # Current process PID
            hwnd = self._find_window_by_pid(pid)
            return {
                "status": "Running",
                "pid": pid,
                "hwnd": hwnd if hwnd else "N/A",
            }
        except Exception as e:
            return {
                "status": "Error",
                "pid": "N/A",
                "hwnd": "N/A",
            }

    def _get_widget_overlay_status(self):
        """Get Widget Overlay status information."""
        try:
            # Check if overlay is active
            # This would need to be implemented based on your overlay system
            return {
                "status": "Unknown",
                "pid": "N/A",
                "hwnd": "N/A",
            }
        except Exception as e:
            return {
                "status": "Error",
                "pid": "N/A",
                "hwnd": "N/A",
            }

    def _find_window_by_pid(self, pid):
        """Find window handle by process ID."""
        try:
            import win32gui
            import win32process

            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if window_pid == pid:
                        windows.append(hwnd)
                return True

            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            return windows[0] if windows else None
        except Exception:
            return None

    def _detect_black_border_bounds(self, widget_coords):
        """Detect actual black border bounds by sampling pixels for color #0c0a10."""
        try:
            import pyautogui

            # Target black border color (RGB values for #0c0a10)
            target_color = (12, 10, 16)  # RGB values for #0c0a10
            tolerance = 5  # Allow some tolerance for color matching

            width = widget_coords["width"]
            height = widget_coords["height"]
            widget_x = widget_coords["x"]
            widget_y = widget_coords["y"]

            # Sample pixels to find the actual playable area bounds
            # Start from edges and work inward to find where black borders end

            # Find left boundary
            left_bound = 0
            for x in range(width):
                pixel = pyautogui.pixel(widget_x + x, widget_y + height // 2)
                if not self._is_black_border_color(pixel, target_color, tolerance):
                    left_bound = x
                    break

            # Find right boundary
            right_bound = width
            for x in range(width - 1, -1, -1):
                pixel = pyautogui.pixel(widget_x + x, widget_y + height // 2)
                if not self._is_black_border_color(pixel, target_color, tolerance):
                    right_bound = x + 1
                    break

            # Find top boundary
            top_bound = 0
            for y in range(height):
                pixel = pyautogui.pixel(widget_x + width // 2, widget_y + y)
                if not self._is_black_border_color(pixel, target_color, tolerance):
                    top_bound = y
                    break

            # Find bottom boundary
            bottom_bound = height
            for y in range(height - 1, -1, -1):
                pixel = pyautogui.pixel(widget_x + width // 2, widget_y + y)
                if not self._is_black_border_color(pixel, target_color, tolerance):
                    bottom_bound = y + 1
                    break

            return {
                "x": widget_x + left_bound,
                "y": widget_y + top_bound,
                "width": right_bound - left_bound,
                "height": bottom_bound - top_bound,
            }

        except Exception as e:
            # Fall back to ratio-based calculation if pixel detection fails
            return None

    def _is_black_border_color(self, pixel, target_color, tolerance):
        """Check if a pixel matches the black border color within tolerance."""
        r, g, b = pixel[:3]  # Handle both RGB and RGBA
        target_r, target_g, target_b = target_color

        return (
            abs(r - target_r) <= tolerance
            and abs(g - target_g) <= tolerance
            and abs(b - target_b) <= tolerance
        )

    def _get_playable_area_coordinates(self):
        """Get playable area coordinates using ratio-based calculation."""
        try:
            widget_coords = self._get_widgetinc_coordinates()

            if widget_coords["width"] <= 0 or widget_coords["height"] <= 0:
                return {"x": 0, "y": 0, "width": 0, "height": 0}

            # Calculate 3:2 aspect ratio area (fast calculation)
            widget_width = widget_coords["width"]
            widget_height = widget_coords["height"]
            target_ratio = 3.0 / 2.0  # 1.5

            current_ratio = widget_width / widget_height

            if current_ratio > target_ratio:
                # Window is wider than 3:2, add left/right black bars
                playable_width = int(widget_height * target_ratio)
                playable_height = widget_height
                playable_x = widget_coords["x"] + (widget_width - playable_width) // 2
                playable_y = widget_coords["y"]
            else:
                # Window is taller than 3:2, add top/bottom black bars
                playable_width = widget_width
                playable_height = int(widget_width / target_ratio)
                playable_x = widget_coords["x"]
                playable_y = widget_coords["y"] + (widget_height - playable_height) // 2

            return {
                "x": playable_x,
                "y": playable_y,
                "width": playable_width,
                "height": playable_height,
            }

        except Exception as e:
            self.logger.error(f"Error calculating playable area: {e}")
            return {"x": 0, "y": 0, "width": 0, "height": 0}

    def _get_playable_area_info(self):
        """Get detailed information about the playable area including pixel scaling."""
        try:
            widget_coords = self._get_widgetinc_coordinates()
            playable_coords = self._get_playable_area_coordinates()

            if playable_coords["width"] > 0 and playable_coords["height"] > 0:
                # Calculate pixel scaling based on 192x128 background
                background_width = 192
                background_height = 128

                # Background pixel scaling
                bg_pixel_width = playable_coords["width"] / background_width
                bg_pixel_height = playable_coords["height"] / background_height

                # Sprite pixel scaling (approximately 2x density)
                sprite_pixel_width = bg_pixel_width / 2
                sprite_pixel_height = bg_pixel_height / 2

                # Calculate black border sizes
                left_border = playable_coords["x"] - widget_coords["x"]
                top_border = playable_coords["y"] - widget_coords["y"]
                right_border = (widget_coords["x"] + widget_coords["width"]) - (
                    playable_coords["x"] + playable_coords["width"]
                )
                bottom_border = (widget_coords["y"] + widget_coords["height"]) - (
                    playable_coords["y"] + playable_coords["height"]
                )

                return {
                    "bg_pixel_width": round(bg_pixel_width, 2),
                    "bg_pixel_height": round(bg_pixel_height, 2),
                    "sprite_pixel_width": round(sprite_pixel_width, 2),
                    "sprite_pixel_height": round(sprite_pixel_height, 2),
                    "left_border": left_border,
                    "right_border": right_border,
                    "top_border": top_border,
                    "bottom_border": bottom_border,
                    "aspect_ratio": round(
                        playable_coords["width"] / playable_coords["height"], 3
                    ),
                }
            return None
        except Exception as e:
            return None

    def _get_widgetinc_coordinates(self):
        """Get WidgetInc.exe client window coordinates (content area without decorations)."""
        try:
            # Get window coordinates using win32gui
            import win32gui
            import win32process
            import psutil

            # Find WidgetInc.exe process
            for proc in psutil.process_iter(["pid", "name"]):
                if proc.info["name"] == "WidgetInc.exe":
                    pid = proc.info["pid"]
                    hwnd = self._find_window_by_pid(pid)

                    if hwnd:
                        # Get client rectangle (content area without decorations)
                        client_rect = win32gui.GetClientRect(hwnd)
                        client_screen_pos = win32gui.ClientToScreen(hwnd, (0, 0))

                        # Client rect is (left, top, right, bottom) where left/top are usually 0
                        client_width = client_rect[2] - client_rect[0]
                        client_height = client_rect[3] - client_rect[1]

                        return {
                            "x": client_screen_pos[0],
                            "y": client_screen_pos[1],
                            "width": client_width,
                            "height": client_height,
                        }

            # If process not found, return zeros
            return {
                "x": 0,
                "y": 0,
                "width": 0,
                "height": 0,
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

    def _get_mouse_percentage_widget(self):
        """Get mouse position as percentage inside WidgetInc.exe window."""
        try:
            import pyautogui

            # Get current mouse position
            mouse_pos = pyautogui.position()

            # Get WidgetInc.exe coordinates
            widget_coords = self._get_widgetinc_coordinates()

            if widget_coords["width"] > 0 and widget_coords["height"] > 0:
                # Check if mouse is inside widget window
                if (
                    widget_coords["x"]
                    <= mouse_pos.x
                    <= widget_coords["x"] + widget_coords["width"]
                    and widget_coords["y"]
                    <= mouse_pos.y
                    <= widget_coords["y"] + widget_coords["height"]
                ):

                    # Calculate percentage position
                    rel_x = mouse_pos.x - widget_coords["x"]
                    rel_y = mouse_pos.y - widget_coords["y"]

                    percent_x = (rel_x / widget_coords["width"]) * 100
                    percent_y = (rel_y / widget_coords["height"]) * 100

                    return f"{percent_x:.1f}%, {percent_y:.1f}%"
                else:
                    return "Outside"
            else:
                return "N/A"
        except Exception as e:
            return "Error"

    def _get_mouse_percentage_playable(self):
        """Get mouse position as percentage inside playable area."""
        try:
            import pyautogui

            # Get current mouse position
            mouse_pos = pyautogui.position()

            # Get playable area coordinates
            playable_coords = self._get_playable_area_coordinates()

            if playable_coords["width"] > 0 and playable_coords["height"] > 0:
                # Check if mouse is inside playable area
                if (
                    playable_coords["x"]
                    <= mouse_pos.x
                    <= playable_coords["x"] + playable_coords["width"]
                    and playable_coords["y"]
                    <= mouse_pos.y
                    <= playable_coords["y"] + playable_coords["height"]
                ):

                    # Calculate percentage position
                    rel_x = mouse_pos.x - playable_coords["x"]
                    rel_y = mouse_pos.y - playable_coords["y"]

                    percent_x = (rel_x / playable_coords["width"]) * 100
                    percent_y = (rel_y / playable_coords["height"]) * 100

                    # Also calculate background pixel coordinates (192x128 grid)
                    bg_x = int((rel_x / playable_coords["width"]) * 192)
                    bg_y = int((rel_y / playable_coords["height"]) * 128)

                    return f"{percent_x:.1f}%, {percent_y:.1f}% (BG:{bg_x},{bg_y})"
                else:
                    return "Outside"
            else:
                return "N/A"
        except Exception as e:
            return "Error"

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
