"""
Integrator Automator (Frame ID: 5.3)
Handles automation for the Integrator frame in WidgetInc.
"""

import time
from typing import Any, Dict
import random
import pyautogui

from automation.base_automator import BaseAutomator
from utility.window_utils import get_frame_screenshot
from utility.coordinate_utils import conv_frame_coords_to_screen_coords


class IntegratorAutomator(BaseAutomator):
    """Automation logic for Integrator (Frame 5.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        output = self.frame_data["frame_xy"]["bbox"]["output"]
        input1 = self.frame_data["frame_xy"]["bbox"]["input1"]
        input2 = self.frame_data["frame_xy"]["bbox"]["input2"]
        input3 = self.frame_data["frame_xy"]["bbox"]["input3"]

        green = self.frame_data["colors"]["green"]
        red = self.frame_data["colors"]["red"]

        def get_state_tuple_for_box(box, screenshot, green, red, offset):
            x1, y1, x2, y2 = box
            width = x2 - x1
            height = y2 - y1
            third_w = width * 0.375
            third_h = height * 0.375

            # Points: just outside the border, split in thirds
            points = [
                (x1 + third_w, y1 - offset),  # Top left third
                (x2 - third_w, y1 - offset),  # Top right third
                (x2 + offset, y1 + third_h),  # Right upper third
                (x2 + offset, y2 - third_h),  # Right lower third
                (x1 + third_w, y2 + offset),  # Bottom left third
                (x2 - third_w, y2 + offset),  # Bottom right third
            ]

            state_tuple = []
            for point in points:
                pixel_color = screenshot.getpixel(point)
                if pixel_color in green:
                    state_tuple.append(1)
                elif pixel_color in red:
                    state_tuple.append(2)
                else:
                    state_tuple.append(0)
            return tuple(state_tuple)

        input_boxes = [input1, input2, input3]

        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break
            screenshot = get_frame_screenshot()
            input_boxes = [input1, input2, input3]

            output_tuple = get_state_tuple_for_box(output, screenshot, green, red, offset=5)
            self.logger.debug(f"Output pixel states: {output_tuple}  # 0=unknown, 1=green, 2=red")

            winner = None
            for idx, box in enumerate(input_boxes, 1):
                input_tuple = get_state_tuple_for_box(box, screenshot, green, red, offset=0)
                self.logger.debug(f"Input{idx} pixel states: {input_tuple}  # 0=unknown, 1=green, 2=red")
                if input_tuple == output_tuple:
                    self.logger.info(f"Winner: Input{idx} matches output!")
                    winner = idx
                    # Click the center of the winning input box
                    x1, y1, x2, y2 = box
                    center_x = int((x1 + x2) / 2)
                    center_y = int((y1 + y2) / 2)
                    screen_x, screen_y = conv_frame_coords_to_screen_coords(center_x, center_y)
                    pyautogui.click(screen_x, screen_y)
                    break

            if winner is None:
                self.logger.warning("No input matches the output. Clicking random input to continue.")
                # Click a random input box center
                box = random.choice(input_boxes)
                x1, y1, x2, y2 = box
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                self.engine.frame_click(center_x, center_y)

            if not self.sleep(1.5):
                break
