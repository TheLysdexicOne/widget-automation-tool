"""
Window Utilities - WindowManager API Functions

This module provides essential utility functions that use the WindowManager class.
All functions are backed by the WindowManager's proactive caching system.
"""

import logging
import pyautogui
from typing import Any, Dict, Tuple

from .cache_manager import get_window_manager, PIXEL_ART_GRID_WIDTH, PIXEL_ART_GRID_HEIGHT

logger = logging.getLogger(__name__)


def calculate_overlay_position(window_info: Dict[str, Any]) -> Tuple[int, int, int]:
    """
    Calculate overlay position in top-right corner of target window.

    Args:
        window_info: Window information (unused, kept for compatibility)

    Returns:
        Tuple of (x, y, available_height) coordinates
    """
    try:
        # Use WindowManager to get cached overlay position
        window_manager = get_window_manager()
        overlay_position = window_manager.get_overlay_position()

        if not overlay_position:
            return (100, 100, 100)  # Fallback

        return (overlay_position["x"], overlay_position["y"], overlay_position["available_height"])

    except Exception as e:
        logger.error(f"Error calculating overlay position: {e}")
        return (100, 100, 100)


def grid_to_screen_coordinates(grid_x: int, grid_y: int) -> Tuple[int, int]:
    """
    Convert grid coordinates to screen coordinates for clicking.

    Takes grid coordinates and returns the center pixel of that grid cell in screen coordinates.

    Args:
        grid_x: Grid X coordinate (0 to 191)
        grid_y: Grid Y coordinate (0 to 127)

    Returns:
        Tuple of (screen_x, screen_y) coordinates for clicking
    """
    try:
        window_manager = get_window_manager()
        playable_area = window_manager.get_playable_area()
        pixel_size = window_manager.get_pixel_size()

        if not playable_area or not pixel_size:
            logger.warning("No valid playable area or pixel size for grid conversion")
            return (0, 0)

        # Clamp grid coordinates to valid range
        grid_x = max(0, min(PIXEL_ART_GRID_WIDTH - 1, grid_x))
        grid_y = max(0, min(PIXEL_ART_GRID_HEIGHT - 1, grid_y))

        # Calculate pixel center within the grid cell
        pixel_x = (grid_x + 0.5) * pixel_size
        pixel_y = (grid_y + 0.5) * pixel_size

        # Convert to screen coordinates
        screen_x = int(playable_area["x"] + pixel_x)
        screen_y = int(playable_area["y"] + pixel_y)

        return (screen_x, screen_y)

    except Exception as e:
        logger.error(f"Error converting grid to screen coordinates: {e}")
        return (0, 0)


def get_pixel_color(coords):
    x, y = coords
    return pyautogui.pixel(x, y)


def get_grid_color(grid):
    coords = grid_to_screen_coordinates(grid[0], grid[1])
    return get_pixel_color(coords)
