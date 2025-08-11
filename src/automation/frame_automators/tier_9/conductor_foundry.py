"""
Conductor Foundry Automator (Frame ID: 9.2)
Handles automation for the Conductor Foundry frame in WidgetInc.
"""

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class ConductorFoundryAutomator(BaseAutomator):
    """Automation logic for Conductor Foundry (Frame 9.2)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        nullify = self.create_button("nullify")

        piston1_retracted = self.frame_data["interactions"]["piston1_retracted"]
        piston1_extended = self.frame_data["interactions"]["piston1_extended"]
        piston2_retracted = self.frame_data["interactions"]["piston2_retracted"]
        piston2_extended = self.frame_data["interactions"]["piston2_extended"]

        piston_color_map = self.frame_data["colors"]["piston_color_map"]

        # Main automation loop
        while self.should_continue:
            if self.pixel(*piston1_retracted) in piston_color_map:
                self.mouseDown(*piston1_retracted, duration=0.1)
                self.moveTo(*piston1_extended)
                self.mouseUp()
            if self.pixel(*piston2_retracted) in piston_color_map:
                self.mouseDown(*piston2_retracted, duration=0.1)
                self.moveTo(*piston2_extended)
                self.mouseUp()

            nullify.click()

            if not self.sleep(2.5):
                break
