"""
Window Utilities - WindowManager API Functions

This module provides essential utility functions that use the WindowManager class.
All functions are backed by the WindowManager's proactive caching system.
"""

import logging
import pyautogui
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
        frame_area = window_manager.get_frame_area()
        pixel_size = window_manager.get_pixel_size()

        if not frame_area or not pixel_size:
            logger.warning("No valid frame area or pixel size for grid conversion")
            return (0, 0)

        # Clamp grid coordinates to valid range
        grid_x = max(0, min(PIXEL_ART_GRID_WIDTH - 1, grid_x))
        grid_y = max(0, min(PIXEL_ART_GRID_HEIGHT - 1, grid_y))

        # Calculate pixel center within the grid cell
        pixel_x = (grid_x + 0.5) * pixel_size
        pixel_y = (grid_y + 0.5) * pixel_size

        # Convert to screen coordinates
        screen_x = int(frame_area["x"] + pixel_x)
        screen_y = int(frame_area["y"] + pixel_y)

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


def get_vertical_bar_data(start_point, empty_color, filled_colors: tuple):
    """
    Analyze vertical bar from start_point using PIL-based bounds detection.
    Returns both bounds and fill percentage in a single pass.

    Args:
        start_point: Screen coordinates (x, y) to start scanning from
        empty_color: RGB tuple for empty vertical bar color
        filled_colors: List of RGB tuples for filled vertical bar colors

    Returns:
        Dict with keys: 'top', 'bottom', 'height', 'percent_filled'
    """

    screenshot = get_monitor_screenshot()
    if not screenshot:
        return {"top": 0, "bottom": 0, "height": 0, "percent_filled": 0}

    frame_x, frame_y = screen_to_frame_coords(start_point[0], start_point[1])
    frame_x, frame_y = start_point[0], start_point[1]  # Use original coordinates
    width, height = screenshot.size

    filled_count = 0

    # Find top bound and count filled pixels going up
    y_top = frame_y
    while y_top > 0:
        pixel = screenshot.getpixel((frame_x, y_top))
        if pixel != empty_color and pixel not in filled_colors:
            break
        if pixel in filled_colors:
            filled_count += 1
        y_top -= 1
    y_top += 1

    # Find bottom bound and count filled pixels going down
    y_bottom = frame_y
    while y_bottom < height - 1:
        pixel = screenshot.getpixel((frame_x, y_bottom))
        if pixel != empty_color and pixel not in filled_colors:
            break
        if pixel in filled_colors:
            filled_count += 1
        y_bottom += 1
    y_bottom -= 1

    # Subtract the start pixel if it was counted twice
    start_pixel = screenshot.getpixel((frame_x, frame_y))
    if start_pixel in filled_colors:
        filled_count -= 1

    box_height = y_bottom - y_top + 1
    percent_filled = (filled_count / box_height * 100) if box_height > 0 else 0

    # # Visualize bounds with white line
    # screenshot_copy = screenshot.copy()
    # for y in range(y_top, y_bottom + 1):
    #     if 0 <= frame_x < width and 0 <= y < height:
    #         screenshot_copy.putpixel((frame_x, y), (255, 255, 255))  # White line

    # # Show the visualization
    # screenshot_copy.show()

    return {"top": y_top, "bottom": y_bottom, "height": box_height, "percent_filled": percent_filled}


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


def get_frame_screenshot():
    """
    Screenshot just the frame area using ImageGrab.grab.
    Returns a PIL Image or None if frame area not found.
    """
    window_manager = get_cache_manager()
    frame_area = window_manager.get_frame_area()
    if not frame_area:
        logger.warning("No frame area available for screenshot.")
        return None
    x = frame_area["x"]
    y = frame_area["y"]
    width = frame_area["width"]
    height = frame_area["height"]
    bbox = (x, y, x + width, y + height)
    # all_screens=True ensures correct multi-monitor capture
    return ImageGrab.grab(bbox=bbox, all_screens=True)


def grid_to_frame_coords(grid_x: int, grid_y: int) -> Tuple[int, int]:
    """
    Convert grid coordinates to frame area coordinates.

    Args:
        grid_x: Grid X coordinate (0 to 191)
        grid_y: Grid Y coordinate (0 to 127)

    Returns:
        Tuple of (frame_area_x, frame_area_y) coordinates
    """
    window_manager = get_cache_manager()
    frame_area = window_manager.get_frame_area()
    pixel_size = window_manager.get_pixel_size()

    if not frame_area or not pixel_size:
        logger.warning("No valid frame area or pixel size for grid conversion")
        return (0, 0)

    # Clamp grid coordinates to valid range
    grid_x = max(0, min(PIXEL_ART_GRID_WIDTH - 1, grid_x))
    grid_y = max(0, min(PIXEL_ART_GRID_HEIGHT - 1, grid_y))

    # Calculate pixel center within the grid cell
    pixel_x = (grid_x + 0.5) * pixel_size
    pixel_y = (grid_y + 0.5) * pixel_size

    # Convert to frame area coordinates (relative to frame area, not screen)
    frame_area_x = int(pixel_x)
    frame_area_y = int(pixel_y)

    return (frame_area_x, frame_area_y)


def screen_to_frame_coords(screen_x: int, screen_y: int) -> Tuple[int, int]:
    """
    Convert screen coordinates to frame area coordinates.

    Takes screen coordinates and returns coordinates relative to the frame area.

    Args:
        screen_x: Screen X coordinate
        screen_y: Screen Y coordinate

    Returns:
        Tuple of (frame_area_x, frame_area_y) coordinates relative to frame area
    """
    window_manager = get_cache_manager()
    frame_area = window_manager.get_frame_area()

    if not frame_area:
        logger.warning("No valid frame area for screen to frame area conversion")
        return (0, 0)

    # Convert screen coordinates to frame area coordinates
    frame_area_x = screen_x - frame_area["x"]
    frame_area_y = screen_y - frame_area["y"]

    # Clamp to frame area bounds
    frame_area_x = max(0, min(frame_area["width"] - 1, frame_area_x))
    frame_area_y = max(0, min(frame_area["height"] - 1, frame_area_y))

    return (frame_area_x, frame_area_y)
