"""
Global Hotkey Manager
Handles global hotkey detection for stopping automation.
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
        self.logger = logging.getLogger(self.__class__.__name__)
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_callback: Optional[Callable] = None

        # Check capabilities
        self.has_mouse_detection = WIN32_AVAILABLE
        self.has_keyboard_detection = WIN32_AVAILABLE

        if not (self.has_mouse_detection or self.has_keyboard_detection):
            self.logger.warning("No hotkey detection capabilities available")

    def set_stop_callback(self, callback: Callable):
        """Set the callback function to call when stop hotkey is detected."""
        self.stop_callback = callback

    def start_monitoring(self):
        """Start monitoring for global hotkeys."""
        if self.is_monitoring:
            return

        if not (self.has_mouse_detection or self.has_keyboard_detection):
            self.logger.warning("Cannot start hotkey monitoring - no detection capabilities")
            return

        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_hotkeys, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Global hotkey monitoring started (Right-click or Spacebar to stop automation)")

    def stop_monitoring(self):
        """Stop monitoring for global hotkeys."""
        if not self.is_monitoring:
            return

        self.is_monitoring = False

        # Only join if we're not trying to join from the monitor thread itself
        if self.monitor_thread and self.monitor_thread.is_alive():
            if threading.current_thread() != self.monitor_thread:
                self.monitor_thread.join(timeout=1.0)

        self.logger.info("Global hotkey monitoring stopped")

    def _monitor_hotkeys(self):
        """Monitor thread for hotkey detection."""
        self.logger.debug("Hotkey monitoring thread started")

        while self.is_monitoring:
            try:
                # Check for right mouse button
                if self.has_mouse_detection and self._is_right_mouse_pressed():
                    self.logger.info("Right mouse button detected - stopping automation")
                    self._emergency_mouse_cleanup()
                    if self.stop_callback:
                        self.stop_callback()
                    time.sleep(0.5)  # Debounce

                # Check for spacebar
                if self.has_keyboard_detection and self._is_spacebar_pressed():
                    self.logger.info("Spacebar detected - stopping automation")
                    self._emergency_mouse_cleanup()
                    if self.stop_callback:
                        self.stop_callback()
                    time.sleep(0.5)  # Debounce

                time.sleep(0.1)  # Check every 100ms

            except Exception as e:
                self.logger.error(f"Error in hotkey monitoring: {e}")
                time.sleep(0.5)

        self.logger.debug("Hotkey monitoring thread ended")

    def _is_right_mouse_pressed(self) -> bool:
        """Check if right mouse button is currently pressed."""
        if not WIN32_AVAILABLE:
            return False

        try:
            # Check if right mouse button is down
            return win32api.GetAsyncKeyState(win32con.VK_RBUTTON) & 0x8000 != 0
        except Exception:
            return False

    def _is_spacebar_pressed(self) -> bool:
        """Check if spacebar is currently pressed."""
        if WIN32_AVAILABLE:
            try:
                # Use win32api for spacebar detection (more reliable)
                return win32api.GetAsyncKeyState(win32con.VK_SPACE) & 0x8000 != 0
            except Exception:
                pass

        # Fallback: pyautogui doesn't have direct key state checking
        # so we can't reliably detect spacebar without hooking
        return False

    def _emergency_mouse_cleanup(self):
        """Emergency mouse cleanup - release any held mouse buttons."""
        try:
            import pyautogui

            pyautogui.mouseUp()  # Release any mouse button that might be held
            self.logger.debug("Emergency mouse cleanup performed")
        except Exception as e:
            self.logger.error(f"Error during emergency mouse cleanup: {e}")
