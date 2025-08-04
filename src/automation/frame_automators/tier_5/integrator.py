"""
Integrator Automator (Frame ID: 5.3)
Handles automation for the Integrator frame in WidgetInc.
"""

import time
from typing import Any, Dict

from automation.base_automator import BaseAutomator
from utility.window_utils import get_frame_screenshot, get_box, frame_to_screen_coords


class IntegratorAutomator(BaseAutomator):
    """Automation logic for Integrator (Frame 5.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        output = self.frame_data["frame_xy"]["interactions"]["output"]
        input1 = self.frame_data["frame_xy"]["interactions"]["input1"]
        input2 = self.frame_data["frame_xy"]["interactions"]["input2"]
        input3 = self.frame_data["frame_xy"]["interactions"]["input3"]

        border = self.frame_data["colors"]["border"]
        empty = self.frame_data["colors"]["empty"]
        green = self.frame_data["colors"]["green"]
        red = self.frame_data["colors"]["red"]

        screenshot = get_frame_screenshot()
        output_box = get_box(output, border, screenshot)
        input1_box = get_box(input1, border, screenshot)
        input2_box = get_box(input2, border, screenshot)
        input3_box = get_box(input3, border, screenshot)

        def get_state_tuple_for_box(box, screenshot, empty, green, red, offset):
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
                if pixel_color == empty:
                    state_tuple.append(0)
                elif pixel_color in green:
                    state_tuple.append(1)
                elif pixel_color in red:
                    state_tuple.append(2)
                else:
                    state_tuple.append(0)  # Treat unknown color as empty
            return tuple(state_tuple)

        import random
        import pyautogui

        input_boxes = [input1_box, input2_box, input3_box]

        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            screenshot = get_frame_screenshot()
            output_box = get_box(output, border, screenshot)
            input1_box = get_box(input1, border, screenshot)
            input2_box = get_box(input2, border, screenshot)
            input3_box = get_box(input3, border, screenshot)
            input_boxes = [input1_box, input2_box, input3_box]

            output_tuple = get_state_tuple_for_box(output_box, screenshot, empty, green, red, offset=5)
            self.logger.debug(f"Output pixel states: {output_tuple}  # 0=empty, 1=green, 2=red, -1=unknown")

            winner = None
            for idx, box in enumerate(input_boxes, 1):
                input_tuple = get_state_tuple_for_box(box, screenshot, empty, green, red, offset=0)
                self.logger.debug(f"Input{idx} pixel states: {input_tuple}  # 0=empty, 1=green, 2=red, -1=unknown")
                if input_tuple == output_tuple:
                    self.logger.info(f"Winner: Input{idx} matches output!")
                    winner = idx
                    # Click the center of the winning input box
                    x1, y1, x2, y2 = box
                    center_x = int((x1 + x2) / 2)
                    center_y = int((y1 + y2) / 2)
                    screen_x, screen_y = frame_to_screen_coords(center_x, center_y)
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
