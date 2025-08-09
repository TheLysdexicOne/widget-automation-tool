"""
Widget Minitizers Automator (Frame ID: 8.1)
Handles automation for the {filename} frame in WidgetInc.
"""

import pyautogui
import time

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class WidgetMinitizersAutomator(BaseAutomator):
    """Automation logic for Widget Minitizers (Frame 8.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        shrink = self.create_button("shrink")

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            pyautogui.PAUSE = 0
            pyautogui.click(shrink.x, shrink.y)

            if not self.sleep(0.05):
                break
