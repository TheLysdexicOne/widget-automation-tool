"""
Mainframe Assembler Automator (Frame ID: 6.3)
Handles automation for the Mainframe Assembler frame in WidgetInc.
"""

import numpy as np
import pyautogui
import time
from PIL import ImageGrab
from typing import Any, Dict

from automation.base_automator import BaseAutomator


class MainframeAssemblerAutomator(BaseAutomator):
    """Automation logic for Mainframe Assembler (Frame 6.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        bucket_y = self.frame_data["interactions"]["bucket_y"][1]
        intercept_y = self.frame_data["interactions"]["intercept_y"][1]
        full_bbox = self.frame_data["bbox"]["matrix_bbox"]
        x1, x2 = full_bbox[0], full_bbox[2]
        self.logger.info(f"Matrix bottom detected at Y: {intercept_y}")

        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = False

        self.logger.info(f"SPEED DEMON MODE: Monitoring Y={intercept_y}")
        detections = 0

        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            # Single line capture
            screenshot = ImageGrab.grab(bbox=(x1, intercept_y - 2, x2, intercept_y), all_screens=True)
            line = np.array(screenshot)[0]  # First (and only) row
            # Vectorized detection
            valid = line[:, 1] > np.maximum(line[:, 0], line[:, 2])
            if np.any(valid):
                # Click brightest valid pixel
                valid_idx = np.where(valid)[0]
                brightest = valid_idx[np.argmax(line[valid, 1])]

                pyautogui.moveTo(x1 + brightest, bucket_y)
                detections += 1

                time.sleep(0.03)  # Anti-spam
        print(f"DEMON MODE COMPLETE: {detections} strikes")
