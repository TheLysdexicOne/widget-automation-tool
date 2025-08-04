"""
Window Utilities - WindowManager API Functions

This module provides essential utility functions that use the WindowManager class.
All functions are backed by the WindowManager's proactive caching system.
"""

import logging
import os
import numpy as np
import pyautogui
from PIL import Image, ImageGrab
from typing import Any, Dict, List, Optional, Tuple

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


def get_bbox_screenshot(bbox: Tuple[int, int, int, int]):
    """
    Screenshot a specific bounding box using ImageGrab.grab.

    Args:
        bbox: Tuple of (x, y, width, height) coordinates

    Returns:
        PIL Image of the specified bounding box
    """
    x, y, width, height = bbox
    return ImageGrab.grab(bbox=(x, y, x + width, y + height), all_screens=True)


def screen_to_screenshot_coords(screen_x: int, screen_y: int) -> Tuple[int, int]:
    """
    Convert screen coordinates to screenshot coordinates.

    Args:
        screen_x: Screen X coordinate
        screen_y: Screen Y coordinate

    Returns:
        Tuple of (screenshot_x, screenshot_y) coordinates
    """
    window_manager = get_cache_manager()
    leftmost_x = window_manager.get_leftmost_x_offset()

    # Adjust screen coordinates by the leftmost monitor offset
    screenshot_x = screen_x + leftmost_x
    screenshot_y = screen_y  # Y typically doesn't need offset for single-row monitors

    return (screenshot_x, screenshot_y)


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


def grid_to_frame_coords(grid_x: int, grid_y: int) -> tuple[int, int]:
    """Convert grid coordinates to frame-relative coordinates for screenshot analysis."""
    # Use the reliable grid_to_screen_coords first
    screen_x, screen_y = grid_to_screen_coords(grid_x, grid_y)
    frame_x, frame_y = screen_to_frame_coords(screen_x, screen_y)

    return (frame_x, frame_y)


def frame_to_screen_coords(frame_x: int, frame_y: int) -> Tuple[int, int]:
    """
    Convert frame-relative coordinates to absolute screen coordinates.

    Args:
        frame_x: X coordinate relative to the frame area
        frame_y: Y coordinate relative to the frame area

    Returns:
        Tuple of (screen_x, screen_y) coordinates
    """
    window_manager = get_cache_manager()
    frame_area = window_manager.get_frame_area()
    if not frame_area:
        logger.warning("No valid frame area for frame to screen conversion")
        return (0, 0)
    screen_x = frame_area["x"] + frame_x
    screen_y = frame_area["y"] + frame_y
    return (screen_x, screen_y)


def get_box_with_border(start_point, border_color, screenshot=None):
    """
    Find the bounding box of a region starting from start_point using color-based edge detection.

    Args:
        start_point: *FRAME coordinates* (x, y) to start scanning from
        border_color: RGB tuple for border color

    Returns:
        bbox: Tuple (left, top, right, bottom) representing the detected box bounds
    """
    if screenshot is None:
        screenshot = get_frame_screenshot()
    if not screenshot:
        return (0, 0, 0, 0)

    width, height = screenshot.size
    x0, y0 = start_point

    # Find left edge
    x = x0
    # Scan left until we find the border
    while x > 0 and screenshot.getpixel((x, y0)) != border_color:
        x -= 1
    # Continue scanning left until border is no longer found
    while x > 0 and screenshot.getpixel((x, y0)) == border_color:
        x -= 1
    left = x + 1

    # Find right edge
    x = x0
    while x < width - 1 and screenshot.getpixel((x, y0)) != border_color:
        x += 1
    while x < width - 1 and screenshot.getpixel((x, y0)) == border_color:
        x += 1
    right = x - 1

    # Find top edge
    y = y0
    while y > 0 and screenshot.getpixel((x0, y)) != border_color:
        y -= 1
    while y > 0 and screenshot.getpixel((x0, y)) == border_color:
        y -= 1
    top = y + 1

    # Find bottom edge
    y = y0
    while y < height - 1 and screenshot.getpixel((x0, y)) != border_color:
        y += 1
    while y < height - 1 and screenshot.getpixel((x0, y)) == border_color:
        y += 1
    bottom = y - 1

    bbox = (left, top, right, bottom)
    logger.debug(f"Detected bounding box: {bbox} starting from {start_point}")
    return bbox


def get_box_no_border(
    approx_box: tuple[int, int, int, int],
    allowed_colors: list[tuple[int, int, int]],
    screenshot: Optional[Image.Image] = None,
):
    if screenshot is None:
        screenshot = get_frame_screenshot()

    # O(1) color lookup instead of O(n)
    allowed_colors_set = set(allowed_colors)

    # Numpy array access is much faster than PIL getpixel()
    img_array = np.array(screenshot)
    height, width = img_array.shape[:2]

    x1, y1, x2, y2 = approx_box

    def is_allowed_color(x, y):
        if 0 <= x < width and 0 <= y < height:
            # Note: numpy uses [y, x] indexing, PIL uses (x, y)
            pixel = tuple(img_array[y, x])
            return pixel in allowed_colors_set
        return False

    def test_vertical_line(x):
        if not (0 <= x < width):
            return False
        vertical_pixels = img_array[y1 : y2 + 1, x]
        for pixel in vertical_pixels:
            if tuple(pixel) not in allowed_colors_set:
                return False
        return True

    def test_horizontal_line(y):
        if not (0 <= y < height):
            return False
        horizontal_pixels = img_array[y, x1 : x2 + 1]
        for pixel in horizontal_pixels:
            if tuple(pixel) not in allowed_colors_set:
                return False
        return True

    # Initial validation
    if not (
        test_vertical_line(x1) and test_horizontal_line(y1) and test_vertical_line(x2) and test_horizontal_line(y2)
    ):
        raise ValueError("Initial box test failed...")

    def get_left_edge(x1):
        x = x1
        while x > 0 and is_allowed_color(x, y1):
            x -= min(8, x)  # Adaptive step size
        while x < x1 and not is_allowed_color(x, y1):
            x += 1
        while x <= x1 and not test_vertical_line(x):
            x += 1
        return x

    def get_right_edge(x2):
        x = x2
        while x < width - 1 and is_allowed_color(x, y1):
            x += min(8, width - 1 - x)
        while x > x2 and not is_allowed_color(x, y1):
            x -= 1
        while x >= x2 and not test_vertical_line(x):
            x -= 1
        return x

    def get_top_edge(y1):
        y = y1
        while y > 0 and is_allowed_color(x1, y):
            y -= min(8, y)
        while y < y1 and not is_allowed_color(x1, y):
            y += 1
        while y <= y1 and not test_horizontal_line(y):
            y += 1
        return y

    def get_bottom_edge(y2):
        y = y2
        while y < height - 1 and is_allowed_color(x1, y):
            y += min(8, height - 1 - y)
        while y > y2 and not is_allowed_color(x1, y):
            y -= 1
        while y >= y2 and not test_horizontal_line(y):
            y -= 1
        return y

    return (get_left_edge(x1), get_top_edge(y1), get_right_edge(x2), get_bottom_edge(y2))
