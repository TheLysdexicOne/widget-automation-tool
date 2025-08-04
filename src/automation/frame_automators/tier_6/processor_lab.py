"""
Processor Lab Automator (Frame ID: 6.2)
Handles automation for the Processor Lab frame in WidgetInc.
"""

import pyautogui
import time

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class ProcessorLabAutomator(BaseAutomator):
    """Automation logic for Processor Lab (Frame 6.2)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        pyautogui.PAUSE = 0

        process = self.create_button("process")
        handle = self.frame_data["interactions"]["handle"]
        release = self.frame_data["interactions"]["release"]
        handle_colors = self.frame_data["colors"]["handle_colors"]

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break
            color = pyautogui.pixel(handle[0], handle[1])
            if color in handle_colors:
                pyautogui.mouseDown(handle[0], handle[1])
                pyautogui.moveTo(release[0], release[1], duration=0.2)
                pyautogui.mouseUp()
                color = (0, 0, 0)
                while self.should_continue and color not in handle_colors:
                    process.click(ignore=True)
                    self.sleep(0.01)
                    color = pyautogui.pixel(handle[0], handle[1])

            if not self.sleep(0.1):
                break
