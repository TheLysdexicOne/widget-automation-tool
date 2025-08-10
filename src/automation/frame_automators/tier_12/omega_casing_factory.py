"""
Omega Casing Factory Automator (Frame ID: 12.4)
Handles automation for the Omega Casing Factory frame in WidgetInc.
"""

import pyautogui
import time

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class OmegaCasingFactoryAutomator(BaseAutomator):
    """Automation logic for Omega Casing Factory (Frame 12.4)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        lever_off = self.frame_data["interactions"]["lever_off"]
        lever_on = self.frame_data["interactions"]["lever_on"]
        handle_up = self.frame_data["interactions"]["handle_up"]
        handle_down = self.frame_data["interactions"]["handle_down"]
        watch_point = self.frame_data["interactions"]["watch_point"]

        print(handle_up)

        background_colors = self.frame_data["colors"]["background_colors"]
        lever_color = self.frame_data["colors"]["lever_color"]

        if pyautogui.pixel(*watch_point) in background_colors:
            pyautogui.mouseDown(*lever_off)
            pyautogui.moveTo(*lever_on)
        while self.should_continue and pyautogui.pixel(*watch_point) in background_colors:
            self.sleep(0.1)

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            self.logger.debug("Moving Handle")
            pyautogui.mouseDown(*handle_up)
            pyautogui.moveTo(*handle_down, duration=0.1)
            pyautogui.mouseUp()

            while pyautogui.pixel(*lever_off) != lever_color:
                self.sleep(0.05)
            pyautogui.mouseDown(*lever_off)
            pyautogui.moveTo(*lever_on, duration=0.1)
            while self.should_continue and pyautogui.pixel(*watch_point) not in background_colors:
                self.logger.debug("waiting for object to pass")
                self.sleep(0.05)

            while self.should_continue and pyautogui.pixel(*watch_point) in background_colors:
                self.logger.debug("waiting for new object")
                self.sleep(0.05)
            pyautogui.mouseUp()
            continue
