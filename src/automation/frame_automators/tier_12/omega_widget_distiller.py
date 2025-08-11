"""
Omega Widget Distiller Automator (Frame ID: 12.3)
Handles automation for the Omega Widget Distiller frame in WidgetInc.
"""

import json

from typing import Any, Dict
from automation.base_automator import BaseAutomator


class OmegaWidgetDistillerAutomator(BaseAutomator):
    """Automation logic for Omega Widget Distiller (Frame 12.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

        # Load widget color map
        with open("src/automation/frame_automators/tier_12/widget_color_map.json", "r") as f:
            self.widget_color_map = set(tuple(c) for c in json.load(f))

        self.drag_point_1 = self.frame_data["interactions"]["drag_point_1"]
        self.drag_point_2 = self.frame_data["interactions"]["drag_point_2"]
        self.drag_point_3 = self.frame_data["interactions"]["drag_point_3"]
        self.watch_bbox = self.frame_data["bbox"]["watch_bbox"]

    def run_automation(self):
        # Main automation loop
        while self.should_continue:
            x1, y1, x2, y2 = self.watch_bbox
            center_y = round((y1 + y2) // 2)  # vertical center of the bbox

            found = False
            # Scan right-to-left, skipping 5px at a time
            for x in range(x2, x1 - 1, -5):
                color = self.pixel(x, center_y)
                if self.should_continue and color[:3] in self.widget_color_map:
                    self.logger.info(f"Widget color found at ({x}, {center_y}): {color}")
                    self.moveTo(x, center_y, duration=0.1)
                    self.mouseDown()
                    self.moveTo(*self.drag_point_1, duration=0.5)
                    self.moveTo(*self.drag_point_2, duration=1)
                    self.moveTo(*self.drag_point_3, duration=0.5)
                    self.sleep(1)
                    self.mouseUp()
                    found = True
                    break

            if not found:
                self.logger.info("Widget color not found, adjusting search area.")
                # Optionally, adjust the search area or take other actions
                pass

            if not self.sleep(0.05):
                break
