from PIL import ImageGrab
import numpy as np
import win32gui
import time
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from utility.cache_manager import get_cache_manager

_window_manager = get_cache_manager()

window_info = _window_manager.get_window_info()

if window_info is None:
    print("No window info found. Make sure WidgetInc is running.")
    sys.exit(1)

hwnd = window_info["hwnd"]

print(f"Window handle: {hwnd}")

# Get window rectangle (left, top, right, bottom)
windowRect = win32gui.GetWindowRect(hwnd)
clientRect = win32gui.GetClientRect(hwnd)

# Calculate client rect coordinates relative to window rect
window_left, window_top, window_right, window_bottom = windowRect
client_left, client_top, client_right, client_bottom = clientRect

# Get the offset of the client area within the window (accounts for title bar, borders)
client_offset = win32gui.ClientToScreen(hwnd, (0, 0))
client_abs_left, client_abs_top = client_offset

# Client width/height
client_width = client_right - client_left
client_height = client_bottom - client_top

# Calculate absolute client area coordinates (screen coordinates)
client_screen_left = client_abs_left
client_screen_top = client_abs_top
client_screen_right = client_abs_left + client_width
client_screen_bottom = client_abs_top + client_height

print(f"Window rectangle: {windowRect}")
print(
    f"Client area (screen coords): ({client_screen_left}, {client_screen_top}, {client_screen_right}, {client_screen_bottom})"
)

# Take screenshot of client area using PIL
client_bbox = (client_screen_left, client_screen_top, client_screen_right, client_screen_bottom)
client_only = ImageGrab.grab(bbox=client_bbox, all_screens=True)

print(f"Client area size: {client_only.size}")

# Find actual frame area by removing black borders (#0c0a10)
border_color = (12, 10, 16)  # #0c0a10 in RGB

# Convert to numpy array for easier processing
img_array = np.array(client_only)
height, width, _ = img_array.shape

# Black borders are only on left and right, height goes to full bounds
top_border = 0
bottom_border = height

# Find left border - check at middle Y position
mid_y = height // 2
left_border = 0
for x in range(width):
    # Check if this pixel at mid-height is the border color
    pixel = img_array[mid_y, x]  # Single pixel at middle height
    if not np.array_equal(pixel, border_color):
        left_border = x
        print(f"Found left border at x={x} (checked at y={mid_y})")
        break

print(f"Left border search complete: left_border={left_border}")

# Find right border - check at middle Y position
right_border = width
for x in range(width - 1, -1, -1):
    # Check if this pixel at mid-height is the border color
    pixel = img_array[mid_y, x]  # Single pixel at middle height
    if not np.array_equal(pixel, border_color):
        right_border = x + 1
        print(f"Found right border at x={x} (right_border={right_border}, checked at y={mid_y})")
        break

print(f"Right border search complete: right_border={right_border}")

# Check a few sample pixels to debug
print(f"Sample pixel at ({mid_y}, 0): {img_array[mid_y, 0]}")
print(f"Sample pixel at ({mid_y}, 10): {img_array[mid_y, 10] if width > 10 else 'N/A'}")
print(f"Border color we're looking for: {border_color}")

# Crop to actual frame area (no black borders)
frame_area = client_only.crop((left_border, top_border, right_border, bottom_border))

# Calculate absolute screen coordinates of the frame area
frame_screen_left = client_screen_left + left_border
frame_screen_top = client_screen_top + top_border
frame_screen_right = client_screen_left + right_border
frame_screen_bottom = client_screen_top + bottom_border

print(f"Border bounds: left={left_border}, top={top_border}, right={right_border}, bottom={bottom_border}")
print(f"Frame area size: {frame_area.size}")
print(f"Frame area dimensions: {right_border - left_border} x {bottom_border - top_border}")
print(
    f"Frame area (screen coords): ({frame_screen_left}, {frame_screen_top}, {frame_screen_right}, {frame_screen_bottom})"
)
