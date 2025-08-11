"""
Silicon Extruder Automator (Frame ID: 6.1)
Handles automation for the Silicon Extruder frame in WidgetInc.
"""

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class SiliconExtruderAutomator(BaseAutomator):
    """Automation logic for Silicon Extruder (Frame 6.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        slider_left = self.frame_data["interactions"]["slider_left"]
        slider_right = self.frame_data["interactions"]["slider_right"]
        slider_color = self.pixel(*slider_left)

        # Main automation loop
        while self.should_continue:
            color = self.pixel(*slider_left)
            if color == slider_color:
                self.mouseDown(*slider_left)
                self.moveTo(*slider_right, duration=0.1)
                self.mouseUp()

            if not self.sleep(0.1):
                break
