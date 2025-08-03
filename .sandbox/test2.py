from PIL import ImageGrab
import screeninfo
import time


def get_leftmost_x_offset():
    monitors = screeninfo.get_monitors()
    leftmost = min(monitor.x for monitor in monitors)
    return abs(leftmost)


def get_bounds(start_point, empty_color, filled_colors: list):
    """
    Scan vertically from start_point to find the bounds of empty/filled color area.
    """
    start_time = time.time()
    screenshot = ImageGrab.grab(bbox=(-2307, 23, -254, 1392), all_screens=True)
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

    box_height = y_bottom - y_top + 1

    print(f"Top: {y_top - offset_x}, Bottom: {y_bottom - offset_x}, Height: {box_height}")
    elapsed_time = time.time() - start_time
    print(f"Elapsed time: {elapsed_time:.2f} seconds")

    return {"top": y_top - offset_x, "bottom": y_bottom - offset_x, "height": box_height}


if __name__ == "__main__":
    start_time = time.time()
    start_point = (-742, 631)
    empty_color = (17, 11, 37)
    filled_colors = [(72, 237, 56), (23, 97, 19), (45, 175, 37)]
    bounds = get_bounds(start_point, empty_color, filled_colors)
    print(f"Bounds: {bounds}")
    elapsed_time = time.time() - start_time
    print(f"Total elapsed time: {elapsed_time:.2f} seconds")
