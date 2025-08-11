"""
Fuel Rod Assembler Automator (Frame ID: 7.2)
Handles automation for the Fuel Rod Assembler frame in WidgetInc.
"""

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class FuelRodAssemblerAutomator(BaseAutomator):
    """Automation logic for Fuel Rod Assembler (Frame 7.2)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        refine = self.create_button("refine")
        lever_up = self.frame_data["interactions"]["lever_up"]
        lever_down = self.frame_data["interactions"]["lever_down"]
        drop_point = self.frame_data["interactions"]["drop_point"]
        pickup_point = self.frame_data["interactions"]["pickup_point"]

        x1, y1, x2, y2 = self.frame_data["bbox"]["pickup_bbox"]

        y = round((y1 + y2) // 2)
        print(f"Pickup bbox Y: {y}")

        background_colors = self.frame_data["colors"]["background_colors"]

        # Main automation loop
        while self.should_continue:
            self.mouseDown(lever_up[0], lever_up[1])
            self.moveTo(lever_down[0], lever_down[1], duration=0.2)
            self.mouseUp()
            self.sleep(1.5)
            for x in range(x1, x2 + 1, 5):
                color = self.pixel(x, int(y))
                if self.should_continue and color not in background_colors:
                    self.mouseDown(x + 20, y)
                    self.moveTo(pickup_point[0], pickup_point[1], duration=0.5)
                    self.moveTo(drop_point[0], drop_point[1], duration=1.5)

                    self.sleep(1)
                    self.mouseUp()
                    self.sleep(0.5)
                    break

            for _ in range(4):
                refine.click()
                self.sleep(0.05)

            if not self.sleep(0.1):
                break
