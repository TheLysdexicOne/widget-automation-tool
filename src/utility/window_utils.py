"""
Window positioning and client area utilities.
Centralizes window manipulation logic following KISS principles.
"""

import logging
from typing import Tuple, Optional

try:
    import win32gui
    import win32process
    import psutil

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

logger = logging.getLogger(__name__)


def get_client_area_coordinates(window) -> Optional[Tuple[int, int, int, int]]:
    """
    Get client area coordinates (content area without title bar/borders).

    Args:
        window: Window object with _hWnd attribute or title

    Returns:
        Tuple of (x, y, width, height) or None if failed
    """
    if not WIN32_AVAILABLE:
        logger.warning(
            "win32gui not available - falling back to full window coordinates"
        )
        return None

    try:
        # Get window handle
        hwnd = None
        if hasattr(window, "_hWnd"):
            hwnd = window._hWnd
        else:
            # Fallback: find WidgetInc.exe window
            hwnd = _find_widgetinc_window()

        if not hwnd:
            return None

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


def _find_widgetinc_window() -> Optional[int]:
    """Find WidgetInc.exe window handle."""
    try:
        for proc in psutil.process_iter(["pid", "name"]):
            if proc.info["name"] == "WidgetInc.exe":
                pid = proc.info["pid"]

                def enum_windows_proc(hwnd, lParam):
                    if win32gui.IsWindowVisible(hwnd):
                        _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                        if found_pid == pid:
                            lParam.append(hwnd)
                    return True

                windows = []
                win32gui.EnumWindows(enum_windows_proc, windows)
                if windows:
                    return windows[0]

    except Exception as e:
        logger.error(f"Error finding WidgetInc window: {e}")

    return None


def calculate_overlay_position(
    window,
    overlay_width: int,
    overlay_height: int,
    offset_x: int = -8,
    offset_y: int = 40,
) -> Tuple[int, int]:
    """
    Calculate overlay position in top-right corner of target window.

    Args:
        window: Target window object
        overlay_width: Width of overlay
        overlay_height: Height of overlay
        offset_x: X offset from right edge (negative = left of edge)
        offset_y: Y offset from top edge

    Returns:
        Tuple of (x, y) coordinates
    """
    # Try client area coordinates first
    client_coords = get_client_area_coordinates(window)

    if client_coords:
        client_x, client_y, client_width, client_height = client_coords
        target_x = client_x + client_width - overlay_width + offset_x
        target_y = client_y + offset_y
    else:
        # Fallback to full window coordinates
        target_x = window.left + window.width - overlay_width + offset_x
        target_y = window.top + offset_y

    return (target_x, target_y)
