"""
Training Center Automator (Frame ID: 10.1)
Handles automation for the Training Center frame in WidgetInc.
"""

import pyautogui
import time

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class TrainingCenterAutomator(BaseAutomator):
    """Automation logic for Training Center (Frame 10.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        pyautogui.PAUSE = 0
        interactions = self.frame_data["interactions"]

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            for key in interactions:
                x, y = interactions[key]
                r, g, b = pyautogui.pixel(x, y)
                if r > 240:
                    pyautogui.click(x, y)

            if not self.sleep(0.05):
                break
