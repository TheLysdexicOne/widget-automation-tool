"""
Battery Assembler Automator (Frame ID: 3.3)
Handles automation for the Battery Assembler frame in WidgetInc.
"""

import time
import pyautogui
from typing import Any, Dict

from automation.base_automator import BaseAutomator


class BatteryAssemblerAutomator(BaseAutomator):
    """Automation logic for Battery Assembler (Frame 3.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        """Optimized alternating plus/minus clicking with progress detection."""
        start_time = time.time()

        plus = self.create_button("plus")
        minus = self.create_button("minus")
        pbar_x, pbar_y = self.frame_data["interactions"]["progress_bar"]
        pbar_color = (0, 95, 149)
        if plus.active():
            use_plus = True
        else:
            use_plus = False
        last_progress_time = time.time()
        progress_timeout = 5.0  # Stop if no progress for 5 seconds

        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            # Check for progress timeout
            if time.time() - last_progress_time > progress_timeout:
                self.log_storage_error()
                break

            # Alternate between plus and minus buttons
            button = plus if use_plus else minus
            if button.active():
                button.click()
                use_plus = not use_plus  # Switch to other button

            # Check if progress bar shows activity (color changed)
            if pyautogui.pixel(pbar_x, pbar_y) == pbar_color:
                last_progress_time = time.time()  # Reset progress timer

            if not self.sleep(0.01):
                break
