"""
Omega Project Assembler Automator (Frame ID: 12.6)
Handles automation for the Omega Project Assembler frame in WidgetInc.
"""

import pyautogui
import time

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class OmegaProjectAssemblerAutomator(BaseAutomator):
    """Automation logic for Omega Project Assembler (Frame 12.6)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        imbue = self.create_button("imbue")
        sacrifice = self.create_button("sacrifice")
        install = self.create_button("install")
        assemble = self.create_button("assemble")

        lever_up = self.frame_data["interactions"]["lever_up"]
        lever_down = self.frame_data["interactions"]["lever_down"]
        slider_left = self.frame_data["interactions"]["slider_left"]
        slider_right = self.frame_data["interactions"]["slider_right"]

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            pyautogui.mouseDown(lever_up[0], lever_up[1])
            pyautogui.moveTo(lever_down[0], lever_down[1], duration=0.1)
            pyautogui.mouseUp(duration=0.1)

            imbue.click()
            sacrifice.click()
            install.click()

            pyautogui.mouseDown(slider_left[0], slider_left[1])
            pyautogui.moveTo(slider_right[0], slider_right[1], duration=0.1)
            pyautogui.mouseUp(duration=0.1)

            assemble.click()

            while not assemble.active():
                if not self.sleep(0.1):
                    break
