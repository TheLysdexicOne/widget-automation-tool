"""
Omega Shielding Plant Automator (Frame ID: 12.5)
Handles automation for the Omega Shielding Plant frame in WidgetInc.
"""

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class OmegaShieldingPlantAutomator(BaseAutomator):
    """Automation logic for Omega Shielding Plant (Frame 12.5)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        lever_up = self.frame_data["interactions"]["lever_up"]
        lever_down = self.frame_data["interactions"]["lever_down"]
        indicator_x = self.frame_data["interactions"]["indicator_x"][0]

        watch_bbox = self.frame_data["bbox"]["watch_bbox"]
        center_x = (self.frame_data["bbox"]["watch_bbox"][0] + self.frame_data["bbox"]["watch_bbox"][2]) // 2
        bottom_y = self.frame_data["bbox"]["watch_bbox"][3]
        indicator_color = self.frame_data["colors"]["indicator_color"]
        background_color = self.frame_data["colors"]["background_color"]

        indicator_xy1 = (indicator_x, watch_bbox[1])

        # Main automation loop
        while self.should_continue:
            # Find indicator y
            for y in range(watch_bbox[1], watch_bbox[3]):
                if self.pixelMatchesColor(indicator_xy1[0], y, indicator_color):
                    indicator_y = y
                    break
            print(y)

            self.mouseDown(lever_up[0], lever_up[1])
            self.moveTo(lever_down[0], lever_down[1])

            # watch bbox at indicator y value
            while self.should_continue and self.pixel(center_x, indicator_y + 20) == background_color:
                self.sleep(0.05)

            self.mouseUp()
            while self.should_continue and self.pixel(center_x, bottom_y) != background_color:
                self.sleep(0.1)

            if not self.sleep(0.1):
                break
