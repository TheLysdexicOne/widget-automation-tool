"""
Widget Factory Automator (Frame ID: 1.3)
Handles automation for the Widget Factory frame in WidgetInc.
"""

import time
from typing import Any, Dict

import pyautogui
from automation.base_automator import BaseAutomator


class WidgetFactoryAutomator(BaseAutomator):
    """Automation logic for Widget Factory (Frame 1.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        """Click create button repeatedly."""
        start_time = time.time()
        pyautogui.PAUSE = 0
        # Create button engine for clean syntax
        create = self.create_button("create")
        pbar = self.frame_data["interactions"]["pbar"]
        pbar_color = self.frame_data["colors"]["pbar_color"]

        fail = 0
        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break
            if not create.inactive():
                create.click()
                if not pyautogui.pixel(*pbar) == pbar_color:
                    fail += 1
                    if fail > 10:
                        self.log_storage_error()
                        break
                    else:
                        fail = 0
            if not self.sleep(0.05):
                break
