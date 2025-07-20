"""
Window Utilities - Comprehensive Window Detection and Coordinate Logic

This module provides all window-related functionality including:
- Target window detection (process finding, window finding)
- Window information gathering (coordinates, dimensions)
- Playable area calculations (3:2 aspect ratio)
- Overlay positioning calculations
- Mouse position analysis within playable areas

Consolidates functionality from legacy window_utils.py for KISS principles.
Used by main overlay, tracker app, and future mouse tracking.
"""

import logging
from typing import Optional, Dict, Any, Tuple
import time

try:
    import win32gui
    import win32process
    import psutil

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

logger = logging.getLogger(__name__)

# Process cache for performance optimization
_process_cache = {
    "pid": None,
    "timestamp": 0,
    "cache_duration": 2.0,
}  # Cache for 2 seconds

# Pixel Art Grid Constants - Single Source of Truth
# These define the background pixel grid dimensions for the WidgetInc game
PIXEL_ART_GRID_WIDTH = 192  # Background pixels horizontally
PIXEL_ART_GRID_HEIGHT = 128  # Background pixels vertically


def calculate_pixel_size(playable_width: int, playable_height: int) -> float:
    """
    Calculate pixel size for pixel art grid scaling.

    This is the single source of truth for pixel size calculation.
    Returns pixels per background grid unit, ensuring perfect squares.

    Args:
        playable_width: Width of playable area in pixels
        playable_height: Height of playable area in pixels

    Returns:
        Pixel size (pixels per background grid unit)
    """
    if playable_width <= 0 or playable_height <= 0:
        return 0.0

    pixel_size_x = playable_width / PIXEL_ART_GRID_WIDTH
    pixel_size_y = playable_height / PIXEL_ART_GRID_HEIGHT

    # Use smaller dimension to ensure perfect square pixels
    return min(pixel_size_x, pixel_size_y)


def find_target_process(target_process_name: str = "WidgetInc.exe") -> Optional[int]:
    """
    Find the target process and return its PID.
    Optimized for performance with caching and faster Windows-specific enumeration.

    Args:
        target_process_name: Name of the process to find

    Returns:
        PID of the process or None if not found
    """
    if not WIN32_AVAILABLE:
        return None

    # Check cache first
    current_time = time.time()
    if (
        _process_cache["pid"] is not None
        and current_time - _process_cache["timestamp"]
        < _process_cache["cache_duration"]
    ):
        # Verify cached PID is still valid
        try:
            proc = psutil.Process(_process_cache["pid"])
            if proc.is_running() and proc.name() == target_process_name:
                return _process_cache["pid"]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Cached process is gone, invalidate cache
            _process_cache["pid"] = None

    try:
        # Ultra-fast approach: Use win32gui.EnumWindows to find WidgetInc windows directly
        # This skips process enumeration entirely and goes straight to windows
        target_pids = []

        def enum_windows_callback(hwnd, _):
            try:
                # Get window title first (fastest check)
                title = win32gui.GetWindowText(hwnd)
                if "WidgetInc" in title and win32gui.IsWindowVisible(hwnd):
                    # Only get PID if the window title matches
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    if pid not in target_pids:
                        target_pids.append(pid)
            except:
                pass  # Skip problematic windows
            return True

        # Enumerate windows looking for WidgetInc
        win32gui.EnumWindows(enum_windows_callback, None)

        # Verify we found a valid process
        for pid in target_pids:
            try:
                proc = psutil.Process(pid)
                if proc.is_running() and proc.name() == target_process_name:
                    # Cache the result
                    _process_cache["pid"] = pid
                    _process_cache["timestamp"] = current_time
                    return pid
            except:
                continue

        # Fallback to traditional method if window enumeration fails
        logger.debug("Window enumeration failed, falling back to process enumeration")
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                proc_info = proc.info
                if proc_info["name"] == target_process_name and proc.is_running():
                    _process_cache["pid"] = proc_info["pid"]
                    _process_cache["timestamp"] = current_time
                    return proc_info["pid"]
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception:
                continue

    except Exception as e:
        logger.error(f"Error finding target process {target_process_name}: {e}")

    return None


def find_window_by_pid(pid: int) -> Optional[int]:
    """
    Find window handle by process ID.

    Args:
        pid: Process ID to search for

    Returns:
        Window handle (HWND) or None if not found
    """
    if not WIN32_AVAILABLE:
        return None

    def enum_windows_proc(hwnd, windows):
        try:
            _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
            if window_pid == pid and win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "WidgetInc" in title:
                    windows.append(hwnd)
        except:
            pass
        return True

    windows = []
    win32gui.EnumWindows(enum_windows_proc, windows)
    return windows[0] if windows else None


