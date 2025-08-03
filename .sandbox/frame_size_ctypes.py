from PIL import Image
from ctypes import windll
import numpy as np
import win32gui

import win32ui
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from utility.cache_manager import get_cache_manager

_window_manager = get_cache_manager()
window_info = _window_manager.get_window_info()
if window_info is None or "hwnd" not in window_info:
    raise RuntimeError("Window info is missing or does not contain 'hwnd'.")
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

# Client rect relative to window rect
rel_left = client_abs_left - window_left
rel_top = client_abs_top - window_top
rel_right = rel_left + client_width
rel_bottom = rel_top + client_height

rect = (rel_left, rel_top, rel_right, rel_bottom)
left, top, right, bottom = windowRect
print(f"Window rectangle: {rect}")

# Bring window to foreground to ensure screenshot works (optional, but not always needed)
# win32gui.SetForegroundWindow(hwnd)

# To screenshot a covered/inactive window, use PrintWindow via win32gui

hwndDC = win32gui.GetWindowDC(hwnd)
mfcDC = win32ui.CreateDCFromHandle(hwndDC)
saveDC = mfcDC.CreateCompatibleDC()

width = right - left
height = bottom - top

saveBitMap = win32ui.CreateBitmap()
saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
saveDC.SelectObject(saveBitMap)
result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
bmpinfo = saveBitMap.GetInfo()
bmpstr = saveBitMap.GetBitmapBits(True)
img = Image.frombuffer("RGB", (bmpinfo["bmWidth"], bmpinfo["bmHeight"]), bmpstr, "raw", "BGRX", 0, 1)

# Cleanup
win32gui.DeleteObject(saveBitMap.GetHandle())
saveDC.DeleteDC()
mfcDC.DeleteDC()
win32gui.ReleaseDC(hwnd, hwndDC)

if result == 1:
    screenshot = img

    # Crop to client area only (remove window decorations)
    # The client rect coordinates are relative to the window
    client_only = screenshot.crop((rel_left, rel_top, rel_right, rel_bottom))

    print(f"Original window size: {screenshot.size}")
    print(f"Client area size: {client_only.size}")
    print(f"Client rect relative to window: ({rel_left}, {rel_top}, {rel_right}, {rel_bottom})")

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

    print(f"Border bounds: left={left_border}, top={top_border}, right={right_border}, bottom={bottom_border}")
    print(f"Frame area size: {frame_area.size}")
    print(f"Frame area dimensions: {right_border - left_border} x {bottom_border - top_border}")

    # Show both for comparison
    # client_only.show()  # Client area with borders
    # frame_area.show()  # Actual frame area without borders
else:
    raise RuntimeError("PrintWindow failed to capture the window image.")
