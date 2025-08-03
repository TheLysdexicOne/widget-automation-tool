"""
Widget Spinner Automator (Frame ID: 2.4)
Handles automation for the Widget Spinner frame in WidgetInc.
"""

import time
import pyautogui
from typing import Any, Dict

from automation.base_automator import BaseAutomator


class WidgetSpinnerAutomator(BaseAutomator):
    """Automation logic for Widget Spinner (Frame 2.4)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        # Create button engines for clean syntax
        spin = self.create_button("spin")
        watch_point = self.frame_data["interactions"]["watch_point"]
        watch_color = self.frame_data["colors"]["watch_color"]
        fail = 0
        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            current_color = pyautogui.pixel(watch_point[0], watch_point[1])
            if current_color != watch_color:
                spin.click()
                self.sleep(0.1)
                if spin.active():
                    fail += 1
                else:
                    fail = 0
            if fail > 3:
                self.log_storage_error()
            if not self.sleep(0.01):
                break
