import psutil
import time
import json
from mouse_control import get_widget_inc_window, focus_widget_inc


class WidgetIncManager:
    def __init__(self, config_path="config/settings.json"):
        self.load_config(config_path)
        self.window = None

    def load_config(self, config_path):
        """Load configuration settings"""
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                self.executable_name = config["target_application"]["executable"]
                self.window_title = config["target_application"]["window_title"]
                self.process_name = config["target_application"]["process_name"]
                self.startup_timeout = config["target_application"]["startup_timeout"]
        except Exception as e:
            print(f"Error loading config: {e}")
            # Fallback defaults
            self.executable_name = "WidgetInc.exe"
            self.window_title = "WidgetInc"
            self.process_name = "WidgetInc"
            self.startup_timeout = 30

    def is_widget_inc_running(self):
        """Check if WidgetInc.exe is running"""
        for process in psutil.process_iter(["pid", "name"]):
            try:
                if process.info["name"].lower() == self.executable_name.lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def find_widget_inc_window(self):
        """Find and store reference to WidgetInc window"""
        self.window = get_widget_inc_window()
        return self.window is not None

    def wait_for_widget_inc(self, timeout=None):
        """Wait for WidgetInc to start and window to appear"""
        if timeout is None:
            timeout = self.startup_timeout

        start_time = time.time()

        print("Waiting for WidgetInc...")
        while time.time() - start_time < timeout:
            if self.is_widget_inc_running() and self.find_widget_inc_window():
                print("WidgetInc found and ready!")
                return True

            print(".", end="", flush=True)
            time.sleep(1)

        print(f"\nTimeout waiting for WidgetInc after {timeout} seconds")
        return False

    def ensure_widget_inc_ready(self):
        """Ensure WidgetInc is running and focused"""
        if not self.is_widget_inc_running():
            print("WidgetInc.exe is not running. Please start WidgetInc and try again.")
            return False

        if not self.find_widget_inc_window():
            print("WidgetInc window not found. Please ensure WidgetInc is visible.")
            return False

        if not focus_widget_inc():
            print("Could not focus WidgetInc window.")
            return False

        print("WidgetInc is ready for automation!")
        return True

    def get_window_info(self):
        """Get detailed information about the WidgetInc window"""
        if self.window:
            try:
                return {
                    "title": self.window.title,
                    "left": self.window.left,
                    "top": self.window.top,
                    "width": self.window.width,
                    "height": self.window.height,
                    "is_minimized": self.window.isMinimized,
                    "is_maximized": self.window.isMaximized,
                }
            except Exception as e:
                print(f"Error getting window info: {e}")
                return None
        return None
