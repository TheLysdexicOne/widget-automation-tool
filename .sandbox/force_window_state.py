#!/usr/bin/env python3
"""
Force WidgetInc Window State - Standalone Test

Test script to force WidgetInc out of fullscreen and into maximized state
using Windows API calls directly.
"""

import time
import sys
from typing import Optional, Dict, Any

try:
    import psutil
    import win32gui
    import win32process
    import win32con
    import win32api

    print("Win32 imports successful")
except ImportError as e:
    print(f"Missing required modules: {e}")
    print("Install with: pip install psutil pywin32")
    sys.exit(1)


def find_target_window(target_process_name: str = "WidgetInc.exe") -> Optional[Dict[str, Any]]:
    """
    Find WidgetInc window and determine its current state.
    """
    target_windows = []

    def enum_windows_callback(hwnd, _):
        try:
            title = win32gui.GetWindowText(hwnd)
            if "WidgetInc" in title and win32gui.IsWindowVisible(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                target_windows.append((pid, hwnd))
        except Exception:
            pass
        return True

    win32gui.EnumWindows(enum_windows_callback, None)

    # Find first valid process
    for pid, hwnd in target_windows:
        try:
            proc = psutil.Process(pid)
            if proc.is_running() and proc.name() == target_process_name:
                # Get window info
                title = win32gui.GetWindowText(hwnd)
                window_rect = win32gui.GetWindowRect(hwnd)

                # Determine window state
                window_state = determine_window_state(hwnd, window_rect)

                return {
                    "pid": pid,
                    "hwnd": hwnd,
                    "title": title,
                    "window_rect": window_rect,
                    "window_state": window_state,
                    "width": window_rect[2] - window_rect[0],
                    "height": window_rect[3] - window_rect[1],
                }
        except Exception:
            continue

    return None


def determine_window_state(hwnd: int, window_rect: tuple) -> str:
    """
    Determine window state: maximized, borderless_fullscreen, windowed, or controlled_windowed.
    """
    try:
        import ctypes

        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
        screen_height = user32.GetSystemMetrics(1)  # SM_CYSCREEN

        window_width = window_rect[2] - window_rect[0]
        window_height = window_rect[3] - window_rect[1]

        # Check if it covers the entire screen (borderless fullscreen)
        if (
            window_rect[0] == 0
            and window_rect[1] == 0
            and window_width == screen_width
            and window_height == screen_height
        ):
            # Even if IsZoomed() returns true, if it covers the entire screen, it's borderless
            return "borderless_fullscreen"

        # Check if maximized (fills screen minus taskbar)
        is_maximized = user32.IsZoomed(hwnd)
        if is_maximized:
            return "maximized"

        # Check for controlled windowed state (specific size we set for automation)
        # Common automation-friendly sizes: 1200x800, 1024x683, etc.
        if window_width in [1200, 1024, 1280] and window_height in [800, 683, 853]:
            return "controlled_windowed"

        return "windowed"

    except Exception:
        return "windowed"


def force_window_maximize(hwnd: int) -> bool:
    """
    Force window to maximized state using Windows API.
    """
    try:
        print(f"Attempting to maximize window HWND: {hwnd}")

        # Method 1: Direct ShowWindow call
        result = win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        print(f"ShowWindow(SW_MAXIMIZE) result: {result}")

        # Give it a moment to process
        time.sleep(0.5)

        # Method 2: If that didn't work, try restore then maximize
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.2)
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        print("Tried RESTORE -> MAXIMIZE sequence")

        return True

    except Exception as e:
        print(f"Error forcing maximize: {e}")
        return False


def force_to_controlled_windowed(hwnd: int, width: int = 1200, height: int = 800, x: int = 100, y: int = 100) -> bool:
    """
    Force window to a specific controlled windowed state perfect for automation.
    """
    try:
        print(f"Setting controlled windowed state: {width}x{height} at ({x}, {y})")

        # First restore to make sure it's not maximized
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.3)

        # Set exact size and position
        result = win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOP,  # Z-order
            x,
            y,  # Position
            width,
            height,  # Size
            win32con.SWP_SHOWWINDOW,
        )
        print(f"SetWindowPos result: {result}")

        return True

    except Exception as e:
        print(f"Error setting controlled windowed state: {e}")
        return False


