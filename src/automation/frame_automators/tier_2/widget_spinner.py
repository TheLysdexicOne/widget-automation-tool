"""
Widget Spinner Automator (Frame ID: 2.4)
Handles automation for the Widget Spinner frame in WidgetInc.
"""

import time
from typing import Any, Dict

from automation.base_automator import BaseAutomator
from utility.window_utils import grid_to_screen_coords


class WidgetSpinnerAutomator(BaseAutomator):
    """Automation logic for Widget Spinner (Frame 2.4)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        # Create button engines for clean syntax
        spin = self.create_button("spin")
        point = (87, 33)
        scan_point = grid_to_screen_coords(point[0], point[1])
        scan_color = (57, 63, 70)

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            if not self.scan.pixel_watcher(scan_point, scan_color, timeout=30.0, check_interval=0.004):
                self.log_timeout_error()
                break
            spin.click()
            if not self.sleep(0.25):
                break
