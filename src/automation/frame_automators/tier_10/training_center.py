"""
Training Center Automator (Frame ID: 10.1)
Handles automation for the Training Center frame in WidgetInc.
"""

import pyautogui


from typing import Any, Dict
from automation.base_automator import BaseAutomator


class TrainingCenterAutomator(BaseAutomator):
    """Automation logic for Training Center (Frame 10.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        pyautogui.PAUSE = 0

    def run_automation(self):
        interactions = self.frame_data["interactions"]["lights"]

        # Main automation loop
        while self.should_continue:
            for key in interactions:
                x, y = interactions[key]
                r, g, b = self.pixel(x, y)
                if r > 240:
                    self.click(x, y)

            if not self.sleep(0.05):
                break