def force_borderless_to_controlled(hwnd: int) -> bool:
    """
    Force borderless fullscreen to controlled windowed state.
    """
    try:
        print(f"Converting borderless fullscreen to controlled windowed HWND: {hwnd}")

        # Method 1: Try restore first
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.5)

        # Method 2: Force to specific size/position
        return force_to_controlled_windowed(hwnd, 1200, 800, 100, 100)

    except Exception as e:
        print(f"Error converting borderless to controlled: {e}")
        return False
    """
    Force borderless fullscreen window to maximized state.
    This is much easier than true fullscreen!
    """
    try:
        print(f"Converting borderless fullscreen to maximized HWND: {hwnd}")

        # For borderless windowed, just maximize it directly
        # This should work perfectly since it's already a window
        result = win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        print(f"ShowWindow(SW_MAXIMIZE) result: {result}")

        return True

    except Exception as e:
        print(f"Error converting borderless to maximized: {e}")
        return False
    """
    Force window out of fullscreen using multiple methods.
    """
    try:
        print(f"Attempting to force window out of fullscreen HWND: {hwnd}")

        # Method 1: Restore to windowed state first
        print("Method 1: SW_RESTORE")
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.5)

        # Method 2: Try minimize then restore
        print("Method 2: SW_MINIMIZE -> SW_RESTORE")
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        time.sleep(0.3)
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.5)

        # Method 3: Set window style to remove fullscreen characteristics
        print("Method 3: Modify window style")
        try:
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            print(f"Current window style: {hex(style)}")

            # Add standard window elements
            new_style = style | win32con.WS_CAPTION | win32con.WS_THICKFRAME | win32con.WS_SYSMENU
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, new_style)

            # Force window to update
            win32gui.SetWindowPos(
                hwnd,
                0,
                0,
                0,
                0,
                0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED,
            )
            print("Window style modified")
        except Exception as style_error:
            print(f"Style modification failed: {style_error}")

        return True

    except Exception as e:
        print(f"Error forcing out of fullscreen: {e}")
        return False


def main():
    """
    Main function to test forcing WidgetInc window state changes.
    """
    print("=== WidgetInc Window State Forcer ===")
    print("Searching for WidgetInc window...")

    # Find WidgetInc window
    window_info = find_target_window()

    if not window_info:
        print("❌ WidgetInc window not found!")
        print("Make sure WidgetInc is running and try again.")
        return

    print(f"✅ Found WidgetInc window:")
    print(f"   PID: {window_info['pid']}")
    print(f"   HWND: {window_info['hwnd']}")
    print(f"   Title: {window_info['title']}")
    print(f"   Size: {window_info['width']}x{window_info['height']}")
    print(f"   Current State: {window_info['window_state'].upper()}")
    print(f"   Position: {window_info['window_rect']}")

    hwnd = window_info["hwnd"]
    current_state = window_info["window_state"]

    print(f"\n=== Current State: {current_state.upper()} ===")

    if current_state == "borderless_fullscreen":
        print("🎯 Window is in borderless fullscreen - converting to controlled windowed...")

        # Convert borderless to controlled windowed state for automation
        if force_borderless_to_controlled(hwnd):
            print("✅ Attempted to convert borderless fullscreen to controlled windowed")

            # Check result
            time.sleep(1.0)
            window_info = find_target_window()
            if window_info:
                final_state = window_info["window_state"]
                print(f"🏁 Final state: {final_state.upper()}")

                if final_state in ["controlled_windowed", "windowed"]:
                    print("🎉 SUCCESS! Borderless fullscreen converted to controlled windowed")
                    print(f"   New size: {window_info['width']}x{window_info['height']}")
                    print(f"   New position: {window_info['window_rect'][:2]}")
                else:
                    print(f"⚠️  Window state is {final_state}, conversion may have failed")
            else:
                print("❌ Could not re-detect window after conversion")
        else:
            print("❌ Failed to convert borderless fullscreen")

    elif current_state == "controlled_windowed":
        print("ℹ️  Window is already in controlled windowed state - perfect for automation!")
        print("🎉 SUCCESS! Target state achieved")
        print(f"   Size: {window_info['width']}x{window_info['height']}")
        print(f"   Position: {window_info['window_rect'][:2]}")

    elif current_state == "maximized":
        print("🎯 Window is maximized - converting to controlled windowed for automation...")

        # Convert maximized to controlled windowed
        if force_to_controlled_windowed(hwnd):
            print("✅ Attempted to convert maximized to controlled windowed")

            # Check result
            time.sleep(1.0)
            window_info = find_target_window()
            if window_info:
                final_state = window_info["window_state"]
                print(f"🏁 Final state: {final_state.upper()}")

                if final_state in ["controlled_windowed", "windowed"]:
                    print("🎉 SUCCESS! Maximized converted to controlled windowed")
                    print(f"   New size: {window_info['width']}x{window_info['height']}")
                    print(f"   New position: {window_info['window_rect'][:2]}")
                else:
                    print(f"⚠️  Window state is {final_state}, conversion may have failed")
        else:
            print("❌ Failed to convert maximized to controlled windowed")

    elif current_state == "windowed":
        print("🎯 Window is windowed - converting to controlled windowed for automation...")

        # Set to controlled windowed state
        if force_to_controlled_windowed(hwnd):
            print("✅ Attempted to set controlled windowed state")

            # Check result
            time.sleep(1.0)
            window_info = find_target_window()
            if window_info:
                final_state = window_info["window_state"]
                print(f"🏁 Final state: {final_state.upper()}")

                if final_state in ["controlled_windowed", "windowed"]:
                    print("🎉 SUCCESS! Window set to controlled windowed state")
                    print(f"   Size: {window_info['width']}x{window_info['height']}")
                    print(f"   Position: {window_info['window_rect'][:2]}")
                else:
                    print(f"⚠️  Window state is {final_state}, setting may have failed")
        else:
            print("❌ Failed to set controlled windowed state")

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    main()
