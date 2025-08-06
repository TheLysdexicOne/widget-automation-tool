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

from .cache_manager import get_cache_manager

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


def get_leftmost_x_offset():
    window_manager = get_cache_manager()
    return window_manager.get_leftmost_x_offset()


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
