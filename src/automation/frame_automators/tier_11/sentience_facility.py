"""
Sentience Facility Automator (Frame ID: 11.1)
Handles automation for the Sentience Facility frame in WidgetInc.
"""

import pyautogui
import numpy as np
from typing import Any, Dict, List, Tuple
from automation.base_automator import BaseAutomator
from utility.window_utils import get_frame_screenshot
from utility.coordinate_utils import conv_frame_coords_to_screen_coords


class SentienceFacilityAutomator(BaseAutomator):
    """Automation logic for Sentience Facility (Frame 11.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def _extract_counts(self, screenshot, bboxes: List[Tuple[int, int, int, int]]):
        """Return list of record dicts with metrics for each bbox (no labeling)."""
        color_tables = self._color_tables
        arr_full = np.array(screenshot)[..., :3]
        records = []
        for bbox in bboxes:
            x1, y1, x2, y2 = map(int, bbox)
            if x2 <= x1 or y2 <= y1:
                continue
            region = arr_full[y1:y2, x1:x2]
            if region.size == 0:
                continue
            h, w, _ = region.shape
            counts = {}
            for name, rgb_list in color_tables.items():
                mask_total = np.zeros((h, w), dtype=bool)
                for r, g, b in rgb_list:
                    mask_total |= (region[:, :, 0] == r) & (region[:, :, 1] == g) & (region[:, :, 2] == b)
                counts[name] = int(mask_total.sum())
            black_mask = (region[:, :, 0] == 0) & (region[:, :, 1] == 0) & (region[:, :, 2] == 0)
            counts["black"] = int(black_mask.sum())
            # total tracked (colors + empty + black)
            counts["total"] = sum(counts.values())
            # Fill includes black + empty + colors (everything we track)
            fill = counts["total"]
            area = h * w
            fill_ratio = fill / area if area > 0 else 0.0
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            records.append(
                {
                    "bbox": bbox,
                    "center": (cx, cy),
                    "fill": fill,
                    "area": area,
                    "fill_ratio": fill_ratio,
                    "black": counts["black"],
                    "counts": counts,
                }
            )
        return records

    def _assign_labels(self, records: List[Dict]):
        """Assign shape labels based on fill_ratio ordering (highest -> square ...)."""
        if len(records) != 4:
            return {}
        # Sort by fill_ratio desc then by black ascending (less outline = fuller interior)
        records.sort(key=lambda r: (-r["fill_ratio"], r["black"]))
        mapping = {}
        for rec, label in zip(records, self.shapes_big_to_small):
            rec["counts"]["shape"] = label
            mapping[rec["center"]] = label
        return mapping

    def _classify_groups(self, screenshot, source_bboxes, target_bboxes):
        """Classify both source and target groups from a single screenshot for consistency."""
        source_records = self._extract_counts(screenshot, source_bboxes)
        target_records = self._extract_counts(screenshot, target_bboxes)
        source_map = self._assign_labels(source_records)
        target_map = self._assign_labels(target_records)

        print("[SentienceFacility] Source shapes:")
        for r in source_records:
            print(r["center"], {**r["counts"], "fill_ratio": round(r["fill_ratio"], 3)})
        print("[SentienceFacility] Target shapes:")
        for r in target_records:
            print(r["center"], {**r["counts"], "fill_ratio": round(r["fill_ratio"], 3)})
        return source_map, target_map

    def run_automation(self):
        # Load bboxes
        self.source_shape_1 = self.frame_data["frame_xy"]["bbox"]["source_shape_1"]
        self.source_shape_2 = self.frame_data["frame_xy"]["bbox"]["source_shape_2"]
        self.source_shape_3 = self.frame_data["frame_xy"]["bbox"]["source_shape_3"]
        self.source_shape_4 = self.frame_data["frame_xy"]["bbox"]["source_shape_4"]
        self.target_shape_1 = self.frame_data["frame_xy"]["bbox"]["target_shape_1"]
        self.target_shape_2 = self.frame_data["frame_xy"]["bbox"]["target_shape_2"]
        self.target_shape_3 = self.frame_data["frame_xy"]["bbox"]["target_shape_3"]
        self.target_shape_4 = self.frame_data["frame_xy"]["bbox"]["target_shape_4"]

        self.all_shapes = [
            self.source_shape_1,
            self.source_shape_2,
            self.source_shape_3,
            self.source_shape_4,
            self.target_shape_1,
            self.target_shape_2,
            self.target_shape_3,
            self.target_shape_4,
        ]

        self.source_colors = {
            "yellow": self.frame_data["colors"]["yellow"],
            "blue": self.frame_data["colors"]["blue"],
            "green": self.frame_data["colors"]["green"],
            "red": self.frame_data["colors"]["red"],
            "empty": self.frame_data["colors"]["empty"],
        }

        # Pre-compute color tables once
        self._color_tables = {name: [tuple(c) for c in colors] for name, colors in self.source_colors.items()}

        self.shapes_big_to_small = ["square", "circle", "triangle", "diamond"]

        def center_of(b):
            x1, y1, x2, y2 = map(int, b)
            return ((x1 + x2) // 2, (y1 + y2) // 2)

        source_bboxes = self.all_shapes[:4]
        target_bboxes = self.all_shapes[4:]

        while self.should_continue:
            screenshot = get_frame_screenshot()
            if screenshot is None:
                if not self.sleep(0.25):
                    return
                continue

            source_map, target_map = self._classify_groups(screenshot, source_bboxes, target_bboxes)
            # Ordered source labels (one each)
            self.ordered_sources = [source_map.get(center_of(b), "unknown") for b in source_bboxes]
            print("[SentienceFacility] Source order:", self.ordered_sources)

            # Build target label -> center lookup
            label_to_target_center = {}
            for b in target_bboxes:
                c = center_of(b)
                lbl = target_map.get(c)
                if lbl:
                    label_to_target_center[lbl] = c

            # Click in source order
            for lbl in self.ordered_sources:
                tc = label_to_target_center.get(lbl)
                if not tc:
                    continue
                tx, ty = tc
                sx, sy = conv_frame_coords_to_screen_coords(tx, ty)
                pyautogui.click(sx, sy)
                if not self.sleep(0.1):
                    return

            # Pause for reshuffle
            if not self.sleep(1.0):
                return
