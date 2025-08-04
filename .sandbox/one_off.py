import time
from typing import Optional
from PIL import ImageGrab, Image
import pyautogui
import tempfile
import sys
import os
import json


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from utility.window_utils import get_frame_screenshot, grid_to_frame_coords  # , get_box_no_border
from utility.cache_manager import get_cache_manager


def get_box_no_border(
    approx_box: tuple[int, int, int, int],
    allowed_colors: list[tuple[int, int, int]],
    screenshot: Optional[Image.Image] = None,
):
    """
    Get a box without borders from the screenshot.

    Args:
        approx_box (tuple): Approximate bounding box (x1, y1, x2, y2).
        allowed_colors (list): List of allowed colors for the box.
    """

    def test_vertical_line(x):
        for y_offset in range(y1, y2 + 1):
            pixel = screenshot.getpixel((x, y_offset))
            if pixel not in allowed_colors:
                # print(f"Invalid pixel at ({x}, {y_offset}) with color {pixel}")
                return False
        return True

    def test_horizontal_line(y):
        for x_offset in range(x1, x2 + 1):
            pixel = screenshot.getpixel((x_offset, y))
            if pixel not in allowed_colors:
                # print(f"Invalid pixel at ({x_offset}, {y}) with color {pixel}")
                return False
        return True

    def get_left_edge(x1):
        x = x1
        pixel = screenshot.getpixel((x, y1))
        while x > 0 and pixel in allowed_colors:
            x -= 4
            pixel = screenshot.getpixel((x, y1))
            # print("increasing left by 4")
        while x > 0 and pixel not in allowed_colors:
            x += 1
            pixel = screenshot.getpixel((x, y1))
            # print("decreasing left by 1")
        while not test_vertical_line(x):
            x += 1
            # print("vertical test not passed, increasing by 1")
        return x

    def get_right_edge(x2):
        x = x2
        pixel = screenshot.getpixel((x, y1))
        while x < screenshot.width and pixel in allowed_colors:
            x += 4
            pixel = screenshot.getpixel((x, y1))
            # print("increasing right by 4")
        while x < screenshot.width and pixel not in allowed_colors:
            x -= 1
            pixel = screenshot.getpixel((x, y1))
            # print("decreasing right by 1")
        while not test_vertical_line(x):
            x -= 1
            # print("vertical test not passed, decreasing by 1")
        return x

    def get_top_edge(y1):
        y = y1
        pixel = screenshot.getpixel((x1, y))
        while y > 0 and pixel in allowed_colors:
            y -= 4
            pixel = screenshot.getpixel((x1, y))
            # print("increasing top by 4")
        while y > 0 and pixel not in allowed_colors:
            y += 1
            pixel = screenshot.getpixel((x1, y))
            # print("decreasing top by 1")
        while not test_horizontal_line(y):
            y += 1
            # print("horizontal test not passed, increasing by 1")
        return y

    def get_bottom_edge(y2):
        y = y2
        pixel = screenshot.getpixel((x1, y))
        while y < screenshot.height and pixel in allowed_colors:
            y += 4
            pixel = screenshot.getpixel((x1, y))
            # print("increasing bottom by 4")
        while y < screenshot.height and pixel not in allowed_colors:
            y -= 1
            pixel = screenshot.getpixel((x1, y))
            # print("decreasing bottom by 1")
        while not test_horizontal_line(y):
            y -= 1
            # print("horizontal test not passed, decreasing by 1")
        return y

    if screenshot is None:
        screenshot = get_frame_screenshot()

    x1, y1, x2, y2 = approx_box
    print(x1, y1, x2, y2)

    # Inital tests for the approximate 4 sides
    left = test_vertical_line(x1)
    top = test_horizontal_line(y1)
    right = test_vertical_line(x2)
    bottom = test_horizontal_line(y2)
    if not left or not top or not right or not bottom:
        raise ValueError("Initial box test failed...")

    x1 = get_left_edge(x1)
    x2 = get_right_edge(x2)
    y1 = get_top_edge(y1)
    y2 = get_bottom_edge(y2)
    return (x1, y1, x2, y2)

    left = test_vertical_line(x1)
    top = test_horizontal_line(y1)
    right = test_vertical_line(x2)
    bottom = test_horizontal_line(y2)
    print(f"Left: {left}\nTop: {top}\nRight: {right}\nBottom: {bottom}")
    print(f"Final box: ({x1}, {y1}, {x2}, {y2})")
    print(f"Width: {x2 - x1}, Height: {y2 - y1}")
    screenshot.save("screenshot.png")


screenshot = get_frame_screenshot()

window_manager = get_cache_manager()
window_info = window_manager.get_window_info()
frame_data = window_manager.get_frame_data("6.3")


bucket_y = frame_data["frame_xy"]["interactions"]["bucket_y"][1]
matrix_bbox = frame_data["frame_xy"]["bbox"]["matrix_bbox"]
matrix_colors = [(r, g, b) for r in range(31) for g in range(256) for b in range(31)]

start_time = time.time()
box = get_box_no_border(matrix_bbox, matrix_colors)
print(f"Box: {box}")
print(f"Width: {box[2] - box[0]}, Height: {box[3] - box[1]}")
elapsed_time = time.time() - start_time
print(f"Time taken: {elapsed_time:.2f} seconds")
print(len(matrix_colors))


def is_matrix_color(pixel):
    r, g, b = pixel[:3]
    return r <= 30 and b <= 30
