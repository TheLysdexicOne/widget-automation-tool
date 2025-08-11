"""
Processor Lab Automator (Frame ID: 6.2)
Handles automation for the Processor Lab frame in WidgetInc.
"""

import pyautogui


from typing import Any, Dict
from automation.base_automator import BaseAutomator


class ProcessorLabAutomator(BaseAutomator):
    """Automation logic for Processor Lab (Frame 6.2)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        pyautogui.PAUSE = 0

    def run_automation(self):
        process = self.create_button("process")
        piston_retracted = self.frame_data["interactions"]["piston_retracted"]
        piston_extended = self.frame_data["interactions"]["piston_extended"]
        piston_colors = self.frame_data["colors"]["piston_colors"]

        # Main automation loop
        while self.should_continue:
            color = self.pixel(piston_retracted[0], piston_retracted[1])
            if color in piston_colors:
                self.mouseDown(piston_retracted[0], piston_retracted[1])
                self.moveTo(piston_extended[0], piston_extended[1], duration=0.2)
                self.mouseUp()
                color = (0, 0, 0)
                while self.should_continue and color not in piston_colors:
                    process.click(ignore=True)
                    self.sleep(0.01)
                    color = self.pixel(piston_extended[0], piston_extended[1])

            if not self.sleep(0.1):
                break
