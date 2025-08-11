"""
Integrator Automator (Frame ID: 5.3)
Handles automation for the Integrator frame in WidgetInc.
"""

from typing import Any, Dict
import random

from automation.base_automator import BaseAutomator
from utility.window_utils import get_frame_screenshot


class IntegratorAutomator(BaseAutomator):
    """Automation logic for Integrator (Frame 5.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        # Frame-relative bounding boxes
        bbox_frame = self.frame_data["frame_xy"]["bbox"]
        output = bbox_frame["output"]
        input1 = bbox_frame["input1"]
        input2 = bbox_frame["input2"]
        input3 = bbox_frame["input3"]
        input_boxes = [input1, input2, input3]

        # Interaction click points (frame coords) - use these instead of computing centers
        int_data = self.frame_data["interactions"]
        input_clicks = [
            int_data["input1_click"],
            int_data["input2_click"],
            int_data["input3_click"],
        ]

        colors = self.frame_data["colors"]
        green = colors["green"]
        red = colors["red"]

        def get_state_tuple_for_box(box, screenshot, green_colors, red_colors, offset):
            x1, y1, x2, y2 = box
            w = x2 - x1
            h = y2 - y1
            dx = w * 0.375
            dy = h * 0.375
            pts = (
                (x1 + dx, y1 - offset),
                (x2 - dx, y1 - offset),
                (x2 + offset, y1 + dy),
                (x2 + offset, y2 - dy),
                (x1 + dx, y2 + offset),
                (x2 - dx, y2 + offset),
            )
            out = []
            for p in pts:
                if not self.should_continue:
                    break
                pixel_color = screenshot.getpixel(p)
                if pixel_color in green_colors:
                    out.append(1)
                elif pixel_color in red_colors:
                    out.append(2)
                else:
                    out.append(0)
            return tuple(out)

        while self.should_continue:
            screenshot = get_frame_screenshot()

            # Output signature
            output_tuple = get_state_tuple_for_box(output, screenshot, green, red, offset=5)
            self.log_debug(f"Output states: {output_tuple}")

            winner_index = None
            for idx, box in enumerate(input_boxes):
                if not self.should_continue:
                    break
                input_tuple = get_state_tuple_for_box(box, screenshot, green, red, offset=0)
                self.log_debug(f"Input{idx + 1} states: {input_tuple}")
                if input_tuple == output_tuple:
                    winner_index = idx
                    self.log_info(f"Winner: Input{idx + 1} matches output")
                    break

            if winner_index is not None:
                x, y = input_clicks[winner_index][:2]
                self.click(int(x), int(y))
            else:
                self.log_debug("No exact match; selecting random input")
                x, y = random.choice(input_clicks)[:2]
                self.click(int(x), int(y))

            if not self.sleep(1.5):
                break
