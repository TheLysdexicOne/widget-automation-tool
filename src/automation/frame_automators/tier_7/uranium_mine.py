"""
Uranium Mine Automator (Frame ID: 7.1)
Handles automation for the Uranium Mine frame in WidgetInc.
"""

import pyautogui
import time

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class UraniumMineAutomator(BaseAutomator):
    """Automation logic for Uranium Mine (Frame 7.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        left = self.create_button("left")
        right = self.create_button("right")

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            for button in [left, right]:
                while self.should_continue and not button.inactive():
                    pyautogui.mouseDown(button.x, button.y)
                pyautogui.mouseUp()

            if not self.sleep(0.1):
                break
