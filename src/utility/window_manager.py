"""
Window Manager - Proactive Window Cache Management

This module provides the WindowManager class that handles all WidgetInc window
detection and caching with proactive updates every 500ms.

The WindowManager provides clean APIs for other components to use without
worrying about cache management or window enumeration performance.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

import psutil
import win32gui
import win32process
from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class CompactJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that keeps arrays on single lines."""

    def encode(self, obj):
        if isinstance(obj, list) and len(obj) <= 4:
            # Keep short arrays (like coordinates) on one line
            return json.dumps(obj, separators=(",", ":"))
        return super().encode(obj)

    def iterencode(self, obj, _one_shot=False):
        """Encode the given object and yield each string representation as available."""
        if isinstance(obj, list) and len(obj) <= 4:
            yield self.encode(obj)
        else:
            yield from super().iterencode(obj, _one_shot)


# Constants
TARGET_PROCESS_NAME = "WidgetInc.exe"
logger = logging.getLogger(__name__)

# Pixel Art Grid Constants - Single Source of Truth
PIXEL_ART_GRID_WIDTH = 192  # Background pixels horizontally
PIXEL_ART_GRID_HEIGHT = 128  # Background pixels vertically


class WindowManager(QObject):
    """
    Manages WidgetInc window detection and caching with proactive updates.

    Validates cache every 500ms and provides clean APIs for window information.
    Other components can request data without worrying about cache management.
    """

    # Signals for when window state changes
    window_found = pyqtSignal(dict)  # Emitted when window is found/changes
    window_lost = pyqtSignal()  # Emitted when window is lost

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Cache storage
        self._cache = {
            "window_info": None,
            "timestamp": 0,
            "is_valid": False,
            "last_state": None,  # Track window state changes
        }

        # Validation timer - checks every 500ms
        self._timer = QTimer()
        self._timer.timeout.connect(self._validate_cache)
        self._timer.start(500)

        # Initial cache population
        self._validate_cache()

        # Set up cache logging directory
        self._cache_log_dir = Path(__file__).parent.parent.parent / "logs" / "cache"
        self._cache_log_dir.mkdir(parents=True, exist_ok=True)

        self.logger.debug("WindowManager initialized with 500ms validation timer")

    def _validate_cache(self):
        """Proactively validate and update cache if needed."""
        try:
            current_window = self._find_target_window()
            cache_window = self._cache.get("window_info")

            # Check if window state changed
            if current_window is None and cache_window is not None:
                # Window was lost
                self._cache["window_info"] = None
                self._cache["is_valid"] = False
                self._cache["last_state"] = None
                self.window_lost.emit()
                self._save_cache_to_file()
                self.logger.debug("Window lost - cache cleared")

            elif current_window is not None:
                # Window exists - check if it changed
                if cache_window is None or self._window_changed(cache_window, current_window):
                    # Window found or changed - update cache
                    self._cache["window_info"] = current_window
                    self._cache["is_valid"] = True
                    self._cache["timestamp"] = time.time()
                    self._cache["last_state"] = self._get_window_state(current_window)
                    self.window_found.emit(current_window)
                    self._save_cache_to_file()
                    self.logger.debug("Window cache updated")

        except Exception as e:
            self.logger.error(f"Error validating cache: {e}")
            self._cache["is_valid"] = False

    def _save_cache_to_file(self):
        """Save current cache state to logs/cache/cache.json for debugging."""
        try:
            cache_file = self._cache_log_dir / "cache.json"

            # Calculate current playable area, overlay position, and pixel size for debugging
            playable_area = self._calculate_playable_area()
            overlay_position = self._calculate_overlay_position()
            pixel_size = self._calculate_pixel_size()

            # Prepare cache data for JSON serialization
            cache_data = {
                "timestamp": self._cache["timestamp"],
                "is_valid": self._cache["is_valid"],
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self._cache["timestamp"])),
                "window_info": self._cache["window_info"],
                "playable_area": playable_area,
                "overlay_position": overlay_position,
                "pixel_size": pixel_size,
                "last_state": self._cache["last_state"],
            }

            with open(cache_file, "w", encoding="utf-8") as f:
                # First pass: normal JSON with indentation
                json_str = json.dumps(cache_data, indent=2, default=str)

                # Second pass: compact coordinate arrays
                import re

                # Match arrays that span multiple lines with up to 4 numbers
                pattern = r"\[\s*(-?\d+(?:\.\d+)?),?\s*\n\s*(-?\d+(?:\.\d+)?),?\s*\n\s*(-?\d+(?:\.\d+)?),?\s*\n\s*(-?\d+(?:\.\d+)?)\s*\]"
                json_str = re.sub(pattern, r"[\1, \2, \3, \4]", json_str)

                # Handle 2-element arrays too
                pattern2 = r"\[\s*(-?\d+(?:\.\d+)?),?\s*\n\s*(-?\d+(?:\.\d+)?)\s*\]"
                json_str = re.sub(pattern2, r"[\1, \2]", json_str)

                f.write(json_str)

        except Exception as e:
            self.logger.debug(f"Could not save cache to file: {e}")
            # Don't let cache logging errors affect main functionality

    def _window_changed(self, old_window: Dict, new_window: Dict) -> bool:
        """Check if window state has meaningfully changed."""
        if not old_window or not new_window:
            return True

        # Compare key properties that matter for positioning
        old_rect = old_window.get("window_rect", ())
        new_rect = new_window.get("window_rect", ())
        old_client = old_window.get("client_rect", ())
        new_client = new_window.get("client_rect", ())

        return old_rect != new_rect or old_client != new_client or old_window.get("hwnd") != new_window.get("hwnd")

    def _get_window_state(self, window_info: Dict) -> Dict:
        """Extract key state information for change detection."""
        return {
            "hwnd": window_info.get("hwnd"),
            "window_rect": window_info.get("window_rect"),
            "client_rect": window_info.get("client_rect"),
        }

    def _find_target_window(self) -> Optional[Dict[str, Any]]:
        """Find WidgetInc window - internal method."""
        try:

            def enum_windows_callback(hwnd, _):
                try:
                    title = win32gui.GetWindowText(hwnd)
                    if "WidgetInc" in title and win32gui.IsWindowVisible(hwnd):
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        proc = psutil.Process(pid)
                        if proc.name() == TARGET_PROCESS_NAME:
                            window_info = self._build_window_info(pid, hwnd)
                            if window_info:
                                target_windows.append(window_info)
                except Exception:
                    pass
                return True

            target_windows = []
            win32gui.EnumWindows(enum_windows_callback, None)

            return target_windows[0] if target_windows else None

        except Exception as e:
            self.logger.error(f"Error in window detection: {e}")
            return None

    def _build_window_info(self, pid: int, hwnd: int) -> Optional[Dict[str, Any]]:
        """Build window information dictionary."""
        try:
            title = win32gui.GetWindowText(hwnd)
            window_rect = win32gui.GetWindowRect(hwnd)
            client_rect = win32gui.GetClientRect(hwnd)

            # Calculate client area in screen coordinates (like tracker)
            client_left_top = win32gui.ClientToScreen(hwnd, (client_rect[0], client_rect[1]))
            client_right_bottom = win32gui.ClientToScreen(hwnd, (client_rect[2], client_rect[3]))
            client_x = client_left_top[0]
            client_y = client_left_top[1]
            client_w = client_right_bottom[0] - client_left_top[0]
            client_h = client_right_bottom[1] - client_left_top[1]

            return {
                "pid": pid,
                "hwnd": hwnd,
                "title": title,
                "window_rect": window_rect,
                "client_rect": client_rect,
                "client_screen": {"x": client_x, "y": client_y, "width": client_w, "height": client_h},
            }
        except Exception as e:
            self.logger.error(f"Error building window info: {e}")
            return None

    def _calculate_playable_area(self) -> Optional[Dict[str, int]]:
        """
        Calculate 3:2 aspect ratio playable area using cached window info.
        Uses the same logic as the tracker app for consistency.
        """
        window_info = self._cache.get("window_info")
        if not window_info or not self._cache["is_valid"]:
            return None

        try:
            client_screen = window_info["client_screen"]
            client_x = client_screen["x"]
            client_y = client_screen["y"]
            client_w = client_screen["width"]
            client_h = client_screen["height"]

            # Calculate 3:2 aspect ratio playable area (tracker logic)
            target_ratio = 3.0 / 2.0
            client_ratio = client_w / client_h if client_h else 1

            if client_ratio > target_ratio:
                # Client is wider than 3:2 - fit height, center width
                playable_height = client_h
                playable_width = int(playable_height * target_ratio)
                px = client_x + (client_w - playable_width) // 2
                py = client_y
            else:
                # Client is taller than 3:2 - fit width, center height
                playable_width = client_w
                playable_height = int(playable_width / target_ratio)
                px = client_x
                py = client_y + (client_h - playable_height) // 2

            return {"x": px, "y": py, "width": playable_width, "height": playable_height}

        except Exception as e:
            self.logger.error(f"Error calculating playable area: {e}")
            return None

    def _calculate_pixel_size(self) -> Optional[float]:
        """
        Calculate pixel art grid size based on playable area.
        Returns pixels per background grid unit (192x128 grid).
        """
        playable_area = self._calculate_playable_area()
        if not playable_area:
            return None

        try:
            # Pixel art grid dimensions (background grid)
            PIXEL_ART_GRID_WIDTH = 192
            PIXEL_ART_GRID_HEIGHT = 128

            playable_width = playable_area["width"]
            playable_height = playable_area["height"]

            if playable_width <= 0 or playable_height <= 0:
                return None

            # Calculate pixel size for both dimensions
            pixel_size_x = playable_width / PIXEL_ART_GRID_WIDTH
            pixel_size_y = playable_height / PIXEL_ART_GRID_HEIGHT

            # Use smaller dimension to ensure perfect square pixels
            # Round to 4 decimal places to minimize grid alignment drift
            return round(min(pixel_size_x, pixel_size_y), 4)

        except Exception as e:
            self.logger.error(f"Error calculating pixel size: {e}")
            return None

    def _calculate_overlay_position(self) -> Optional[Dict[str, int]]:
        """
        Calculate overlay position in top-right corner of window.
        Returns cached position for the overlay application.
        """
        playable_area = self._calculate_playable_area()
        window_info = self._cache.get("window_info")

        if not playable_area or not window_info or not self._cache["is_valid"]:
            return None

        try:
            client_screen = window_info["client_screen"]
            client_y = client_screen["y"]
            client_width = client_screen["width"]
            client_height = client_screen["height"]

            playable_x = playable_area["x"]
            playable_width = playable_area["width"]

            # Calculate overlay position to the right of playable area
            offset_y = max(32, client_width // 80)
            overlay_x = playable_x + playable_width + 1
            overlay_y = client_y + offset_y
            available_height = client_height - offset_y

            return {
                "x": overlay_x,
                "y": overlay_y,
                "available_height": available_height,
            }

        except Exception as e:
            self.logger.error(f"Error calculating overlay position: {e}")
            return None

    # Public API methods
    def get_window_info(self) -> Optional[Dict[str, Any]]:
        """Get current window info (always fresh from cache)."""
        if self._cache["is_valid"]:
            return self._cache["window_info"]
        return None

    def get_playable_area(self) -> Optional[Dict[str, int]]:
        """Get playable area coordinates from cache (fast cached calculation)."""
        return self._calculate_playable_area()

    def get_overlay_position(self) -> Optional[Dict[str, int]]:
        """Get overlay position coordinates from cache (fast cached calculation)."""
        return self._calculate_overlay_position()

    def get_pixel_size(self) -> Optional[float]:
        """Get pixel art grid size from cache (fast cached calculation)."""
        return self._calculate_pixel_size()

    def is_window_available(self) -> bool:
        """Check if WidgetInc window is currently available."""
        return self._cache["is_valid"] and self._cache["window_info"] is not None

    def force_refresh(self):
        """Force immediate cache refresh."""
        self._validate_cache()


# Global WindowManager instance
_window_manager = None


def get_window_manager() -> WindowManager:
    """Get the global WindowManager instance."""
    global _window_manager
    if _window_manager is None:
        _window_manager = WindowManager()
    return _window_manager
