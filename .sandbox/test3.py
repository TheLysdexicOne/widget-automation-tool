import time
import sys
import os
import cv2
import numpy as np
import screeninfo

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from utility.window_utils import get_frame_screenshot, screen_to_frame_coords


def get_leftmost_x_offset():
    monitors = screeninfo.get_monitors()
    leftmost = min(monitor.x for monitor in monitors)
    return abs(leftmost)


def get_bounds_ultra_fast(start_point, empty_color, filled_colors: list):
    """
    Test 1: Ultra-fast bounds detection using NumPy array slicing
    """
    screenshot = get_frame_screenshot()
    if not screenshot:
        return {"top": 0, "bottom": 0, "height": 0}

    frame_x, frame_y = screen_to_frame_coords(start_point[0], start_point[1])

    # Convert to numpy array once and slice the column
    img_array = np.array(screenshot)
    column = img_array[:, frame_x]  # Extract entire column at frame_x

    # Create target color arrays for vectorized comparison
    empty_arr = np.array(empty_color)
    filled_arrays = [np.array(color) for color in filled_colors]

    # Vectorized color matching - find all valid pixels in one operation
    is_empty = np.all(column == empty_arr, axis=1)
    is_filled = np.any([np.all(column == filled_arr, axis=1) for filled_arr in filled_arrays], axis=0)
    valid_mask = is_empty | is_filled

    # Find bounds using array operations
    valid_indices = np.where(valid_mask)[0]
    if len(valid_indices) == 0:
        return {"top": 0, "bottom": 0, "height": 0}

    # Split around start point for proper boundary detection
    above_start = valid_indices[valid_indices <= frame_y]
    below_start = valid_indices[valid_indices >= frame_y]

    if len(above_start) == 0 or len(below_start) == 0:
        return {"top": 0, "bottom": 0, "height": 0}

    # Find continuous region around start point
    y_top = above_start[-1]  # Last valid pixel above/at start
    y_bottom = below_start[0]  # First valid pixel at/below start

    # Expand bounds while pixels are continuous
    for i in range(len(above_start) - 1, -1, -1):
        if above_start[i] == y_top - (len(above_start) - 1 - i):
            y_top = above_start[i]
        else:
            break

    for i in range(len(below_start)):
        if below_start[i] == y_bottom + i:
            y_bottom = below_start[i]
        else:
            break

    # Visualize (minimal overhead)
    screenshot_copy = screenshot.copy()
    for y in range(y_top, y_bottom + 1):
        screenshot_copy.putpixel((frame_x, y), (255, 255, 255))
    screenshot_copy.show()

    return {"top": y_top, "bottom": y_bottom, "height": y_bottom - y_top + 1}


def get_bounds_pil(start_point, empty_color, filled_colors: list):
    """
    Test 2: PIL-based bounds detection with frame screenshot
    """
    screenshot = get_frame_screenshot()
    if not screenshot:
        return {"top": 0, "bottom": 0, "height": 0}

    frame_x, frame_y = screen_to_frame_coords(start_point[0], start_point[1])
    width, height = screenshot.size

    # Find top bound
    y_top = frame_y
    while y_top > 0:
        pixel = screenshot.getpixel((frame_x, y_top))
        if pixel != empty_color and pixel not in filled_colors:
            break
        y_top -= 1
    y_top += 1

    # Find bottom bound
    y_bottom = frame_y
    while y_bottom < height - 1:
        pixel = screenshot.getpixel((frame_x, y_bottom))
        if pixel != empty_color and pixel not in filled_colors:
            break
        y_bottom += 1
    y_bottom -= 1

    box_height = y_bottom - y_top + 1

    # Visualize bounds with white line
    screenshot_copy = screenshot.copy()
    for y in range(y_top, y_bottom + 1):
        if 0 <= frame_x < width and 0 <= y < height:
            screenshot_copy.putpixel((frame_x, y), (255, 255, 255))  # White line

    # Show the visualization
    screenshot_copy.show()

    return {"top": y_top, "bottom": y_bottom, "height": box_height}


def get_bounds_cv2(screenshot, start_point, empty_color, filled_colors):
    """
    Test 3: OpenCV-based bounds detection with frame screenshot
    """
    img_array = np.array(screenshot)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    frame_x, frame_y = screen_to_frame_coords(start_point[0], start_point[1])
    height, width = img_bgr.shape[:2]

    # Find top bound (scan upward from start point)
    y_top = frame_y
    while y_top > 0:
        pixel_bgr = img_bgr[y_top, frame_x]
        pixel_rgb = (pixel_bgr[2], pixel_bgr[1], pixel_bgr[0])  # Convert BGR to RGB
        if pixel_rgb != empty_color and pixel_rgb not in filled_colors:
            break
        y_top -= 1
    y_top += 1

    # Find bottom bound (scan downward from start point)
    y_bottom = frame_y
    while y_bottom < height - 1:
        pixel_bgr = img_bgr[y_bottom, frame_x]
        pixel_rgb = (pixel_bgr[2], pixel_bgr[1], pixel_bgr[0])  # Convert BGR to RGB
        if pixel_rgb != empty_color and pixel_rgb not in filled_colors:
            break
        y_bottom += 1
    y_bottom -= 1

    # Visualize bounds with white line in OpenCV format
    img_vis = img_bgr.copy()
    for y in range(y_top, y_bottom + 1):
        if 0 <= frame_x < width and 0 <= y < height:
            img_vis[y, frame_x] = [255, 255, 255]  # White line in BGR

    # Convert back to RGB for PIL display
    img_rgb = cv2.cvtColor(img_vis, cv2.COLOR_BGR2RGB)
    from PIL import Image

    pil_img = Image.fromarray(img_rgb)
    pil_img.show()

    return {"top": y_top, "bottom": y_bottom}


if __name__ == "__main__":
    start_point = (-742, 631)
    empty_color = (17, 11, 37)
    filled_colors = [(72, 237, 56), (23, 97, 19), (45, 175, 37)]

    print("=== Pass = 'top': 582, 'bottom': 1057, 'height'476' ===")
    print("=== Test 1: Ultra-fast NumPy bounds detection ===")
    start_time = time.time()
    bounds_ultra = get_bounds_ultra_fast(start_point, empty_color, filled_colors)
    elapsed_time = time.time() - start_time
    print(f"Ultra Bounds: {bounds_ultra}")
    print(f"Ultra elapsed time: {elapsed_time:.4f} seconds")

    print("\n=== Test 2: PIL-based bounds detection ===")
    start_time = time.time()
    bounds_pil = get_bounds_pil(start_point, empty_color, filled_colors)
    elapsed_time = time.time() - start_time
    print(f"PIL Bounds: {bounds_pil}")
    print(f"PIL elapsed time: {elapsed_time:.4f} seconds")

    print("\n=== Test 3: OpenCV-based bounds detection ===")
    start_time = time.time()
    screenshot = get_frame_screenshot()
    if screenshot:
        bounds_cv2 = get_bounds_cv2(screenshot, start_point, empty_color, filled_colors)
        elapsed_time = time.time() - start_time
        print(f"CV2 Bounds: top={bounds_cv2['top']}, bottom={bounds_cv2['bottom']}")
        print(f"CV2 elapsed time: {elapsed_time:.4f} seconds")
    else:
        print("Could not get frame screenshot")
        elapsed_time = time.time() - start_time
        print(f"CV2 elapsed time: {elapsed_time:.4f} seconds")
