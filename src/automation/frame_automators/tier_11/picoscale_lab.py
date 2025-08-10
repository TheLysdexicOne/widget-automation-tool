"""
Picoscale Lab Automator (Frame ID: 11.2)
Handles automation for the Picoscale Lab frame in WidgetInc.
"""

from imagehash import phash

import time

from PIL import ImageGrab
from typing import Any, Dict
from automation.base_automator import BaseAutomator


class PicoscaleLabAutomator(BaseAutomator):
    """Automation logic for Picoscale Lab (Frame 11.2)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        pass_button = self.create_button("pass")
        fail_button = self.create_button("fail")

        sample_bbox = self.frame_data["bbox"]["sample"]
        compare_bbox = self.frame_data["bbox"]["compare"]

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            sample_hash = phash(ImageGrab.grab(bbox=sample_bbox, all_screens=True))
            compare_hash = phash(ImageGrab.grab(bbox=compare_bbox, all_screens=True))

            # Use Hamming distance for tolerance
            threshold = 2  # Allow up to 4 bits difference
            if sample_hash - compare_hash <= threshold:
                pass_button.click()
            else:
                fail_button.click()
            while self.should_continue and not fail_button.active():
                self.sleep(0.1)
            if not self.sleep(0.1):
                break
