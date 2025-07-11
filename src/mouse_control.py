import pyautogui
import pygetwindow as gw
import time


def get_widget_inc_window():
    """Get the WidgetInc window"""
    try:
        # Try to find by window title first
        windows = gw.getWindowsWithTitle("WidgetInc")
        if windows:
            return windows[0]

        # If not found by title, try partial matches
        all_windows = gw.getAllWindows()
        for window in all_windows:
            if "widget" in window.title.lower() and "inc" in window.title.lower():
                return window

        print("WidgetInc window not found")
        return None
    except Exception as e:
        print(f"Error finding WidgetInc window: {e}")
        return None


def get_window_bounds(window_title="WidgetInc"):
    """Get the bounds of the WidgetInc window"""
    window = get_widget_inc_window()
    if window:
        try:
            return window.left, window.top, window.width, window.height
        except Exception as e:
            print(f"Error getting window bounds: {e}")
            return None
    return None


def percentage_to_absolute(x_percent, y_percent, window_title="WidgetInc"):
    """Convert percentage coordinates to absolute screen coordinates for WidgetInc"""
    bounds = get_window_bounds(window_title)
    if bounds:
        left, top, width, height = bounds
        x = left + (width * x_percent / 100)
        y = top + (height * y_percent / 100)
        return int(x), int(y)

    # Fallback to screen coordinates
    screen_width, screen_height = pyautogui.size()
    x = screen_width * x_percent / 100
    y = screen_height * y_percent / 100
    return int(x), int(y)


def move_mouse_to(x, y, duration=0.25):
    """Move mouse to absolute coordinates"""
    pyautogui.moveTo(x, y, duration)


def move_mouse_to_percent(
    x_percent, y_percent, window_title="WidgetInc", duration=0.25
):
    """Move mouse to percentage coordinates within WidgetInc window"""
    x, y = percentage_to_absolute(x_percent, y_percent, window_title)
    pyautogui.moveTo(x, y, duration)


def click_mouse(x=None, y=None, button="left"):
    """Click at absolute coordinates"""
    if x is not None and y is not None:
        move_mouse_to(x, y)
    pyautogui.click(button=button)


def click_mouse_percent(x_percent, y_percent, window_title="WidgetInc", button="left"):
    """Click at percentage coordinates within WidgetInc window"""
    x, y = percentage_to_absolute(x_percent, y_percent, window_title)
    pyautogui.click(x, y, button=button)


def scroll_mouse(amount):
    """Scroll mouse wheel"""
    pyautogui.scroll(amount)


def double_click_mouse(x=None, y=None):
    """Double click at coordinates"""
    if x is not None and y is not None:
        move_mouse_to(x, y)
    pyautogui.doubleClick()


def focus_widget_inc():
    """Bring WidgetInc window to focus"""
    window = get_widget_inc_window()
    if window:
        try:
            if window.isMinimized:
                window.restore()
            window.activate()
            time.sleep(0.5)  # Wait for window to focus
            return True
        except Exception as e:
            print(f"Error focusing WidgetInc window: {e}")
            return False
    return False