def get_window_info(hwnd: int) -> Optional[Dict[str, Any]]:
    """
    Get comprehensive window information.

    Args:
        hwnd: Window handle

    Returns:
        Dictionary with window information or None if failed
    """
    if not WIN32_AVAILABLE or not hwnd:
        return None

    try:
        # Get basic window info
        title = win32gui.GetWindowText(hwnd)
        window_rect = win32gui.GetWindowRect(hwnd)
        client_rect = win32gui.GetClientRect(hwnd)

        # Calculate client area screen position
        client_screen_pos = win32gui.ClientToScreen(hwnd, (0, 0))

        return {
            "hwnd": hwnd,
            "title": title,
            "window_rect": window_rect,  # (left, top, right, bottom)
            "client_rect": client_rect,  # (left, top, right, bottom) relative to window
            "client_screen_pos": client_screen_pos,  # (x, y) absolute screen position
            "window_width": window_rect[2] - window_rect[0],
            "window_height": window_rect[3] - window_rect[1],
            "client_width": client_rect[2] - client_rect[0],
            "client_height": client_rect[3] - client_rect[1],
            "client_x": client_screen_pos[0],
            "client_y": client_screen_pos[1],
        }

    except Exception as e:
        logger.error(f"Error getting window info for HWND {hwnd}: {e}")
        return None


def calculate_playable_area(window_info: Dict[str, Any]) -> Optional[Dict[str, int]]:
    """
    Calculate the playable area coordinates (3:2 aspect ratio centered in client area).

    Args:
        window_info: Window information from get_window_info()

    Returns:
        Dictionary with playable area coordinates or None if failed
    """
    if not window_info:
        return None

    try:
        client_x = window_info["client_x"]
        client_y = window_info["client_y"]
        client_width = window_info["client_width"]
        client_height = window_info["client_height"]

        # Calculate 3:2 aspect ratio area centered in client
        target_ratio = 3.0 / 2.0
        client_ratio = client_width / client_height if client_height else 1

        if client_ratio > target_ratio:
            # Client is wider than 3:2 - fit height, center width
            playable_height = client_height
            playable_width = int(playable_height * target_ratio)
            playable_x = client_x + (client_width - playable_width) // 2
            playable_y = client_y
        else:
            # Client is taller than 3:2 - fit width, center height
            playable_width = client_width
            playable_height = int(playable_width / target_ratio)
            playable_x = client_x
            playable_y = client_y + (client_height - playable_height) // 2

        return {
            "x": playable_x,
            "y": playable_y,
            "width": playable_width,
            "height": playable_height,
        }

    except Exception as e:
        logger.error(f"Error calculating playable area: {e}")
        return None


def find_target_window(
    target_process_name: str = "WidgetInc.exe",
) -> Optional[Dict[str, Any]]:
    """
    Complete target window detection - finds process, window, and calculates coordinates.

    Args:
        target_process_name: Name of the process to find

    Returns:
        Complete target information including window info and playable area, or None if not found
    """
    # Find the process
    pid = find_target_process(target_process_name)
    if not pid:
        return None

    # Find the window
    hwnd = find_window_by_pid(pid)
    if not hwnd:
        return None

    # Get window information
    window_info = get_window_info(hwnd)
    if not window_info:
        return None

    # Calculate playable area
    playable_area = calculate_playable_area(window_info)

    return {
        "pid": pid,
        "window_info": window_info,
        "playable_area": playable_area,
    }


def is_window_valid(hwnd: int) -> bool:
    """
    Check if window handle is still valid.

    Args:
        hwnd: Window handle to check

    Returns:
        True if window is valid and visible, False otherwise
    """
    if not WIN32_AVAILABLE or not hwnd:
        return False

    try:
        return win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd)
    except:
        return False


def calculate_overlay_position(
    window_info: Dict[str, Any],
    overlay_width: int,
    overlay_height: int,
    offset_x: int = -8,
    offset_y: int = 40,
) -> Tuple[int, int]:
    """
    Calculate overlay position in top-right corner of target window.

    Args:
        window_info: Window information from get_window_info()
        overlay_width: Width of overlay
        overlay_height: Height of overlay
        offset_x: X offset from right edge (negative = left of edge)
        offset_y: Y offset from top edge

    Returns:
        Tuple of (x, y) coordinates
    """
    try:
        # Use client area coordinates from window_info
        client_x = window_info["client_x"]
        client_y = window_info["client_y"]
        client_width = window_info["client_width"]
        client_height = window_info["client_height"]

        target_x = client_x + client_width - overlay_width + offset_x
        target_y = client_y + offset_y

        return (target_x, target_y)

    except Exception as e:
        logger.error(f"Error calculating overlay position: {e}")
        # Fallback to basic positioning
        return (100, 100)


