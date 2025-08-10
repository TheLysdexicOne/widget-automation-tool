"""
Rocket Fuel Distiller Automator (Frame ID: 13.2)
Handles automation for the Rocket Fuel Distiller frame in WidgetInc.
"""

import time

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class RocketFuelDistillerAutomator(BaseAutomator):
    """Automation logic for Rocket Fuel Distiller (Frame 13.2)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        distill = self.create_button("distill")

        piston1 = self.frame_data["interactions"]["piston1_retracted"]
        piston2 = self.frame_data["interactions"]["piston2_retracted"]
        piston3 = self.frame_data["interactions"]["piston3_retracted"]

        extended_x = self.frame_data["interactions"]["piston_extended"][0]

        piston_color_map = self.frame_data["colors"]["piston_color_map"]
        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break
            while self.should_continue and self.pixel(*piston3) not in piston_color_map:
                self.sleep(0.1)
            self.mouseDown(*piston3)
            self.moveTo(extended_x, piston3[1], duration=0.1)
            self.mouseUp()

            while self.should_continue and self.pixel(*piston2) not in piston_color_map:
                self.sleep(0.1)
            self.mouseDown(*piston2)
            self.moveTo(extended_x, piston2[1], duration=0.1)
            self.mouseUp()

            while self.should_continue and self.pixel(*piston1) not in piston_color_map:
                self.sleep(0.1)
            self.mouseDown(*piston1)
            self.moveTo(extended_x, piston1[1], duration=0.1)
            self.mouseUp()

            distill.click()

            if not self.sleep(0.1):
                break
