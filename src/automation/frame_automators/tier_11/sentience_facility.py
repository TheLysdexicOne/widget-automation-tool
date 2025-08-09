"""
Sentience Facility Automator (Frame ID: 11.1)
Handles automation for the Sentience Facility frame in WidgetInc.
"""

import pyautogui
import numpy as np
from typing import Any, Dict
from automation.base_automator import BaseAutomator
from utility.window_utils import get_frame_screenshot
from utility.coordinate_utils import conv_frame_coords_to_screen_coords


class SentienceFacilityAutomator(BaseAutomator):
    """Automation logic for Sentience Facility (Frame 11.1)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def determine_shape(self, debug: bool = True):
        """Detect shapes (circle, triangle, square, diamond) with a minimal, robust method.
        Approach:
          1. Crop around each coordinate.
          2. Build foreground mask combining saturation & contrast vs local median.
          3. Extract central blob (flood fill from center; if fails pick nearest mask pixel to center).
          4. Sample radial distances at fixed angles; compute coefficient of variation (cv) and corner peaks.
          5. Orientation from second-moment matrix distinguishes square (0°) vs diamond (~45°).
          6. Initial label rules:
             - triangle: exactly 3 strong peaks OR (cv high & 3<=peaks<=4 & centroid lower)
             - circle: cv < 0.12 and peaks not 3/4 (or <=2)
             - square/diamond: peaks ==4 -> orientation angle threshold
             - fallback by heuristics.
          7. Enforce uniqueness per group of 4 using scoring.
        Returns mapping {(frame_x, frame_y): label}.
        """
        screenshot = get_frame_screenshot()
        if screenshot is None:
            return {}
        CROP = 44
        ANGLES = 90  # 4° resolution
        angle_vals = np.linspace(0, 2 * np.pi, ANGLES, endpoint=False)
        results = []
        for fx, fy in self.all_shapes:
            sc_x, sc_y = conv_frame_coords_to_screen_coords(fx, fy)
            left = int(sc_x - CROP // 2)
            top = int(sc_y - CROP // 2)
            region = screenshot.crop((left, top, left + CROP, top + CROP))
            arr = np.array(region)[..., :3]
            h, w, _ = arr.shape
            # Convert to HSV (manual)
            arr_f = arr.astype(float) / 255.0
            maxc = arr_f.max(axis=2)
            minc = arr_f.min(axis=2)
            diff = maxc - minc
            saturation = np.where(maxc == 0, 0, diff / (maxc + 1e-6))
            gray = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
            med_gray = np.median(gray)
            med_sat = np.median(saturation)
            mask_sat = saturation > (med_sat + 0.15)
            mask_contrast = np.abs(gray - med_gray) > 18
            mask = mask_sat | mask_contrast
            # Clean small noise near borders by zeroing 1-pixel frame
            mask[0, :] = mask[-1, :] = mask[:, 0] = mask[:, -1] = False
            # Flood-fill central blob
            cy0, cx0 = h // 2, w // 2
            if not mask[cy0, cx0]:
                # Find nearest True pixel to center
                ys, xs = np.nonzero(mask)
                if ys.size == 0:
                    results.append({"xy": (fx, fy), "valid": False})
                    continue
                dists = (ys - cy0) ** 2 + (xs - cx0) ** 2
                idx_min = int(dists.argmin())
                cy0, cx0 = int(ys[idx_min]), int(xs[idx_min])
            visited = np.zeros_like(mask, dtype=bool)
            blob = np.zeros_like(mask, dtype=bool)
            stack = [(cy0, cx0)]
            while stack:
                y, x = stack.pop()
                if not (0 <= y < h and 0 <= x < w):
                    continue
                if visited[y, x] or not mask[y, x]:
                    continue
                visited[y, x] = True
                blob[y, x] = True
                stack.extend([(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)])
            if blob.sum() < 25:  # too small / failure
                results.append({"xy": (fx, fy), "valid": False})
                continue
            ys_b, xs_b = np.nonzero(blob)
            cy = ys_b.mean()
            cx = xs_b.mean()
            centroid_y_norm = cy / (h + 1e-6)
            # Radial sampling
            radii = []
            for ang in angle_vals:
                dx = np.cos(ang)
                dy = np.sin(ang)
                r = 0
                while True:
                    px = int(round(cx + dx * r))
                    py = int(round(cy + dy * r))
                    if px < 0 or px >= w or py < 0 or py >= h or not blob[py, px]:
                        break
                    r += 1
                radii.append(r)
            radii = np.array(radii, dtype=float)
            max_r = radii.max()
            mean_r = radii.mean()
            std_r = radii.std()
            rad_cv = std_r / (mean_r + 1e-6)
            # Peak detection (corners)
            peaks = []
            thresh_peak = max_r * 0.90
            for i in range(len(radii)):
                prev_r = radii[i - 1]
                next_r = radii[(i + 1) % len(radii)]
                if radii[i] >= prev_r and radii[i] >= next_r and radii[i] >= thresh_peak:
                    peaks.append(i)
            peak_count = len(peaks)
            # Orientation via second moments
            xm = xs_b - cx
            ym = ys_b - cy
            cov_xx = (xm * xm).mean()
            cov_yy = (ym * ym).mean()
            cov_xy = (xm * ym).mean()
            angle = 0.5 * np.degrees(np.arctan2(2 * cov_xy, (cov_xx - cov_yy + 1e-9)))
            angle = abs(angle) % 90.0
            if angle > 45:
                angle = 90 - angle
            # Initial classification
            if peak_count == 3:
                label = "triangle"
            elif rad_cv < 0.12 and (peak_count <= 2 or peak_count >= 6):
                label = "circle"
            elif peak_count == 4:
                if 18 <= angle <= 40:
                    label = "diamond"
                else:
                    label = "square"
            else:
                if centroid_y_norm > 0.56 and rad_cv >= 0.12 and peak_count <= 4:
                    label = "triangle"
                elif rad_cv < 0.10:
                    label = "circle"
                elif 18 <= angle <= 40:
                    label = "diamond"
                else:
                    label = "square"
            results.append(
                {
                    "xy": (fx, fy),
                    "valid": True,
                    "label": label,
                    "rad_cv": rad_cv,
                    "peaks": peak_count,
                    "angle": angle,
                    "cy_norm": centroid_y_norm,
                }
            )
        if debug:
            print("[SentienceFacility] Raw shape metrics:")
            for r in results:
                print(r)

        # Group uniqueness enforcement
        def enforce(group):
            grp = [r for r in group if r["valid"]]
            if len(grp) < 4:
                # bail out best guess
                return {r["xy"]: r.get("label") for r in grp}
            # Preselect by clear criteria
            by_label = {"circle": None, "triangle": None, "diamond": None, "square": None}
            # Circle: lowest rad_cv
            circle = min(grp, key=lambda r: r["rad_cv"])
            by_label["circle"] = circle
            # Triangle: highest cy_norm or explicit triangle
            triangles = [r for r in grp if r["label"] == "triangle"] or grp
            by_label["triangle"] = max(triangles, key=lambda r: r["cy_norm"])
            # Diamond: angle near 30 among peak_count 4
            diamonds = [r for r in grp if r["peaks"] == 4]
            if diamonds:
                by_label["diamond"] = min(diamonds, key=lambda r: abs(r["angle"] - 30))
            # Square: remaining best (peaks==4 & small angle)
            remaining = [r for r in grp if id(r) not in {id(v) for v in by_label.values() if v is not None}]
            if remaining:
                squares = [r for r in remaining if r["peaks"] == 4]
                cand_sq = squares or remaining
                by_label["square"] = min(cand_sq, key=lambda r: (abs(r["angle"]), r["rad_cv"]))
            # Resolve duplicates / fill any missing with unused
            used = set()
            final = {}
            for name in ["circle", "triangle", "diamond", "square"]:
                r = by_label.get(name)
                if r and id(r) not in used:
                    final[name] = r
                    used.add(id(r))
            for r in grp:
                if id(r) not in used:
                    for name in ["circle", "triangle", "diamond", "square"]:
                        if name not in final:
                            final[name] = r
                            used.add(id(r))
                            break
            return {v["xy"]: k for k, v in final.items()}

        half = len(results) // 2
        mapping = {}
        mapping.update(enforce(results[:half]))
        mapping.update(enforce(results[half:]))
        if debug:
            print("[SentienceFacility] Final mapping:", mapping)
        return mapping

    def run_automation(self):
        self.source_shape_1 = self.frame_data["frame_xy"]["interactions"]["source_shape_1"]
        self.source_shape_2 = self.frame_data["frame_xy"]["interactions"]["source_shape_2"]
        self.source_shape_3 = self.frame_data["frame_xy"]["interactions"]["source_shape_3"]
        self.source_shape_4 = self.frame_data["frame_xy"]["interactions"]["source_shape_4"]
        self.target_shape_1 = self.frame_data["frame_xy"]["interactions"]["target_shape_1"]
        self.target_shape_2 = self.frame_data["frame_xy"]["interactions"]["target_shape_2"]
        self.target_shape_3 = self.frame_data["frame_xy"]["interactions"]["target_shape_3"]
        self.target_shape_4 = self.frame_data["frame_xy"]["interactions"]["target_shape_4"]

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

        self.possible_shapes = ["triangle", "circle", "square", "diamond"]

        print("Determining shapes...")
        self.shapes = self.determine_shape()
        print("Shapes determined:", self.shapes)

        # Main automation loop
        # while self.should_continue:
        #     if time.time() - start_time > self.max_run_time:
        #         break

        #     if not self.sleep(0.05):
        #         break
