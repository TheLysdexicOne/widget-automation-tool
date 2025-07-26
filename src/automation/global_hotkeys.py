"""
Global Hotkey Manager
Handles global hotkey detection for automation control.
"""

import logging
import threading
import time
from typing import Callable, Optional

try:
    import win32api
    import win32con

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


class GlobalHotkeyManager:
    """Manages global hotkeys for automation control."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.GlobalHotkeyManager")
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_callback: Optional[Callable] = None

    def start_monitoring(self, stop_callback: Callable):
        """Start monitoring for global hotkeys."""
        if not WIN32_AVAILABLE:
            self.logger.warning("Win32 not available - global hotkeys disabled")
            return False

        if self.is_monitoring:
            self.logger.debug("Global hotkey monitoring already running")
            return True

        self.stop_callback = stop_callback
        self.is_monitoring = True

        # Start monitoring in a separate thread
        self.monitor_thread = threading.Thread(target=self._monitor_hotkeys, daemon=True)
        self.monitor_thread.start()

        self.logger.info("Started global hotkey monitoring (Right-click + Spacebar)")
        return True

    def stop_monitoring(self):
        """Stop monitoring for global hotkeys."""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        self.stop_callback = None

        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)

        self.logger.info("Stopped global hotkey monitoring")

    def _monitor_hotkeys(self):
        """Monitor for hotkey presses in background thread."""
        if not WIN32_AVAILABLE:
            return

        try:
            while self.is_monitoring:
                # Check for right mouse button
                right_click_state = win32api.GetAsyncKeyState(win32con.VK_RBUTTON)

                # Check for spacebar
                spacebar_state = win32api.GetAsyncKeyState(win32con.VK_SPACE)

                # If either key is pressed (high bit set indicates currently pressed)
                if (right_click_state & 0x8000) or (spacebar_state & 0x8000):
                    if self.stop_callback:
                        self.logger.info("Global hotkey detected - stopping automation")
                        self.stop_callback()
                    break

                # Small delay to prevent excessive CPU usage
                time.sleep(0.05)  # Check every 50ms

        except Exception as e:
            self.logger.error(f"Error in global hotkey monitoring: {e}")
        finally:
            self.is_monitoring = False
