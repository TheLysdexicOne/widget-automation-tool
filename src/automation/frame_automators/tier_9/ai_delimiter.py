"""
AI Delimiter Automator (Frame ID: 9.4)
Handles automation for the AI Delimiter frame in WidgetInc.
"""

import pyautogui
import numpy as np
import time
import math

from typing import Any, Dict
from automation.base_automator import BaseAutomator
from utility.coordinate_utils import conv_frame_coords_to_screen_coords
from utility.window_utils import get_frame_screenshot


class AiDelimiterAutomator(BaseAutomator):
    """Automation logic for AI Delimiter (Frame 9.4)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)
        # Pre-pack ball colors for fast comparison (R<<16 | G<<8 | B)
        colors = frame_data["colors"]["ball_colors"]
        self._ball_colors_packed = np.array([(c[0] << 16) | (c[1] << 8) | c[2] for c in colors], dtype=np.uint32)
        self._last_ball_frame_xy = None
        self._misses = 0

    def _update_velocity(self, new_pos, now):
        """
        Maintain simple constant velocity model using last sample.
        new_pos: (frame_x, frame_y)
        """
        if not hasattr(self, "_ball_prev"):
            self._ball_prev = (new_pos, now)
            self._velocity = (0, 0)
            return
        (px, py), pt = self._ball_prev
        dt = max(1e-6, now - pt)
        vx = (new_pos[0] - px) / dt
        vy = (new_pos[1] - py) / dt
        # Light smoothing
        if hasattr(self, "_velocity"):
            vx = 0.6 * self._velocity[0] + 0.4 * vx
            vy = 0.6 * self._velocity[1] + 0.4 * vy
        self._velocity = (vx, vy)
        self._ball_prev = (new_pos, now)

    def _predict_intercept_x(self, ball_pos, velocity, arena_bbox, paddle_y):
        """
        Predict x where ball will cross paddle_y (frame coords) using
        simple axis-aligned elastic bounces on arena_bbox walls.
        arena_bbox: (ax1, ay1, ax2, ay2)
        Returns predicted frame_x (clamped) or None if moving away.
        """
        if velocity[1] <= 0:
            return None  # Moving up; no imminent paddle intercept
        x, y = ball_pos
        vx, vy = velocity
        ax1, ay1, ax2, ay2 = arena_bbox
        width = ax2 - ax1
        # Simulate until y >= paddle_y
        # Time to reach paddle ignoring bounces:
        # We reflect x when hitting side walls
        # Advance in segments between horizontal wall hits.
        if width <= 0:
            return None
        # Work in local coords
        lx = x - ax1
        ly = y
        target = paddle_y
        while ly < target and vy > 0 and ly < ay2 + (paddle_y - ay1) * 2:
            # Time until paddle
            t_paddle = (target - ly) / vy
            # Time until side wall (depending on direction)
            if vx > 0:
                dist_side = width - lx
            elif vx < 0:
                dist_side = lx
            else:
                dist_side = math.inf
            t_side = dist_side / abs(vx) if vx != 0 else math.inf
            if t_paddle <= t_side:
                # Reaches paddle before side bounce
                lx += vx * t_paddle
                ly = target
                break
            else:
                # Bounce off side
                lx += vx * t_side
                ly += vy * t_side
                vx = -vx  # reflect
                # Clamp numeric drift
                lx = max(0, min(width, lx))
        predicted_x = int(round(ax1 + max(0, min(width, lx))))
        return predicted_x

    def find_ball_fast(self, watch_box, search_radius=40, max_misses_before_full=5, return_frame=True):
        """
        Fast ball tracker:
        - Crops only watch_box once
        - If we have last position, restrict search to a local ROI
        - Falls back to full watch_box after several misses
        - Returns screen coordinates of any detected ball pixel or None
        """
        x1, y1, x2, y2 = watch_box
        screenshot = get_frame_screenshot()
        if screenshot is None:
            return None
        cropped = screenshot.crop((x1, y1, x2, y2)).convert("RGB")
        arr = np.array(cropped, dtype=np.uint8)

        h, w, _ = arr.shape

        # Determine ROI (relative coords inside cropped)
        if self._last_ball_frame_xy and self._misses < max_misses_before_full:
            lx, ly = self._last_ball_frame_xy
            rel_x = lx - x1
            rel_y = ly - y1
            rx1 = max(0, rel_x - search_radius)
            ry1 = max(0, rel_y - search_radius)
            rx2 = min(w, rel_x + search_radius + 1)
            ry2 = min(h, rel_y + search_radius + 1)
        else:
            rx1, ry1, rx2, ry2 = 0, 0, w, h  # full region

        sub = arr[ry1:ry2, rx1:rx2]
        if sub.size == 0:
            return None

        # Pack RGB into uint32
        packed = (
            (sub[:, :, 0].astype(np.uint32) << 16)
            | (sub[:, :, 1].astype(np.uint32) << 8)
            | sub[:, :, 2].astype(np.uint32)
        )

        # Build mask via vectorized membership
        mask = np.isin(packed, self._ball_colors_packed, assume_unique=False)

        if not mask.any():
            self._misses += 1
            return None

        # Find first pixel (top-to-bottom, left-to-right)
        rows_with_hits = np.flatnonzero(mask.any(axis=1))
        r = rows_with_hits[0]
        c = np.flatnonzero(mask[r])[0]

        # Absolute frame coordinates
        frame_x = x1 + rx1 + c
        frame_y = y1 + ry1 + r
        self._last_ball_frame_xy = (frame_x, frame_y)
        self._misses = 0
        if return_frame:
            return (frame_x, frame_y)
        screen_x, screen_y = conv_frame_coords_to_screen_coords(frame_x, frame_y)
        return (screen_x, screen_y)

    def run_automation(self):
        start_time = time.time()
        watch_box = self.frame_data["frame_xy"]["bbox"]["watch_bbox"]
        # Use watch_box horizontally; paddle_y just below its bottom
        ax1, ay1, ax2, ay2 = watch_box
        paddle_y = ay2 + 20  # heuristic offset; adjust as needed

        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            now = time.time()
            pos = self.find_ball_fast(watch_box, return_frame=True)
            if pos:
                self._update_velocity(pos, now)
                if hasattr(self, "_velocity"):
                    predicted_x = self._predict_intercept_x(pos, self._velocity, (ax1, ay1, ax2, ay2), paddle_y)
                    if predicted_x is not None:
                        sx, sy = conv_frame_coords_to_screen_coords(predicted_x, paddle_y)
                        pyautogui.moveTo(sx, sy, _pause=False)

            if not self.sleep(0.01):
                break
