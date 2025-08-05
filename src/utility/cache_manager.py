"""
Window Manager - Proactive Window Cache Management

This module provides the WindowManager class that handles all WidgetInc window
detection and caching with proactive updates every 500ms.

The WindowManager provides clean APIs for other components to use without
worrying about cache management or window enumeration performance.
"""

import json
import logging
import pyautogui
import time
from pathlib import Path
from typing import Any, Dict, Optional
import re

import psutil
import win32gui
import win32process
from PyQt6.QtCore import QObject, QTimer, pyqtSignal


# Constants
TARGET_PROCESS_NAME = "WidgetInc.exe"
logger = logging.getLogger(__name__)

# Pixel Art Grid Constants - Single Source of Truth
PIXEL_ART_GRID_WIDTH = 192  # Background pixels horizontally
PIXEL_ART_GRID_HEIGHT = 128  # Background pixels vertically


class CacheManager(QObject):
    """
    Manages WidgetInc window detection and database caching with proactive updates.

    Validates cache every 500ms and provides clean APIs for window information.
    Also handles coordinate cache generation from frames database.
    Other components can request data without worrying about cache management.
    """

    # Signals for when window state changes
    window_found = pyqtSignal(dict)  # Emitted when window is found/changes
    window_lost = pyqtSignal()  # Emitted when window is lost

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Set up cache logging directory first
        self._cache_log_dir = Path(__file__).parent.parent.parent / "logs" / "cache"
        self._cache_log_dir.mkdir(parents=True, exist_ok=True)

        # Database file tracking
        self._frames_db_file = Path(__file__).parent.parent.parent / "config" / "data" / "frames_database.json"
        self._last_db_mtime = 0
        self._last_error_shown = None  # Track last error to avoid spam
        self._last_console_error_time = 0  # Track console error logging (every 10 seconds)

        # Cache storage
        self._cache = {
            "window_info": None,
            "timestamp": 0,
            "is_valid": False,
            "last_state": None,  # Track window state changes
            "frame_area": None,
            "frame_area_refined": None,  # Store refined frame area with border checking
            "refinement_failed": False,  # Track if border refinement failed
            "overlay_position": None,
            "pixel_size": None,
            "monitor_info": None,  # Store monitor info for multi-monitor support
            "leftmost_x_offset": None,  # Store leftmost x offset
        }

        # Validation timer - checks every 1000ms (1 second)
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer_tick)
        self._timer.start(1000)

        # Timer tick counter for less frequent database checks
        self._timer_tick_count = 0

        # Initial cache population and database tracking
        # Only check database on startup, not continuously
        if self._frames_db_file.exists():
            self._last_db_mtime = self._frames_db_file.stat().st_mtime
        self._validate_cache()

        self.logger.debug("WindowManager initialized with 1000ms validation timer and database file watching")

    def _on_timer_tick(self):
        """Handle timer tick - validate cache every tick, check database less frequently."""
        self._timer_tick_count += 1

        # Always update coordinate cache
        self._validate_cache()

        # Check database every 6th tick (every 30 seconds instead of every 5 seconds)
        if self._timer_tick_count % 6 == 0:
            self._check_database_changes()

    def _validate_cache(self):
        """Proactively validate and update cache if needed."""
        try:
            # No longer check database changes here - moved to timer tick

            current_window = self._find_target_window()
            cache_window = self._cache.get("window_info")

            # Check if window state changed
            if current_window is None and cache_window is not None:
                # Window was lost
                self._cache["window_info"] = None
                self._cache["is_valid"] = False
                self._cache["last_state"] = None
                self._cache["frame_area"] = None
                self._cache["frame_area_refined"] = None
                self._cache["refinement_failed"] = False
                self._cache["overlay_position"] = None
                self._cache["pixel_size"] = None
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

                    # Recalculate and cache derived values
                    self._cache["frame_area"] = self._calculate_frame_area()
                    self._cache["frame_area_refined"] = None  # Reset refined area on window change
                    self._cache["refinement_failed"] = False  # Reset refinement failure flag
                    self._cache["overlay_position"] = self._calculate_overlay_position()
                    self._cache["pixel_size"] = self._calculate_pixel_size()
                    self._cache["monitor_info"] = self._get_monitor_info()
                    self._cache["leftmost_x_offset"] = self._get_leftmost_x_offset()

                    self.window_found.emit(current_window)
                    self._save_cache_to_file()
                    self.logger.debug("Window cache updated")

        except Exception as e:
            self.logger.error(f"Error validating cache: {e}")
            self._cache["is_valid"] = False

    def _check_database_changes(self):
        """Check if frames_database.json has been modified and regenerate cache if valid."""
        try:
            if not self._frames_db_file.exists():
                return

            current_mtime = self._frames_db_file.stat().st_mtime
            if current_mtime != self._last_db_mtime:
                self.logger.debug("Database file modified, checking validity...")

                # Validate JSON before proceeding
                if self._validate_database_json():
                    self.logger.info("Database file is valid, regenerating coordinate cache...")
                    self.generate_db_cache()
                    self._last_db_mtime = current_mtime
                    # Clear any previous error if validation now passes
                    self._last_error_shown = None
                else:
                    self.logger.warning("Database file is invalid, skipping cache regeneration")
                    # Show error popup only once per unique error
                    self._show_database_error_popup()
                    # Log error to console every 10 seconds
                    self._log_console_error()

        except Exception as e:
            self.logger.error(f"Error checking database changes: {e}")

    def _validate_database_json(self) -> bool:
        """Lightweight validation: Check JSON syntax and 'frames' key exists."""
        try:
            with open(self._frames_db_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Only check basic structure - JSON syntax and frames key
            if not isinstance(data, dict) or "frames" not in data:
                error_msg = "Database missing 'frames' key or invalid structure"
                self.logger.error(error_msg)
                self._last_validation_error = {"type": "structure", "message": error_msg}
                return False

            self.logger.debug("Database JSON validation passed (lightweight)")
            self._last_validation_error = None
            return True

        except json.JSONDecodeError as e:
            error_msg = f"Database JSON syntax error: {e}"
            self.logger.error(error_msg)

            self._last_validation_error = {
                "type": "json",
                "message": error_msg,
                "line": getattr(e, "lineno", None),
                "col": getattr(e, "colno", None),
            }
            return False
        except Exception as e:
            error_msg = f"Error validating database JSON: {e}"
            self.logger.error(error_msg)
            self._last_validation_error = {"type": "other", "message": error_msg}
            return False

    def _show_database_error_popup(self):
        """Show a single error popup with context, avoiding spam."""
        if not hasattr(self, "_last_validation_error") or not self._last_validation_error:
            return

        error_info = self._last_validation_error
        current_error_key = f"{error_info['type']}:{error_info['message']}"

        # Only show popup if this is a new/different error
        if self._last_error_shown == current_error_key:
            return

        self._last_error_shown = current_error_key

        # Skip error sound to avoid potential hanging issues
        # self._play_error_sound()

        # Create detailed error message with context
        title = "Database Validation Error"
        message = f"Error in frames_database.json:\n\n{error_info['message']}"

        # Add context based on error type
        if error_info["type"] == "json" and error_info.get("line") is not None:
            message += f"\n\nAt line {error_info['line']}"
            if error_info.get("col"):
                message += f", column {error_info['col']}"

        # Use static method with window flags to bring to front
        # Use native Windows MessageBox for guaranteed visibility over WindowStaysOnTopHint
        try:
            import ctypes

            # Use Windows MessageBox which always comes to front
            MB_ICONERROR = 0x10
            MB_OK = 0x0
            MB_TOPMOST = 0x40000

            ctypes.windll.user32.MessageBoxW(None, message, title, MB_ICONERROR | MB_OK | MB_TOPMOST)
        except Exception as e:
            # Fallback to Qt dialog if Windows MessageBox fails
            self.logger.debug(f"Windows MessageBox failed, using Qt fallback: {e}")

            from PyQt6.QtWidgets import QMessageBox, QApplication
            from PyQt6.QtCore import Qt

            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.setWindowFlags(
                Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint
            )
            msg_box.show()
            msg_box.raise_()
            msg_box.activateWindow()
            QApplication.processEvents()
            msg_box.exec()

    def _log_console_error(self):
        """Log error to console every 10 seconds to keep it visible."""
        if not hasattr(self, "_last_validation_error") or not self._last_validation_error:
            return

        current_time = time.time()
        # Only log to console every 10 seconds
        if current_time - self._last_console_error_time >= 10:
            error_info = self._last_validation_error
            self.logger.error(f"DATABASE ERROR (repeating): {error_info['message']}")
            self._last_console_error_time = current_time

    def _play_error_sound(self):
        """Play error sound if available."""
        try:
            from PyQt6.QtMultimedia import QSoundEffect
            from PyQt6.QtCore import QUrl

            sound_path = Path(__file__).parent.parent.parent / "assets" / "sounds" / "error1.mp3"
            print(f"Playing error sound from {sound_path}")
            if sound_path.exists():
                sound_effect = QSoundEffect()
                sound_effect.setSource(QUrl.fromLocalFile(str(sound_path)))
                sound_effect.play()
        except Exception as e:
            self.logger.debug(f"Could not play error sound: {e}")

    def _save_cache_to_file(self):
        """Save current cache state to logs/cache/cache.cache for debugging."""
        try:
            cache_file = Path(__file__).parent.parent.parent / "config" / "cache" / "cache.cache"

            # Use cached values directly instead of recalculating
            cache_data = {
                "timestamp": self._cache["timestamp"],
                "is_valid": self._cache["is_valid"],
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self._cache["timestamp"])),
                "window_info": self._cache["window_info"],
                "frame_area": self._cache.get("frame_area"),
                "overlay_position": self._cache.get("overlay_position"),
                "pixel_size": self._cache.get("pixel_size"),
                "monitor_info": self._cache.get("monitor_info"),
                "leftmost_x_offset": self._cache.get("leftmost_x_offset"),
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

    def _get_monitor_info(self):
        """Get monitor info for the monitor containing the WidgetInc window."""
        try:
            from screeninfo import get_monitors

            window_info = self._cache.get("window_info")
            if not window_info or not self._cache["is_valid"]:
                return None
            client_screen = window_info["client_screen"]
            wx, wy = client_screen["x"], client_screen["y"]
            for m in get_monitors():
                # Check if window's top-left is within monitor bounds
                if wx >= m.x and wx < m.x + m.width and wy >= m.y and wy < m.y + m.height:
                    return {
                        "name": getattr(m, "name", None),
                        "x": m.x,
                        "y": m.y,
                        "width": m.width,
                        "height": m.height,
                        "is_primary": getattr(m, "is_primary", False),
                    }
            return None
        except Exception as e:
            self.logger.error(f"Error getting monitor info: {e}")
            return None

    def _get_leftmost_x_offset(self):
        """Get the x offset of the leftmost monitor (for multi-monitor screenshots)."""
        try:
            from screeninfo import get_monitors

            monitors = get_monitors()
            if not monitors:
                return 0
            return min(m.x for m in monitors)
        except Exception as e:
            self.logger.error(f"Error getting leftmost x offset: {e}")
            return 0

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

    def _refine_frame_borders_pyautogui(self, frame_area, border_color=(12, 10, 16)):
        """
        Refine frame borders using PyAutoGUI pixel checking.
        Simple border refinement - handle common off-by-1 or off-by-2 pixel errors.
        Ensures x-1 is border on left and adjust to get exactly 2054 width.
        Uses middle Y for validation with 3-pixel buffer from overlay.
        """
        if not frame_area:
            return None

        try:
            x, y, width, height = frame_area["x"], frame_area["y"], frame_area["width"], frame_area["height"]

            # Use middle Y for validation (3-pixel buffer from overlay should be sufficient)
            validation_y = y + height // 2
            target_width = 2054

            self.logger.debug(
                f"Refining borders at validation_y={validation_y}, initial width={width}, target={target_width}"
            )

            # Find correct left boundary - check if x-1 is border, adjust if needed
            left_x = x
            for offset in range(3):  # Check current, +1, +2
                test_x = left_x + offset
                if test_x > 0:
                    try:
                        pixel = pyautogui.pixel(test_x - 1, validation_y)
                        if pixel == border_color:
                            left_x = test_x
                            self.logger.debug(f"Found correct left boundary at x={left_x}")
                            break
                    except Exception as e:
                        self.logger.debug(f"Error checking pixel at {test_x - 1}: {e}")
                        continue
            else:
                # Try moving left by 1 or 2
                for offset in range(1, 3):
                    test_x = left_x - offset
                    if test_x > 0:
                        try:
                            pixel = pyautogui.pixel(test_x - 1, validation_y)
                            if pixel == border_color:
                                left_x = test_x
                                self.logger.debug(f"Found correct left boundary at x={left_x} (moved left by {offset})")
                                break
                        except Exception as e:
                            self.logger.debug(f"Error checking pixel at {test_x - 1}: {e}")
                            continue

            # Calculate refined dimensions with target width
            refined_width = target_width

            self.logger.debug(f"Border refinement complete: left_x={left_x}, width={refined_width}")

            return {
                "x": left_x,
                "y": y,
                "width": refined_width,
                "height": height,
                "adjustments": {"left_shift": left_x - x, "width_change": refined_width - width},
            }

        except Exception as e:
            self.logger.error(f"Error in border refinement: {e}")
            return None

    def _calculate_frame_area(self) -> Optional[Dict[str, int]]:
        """
        Calculate 3:2 aspect ratio frame area using cached window info.
        Uses border refinement when possible for improved accuracy.
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

            # Calculate basic 3:2 aspect ratio frame area (tracker logic)
            target_ratio = 3.0 / 2.0
            client_ratio = client_w / client_h if client_h else 1

            if client_ratio > target_ratio:
                # Client is wider than 3:2 - fit height, center width
                frame_height = client_h
                frame_width = int(frame_height * target_ratio)
                px = client_x + (client_w - frame_width) // 2
                py = client_y
            else:
                # Client is taller than 3:2 - fit width, center height
                frame_width = client_w
                frame_height = int(frame_width / target_ratio)
                px = client_x
                py = client_y + (client_h - frame_height) // 2

            base_frame_area = {"x": px, "y": py, "width": frame_width, "height": frame_height}

            # Try border refinement if not already failed and conditions are met
            if (
                not self._cache.get("refinement_failed", False) and abs(frame_width - 2054) <= 5
            ):  # Only try refinement if we're close to target
                # Check if we already have a refined version
                cached_refined = self._cache.get("frame_area_refined")
                if cached_refined:
                    self.logger.debug("Using cached refined frame area")
                    return cached_refined

                # Use bottom area for border checking - no need to minimize overlay
                refined_area = self._refine_frame_borders_pyautogui(base_frame_area)

                if refined_area:
                    self.logger.info(f"Border refinement successful: width {frame_width} -> {refined_area['width']}")
                    self._cache["frame_area_refined"] = refined_area
                    self._cache["refinement_failed"] = False
                    return refined_area
                else:
                    self.logger.debug("Border refinement failed, using base calculation")
                    self._cache["refinement_failed"] = True

            # Use base calculation if refinement not available or failed
            return base_frame_area

        except Exception as e:
            self.logger.error(f"Error calculating frame area: {e}")
            self._cache["refinement_failed"] = True
            return None

    def _calculate_pixel_size(self) -> Optional[float]:
        """
        Calculate pixel art grid size based on frame area.
        Returns pixels per background grid unit (192x128 grid).
        """
        # Use cached frame area if available
        frame_area = self._cache.get("frame_area")
        if not frame_area:
            frame_area = self._calculate_frame_area()
            if frame_area:
                self._cache["frame_area"] = frame_area

        if not frame_area:
            return None

        try:
            # Pixel art grid dimensions (background grid)
            PIXEL_ART_GRID_WIDTH = 192
            PIXEL_ART_GRID_HEIGHT = 128

            frame_width = frame_area["width"]
            frame_height = frame_area["height"]

            if frame_width <= 0 or frame_height <= 0:
                return None

            # Calculate pixel size for both dimensions
            pixel_size_x = frame_width / PIXEL_ART_GRID_WIDTH
            pixel_size_y = frame_height / PIXEL_ART_GRID_HEIGHT

            # Use smaller dimension to ensure perfect square pixels
            # Round to 4 decimal places to minimize grid alignment drift
            return round(min(pixel_size_x, pixel_size_y), 4)

        except Exception as e:
            self.logger.error(f"Error calculating pixel size: {e}")
            return None

    def _calculate_overlay_position(self, *_) -> Optional[Dict[str, Any]]:
        """
        Calculate overlay position in top-right corner of window.
        Returns cached position for the overlay application with anchor and available dimensions.
        """
        # Use cached frame area if available
        frame_area = self._cache.get("frame_area")
        if not frame_area:
            frame_area = self._calculate_frame_area()
            if frame_area:
                self._cache["frame_area"] = frame_area

        window_info = self._cache.get("window_info")

        if not frame_area or not window_info or not self._cache["is_valid"]:
            return None

        try:
            client_screen = window_info["client_screen"]
            client_y = client_screen["y"]
            client_width = client_screen["width"]
            client_height = client_screen["height"]

            frame_x = frame_area["x"]
            frame_width = frame_area["width"]

            # Calculate overlay position to the right of frame area
            offset_y = max(32, client_width // 80)
            bottom_margin = 100
            overlay_x = frame_x + frame_width + 3
            overlay_y = client_y + offset_y
            available_height = client_height - offset_y - bottom_margin

            return {
                "x": overlay_x,
                "y": overlay_y,
                "available_height": available_height,
            }

        except Exception as e:
            self.logger.error(f"Error calculating overlay position: {e}")
            return None

    def _convert_colors_to_tuples(self, frame_data):
        """Convert color arrays to tuples for pixel comparison."""
        if "colors" in frame_data:
            for color_key, color_value in frame_data["colors"].items():
                if isinstance(color_value, list):
                    if len(color_value) == 3 and all(isinstance(x, (int, float)) for x in color_value):
                        # Single color [r, g, b] -> (r, g, b)
                        frame_data["colors"][color_key] = tuple(color_value)
                    elif all(isinstance(item, list) and len(item) == 3 for item in color_value):
                        # List of colors [[r,g,b], [r,g,b]] -> [(r,g,b), (r,g,b)]
                        frame_data["colors"][color_key] = [tuple(color) for color in color_value]
        return frame_data

    def generate_db_cache(self):
        from .coordinate_utils import conv_screen_to_frame_coords, conv_grid_to_screen_coords

        """Generate frames.cache with screen coordinates as main and frame coordinates as additional key."""

        frames_file = Path(__file__).parent.parent.parent / "config" / "data" / "frames_database.json"
        frames_cache = Path(__file__).parent.parent.parent / "config" / "cache" / "frames.cache"

        with open(frames_file, "r") as f:
            frames_data = json.load(f)

        frames_with_coords = []

        for frame in frames_data["frames"]:
            frame_copy = frame.copy()
            frame_xy = {}

            # Convert button coordinates
            if "buttons" in frame:
                frame_xy["buttons"] = {}
                for button_name, button_data in frame["buttons"].items():
                    if len(button_data) != 3:
                        self.logger.error(f"Invalid button data for {button_name}: {button_data}")
                        import sys

                        sys.exit("Exiting due to invalid database")

                    grid_x, grid_y, color = button_data
                    screen_x, screen_y = conv_grid_to_screen_coords(grid_x, grid_y)
                    frame_x, frame_y = conv_screen_to_frame_coords(screen_x, screen_y)

                    frame_copy["buttons"][button_name] = [screen_x, screen_y, color]
                    frame_xy["buttons"][button_name] = [frame_x, frame_y, color]

            # Convert interaction coordinates
            if "interactions" in frame:
                frame_xy["interactions"] = {}
                for interaction_name, interaction_data in frame["interactions"].items():
                    if len(interaction_data) == 2 and all(isinstance(x, (int, float)) for x in interaction_data):
                        # Single coordinate pair [x, y]
                        grid_x, grid_y = interaction_data
                        screen_x, screen_y = conv_grid_to_screen_coords(grid_x, grid_y)
                        frame_x, frame_y = conv_screen_to_frame_coords(screen_x, screen_y)

                        frame_copy["interactions"][interaction_name] = [screen_x, screen_y]
                        frame_xy["interactions"][interaction_name] = [frame_x, frame_y]

                    elif all(isinstance(item, list) and len(item) == 2 for item in interaction_data):
                        # List of coordinate pairs [[x,y], [x,y], ...]
                        screen_coords = []
                        frame_coords = []
                        for coord_pair in interaction_data:
                            grid_x, grid_y = coord_pair
                            screen_x, screen_y = conv_grid_to_screen_coords(grid_x, grid_y)
                            frame_x, frame_y = conv_screen_to_frame_coords(screen_x, screen_y)

                            screen_coords.append([screen_x, screen_y])
                            frame_coords.append([frame_x, frame_y])

                        frame_copy["interactions"][interaction_name] = screen_coords
                        frame_xy["interactions"][interaction_name] = frame_coords
                    else:
                        self.logger.error(f"Invalid interaction data for {interaction_name}: {interaction_data}")
                        import sys

                        sys.exit("Exiting due to invalid database")

            # Convert bbox coordinates
            if "bbox" in frame:
                frame_xy["bbox"] = {}
                for bbox_name, bbox_data in frame["bbox"].items():
                    if len(bbox_data) == 4 and all(isinstance(x, (int, float)) for x in bbox_data):
                        # Single bbox [x1, y1, x2, y2]
                        grid_x1, grid_y1, grid_x2, grid_y2 = bbox_data
                        screen_x1, screen_y1 = conv_grid_to_screen_coords(grid_x1, grid_y1)
                        screen_x2, screen_y2 = conv_grid_to_screen_coords(grid_x2, grid_y2)
                        frame_x1, frame_y1 = conv_screen_to_frame_coords(screen_x1, screen_y1)
                        frame_x2, frame_y2 = conv_screen_to_frame_coords(screen_x2, screen_y2)

                        frame_copy["bbox"][bbox_name] = [screen_x1, screen_y1, screen_x2, screen_y2]
                        frame_xy["bbox"][bbox_name] = [frame_x1, frame_y1, frame_x2, frame_y2]
                    else:
                        self.logger.error(f"Invalid bbox data for {bbox_name}: {bbox_data}")
                        import sys

                        sys.exit("Exiting due to invalid database")

            # Convert colors to tuples for pixel comparison
            frame_copy = self._convert_colors_to_tuples(frame_copy)

            # Add frame coordinates as additional key
            frame_copy["frame_xy"] = frame_xy
            frames_with_coords.append(frame_copy)

        frames_cache.parent.mkdir(exist_ok=True)
        json_str = json.dumps({"frames": frames_with_coords}, indent=2, separators=(",", ": "))

        # Compact 2-4 element arrays to a single line
        json_str = re.sub(
            r"\[\s*(-?\d+(?:\.\d+)?),?\s*\n\s*(-?\d+(?:\.\d+)?),?\s*\n\s*(-?\d+(?:\.\d+)?)(?:,?\s*\n\s*(-?\d+(?:\.\d+)?))?\s*\]",
            lambda m: "[" + ", ".join(filter(None, m.groups())) + "]",
            json_str,
        )

        with open(frames_cache, "w") as f:
            f.write(json_str)

        self.logger.info(
            f"Generated coordinate cache with screen coordinates as main and frame_xy as additional key at {frames_cache}"
        )

    # Public API methods
    def get_window_info(self) -> Optional[Dict[str, Any]]:
        """Get current window info (always fresh from cache)."""
        if self._cache["is_valid"]:
            return self._cache["window_info"]
        return None

    def get_frame_area(self) -> Optional[Dict[str, int]]:
        """Get frame area coordinates from cache (fast cached calculation)."""
        cached_area = self._cache.get("frame_area")
        if cached_area:
            return cached_area

        # Calculate and cache if not available
        calculated_area = self._calculate_frame_area()
        if calculated_area:
            self._cache["frame_area"] = calculated_area
            self._save_cache_to_file()

        return calculated_area

    def get_overlay_position(self) -> Optional[Dict[str, Any]]:
        """Get overlay position coordinates from cache (fast cached calculation)."""
        cached_position = self._cache.get("overlay_position")
        if cached_position:
            return cached_position

        # Calculate and cache if not available
        calculated_position = self._calculate_overlay_position()
        if calculated_position:
            self._cache["overlay_position"] = calculated_position
            self._save_cache_to_file()

        return calculated_position

    def get_pixel_size(self) -> Optional[float]:
        """Get pixel art grid size from cache (fast cached calculation)."""
        cached_size = self._cache.get("pixel_size")
        if cached_size:
            return cached_size

        # Calculate and cache if not available
        calculated_size = self._calculate_pixel_size()
        if calculated_size:
            self._cache["pixel_size"] = calculated_size
            self._save_cache_to_file()

        return calculated_size

    def is_window_available(self) -> bool:
        """Check if WidgetInc window is currently available."""
        return self._cache["is_valid"] and self._cache["window_info"] is not None

    def get_frame_data(self, frame_id: str) -> Optional[Dict[str, Any]]:
        """Get frame data by ID with colors converted to tuples."""
        # Load from frames.cache (or however you currently load frame data)
        frames_cache = Path(__file__).parent.parent.parent / "config" / "cache" / "frames.cache"

        try:
            with open(frames_cache, "r", encoding="utf-8") as f:
                frames_data = json.load(f)

            for frame in frames_data.get("frames", []):
                if frame.get("id") == frame_id:
                    return self._convert_colors_to_tuples(frame.copy())

            self.logger.warning(f"Frame {frame_id} not found in cache")
            return None

        except Exception as e:
            self.logger.error(f"Error loading frame data for {frame_id}: {e}")
            return None

    def get_monitor_info(self):
        """Public API: Get monitor info for the monitor containing the WidgetInc window."""
        cached = self._cache.get("monitor_info")
        if cached:
            return cached
        info = self._get_monitor_info()
        if info:
            self._cache["monitor_info"] = info
            self._save_cache_to_file()
        return info

    def get_leftmost_x_offset(self):
        """Public API: Get the x offset of the leftmost monitor (for multi-monitor screenshots)."""
        cached = self._cache.get("leftmost_x_offset")
        if cached is not None:
            return cached
        offset = self._get_leftmost_x_offset()
        self._cache["leftmost_x_offset"] = offset
        self._save_cache_to_file()
        return offset


# Global WindowManager instance
_window_manager = None


def get_cache_manager() -> CacheManager:
    """Get the global CacheManager instance."""
    global _window_manager
    if _window_manager is None:
        _window_manager = CacheManager()
    return _window_manager
