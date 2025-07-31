def up(pixels=1, max_distance=1000):
    global current_pos
    result = find_cell_direction(TARGET_COLOR, "up", pixels, TOLERANCE, max_distance, start_pos=current_pos)
    found, match = result
    if found:
        current_pos = found
    return result


def down(pixels=1, max_distance=1000):
    global current_pos
    result = find_cell_direction(TARGET_COLOR, "down", pixels, TOLERANCE, max_distance, start_pos=current_pos)
    found, match = result
    if found:
        current_pos = found
    return result


def left(pixels=1, max_distance=1000):
    global current_pos
    result = find_cell_direction(TARGET_COLOR, "left", pixels, TOLERANCE, max_distance, start_pos=current_pos)
    found, match = result
    if found:
        current_pos = found
    return result


def right(pixels=1, max_distance=1000):
    global current_pos
    result = find_cell_direction(TARGET_COLOR, "right", pixels, TOLERANCE, max_distance, start_pos=current_pos)
    found, match = result
    if found:
        current_pos = found
    return result


import pyautogui
from PIL import ImageGrab

X_OFFSET = 2560
START = (-1280 + X_OFFSET, 720)
# Set this if you want to offset all x-coordinates (e.g. for multi-monitor)
TARGET_COLOR = (15, 15, 15)  # Set your target color here
TOLERANCE = 10  # Color match tolerance
current_pos = None  # Will hold the last found position


def _adjust_start(start, width, height):
    x0, y0 = start
    if x0 < 0:
        x0 = width + x0
    if y0 < 0:
        y0 = height + y0
    return x0, y0


def _pixel_match(pixel, target_rgb, tolerance=TOLERANCE):
    if isinstance(pixel, (int, float)):
        pixel = (int(pixel), int(pixel), int(pixel))
    if not (isinstance(pixel, tuple) and len(pixel) >= 3):
        return False
    return all(abs(int(pixel[i]) - int(target_rgb[i])) <= tolerance for i in range(3))


def find_cell_direction(target_rgb, direction, pixels=1, tolerance=TOLERANCE, max_distance=1000, start_pos=None):
    """
    Scan from START in a direction ('up', 'down', 'left', 'right'),
    checking every 'pixels' pixels, up to max_distance.
    Returns (x, y) if found, else None.
    """
    import json
    import os

    # Always use full screenshot and real coordinates
    screenshot = ImageGrab.grab(all_screens=True)
    x0, y0 = 0, 0
    width, height = screenshot.size

    if start_pos is not None:
        x, y = start_pos
    else:
        x, y = _adjust_start(START, width, height)
    x += START[0] + X_OFFSET

    dx, dy = 0, 0
    if direction == "up":
        dy = -pixels
    elif direction == "down":
        dy = pixels
    elif direction == "left":
        dx = -pixels
    elif direction == "right":
        dx = pixels
    else:
        raise ValueError("Direction must be one of: up, down, left, right")

    global all_matches
    matches = []
    step = 0
    last_match = False
    found_coord = None
    while True:
        cx, cy = x + dx * step, y + dy * step
        if not (0 <= cx < width and 0 <= cy < height):
            break
        pixel = screenshot.getpixel((int(cx), int(cy)))
        is_match = _pixel_match(pixel, target_rgb, tolerance)
        if is_match:
            print(f"\033[92mScanned: ({cx}, {cy}) MATCH\033[0m")
            matches.append({"x": int(cx), "y": int(cy), "rgb": pixel})
            if not found_coord:
                found_coord = (cx, cy)
        else:
            print(f"Scanned: ({cx}, {cy})")
        last_match = is_match
        step += 1

    # Accumulate all matches for this run
    all_matches.extend(matches)
    return (found_coord, last_match)


all_matches = []

if __name__ == "__main__":
    # Example: keep moving down by 4 pixels until the target color is found
    import os, json

    # Clear find_box.json at the start of the run
    out_path = os.path.join(os.path.dirname(__file__), "find_box.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump([], f)

    current_pos = START
    found = None
    match = False
    while (not found) and (current_pos[1] < 1400):
        found, match = down(4)
        print(f"Current position: {current_pos}, Found: {found}, Last match: {match}")
    print(f"Target color found at: {current_pos}")

    # Write all matches at the end of the run
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_matches, f, indent=2)
