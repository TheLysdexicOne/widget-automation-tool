"""
Window Manager - Core window and coordinate management.

This module handles all window detection, coordinate calculations, and tracking.
Following separation of duties: Core (brains) manages window operations.
"""

import logging
import time
from typing import Dict, Optional, Tuple
import psutil
import pyautogui

try:
    import win32gui
    import win32process

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    logging.warning("win32gui not available - some features may be limited")

from PyQt6.QtCore import QObject, pyqtSignal, QTimer


class WindowManager(QObject):
    """Manages window detection, coordinates, and tracking."""

    # Signals for notifying other components
    window_found = pyqtSignal(dict)  # Emits window info
    window_lost = pyqtSignal()
    coordinates_updated = pyqtSignal(dict)  # Emits all coordinate data
    mouse_moved = pyqtSignal(dict)  # Emits mouse position data

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Cache for expensive operations
        self.widget_window_cache = {}
        self.cache_timeout = 2000  # 2 seconds
        self.last_cache_time = 0

        # Mouse tracking
        self.last_mouse_position = None
        self.mouse_update_timer = QTimer()
        self.mouse_update_timer.timeout.connect(self._update_mouse_tracking)

        # Window monitoring
        self.window_update_timer = QTimer()
        self.window_update_timer.timeout.connect(self._update_window_data)

        # Start monitoring
        self.start_monitoring()

    def start_monitoring(self):
        """Start monitoring windows and mouse."""
        self.logger.info("Starting window and mouse monitoring")
        self.mouse_update_timer.start(100)  # 100ms for smooth mouse tracking
        self.window_update_timer.start(2000)  # 2s for window data

    def stop_monitoring(self):
        """Stop monitoring."""
        self.logger.info("Stopping window and mouse monitoring")
        self.mouse_update_timer.stop()
        self.window_update_timer.stop()

    def _update_mouse_tracking(self):
        """Update mouse position and emit signal."""
        try:
            current_pos = pyautogui.position()

            # Only emit if position changed
            if self.last_mouse_position != current_pos:
                self.last_mouse_position = current_pos

                # Calculate all mouse-related data
                mouse_data = self._calculate_mouse_data(current_pos)
                self.mouse_moved.emit(mouse_data)

        except Exception as e:
            self.logger.error(f"Error updating mouse tracking: {e}")

    def _update_window_data(self):
        """Update window data and emit signal."""
        try:
            # Get all coordinate data
            coordinates_data = self.get_all_coordinates()
            self.coordinates_updated.emit(coordinates_data)

        except Exception as e:
            self.logger.error(f"Error updating window data: {e}")

    def get_widgetinc_info(self) -> Dict:
        """Get WidgetInc.exe process and window information."""
        try:
            current_time = time.time() * 1000

            # Use cache if still valid
            if (
                current_time - self.last_cache_time < self.cache_timeout
                and self.widget_window_cache
            ):
                return self.widget_window_cache

            # Find WidgetInc.exe process
            for proc in psutil.process_iter(["pid", "name"]):
                if proc.info["name"] == "WidgetInc.exe":
                    pid = proc.info["pid"]

                    if WIN32_AVAILABLE:
                        hwnd = self._find_window_by_pid(pid)
                        if hwnd:
                            # Get client coordinates
                            client_rect = win32gui.GetClientRect(hwnd)
                            client_screen_pos = win32gui.ClientToScreen(hwnd, (0, 0))

                            client_width = client_rect[2] - client_rect[0]
                            client_height = client_rect[3] - client_rect[1]

                            info = {
                                "status": "Running",
                                "pid": pid,
                                "hwnd": hwnd,
                                "coordinates": {
                                    "x": client_screen_pos[0],
                                    "y": client_screen_pos[1],
                                    "width": client_width,
                                    "height": client_height,
                                },
                            }

                            # Cache the result
                            self.widget_window_cache = info
                            self.last_cache_time = current_time
                            return info

            # Not found
            return {
                "status": "Not Running",
                "pid": None,
                "hwnd": None,
                "coordinates": {"x": 0, "y": 0, "width": 0, "height": 0},
            }

        except Exception as e:
            self.logger.error(f"Error getting WidgetInc info: {e}")
            return {
                "status": "Error",
                "pid": None,
                "hwnd": None,
                "coordinates": {"x": 0, "y": 0, "width": 0, "height": 0},
            }

    def calculate_playable_area(self, window_coords: Dict) -> Dict:
        """Calculate playable area with 3:2 aspect ratio."""
        try:
            if window_coords["width"] <= 0 or window_coords["height"] <= 0:
                return {"x": 0, "y": 0, "width": 0, "height": 0}

            # 3:2 aspect ratio calculation
            target_ratio = 3.0 / 2.0  # 1.5
            current_ratio = window_coords["width"] / window_coords["height"]

            if current_ratio > target_ratio:
                # Window is wider than 3:2, add left/right black bars
                playable_width = int(window_coords["height"] * target_ratio)
                playable_height = window_coords["height"]
                playable_x = (
                    window_coords["x"] + (window_coords["width"] - playable_width) // 2
                )
                playable_y = window_coords["y"]
            else:
                # Window is taller than 3:2, add top/bottom black bars
                playable_width = window_coords["width"]
                playable_height = int(window_coords["width"] / target_ratio)
                playable_x = window_coords["x"]
                playable_y = (
                    window_coords["y"]
                    + (window_coords["height"] - playable_height) // 2
                )

            return {
                "x": playable_x,
                "y": playable_y,
                "width": playable_width,
                "height": playable_height,
            }

        except Exception as e:
            self.logger.error(f"Error calculating playable area: {e}")
            return {"x": 0, "y": 0, "width": 0, "height": 0}

    def get_background_coordinates(self, playable_coords: Dict) -> Dict:
        """Get 192x128 background coordinate information."""
        try:
            if playable_coords["width"] <= 0 or playable_coords["height"] <= 0:
                return None

            # Calculate pixel scaling based on 192x128 background
            bg_pixel_width = playable_coords["width"] / 192
            bg_pixel_height = playable_coords["height"] / 128

            # Calculate borders
            widget_info = self.get_widgetinc_info()
            widget_coords = widget_info["coordinates"]

            left_border = playable_coords["x"] - widget_coords["x"]
            right_border = (widget_coords["x"] + widget_coords["width"]) - (
                playable_coords["x"] + playable_coords["width"]
            )
            top_border = playable_coords["y"] - widget_coords["y"]
            bottom_border = (widget_coords["y"] + widget_coords["height"]) - (
                playable_coords["y"] + playable_coords["height"]
            )

            return {
                "grid_width": 192,
                "grid_height": 128,
                "pixel_width": round(bg_pixel_width, 2),
                "pixel_height": round(bg_pixel_height, 2),
                "sprite_pixel_width": round(bg_pixel_width / 2, 2),
                "sprite_pixel_height": round(bg_pixel_height / 2, 2),
                "borders": {
                    "left": left_border,
                    "right": right_border,
                    "top": top_border,
                    "bottom": bottom_border,
                },
                "aspect_ratio": round(
                    playable_coords["width"] / playable_coords["height"], 3
                ),
            }

        except Exception as e:
            self.logger.error(f"Error getting background coordinates: {e}")
            return None

    def get_all_coordinates(self) -> Dict:
        """Get all coordinate information."""
        try:
            # Get widget window info
            widget_info = self.get_widgetinc_info()
            widget_coords = widget_info["coordinates"]

            # Calculate playable area
            playable_coords = self.calculate_playable_area(widget_coords)

            # Get background info
            background_info = self.get_background_coordinates(playable_coords)

            return {
                "widget_window": widget_info,
                "playable_area": playable_coords,
                "background_info": background_info,
            }

        except Exception as e:
            self.logger.error(f"Error getting all coordinates: {e}")
            return {}

    def _calculate_mouse_data(self, mouse_pos) -> Dict:
        """Calculate all mouse-related data."""
        try:
            # Get current coordinate data
            coords = self.get_all_coordinates()

            if not coords:
                return {
                    "position": f"({mouse_pos.x}, {mouse_pos.y})",
                    "widget_percentage": "N/A",
                    "playable_percentage": "N/A",
                    "background_coordinates": "N/A",
                }

            widget_coords = coords["widget_window"]["coordinates"]
            playable_coords = coords["playable_area"]

            # Calculate widget window percentage
            widget_percent = "Outside"
            if (
                widget_coords["width"] > 0
                and widget_coords["height"] > 0
                and widget_coords["x"]
                <= mouse_pos.x
                <= widget_coords["x"] + widget_coords["width"]
                and widget_coords["y"]
                <= mouse_pos.y
                <= widget_coords["y"] + widget_coords["height"]
            ):

                rel_x = mouse_pos.x - widget_coords["x"]
                rel_y = mouse_pos.y - widget_coords["y"]
                percent_x = (rel_x / widget_coords["width"]) * 100
                percent_y = (rel_y / widget_coords["height"]) * 100
                widget_percent = f"{percent_x:.1f}%, {percent_y:.1f}%"

            # Calculate playable area percentage
            playable_percent = "Outside"
            background_coords = "N/A"
            if (
                playable_coords["width"] > 0
                and playable_coords["height"] > 0
                and playable_coords["x"]
                <= mouse_pos.x
                <= playable_coords["x"] + playable_coords["width"]
                and playable_coords["y"]
                <= mouse_pos.y
                <= playable_coords["y"] + playable_coords["height"]
            ):

                rel_x = mouse_pos.x - playable_coords["x"]
                rel_y = mouse_pos.y - playable_coords["y"]
                percent_x = (rel_x / playable_coords["width"]) * 100
                percent_y = (rel_y / playable_coords["height"]) * 100
                playable_percent = f"{percent_x:.1f}%, {percent_y:.1f}%"

                # Calculate background coordinates (192x128 grid)
                bg_x = int((rel_x / playable_coords["width"]) * 192)
                bg_y = int((rel_y / playable_coords["height"]) * 128)
                background_coords = f"({bg_x}, {bg_y})"

            return {
                "position": f"({mouse_pos.x}, {mouse_pos.y})",
                "widget_percentage": widget_percent,
                "playable_percentage": playable_percent,
                "background_coordinates": background_coords,
            }

        except Exception as e:
            self.logger.error(f"Error calculating mouse data: {e}")
            return {
                "position": f"({mouse_pos.x}, {mouse_pos.y})",
                "widget_percentage": "Error",
                "playable_percentage": "Error",
                "background_coordinates": "Error",
            }

    def _find_window_by_pid(self, pid: int) -> Optional[int]:
        """Find window handle by process ID."""
        if not WIN32_AVAILABLE:
            return None

        try:

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

    def get_all_coordinates(self) -> Dict:
        """Get all coordinate information for monitoring."""
        try:
            widget_info = self.get_widgetinc_info()

            result = {
                "widget_window": widget_info,
                "playable_area": {},
                "background_coords": {},
            }

            # Calculate playable area if widget window is available
            if widget_info.get("coordinates"):
                coords = widget_info["coordinates"]
                playable_area = self._calculate_playable_area(coords)
                result["playable_area"] = playable_area

                # Calculate background coordinates (192x128 grid)
                if (
                    playable_area.get("width", 0) > 0
                    and playable_area.get("height", 0) > 0
                ):
                    bg_pixel_width = playable_area["width"] / 192
                    bg_pixel_height = playable_area["height"] / 128

                    result["background_coords"] = {
                        "grid_width": 192,
                        "grid_height": 128,
                        "pixel_width": bg_pixel_width,
                        "pixel_height": bg_pixel_height,
                    }

            return result

        except Exception as e:
            self.logger.error(f"Error getting all coordinates: {e}")
            return {}

    def _calculate_playable_area(self, window_coords: Dict) -> Dict:
        """Calculate playable area with 3:2 aspect ratio."""
        try:
            if (
                window_coords.get("width", 0) <= 0
                or window_coords.get("height", 0) <= 0
            ):
                return {"x": 0, "y": 0, "width": 0, "height": 0}

            # 3:2 aspect ratio calculation
            target_ratio = 3.0 / 2.0  # 1.5
            current_ratio = window_coords["width"] / window_coords["height"]

            if current_ratio > target_ratio:
                # Window is wider than 3:2, add left/right black bars
                playable_width = int(window_coords["height"] * target_ratio)
                playable_height = window_coords["height"]
                playable_x = (
                    window_coords["x"] + (window_coords["width"] - playable_width) // 2
                )
                playable_y = window_coords["y"]
            else:
                # Window is taller than 3:2, add top/bottom black bars
                playable_width = window_coords["width"]
                playable_height = int(window_coords["width"] / target_ratio)
                playable_x = window_coords["x"]
                playable_y = (
                    window_coords["y"]
                    + (window_coords["height"] - playable_height) // 2
                )

            return {
                "x": playable_x,
                "y": playable_y,
                "width": playable_width,
                "height": playable_height,
            }

        except Exception as e:
            self.logger.error(f"Error calculating playable area: {e}")
            return {"x": 0, "y": 0, "width": 0, "height": 0}
