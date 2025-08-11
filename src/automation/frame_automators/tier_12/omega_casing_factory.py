"""
Omega Casing Factory Automator (Frame ID: 12.4)
Handles automation for the Omega Casing Factory frame in WidgetInc.
"""

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class OmegaCasingFactoryAutomator(BaseAutomator):
    """Automation logic for Omega Casing Factory (Frame 12.4)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        lever_off = self.frame_data["interactions"]["lever_off"]
        lever_on = self.frame_data["interactions"]["lever_on"]
        piston_retracted = self.frame_data["interactions"]["piston_retracted"]
        piston_extended = self.frame_data["interactions"]["piston_extended"]
        watch_point = self.frame_data["interactions"]["watch_point"]

        background_colors = self.frame_data["colors"]["background_colors"]
        lever_color = self.frame_data["colors"]["lever_color"]

        if self.pixel(*watch_point) in background_colors:
            self.mouseDown(*lever_off)
            self.moveTo(*lever_on)
        while self.should_continue and self.pixel(*watch_point) in background_colors:
            self.sleep(0.1)

        # Main automation loop
        while self.should_continue:
            self.mouseDown(*piston_retracted)
            self.moveTo(*piston_extended, duration=0.1)
            self.mouseUp()

            while self.pixel(*lever_off) != lever_color:
                self.sleep(0.05)
            self.mouseDown(*lever_off)
            self.moveTo(*lever_on, duration=0.1)
            while self.should_continue and self.pixel(*watch_point) not in background_colors:
                self.sleep(0.05)

            while self.should_continue and self.pixel(*watch_point) in background_colors:
                self.sleep(0.05)
            self.mouseUp()
            continue
