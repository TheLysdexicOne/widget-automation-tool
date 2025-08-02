"""
Compute Engine Automator (Frame ID: 4.5)
Handles automation for the Compute Engine frame in WidgetInc.
"""

from functools import cache
import time

from typing import Any, Dict

import pyautogui

from automation.base_automator import BaseAutomator
from utility.window_utils import grid_to_screen_coords
from utility.cache_manager import get_cache_manager


class ComputeEngineAutomator(BaseAutomator):
    """Automation logic for Compute Engine (Frame 4.5)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        cache_manager = get_cache_manager()

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break
            answer_grids = [self.frame_data["buttons"][f"answer{i}"][:-1] for i in range(1, 5)]

            pixel_size = cache_manager.get_pixel_size() or 1
            answer_screen_wh = round(8 * pixel_size)

            answer_bboxes = [
                (grid[0], grid[1], grid[0] + answer_screen_wh, grid[1] + answer_screen_wh) for grid in answer_grids
            ]
            print(f"Answer bboxes: {answer_bboxes}")

            equation_bbox = (
                self.frame_data["interactions"]["equation_tl"][0],
                self.frame_data["interactions"]["equation_tl"][1],
                self.frame_data["interactions"]["equation_br"][0],
                self.frame_data["interactions"]["equation_br"][1],
            )

            print(f"Equation bbox: {equation_bbox}")
            answer1 = self.create_button("answer1")
            answer2 = self.create_button("answer2")
            answer3 = self.create_button("answer3")
            answer4 = self.create_button("answer4")
