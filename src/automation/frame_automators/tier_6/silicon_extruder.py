"""
Silicon Extruder Automator (Frame ID: 6.1)
Handles automation for the Silicon Extruder frame in WidgetInc.
"""

import pyautogui
import time

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class SiliconExtruderAutomator(BaseAutomator):
    """Automation logic for Silicon Extruder (Frame 6.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        slider = self.frame_data["interactions"]["slider"]
        slider_color = pyautogui.pixel(slider[0], slider[1])

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            color = pyautogui.pixel(slider[0], slider[1])
            if color == slider_color:
                pyautogui.mouseDown(slider[0], slider[1])
                pyautogui.moveTo(slider[0] + 500, slider[1], duration=0.1)
                pyautogui.mouseUp()

            if not self.sleep(0.1):
                break
