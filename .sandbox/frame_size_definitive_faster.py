import os
import sys
from typing import Optional, Dict
import pyautogui


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from utility.cache_manager import get_cache_manager


def _sample_border_pixels(frame_area, border_color=(12, 10, 16)):
    """
    Sample pixels around the frame area to understand the border situation.
    """
    if not frame_area:
        return

    x, y, width, height = frame_area["x"], frame_area["y"], frame_area["width"], frame_area["height"]
    mid_y = y + height // 2

    print(f"Sampling pixels around frame at mid_y={mid_y}")
    print(f"Looking for border color: {border_color}")

    # Sample pixels to the left of the frame (wider range)
    print("\nLeft side sampling:")
    for offset in range(-50, 21):  # Look further out for borders
        test_x = x + offset
        try:
            pixel = pyautogui.pixel(test_x, mid_y)
            marker = " <-- BORDER" if pixel == border_color else ""
            print(f"  x={test_x}: {pixel}{marker}")
        except Exception as e:
            print(f"  x={test_x}: Error - {e}")

    # Sample pixels to the right of the frame (wider range)
    print("\nRight side sampling:")
    right_edge = x + width
    for offset in range(-10, 51):  # Look further out for borders
        test_x = right_edge + offset
        try:
            pixel = pyautogui.pixel(test_x, mid_y)
            marker = " <-- BORDER" if pixel == border_color else ""
            print(f"  x={test_x}: {pixel}{marker}")
        except Exception as e:
            print(f"  x={test_x}: Error - {e}")


def _refine_frame_borders(frame_area, border_color=(12, 10, 16)):
    """
    Simple border refinement - handle common off-by-1 or off-by-2 pixel errors.
    Ensures x-1 is border on left and adjust to get exactly 2054 width.
    """
    if not frame_area:
        return None

    x, y, width, height = frame_area["x"], frame_area["y"], frame_area["width"], frame_area["height"]
    mid_y = y + height // 2
    target_width = 2054

    print(f"Simple border refinement at mid_y={mid_y}")
    print(f"Initial: x={x}, width={width} (target: {target_width})")

    # Find correct left boundary - check if x-1 is border, adjust if needed
    left_x = x
    for offset in range(3):  # Check current, +1, +2
        test_x = left_x + offset
        if test_x > 0 and pyautogui.pixel(test_x - 1, mid_y) == border_color:
            left_x = test_x
            print(f"Found correct left boundary at x={left_x}")
            break
    else:
        # Try moving left by 1 or 2
        for offset in range(1, 3):
            test_x = left_x - offset
            if test_x > 0 and pyautogui.pixel(test_x - 1, mid_y) == border_color:
                left_x = test_x
                print(f"Found correct left boundary at x={left_x} (moved left by {offset})")
                break

    # Calculate right boundary to get exactly target_width
    refined_width = target_width

    print(f"Final: left_x={left_x}, width={refined_width}")

    return {
        "x": left_x,
        "y": y,
        "width": refined_width,
        "height": height,
        "adjustments": {"left_shift": left_x - x, "width_change": refined_width - width},
    }


def _calculate_frame_area(window_info) -> Optional[Dict[str, int]]:
    """
    Calculate 3:2 aspect ratio frame area using cached window info.
    Uses the same logic as the tracker app for consistency.
    """
    if not window_info:
        return None

    try:
        client_screen = window_info["client_screen"]
        client_x = client_screen["x"]
        client_y = client_screen["y"]
        client_w = client_screen["width"]
        client_h = client_screen["height"]

        # Calculate 3:2 aspect ratio frame area (tracker logic)
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

        return {"x": px, "y": py, "width": frame_width, "height": frame_height}

    except Exception as e:
        print(f"Error calculating frame area: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    _window_manager = get_cache_manager()
    window_info = _window_manager.get_window_info()
    frame_area = _calculate_frame_area(window_info)
    if frame_area:
        print(f"Initial calculated Frame area: {frame_area}")

        border_color = (12, 10, 16)

        # Sample pixels around the area to understand border situation
        _sample_border_pixels(frame_area, border_color)

        # Refine borders using PyAutoGUI pixel checking
        refined_frame = _refine_frame_borders(frame_area, border_color)
        if refined_frame:
            print(f"Refined frame area: {refined_frame}")
            print(f"Adjustments made: {refined_frame['adjustments']}")
        else:
            print("Failed to refine frame borders.")
    else:
        print("Failed to calculate frame area.")
