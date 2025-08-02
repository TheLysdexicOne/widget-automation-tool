from PIL import ImageGrab
import screeninfo
import time


def get_leftmost_x_offset():
    monitors = screeninfo.get_monitors()
    leftmost = min(monitor.x for monitor in monitors)
    return abs(leftmost)


def get_color_difference(start_point, empty_color, filled_colors: list):
    """
    Scan vertically from start_point, tracking empty and filled color pixels,
    and calculate the percentage of filled pixels between the top and bottom bounds.
    """
    start_time = time.time()
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
    elapsed_time = time.time() - start_time
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    return percent_filled


if __name__ == "__main__":
    start_point = (-742, 631)
    empty_color = (17, 11, 37)
    filled_colors = [(72, 237, 56), (23, 97, 19), (45, 175, 37)]
    percent_filled = get_color_difference(start_point, empty_color, filled_colors)
    voltage = percent_filled * 15 / 100
    print(f"Voltage: {round(voltage)}")
