"""
Conductor Foundry Automator (Frame ID: 9.2)
Handles automation for the Conductor Foundry frame in WidgetInc.
"""

import pyautogui
import time

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class ConductorFoundryAutomator(BaseAutomator):
    """Automation logic for Conductor Foundry (Frame 9.2)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        nullify = self.create_button("nullify")

        handle1 = self.frame_data["interactions"]["handle1"]
        handle1_active = self.frame_data["interactions"]["handle1_active"]
        handle2 = self.frame_data["interactions"]["handle2"]
        handle2_active = self.frame_data["interactions"]["handle2_active"]

        handle_colors = self.frame_data["colors"]["handle_colors"]

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            if pyautogui.pixel(*handle1) in handle_colors:
                pyautogui.mouseDown(*handle1, duration=0.1)
                pyautogui.moveTo(*handle1_active)
                pyautogui.mouseUp()
            if pyautogui.pixel(*handle2) in handle_colors:
                pyautogui.mouseDown(*handle2, duration=0.1)
                pyautogui.moveTo(*handle2_active)
                pyautogui.mouseUp()

            nullify.click()

            if not self.sleep(2.5):
                break