def get_client_area_coordinates(hwnd: int) -> Optional[Tuple[int, int, int, int]]:
    """
    Legacy compatibility function - get client area coordinates for a window handle.

    Args:
        hwnd: Window handle

    Returns:
        Tuple of (x, y, width, height) or None if failed
    """
    if not WIN32_AVAILABLE or not hwnd:
        return None

    try:
        # Get client rectangle (content area without decorations)
        client_rect = win32gui.GetClientRect(hwnd)
        client_screen_pos = win32gui.ClientToScreen(hwnd, (0, 0))

        # Calculate dimensions
        client_width = client_rect[2] - client_rect[0]
        client_height = client_rect[3] - client_rect[1]
        client_x, client_y = client_screen_pos

        return (client_x, client_y, client_width, client_height)

    except Exception as e:
        logger.warning(f"Client area detection failed: {e}")
        return None


def calculate_playable_area_percentages(
    x: int, y: int, playable_area: Dict[str, int]
) -> Dict[str, Any]:
    """
    Calculate percentage position within playable area - useful for mouse tracking.

    Args:
        x: Screen x coordinate
        y: Screen y coordinate
        playable_area: Playable area dictionary with x, y, width, height

    Returns:
        Dictionary with inside_playable bool and x_percent, y_percent if inside
    """
    try:
        if not playable_area:
            return {"inside_playable": False, "x_percent": 0.0, "y_percent": 0.0}

        px = playable_area.get("x", 0)
        py = playable_area.get("y", 0)
        pw = playable_area.get("width", 0)
        ph = playable_area.get("height", 0)

        if px <= x <= px + pw and py <= y <= py + ph:
            # Calculate percentage within playable area
            x_percent = ((x - px) / pw) * 100
            y_percent = ((y - py) / ph) * 100

            return {
                "inside_playable": True,
                "x_percent": x_percent,
                "y_percent": y_percent,
                "playable_area": playable_area,
            }
        else:
            return {"inside_playable": False, "x_percent": 0.0, "y_percent": 0.0}

    except Exception as e:
        logger.error(f"Error calculating playable area percentages: {e}")
        return {"inside_playable": False, "x_percent": 0.0, "y_percent": 0.0}


def calculate_pixel_art_grid_position(
    x: int,
    y: int,
    playable_area: Dict[str, int],
    grid_width: int = PIXEL_ART_GRID_WIDTH,
    grid_height: int = PIXEL_ART_GRID_HEIGHT,
) -> Dict[str, Any]:
    """
    Calculate pixel art grid position for a screen coordinate.

    Args:
        x: Screen x coordinate
        y: Screen y coordinate
        playable_area: Playable area dictionary with x, y, width, height
        grid_width: Background pixel grid width (default 192)
        grid_height: Background pixel grid height (default 128)

    Returns:
        Dictionary with grid position and detailed pixel art information
    """
    try:
        if not playable_area:
            return {
                "inside_playable": False,
                "grid_x": 0,
                "grid_y": 0,
                "pixel_size": 0.0,
                "x_percent": 0.0,
                "y_percent": 0.0,
            }

        px = playable_area.get("x", 0)
        py = playable_area.get("y", 0)
        pw = playable_area.get("width", 0)
        ph = playable_area.get("height", 0)

        if px <= x <= px + pw and py <= y <= py + ph:
            # Calculate pixel size using consolidated function
            pixel_size = calculate_pixel_size(pw, ph)

            # Calculate relative position within playable area
            rel_x = x - px
            rel_y = y - py

            # Calculate grid position (which background pixel we're in)
            grid_x = int(rel_x / pixel_size)
            grid_y = int(rel_y / pixel_size)

            # Clamp to grid bounds
            grid_x = max(0, min(grid_width - 1, grid_x))
            grid_y = max(0, min(grid_height - 1, grid_y))

            # Calculate percentage within playable area
            x_percent = (rel_x / pw) * 100
            y_percent = (rel_y / ph) * 100

            return {
                "inside_playable": True,
                "grid_x": grid_x,
                "grid_y": grid_y,
                "pixel_size": pixel_size,
                "x_percent": x_percent,
                "y_percent": y_percent,
                "playable_area": playable_area,
                "grid_dimensions": {"width": grid_width, "height": grid_height},
            }
        else:
            return {
                "inside_playable": False,
                "grid_x": 0,
                "grid_y": 0,
                "pixel_size": 0.0,
                "x_percent": 0.0,
                "y_percent": 0.0,
            }

    except Exception as e:
        logger.error(f"Error calculating pixel art grid position: {e}")
        return {
            "inside_playable": False,
            "grid_x": 0,
            "grid_y": 0,
            "pixel_size": 0.0,
            "x_percent": 0.0,
            "y_percent": 0.0,
        }
