"""
Ascension Facility Automator (Frame ID: 10.3)
Handles automation for the Ascension Facility frame in WidgetInc.
"""

import pyautogui
import time
import numpy as np

from typing import Any, Dict
from automation.base_automator import BaseAutomator
from utility.window_utils import get_frame_screenshot


class AscensionFacilityAutomator(BaseAutomator):
    """Automation logic for Ascension Facility (Frame 10.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()
        canvas = self.frame_data["bbox"]["canvas"]
        space_ship = self.frame_data["bbox"]["space_ship"]
        brick_color = tuple(self.frame_data["colors"]["brick"])
        start = self.frame_data["interactions"]["start"]

        pyautogui.moveTo(*start)
        pyautogui.click()

        ship_w = space_ship[2] - space_ship[0]
        ship_h = space_ship[3] - space_ship[1]
        canvas_x1, canvas_y1, canvas_x2, canvas_y2 = canvas
        canvas_width = canvas_x2 - canvas_x1
        center_x = canvas_x1 + canvas_width // 2
        ship_y = canvas_y2 - ship_h // 2
        initial_x = space_ship[0] + ship_w // 2

        # State
        ship_x_current = initial_x
        avoiding = False
        avoiding_brick_span = None  # (x1,x2)

        def move_ship(x):
            nonlocal ship_x_current
            x = int(max(canvas_x1 + ship_w // 2, min(canvas_x2 - ship_w // 2, x)))
            if x != ship_x_current:
                pyautogui.moveTo(x, ship_y, duration=0.01)
                ship_x_current = x

        move_ship(initial_x)

        def get_bricks(mask: np.ndarray):
            """Return list of bricks as dicts: {x1,x2,bottom} using color mask over full canvas.
            Bricks are vertical stacks with contiguous X spans.
            """
            H, W = mask.shape
            col_has = np.any(mask, axis=0)
            xs = np.flatnonzero(col_has)
            if xs.size == 0:
                return []
            # Find boundaries where gap > 1
            splits = np.where(np.diff(xs) > 1)[0]
            # Start/end indices into xs for each brick span
            start_indices = np.concatenate(([0], splits + 1))
            end_indices = np.concatenate((splits, [xs.size - 1]))
            bricks = []
            for si, ei in zip(start_indices, end_indices):
                x1 = xs[si]
                x2 = xs[ei]
                span_cols = mask[:, x1 : x2 + 1]
                ys = np.flatnonzero(np.any(span_cols, axis=1))
                if ys.size == 0:
                    continue
                bottom = int(ys.max())
                bricks.append({"x1": int(x1), "x2": int(x2), "bottom": bottom})
            return bricks

        # Precompute ship collision vertical threshold
        ship_collision_y = ship_y - ship_h // 2  # y at which brick bottom collides

        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            screenshot = get_frame_screenshot()
            if screenshot is None:
                if not self.sleep(0.02):
                    break
                continue

            # Full canvas crop once
            canvas_img = screenshot.crop((canvas_x1, canvas_y1, canvas_x2, canvas_y2))
            arr = np.array(canvas_img)[..., :3]
            mask = np.all(arr == brick_color, axis=-1)

            bricks = get_bricks(mask)
            # Translate brick x spans to screen coords
            for b in bricks:
                b["x1_sc"] = canvas_x1 + b["x1"]
                b["x2_sc"] = canvas_x1 + b["x2"]
                b["bottom_sc_y"] = canvas_y1 + b["bottom"]

            # Remove bricks fully below ship
            bricks = [b for b in bricks if b["bottom_sc_y"] < ship_y + ship_h // 2]

            # Determine primary (lowest) brick
            primary = max(bricks, key=lambda b: b["bottom_sc_y"], default=None)

            # If avoiding, check if avoiding brick is gone (bottom passed ship)
            if avoiding and avoiding_brick_span is not None:
                still_there = False
                for b in bricks:
                    if b["x1_sc"] == avoiding_brick_span[0] and b["x2_sc"] == avoiding_brick_span[1]:
                        still_there = True
                        break
                if not still_there:
                    # Brick passed; recenter after a slight delay to prep for next
                    move_ship(center_x)
                    avoiding = False
                    avoiding_brick_span = None

            if primary is not None:
                # Predict collision: brick bottom approaching ship collision band and horizontal overlap
                ship_left = ship_x_current - ship_w // 2
                ship_right = ship_x_current + ship_w // 2
                overlap = not (primary["x2_sc"] < ship_left or primary["x1_sc"] > ship_right)
                approaching = primary["bottom_sc_y"] >= ship_collision_y - 120  # within reaction window

                if overlap and approaching and not avoiding:
                    # Decide safe side away from brick center
                    brick_center = (primary["x1_sc"] + primary["x2_sc"]) // 2
                    dist_left_space = brick_center - canvas_x1
                    dist_right_space = canvas_x2 - brick_center
                    if dist_left_space >= dist_right_space:
                        # Move ship to extreme left
                        target_x = canvas_x1 + ship_w // 2 + 2
                    else:
                        target_x = canvas_x2 - ship_w // 2 - 2
                    move_ship(target_x)
                    avoiding = True
                    avoiding_brick_span = (primary["x1_sc"], primary["x2_sc"])
                elif (
                    not avoiding
                    and ship_x_current != center_x
                    and (primary["bottom_sc_y"] < ship_collision_y - 160 or not overlap)
                ):
                    # Early recenter if brick far enough or not threatening
                    move_ship(center_x)
            else:
                # No bricks: recenter
                if ship_x_current != center_x and not avoiding:
                    move_ship(center_x)

            if not self.sleep(0.02):
                break
