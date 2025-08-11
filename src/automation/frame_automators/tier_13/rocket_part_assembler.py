"""
Rocket Part Assembler Automator (Frame ID: 13.3)
Handles automation for the Rocket Part Assembler frame in WidgetInc.
"""

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class RocketPartAssemblerAutomator(BaseAutomator):
    """Automation logic for Rocket Part Assembler (Frame 13.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        lever1 = self.frame_data["interactions"]["lever1"]
        lever2 = self.frame_data["interactions"]["lever2"]
        catch_point1 = self.frame_data["interactions"]["catch_point1"]
        catch_point2 = self.frame_data["interactions"]["catch_point2"]
        piston_retracted = self.frame_data["interactions"]["piston_retracted"]
        piston_extended = self.frame_data["interactions"]["piston_extended"]
        processing_point = self.frame_data["interactions"]["processing_point"]
        drop_point = self.frame_data["interactions"]["drop_point"]

        background_color_map = self.frame_data["colors"]["background_color_map"]
        processing_color = self.frame_data["colors"]["processing_color"]

        # For each lever/catch_point pair, perform the drag-and-drop sequence
        lever_points = [lever1, lever2]
        catch_points = [catch_point1, catch_point2]

        # Main automation loop
        while self.should_continue:
            for lever, catch_point in zip(lever_points, catch_points):
                self.mouseDown(*lever)
                self.moveTo(catch_point[0], catch_point[1], duration=0.1)
                self.mouseUp()

                while self.pixel(*catch_point) in background_color_map:
                    self.sleep(0.05)

                self.mouseDown()
                self.moveTo(drop_point[0], drop_point[1], duration=1.5)
                self.sleep(1)
                self.mouseUp()

            self.mouseDown(*piston_retracted)
            self.moveTo(piston_extended[0], piston_extended[1], duration=1)
            self.mouseUp()

            self.sleep(1)
            while self.pixel(*processing_point) == processing_color:
                self.sleep(0.1)

            if not self.sleep(0.05):
                break
