"""
Omega Processor Lab Automator (Frame ID: 12.1)
Handles automation for the Omega Processor Lab frame in WidgetInc.
"""

import pyautogui
import numpy as np
import time

from typing import Any, Dict
from automation.base_automator import BaseAutomator

from utility.window_utils import get_cropped_bbox_of_frame_screenshot
from utility.coordinate_utils import conv_frame_percent_to_screen_bbox


class OmegaProcessorLabAutomator(BaseAutomator):
    """Automation logic for Omega Processor Lab (Frame 12.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        target = self.frame_data["interactions"]["target"]
        # target = [0, 0]
        processors = {
            "circuit_board": {
                "point": self.frame_data["interactions"]["circuit_board"],
                "handle": self.frame_data["interactions"]["circuit_board_handle"],
                "color_map": self.frame_data["colors"]["circuit_board_color_map"],
            },
            "micro_processor": {
                "point": self.frame_data["interactions"]["micro_processor"],
                "handle": self.frame_data["interactions"]["micro_processor_handle"],
                "color_map": self.frame_data["colors"]["micro_processor_color_map"],
            },
            "nano_processor": {
                "point": self.frame_data["interactions"]["nano_processor"],
                "handle": self.frame_data["interactions"]["nano_processor_handle"],
                "color_map": self.frame_data["colors"]["nano_processor_color_map"],
            },
            "pico_processor": {
                "point": self.frame_data["interactions"]["pico_processor"],
                "handle": self.frame_data["interactions"]["pico_processor_handle"],
                "color_map": self.frame_data["colors"]["pico_processor_color_map"],
            },
        }
        all_processor_colors = set()
        for proc in processors.values():
            all_processor_colors.update(proc["color_map"])
        background_color_map = self.frame_data["colors"]["background_color_map"]
        inspect_bbox = self.frame_data["bbox"]["inspect_bbox"]

        drag_point_2 = self.frame_data["interactions"]["drag_point_2"]

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            # get color of target point and compare it to color_maps of each processor
            target_color = self.pixel(*target)
            self.logger.info(f"Target color: {target_color}")
            for name, data in processors.items():
                color_map = data["color_map"]
                if target_color in color_map:
                    self.logger.info(f"Target matches {name} color map")
                    self.mouseDown(*data["handle"])
                    self.moveTo(data["point"][0], data["point"][1] + 250, duration=0.1)
                    self.mouseUp()
                    break
            else:
                self.fatal_error(f"Target color {target_color} does not match {name} color map")
                break

            self.sleep(3)

            # using numpy to check the center line of the inspect bbox for not background colors
            # Convert inspect_bbox (frame bbox) to screen bbox first
            screen_bbox = (
                conv_frame_percent_to_screen_bbox(inspect_bbox) if isinstance(inspect_bbox[0], float) else inspect_bbox
            )
            # If inspect_bbox is already in screen coords, skip conversion

            img = get_cropped_bbox_of_frame_screenshot(inspect_bbox)
            if img is None:
                self.fatal_error("Failed to capture inspect_bbox screenshot")
                break
            img_np = np.array(img.convert("RGB"))
            height, width, _ = img_np.shape
            center_y = height // 2
            center_line = img_np[center_y, :, :]  # shape: (width, 3)

            # Read left to right, if a non-background color is found, move to that point +5px
            found_non_bg = False
            for x, pixel in enumerate(center_line):
                rgb = tuple(pixel)
                if self.should_continue and rgb not in background_color_map and rgb in all_processor_colors:
                    self.logger.info(f"Non-background color found at center line x={x}: {rgb}")
                    # Convert bbox-relative pixel to screen coordinates (+5px right)
                    screen_x = screen_bbox[0] + x + 10
                    screen_y = screen_bbox[1] + 10 + center_y
                    pyautogui.moveTo(screen_x, screen_y, duration=0.1)
                    pyautogui.mouseDown()
                    # pyautogui.moveTo(*drag_point_1, duration=0.5)
                    pyautogui.moveTo(*drag_point_2, duration=1.5)
                    self.sleep(1)
                    pyautogui.mouseUp()
                    found_non_bg = True
                    break

            if not found_non_bg:
                self.logger.info("All center line pixels are background color.")

            if not self.sleep(2):
                break
