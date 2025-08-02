"""
Window Utilities - WindowManager API Functions

This module provides essential utility functions that use the WindowManager class.
All functions are backed by the WindowManager's proactive caching system.
"""

import logging
import pyautogui
import screeninfo
import time
from PIL import ImageGrab
from typing import Any, Dict, Tuple

from .cache_manager import get_cache_manager, PIXEL_ART_GRID_WIDTH, PIXEL_ART_GRID_HEIGHT

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
        window_manager = get_cache_manager()
        overlay_position = window_manager.get_overlay_position()

        if not overlay_position:
            return (100, 100, 100)  # Fallback

        return (overlay_position["x"], overlay_position["y"], overlay_position["available_height"])

    except Exception as e:
        logger.error(f"Error calculating overlay position: {e}")
        return (100, 100, 100)


def grid_to_screen_coords(grid_x: int, grid_y: int) -> Tuple[int, int]:
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
        window_manager = get_cache_manager()
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


def grid_to_screenshot_coords(grid_x: int, grid_y: int, offset_x=2560) -> Tuple[int, int]:
    """
    Convert grid coordinates to screenshot coordinates.

    Args:
        grid_x: Grid X coordinate (0 to 191)
        grid_y: Grid Y coordinate (0 to 127)

    Returns:
        Tuple of (screenshot_x, screenshot_y) coordinates
    """
    screen_x, screen_y = grid_to_screen_coords(grid_x, grid_y)
    # Adjust for screenshot offset
    return (screen_x + offset_x, screen_y)


def get_pixel_color(coords):
    x, y = coords
    return pyautogui.pixel(x, y)


def get_grid_color(grid):
    coords = grid_to_screen_coords(grid[0], grid[1])
    return get_pixel_color(coords)


def get_fill_by_color(start_point, empty_color, filled_colors: list):
    """
    Scan vertically from start_point, tracking empty and filled color pixels,
    and calculate the percentage of filled pixels between the top and bottom bounds.
    """
    screenshot = ImageGrab.grab(bbox=(-2560, 0, 0, 1440), all_screens=True)
    offset_x = get_leftmost_x_offset()
    x0 = start_point[0] + offset_x
    y0 = start_point[1]
    width, height = screenshot.size

    # Find top bound
    y_top = y0
    while y_top > 0:
        pixel = screenshot.getpixel((x0, y_top))
        if pixel != empty_color and pixel not in filled_colors:
            break
        y_top -= 1
    y_top += 1

    # Find bottom bound
    y_bottom = y0
    while y_bottom < height - 1:
        pixel = screenshot.getpixel((x0, y_bottom))
        if pixel != empty_color and pixel not in filled_colors:
            break
        y_bottom += 1
    y_bottom -= 1

    # Scan from top to bottom, count empty and filled
    empty_count = 0
    filled_count = 0
    for y in range(y_top, y_bottom + 1):
        pixel = screenshot.getpixel((x0, y))
        if pixel == empty_color:
            empty_count += 1
        elif pixel in filled_colors:
            filled_count += 1

    total = empty_count + filled_count
    percent_filled = (filled_count / total * 100) if total > 0 else 0

    print(
        f"Top: {y_top - offset_x}, Bottom: {y_bottom - offset_x}, Filled: {filled_count}, Empty: {empty_count}, Percent filled: {percent_filled:.2f}%"
    )
    return percent_filled


def get_leftmost_x_offset():
    window_manager = get_cache_manager()
    return window_manager.get_leftmost_x_offset()


def get_monitor_screenshot():
    """
    Screenshot the monitor containing the WidgetInc window using ImageGrab.grab.
    Returns a PIL Image or None if monitor not found.
    """
    window_manager = get_cache_manager()
    monitor_info = window_manager.get_monitor_info()
    if not monitor_info:
        logger.warning("No monitor info available for WidgetInc window.")
        return None
    x = monitor_info["x"]
    y = monitor_info["y"]
    width = monitor_info["width"]
    height = monitor_info["height"]
    bbox = (x, y, x + width, y + height)
    # all_screens=True ensures correct multi-monitor capture
    return ImageGrab.grab(bbox=bbox, all_screens=True)


def grid_to_playable_area_coords(grid_x: int, grid_y: int) -> Tuple[int, int]:
    """
    Convert grid coordinates to playable area coordinates.

    Args:
        grid_x: Grid X coordinate (0 to 191)
        grid_y: Grid Y coordinate (0 to 127)

    Returns:
        Tuple of (playable_area_x, playable_area_y) coordinates
    """
    window_manager = get_cache_manager()
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

    # Convert to playable area coordinates (relative to playable area, not screen)
    playable_area_x = int(pixel_x)
    playable_area_y = int(pixel_y)

    return (playable_area_x, playable_area_y)
