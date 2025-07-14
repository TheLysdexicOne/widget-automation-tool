"""
Process Monitor

Monitors for the target process (WidgetInc.exe) and manages window detection.
"""

import logging
import psutil
import time
from typing import Optional, List

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
import pygetwindow as gw


class ProcessMonitor(QObject):
    """Monitors for target processes and windows."""

    # Signals
    target_found = pyqtSignal(int)  # hwnd
    target_lost = pyqtSignal()

    def __init__(self, app, target_process_name="WidgetInc.exe"):
        super().__init__()
        self.app = app
        self.logger = logging.getLogger(__name__)
        self.target_process_name = target_process_name

        # Monitoring state
        self.is_monitoring = False
        self.current_target_hwnd = None
        self.current_target_pid = None

        # Timer for periodic checks
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._check_target_process)
        self.monitor_interval = 1000  # Check every 1 second

    def start_monitoring(self):
        """Start monitoring for the target process."""
        if self.is_monitoring:
            return

        self.logger.info(f"Starting process monitoring for: {self.target_process_name}")
        self.is_monitoring = True

        # Do an initial check
        self._check_target_process()

        # Start the timer
        self.monitor_timer.start(self.monitor_interval)

    def stop_monitoring(self):
        """Stop monitoring for the target process."""
        if not self.is_monitoring:
            return

        self.logger.info("Stopping process monitoring")
        self.is_monitoring = False

        # Stop the timer
        self.monitor_timer.stop()

        # Clear current target
        if self.current_target_hwnd:
            self._on_target_lost()

    def _check_target_process(self):
        """Check if the target process is running and accessible."""
        try:
            # Look for the target process
            target_processes = self._find_target_processes()

            if not target_processes:
                # No target process found
                if self.current_target_hwnd:
                    self._on_target_lost()
                return

            # Check if we already have a valid target
            if self.current_target_hwnd and self.current_target_pid:
                # Verify the current target is still valid
                if self._is_process_alive(self.current_target_pid):
                    if self._is_window_valid(self.current_target_hwnd):
                        return  # Current target is still valid

                # Current target is no longer valid
                self._on_target_lost()

            # Try to find a valid window for the target process
            for process in target_processes:
                windows = self._get_process_windows(process.pid)
                if windows:
                    # Use the first valid window
                    window = windows[0]
                    self._on_target_found(window, process.pid)
                    break

        except Exception as e:
            self.logger.error(f"Error during process monitoring: {e}")

    def _find_target_processes(self) -> List[psutil.Process]:
        """Find all instances of the target process."""
        target_processes = []

        try:
            for process in psutil.process_iter(["pid", "name"]):
                try:
                    if process.info["name"].lower() == self.target_process_name.lower():
                        target_processes.append(process)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            self.logger.error(f"Error finding target processes: {e}")

        return target_processes

    def _get_process_windows(self, pid: int) -> List:
        """Get windows for a specific process ID."""
        windows = []

        try:
            # Use pygetwindow to find windows
            all_windows = gw.getAllWindows()

            # Get the process name without .exe for window title matching
            process_name_base = self.target_process_name.lower().replace(".exe", "")

            for window in all_windows:
                try:
                    # Check if this window belongs to our target process
                    # First try: exact process name match in title
                    if (
                        hasattr(window, "_hWnd")
                        and window.visible
                        and window.title
                        and process_name_base in window.title.lower()
                        and "Widget Automation Tool" not in window.title
                    ):
                        windows.append(window)
                        self.logger.debug(
                            f"Found target window (exact match): {window.title}"
                        )
                        continue

                    # Second try: for common applications, look for specific patterns
                    if self.target_process_name.lower() == "notepad.exe":
                        if "notepad" in window.title.lower() or window.title.endswith(
                            " - Notepad"
                        ):
                            windows.append(window)
                            self.logger.debug(f"Found Notepad window: {window.title}")
                    elif self.target_process_name.lower() == "calc.exe":
                        if "calculator" in window.title.lower():
                            windows.append(window)
                            self.logger.debug(
                                f"Found Calculator window: {window.title}"
                            )

                except Exception:
                    continue

        except Exception as e:
            self.logger.error(f"Error getting process windows: {e}")

        return windows

    def _is_process_alive(self, pid: int) -> bool:
        """Check if a process is still alive."""
        try:
            process = psutil.Process(pid)
            return process.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def _is_window_valid(self, hwnd) -> bool:
        """Check if a window handle is still valid."""
        try:
            # Try to get window info to verify it's still valid
            # This is a simplified check
            windows = gw.getAllWindows()
            for window in windows:
                if hasattr(window, "_hWnd") and window._hWnd == hwnd:
                    return window.visible
            return False
        except Exception:
            return False

    def _on_target_found(self, window, pid: int):
        """Handle target process/window found."""
        try:
            hwnd = window._hWnd if hasattr(window, "_hWnd") else id(window)

            if hwnd != self.current_target_hwnd:
                self.current_target_hwnd = hwnd
                self.current_target_pid = pid

                self.logger.info(
                    f"Target window found - PID: {pid}, HWND: {hwnd}, Title: {window.title}"
                )
                self.target_found.emit(hwnd)

        except Exception as e:
            self.logger.error(f"Error handling target found: {e}")

    def _on_target_lost(self):
        """Handle target process/window lost."""
        if self.current_target_hwnd:
            self.logger.info(f"Target window lost - HWND: {self.current_target_hwnd}")
            self.current_target_hwnd = None
            self.current_target_pid = None
            self.target_lost.emit()

    def get_current_target_info(self) -> Optional[dict]:
        """Get information about the current target."""
        if not self.current_target_hwnd:
            return None

        try:
            return {
                "hwnd": self.current_target_hwnd,
                "pid": self.current_target_pid,
                "process_name": self.target_process_name,
            }
        except Exception as e:
            self.logger.error(f"Error getting target info: {e}")
            return None
