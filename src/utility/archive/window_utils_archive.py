"""
Archive of unused window utility functions.

These functions were previously used by the tracker app or are legacy functions
that are no longer needed in the main automation overlay application.

Archived functions:
- is_window_valid: Window handle validation (unused)
- get_client_area_coordinates: Legacy window client area calculation (unused)
- calculate_playable_area_percentages: Mouse position percentages (tracker app only)
- calculate_pixel_art_grid_position: Screen to grid conversion (tracker app only)
"""

import logging
from typing import Any, Dict, Optional, Tuple

try:
    import win32gui

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

from ..window_utils import PIXEL_ART_GRID_WIDTH, PIXEL_ART_GRID_HEIGHT, calculate_pixel_size

logger = logging.getLogger(__name__)


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
        return bool(win32gui.IsWindow(hwnd)) and bool(win32gui.IsWindowVisible(hwnd))
    except Exception:
        return False


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


def calculate_playable_area_percentages(x: int, y: int, playable_area: Dict[str, int]) -> Dict[str, Any]:
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

            # Calculate grid position (0-based)
            grid_x = int(rel_x / pixel_size)
            grid_y = int(rel_y / pixel_size)

            # Clamp to valid range (0 to grid_width-1, 0 to grid_height-1)
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
