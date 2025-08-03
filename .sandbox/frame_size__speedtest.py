import time
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))


def test_ctypes_approach():
    """Test the ctypes-based frame detection approach"""
    print("=" * 50)
    print("TESTING: CTYPES APPROACH")
    print("=" * 50)

    start_time = time.perf_counter()

    try:
        from PIL import Image
        from ctypes import windll
        import numpy as np
        import win32gui
        import win32ui
        from utility.cache_manager import get_cache_manager

        _window_manager = get_cache_manager()
        window_info = _window_manager.get_window_info()
        if window_info is None or "hwnd" not in window_info:
            raise RuntimeError("Window info is missing or does not contain 'hwnd'.")
        hwnd = window_info["hwnd"]

        # Get window rectangle
        windowRect = win32gui.GetWindowRect(hwnd)
        clientRect = win32gui.GetClientRect(hwnd)
        window_left, window_top, window_right, window_bottom = windowRect
        client_left, client_top, client_right, client_bottom = clientRect

        # Get client area offset
        client_offset = win32gui.ClientToScreen(hwnd, (0, 0))
        client_abs_left, client_abs_top = client_offset

        # Client dimensions
        client_width = client_right - client_left
        client_height = client_bottom - client_top

        # Client rect relative to window rect
        rel_left = client_abs_left - window_left
        rel_top = client_abs_top - window_top
        rel_right = rel_left + client_width
        rel_bottom = rel_top + client_height

        left, top, right, bottom = windowRect

        # Screenshot using PrintWindow
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
            # Crop to client area
            client_only = img.crop((rel_left, rel_top, rel_right, rel_bottom))

            # Find frame area by removing black borders
            border_color = (12, 10, 16)
            img_array = np.array(client_only)
            height, width, _ = img_array.shape

            # Find borders at middle Y position
            mid_y = height // 2
            left_border = 0
            for x in range(width):
                pixel = img_array[mid_y, x]
                if not np.array_equal(pixel, border_color):
                    left_border = x
                    break

            right_border = width
            for x in range(width - 1, -1, -1):
                pixel = img_array[mid_y, x]
                if not np.array_equal(pixel, border_color):
                    right_border = x + 1
                    break

            frame_width = right_border - left_border
            frame_height = height

            end_time = time.perf_counter()
            execution_time = end_time - start_time

            print(f"Frame dimensions: {frame_width} x {frame_height}")
            print(f"CTYPES EXECUTION TIME: {execution_time:.6f} seconds")
            return execution_time
        else:
            raise RuntimeError("PrintWindow failed")

    except Exception as e:
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        print(f"CTYPES FAILED: {e}")
        print(f"CTYPES EXECUTION TIME: {execution_time:.6f} seconds (failed)")
        return execution_time


def test_pil_approach():
    """Test the PIL-based frame detection approach"""
    print("\n" + "=" * 50)
    print("TESTING: PIL APPROACH")
    print("=" * 50)

    start_time = time.perf_counter()

    try:
        from PIL import ImageGrab
        import numpy as np
        import win32gui
        from utility.cache_manager import get_cache_manager

        _window_manager = get_cache_manager()
        window_info = _window_manager.get_window_info()
        if window_info is None:
            raise RuntimeError("No window info found")

        hwnd = window_info["hwnd"]

        # Get window rectangles
        windowRect = win32gui.GetWindowRect(hwnd)
        clientRect = win32gui.GetClientRect(hwnd)

        window_left, window_top, window_right, window_bottom = windowRect
        client_left, client_top, client_right, client_bottom = clientRect

        # Get client area screen coordinates
        client_offset = win32gui.ClientToScreen(hwnd, (0, 0))
        client_abs_left, client_abs_top = client_offset

        client_width = client_right - client_left
        client_height = client_bottom - client_top

        client_screen_left = client_abs_left
        client_screen_top = client_abs_top
        client_screen_right = client_abs_left + client_width
        client_screen_bottom = client_abs_top + client_height

        # Screenshot using PIL
        client_bbox = (client_screen_left, client_screen_top, client_screen_right, client_screen_bottom)
        client_only = ImageGrab.grab(bbox=client_bbox, all_screens=True)

        # Find frame area by removing black borders
        border_color = (12, 10, 16)
        img_array = np.array(client_only)
        height, width, _ = img_array.shape

        # Find borders at middle Y position
        mid_y = height // 2
        left_border = 0
        for x in range(width):
            pixel = img_array[mid_y, x]
            if not np.array_equal(pixel, border_color):
                left_border = x
                break

        right_border = width
        for x in range(width - 1, -1, -1):
            pixel = img_array[mid_y, x]
            if not np.array_equal(pixel, border_color):
                right_border = x + 1
                break

        frame_width = right_border - left_border
        frame_height = height

        end_time = time.perf_counter()
        execution_time = end_time - start_time

        print(f"Frame dimensions: {frame_width} x {frame_height}")
        print(f"PIL EXECUTION TIME: {execution_time:.6f} seconds")
        return execution_time

    except Exception as e:
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        print(f"PIL FAILED: {e}")
        print(f"PIL EXECUTION TIME: {execution_time:.6f} seconds (failed)")
        return execution_time


