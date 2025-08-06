"""
Mainframe Assembler Automator (Frame ID: 6.3)
Handles automation for the Mainframe Assembler frame in WidgetInc.
"""

import os
import json
import numpy as np
import pyautogui
import time
from PIL import ImageGrab
from typing import Any, Dict, Tuple

from automation.base_automator import BaseAutomator
from utility.window_utils import get_frame_screenshot, get_box_no_border
from utility.coordinate_utils_grid_old import conv_frame_to_screen_bbox, conv_frame_to_screen_coords
from utility.cache_manager import get_cache_manager
from .mainframe_helper import find_matrix_bottom_bound


# Cache file path in config/cache folder (for debugging/inspection)
_CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "config", "cache", "mainframe.cache")

# In-memory cache for fast access
_matrix_cache = {}


def _ensure_cache_directory():
    """Ensure the cache directory exists."""
    cache_dir = os.path.dirname(_CACHE_FILE)
    os.makedirs(cache_dir, exist_ok=True)


def _load_cache_from_disk():
    """Load cache from disk if it exists."""
    global _matrix_cache
    _ensure_cache_directory()

    if os.path.exists(_CACHE_FILE):
        try:
            with open(_CACHE_FILE, "r") as f:
                _matrix_cache = json.load(f)
            print(f"Loaded matrix cache from {_CACHE_FILE}: {_matrix_cache}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Failed to load cache file: {e}")
            _matrix_cache = {}


def _save_cache_to_disk():
    """Save current cache to disk."""
    _ensure_cache_directory()

    try:
        with open(_CACHE_FILE, "w") as f:
            json.dump(_matrix_cache, f, indent=2)
        print(f"Saved matrix cache to {_CACHE_FILE}")
    except IOError as e:
        print(f"Failed to save cache file: {e}")


# Load cache on module import
_load_cache_from_disk()


def get_matrix_detection_data(frame_data: Dict[str, Any]) -> Tuple[Tuple[int, int, int, int], int]:
    """
    Get or calculate matrix detection data with caching based on frame dimensions.

    Returns:
        Tuple of (full_bbox, low_y, detection_y)
    """
    cache_manager = get_cache_manager()
    frame_area = cache_manager.get_frame_area()

    if not frame_area:
        raise RuntimeError("No frame area available for matrix detection")

    # Create cache key from frame dimensions
    frame_width = frame_area["width"]
    frame_height = frame_area["height"]
    cache_key = f"{frame_width}x{frame_height}"

    # Check if we have cached data for these dimensions
    if cache_key in _matrix_cache:
        cached_data = _matrix_cache[cache_key]
        # Convert list back to tuple format (JSON stores tuples as lists)
        full_bbox = tuple(cached_data[0])
        low_y = cached_data[1]
        result = (full_bbox, low_y)
        print(f"Using cached matrix data for {cache_key}: {result}")
        return result

    # Calculate fresh data
    matrix_bbox = frame_data["frame_xy"]["bbox"]["matrix_bbox"]
    matrix_colors = [(r, g, b) for r in range(31) for g in range(256) for b in range(31)]

    full_bbox = get_box_no_border(matrix_bbox, matrix_colors)
    low_y = find_matrix_bottom_bound(full_bbox)

    # Cache the results (in memory and on disk)
    cached_data = [list(full_bbox), low_y]  # Convert tuple to list for JSON
    _matrix_cache[cache_key] = cached_data
    _save_cache_to_disk()

    result = (full_bbox, low_y)
    print(f"Calculated and cached matrix data for {cache_key}: {result}")
    return result


def clear_matrix_cache():
    """Clear the matrix detection cache (useful for testing or when frame changes)."""
    global _matrix_cache
    _matrix_cache.clear()
    _save_cache_to_disk()
    print("Matrix detection cache cleared")


class MainframeAssemblerAutomator(BaseAutomator):
    """Automation logic for Mainframe Assembler (Frame 6.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def run_automation(self):
        start_time = time.time()

        bucket_y = self.frame_data["interactions"]["bucket_y"][1]

        # Get matrix detection data (cached if available)
        full_bbox, intercept_y = get_matrix_detection_data(self.frame_data)
        x1, y1, x2, y2 = conv_frame_to_screen_bbox(full_bbox)
        monitor_region = (x1, y1, x2, y2)
        print({full_bbox, intercept_y})

        intercept_y = conv_frame_to_screen_coords(1, intercept_y)[1]
        intercept_y -= 39

        print(f"Matrix detection data - Full bbox: {monitor_region}, Low Y: {intercept_y}")
        self.logger.info(f"Matrix bounding box: ({x1}, {y1}, {x2}, {y2})")
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
            valid = (
                line[:, 1] > np.maximum(line[:, 0], line[:, 2])
                # np.all(line > bg_thresh, axis=1)
                # & np.all(line <= max_bright, axis=1)
                # & (line[:, 1] > np.maximum(line[:, 0], line[:, 2]))
            )
            if np.any(valid):
                # Click brightest valid pixel
                valid_idx = np.where(valid)[0]
                brightest = valid_idx[np.argmax(line[valid, 1])]

                pyautogui.moveTo(x1 + brightest, bucket_y)
                detections += 1

                time.sleep(0.03)  # Anti-spam
        print(f"DEMON MODE COMPLETE: {detections} strikes")
