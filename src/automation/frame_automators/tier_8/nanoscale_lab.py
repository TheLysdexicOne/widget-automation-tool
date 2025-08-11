"""
Nanoscale Lab Automator (Frame ID: 8.2)
Handles automation for the Nanoscale Lab frame in WidgetInc.
"""

import pyautogui

import numpy as np

from typing import Any, Dict, Tuple
from automation.base_automator import BaseAutomator
from utility.window_utils import get_frame_screenshot
from utility.coordinate_utils import conv_frame_coords_to_screen_coords, conv_screen_coords_to_frame_coords


class NanoscaleLabAutomator(BaseAutomator):
    """Automation logic for Nanoscale Lab (Frame 8.2)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        pyautogui.PAUSE = 0

    def find_slider_position(self) -> Tuple[int, int]:
        """Check track lines for slider colors, then determine the center
        by using #000000 and determinate size"""

        for position in self.slider_start_positions:
            x, y = position
            color = pyautogui.pixel(x, y)

            if color in self.slider_colors:
                print(f"Found slider at position: {position} with color: {color}")
                return (x, y)
        else:
            print("slider not found")
            return (self.slider_start_positions[0][0], self.slider_start_positions[0][1])

    def track_slider(self):
        """
        Finds the centroid of the slider blob near the current mouse position (in frame coordinates),
        but only along the X and Y axes (no diagonal movement).
        Returns (screen_x, screen_y) or None.
        """
        mouse_screen_x, mouse_screen_y = pyautogui.position()
        mouse_frame_xy = conv_screen_coords_to_frame_coords(mouse_screen_x, mouse_screen_y)

        search_radius = 100
        screenshot = get_frame_screenshot()
        if screenshot is None:
            return None

        mx, my = mouse_frame_xy
        fx1 = max(0, int(mx - search_radius))
        fy1 = max(0, int(my - search_radius))
        fx2 = int(mx + search_radius)
        fy2 = int(my + search_radius)
        cropped = screenshot.crop((fx1, fy1, fx2, fy2))
        arr = np.array(cropped)
        arr = arr[..., :3]

        # Build mask for all target colors (no tolerance)
        mask = np.zeros(arr.shape[:2], dtype=bool)
        for color in self.slider_colors:
            color = np.array(color)
            diff = np.abs(arr - color)
            mask |= np.all(diff == 0, axis=-1)

        if not np.any(mask):
            return None

        # Axis-aligned centroid: mean of nonzero indices along each axis
        x_mass = mask.sum(axis=0)
        y_mass = mask.sum(axis=1)

        if np.sum(x_mass) == 0 or np.sum(y_mass) == 0:
            return None

        cx = int(np.round(np.average(np.arange(mask.shape[1]), weights=x_mass)))
        cy = int(np.round(np.average(np.arange(mask.shape[0]), weights=y_mass)))
        abs_cx = fx1 + cx
        abs_cy = fy1 + cy

        # Directional overcompensation
        if hasattr(self, "prev_slider_pos") and self.prev_slider_pos is not None:
            prev_x, prev_y = self.prev_slider_pos
            dx = abs_cx - prev_x
            dy = abs_cy - prev_y
            if dx != 0 or dy != 0:
                mag = max(1, (dx**2 + dy**2) ** 0.5)
                overshoot = 8
                abs_cx += int(overshoot * dx / mag)
                abs_cy += int(overshoot * dy / mag)
        self.prev_slider_pos = (abs_cx, abs_cy)

        sx, sy = conv_frame_coords_to_screen_coords(abs_cx, abs_cy)
        return sx, sy

    def run_automation(self):
        self.slider_colors = self.frame_data["colors"]["slider_colors"]

        tracks = self.frame_data["bbox"]["tracks_bbox"]
        x1, y1, x3, y3 = tracks
        x2 = (x1 + x3) // 2
        y2 = (y1 + y3) // 2

        self.slider_start_positions = [(x, y) for x in (x1, x2, x3) for y in (y1, y2, y3)]
        slider_pos = self.find_slider_position()
        self.slider_x, self.slider_y = slider_pos

        self.mouseDown(self.slider_x, self.slider_y)

        # Main automation loop
        while self.should_continue:
            result = self.track_slider()
            if result is not None:
                self.moveTo(result[0], result[1], duration=0)

            if not self.sleep(0.01):
                break
        self.mouseUp()