def test_pyautogui_approach():
    """Test the PyAutoGUI-based frame detection approach"""
    print("\n" + "=" * 50)
    print("TESTING: PYAUTOGUI APPROACH")
    print("=" * 50)

    start_time = time.perf_counter()

    try:
        import pyautogui
        from utility.cache_manager import get_cache_manager

        _window_manager = get_cache_manager()
        window_info = _window_manager.get_window_info()
        if not window_info:
            raise RuntimeError("No window info found")

        # Calculate initial frame area using cache
        client_screen = window_info["client_screen"]
        client_x = client_screen["x"]
        client_y = client_screen["y"]
        client_w = client_screen["width"]
        client_h = client_screen["height"]

        # Calculate 3:2 aspect ratio frame area
        target_ratio = 3.0 / 2.0
        client_ratio = client_w / client_h if client_h else 1

        if client_ratio > target_ratio:
            frame_height = client_h
            frame_width = int(frame_height * target_ratio)
            px = client_x + (client_w - frame_width) // 2
            py = client_y
        else:
            frame_width = client_w
            frame_height = int(frame_width / target_ratio)
            px = client_x
            py = client_y + (client_h - frame_height) // 2

        # Refine borders using PyAutoGUI
        x, y, frame_width, frame_height = px, py, frame_width, frame_height
        mid_y = y + frame_height // 2
        target_width = 2054
        border_color = (12, 10, 16)

        # Find correct left boundary
        left_x = x
        for offset in range(3):  # Check current, +1, +2
            test_x = left_x + offset
            if test_x > 0 and pyautogui.pixel(test_x - 1, mid_y) == border_color:
                left_x = test_x
                break
        else:
            # Try moving left by 1 or 2
            for offset in range(1, 3):
                test_x = left_x - offset
                if test_x > 0 and pyautogui.pixel(test_x - 1, mid_y) == border_color:
                    left_x = test_x
                    break

        refined_width = target_width

        end_time = time.perf_counter()
        execution_time = end_time - start_time

        print(f"Frame dimensions: {refined_width} x {frame_height}")
        print(f"PYAUTOGUI EXECUTION TIME: {execution_time:.6f} seconds")
        return execution_time

    except Exception as e:
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        print(f"PYAUTOGUI FAILED: {e}")
        print(f"PYAUTOGUI EXECUTION TIME: {execution_time:.6f} seconds (failed)")
        return execution_time


def run_speed_test():
    """Run all three approaches and compare their performance"""
    print("🚀 FRAME DETECTION SPEED TEST")
    print("Testing all three approaches with multiple runs for accuracy...\n")

    # Test each approach multiple times for better accuracy
    runs = 3

    print(f"Running each test {runs} times and averaging results...")

    ctypes_times = []
    pil_times = []
    pyautogui_times = []

    for i in range(runs):
        print(f"\n--- RUN {i + 1}/{runs} ---")
        ctypes_times.append(test_ctypes_approach())
        pil_times.append(test_pil_approach())
        pyautogui_times.append(test_pyautogui_approach())

    # Calculate averages
    avg_ctypes = sum(ctypes_times) / len(ctypes_times)
    avg_pil = sum(pil_times) / len(pil_times)
    avg_pyautogui = sum(pyautogui_times) / len(pyautogui_times)

    # Summary
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE SUMMARY (AVERAGED)")
    print("=" * 60)

    results = [("CTYPES", avg_ctypes), ("PIL", avg_pil), ("PYAUTOGUI", avg_pyautogui)]

    # Sort by execution time
    results.sort(key=lambda x: x[1])

    print(f"🥇 FASTEST:  {results[0][0]:<12} {results[0][1]:.6f} seconds")
    print(f"🥈 MIDDLE:   {results[1][0]:<12} {results[1][1]:.6f} seconds")
    print(f"🥉 SLOWEST:  {results[2][0]:<12} {results[2][1]:.6f} seconds")

    # Calculate performance differences
    fastest = results[0][1]
    print("\nSpeed comparison (relative to fastest):")
    for name, time_taken in results:
        if fastest > 0:
            multiplier = time_taken / fastest
            print(f"  {name:<12} {multiplier:.2f}x")
        else:
            print(f"  {name:<12} N/A (fastest time too small)")

    # Show individual run details
    print("\nIndividual run times:")
    print(f"  CTYPES:    {ctypes_times}")
    print(f"  PIL:       {pil_times}")
    print(f"  PYAUTOGUI: {pyautogui_times}")


if __name__ == "__main__":
    run_speed_test()
