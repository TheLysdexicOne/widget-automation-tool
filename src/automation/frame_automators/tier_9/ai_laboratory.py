"""
AI Laboratory Automator (Frame ID: 9.3)
Handles automation for the AI Laboratory frame in WidgetInc.
"""

import pyautogui
import time
import numpy as np


from typing import Any, Dict
from automation.base_automator import BaseAutomator
from utility.window_utils import get_frame_screenshot
from utility.coordinate_utils import conv_frame_coords_to_screen_coords


class AiLaboratoryAutomator(BaseAutomator):
    """Automation logic for AI Laboratory (Frame 9.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def find_dots(self):
        """
        Finds all white blobs (255,255,255) and (219,219,219) in a sea of black within the canvas bbox.
        Returns a list of (frame_x, frame_y) center points for each blob, sorted top-to-bottom.
        """
        screenshot = get_frame_screenshot()
        if screenshot is None:
            return []
        cropped = screenshot.crop(self.canvas)
        arr = np.array(cropped)[..., :3]
        # Mask for white pixels (255,255,255) or (219,219,219)
        mask = np.all(arr == [255, 255, 255], axis=-1) | np.all(arr == [219, 219, 219], axis=-1)
        # Label blobs (4-connectivity)
        from scipy.ndimage import label, find_objects

        label_result = label(mask)
        if isinstance(label_result, tuple) and len(label_result) == 2:
            labeled, num_features = label_result
        else:
            labeled = label_result
            num_features = 0 if labeled is None else 1
        if num_features == 0:
            return []

        # For each blob, get bounding box and compute center point
        slices = find_objects(labeled)
        centers = []
        for slc in slices:
            if slc is None or len(slc) != 2:
                continue
            y_slice, x_slice = slc
            y1, y2 = y_slice.start, y_slice.stop
            x1, x2 = x_slice.start, x_slice.stop
            cx = (x1 + x2 - 1) // 2
            cy = (y1 + y2 - 1) // 2
            # Convert to frame coordinates
            frame_x = self.canvas[0] + cx
            frame_y = self.canvas[1] + cy

            # Convert to screen coordinates
            frame_x, frame_y = conv_frame_coords_to_screen_coords(frame_x, frame_y)
            centers.append((frame_x, frame_y))

        # Sort by y (top to bottom)
        centers.sort(key=lambda pt: pt[1])
        return centers

    def run_automation(self):
        start_time = time.time()

        self.canvas = self.frame_data["frame_xy"]["bbox"]["canvas"]

        # canvas for blobs of white in a sea of black

        # Main automation loop
        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            dots = self.find_dots()
            for dot in dots:
                pyautogui.moveTo(dot[0], dot[1], duration=0.05)
                pyautogui.click()

            if not self.sleep(1.5):
                break
