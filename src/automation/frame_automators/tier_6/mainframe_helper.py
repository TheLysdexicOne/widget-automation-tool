import numpy as np
import time
import logging

from utility.window_utils import get_frame_screenshot

logger = logging.getLogger(__name__)


def find_matrix_bottom_bound(matrix_bbox_frame: tuple[int, int, int, int]) -> int:
    """
    Simple approach: Find the lowest Y coordinate where matrix green (0,174,0) appears.

    1. Screenshot the matrix bbox multiple times over 2 seconds
    2. Filter out red/blue, keep only green 150-200 range
    3. Overlay screenshots to find brightest green points
    4. Return lowest Y coordinate with brightest green

    Args:
        matrix_bbox_frame: (x1, y1, x2, y2) bounding box in frame coordinates

    Returns:
        Lowest Y coordinate in frame coordinates where matrix green is detected
    """
    x1, y1, x2, y2 = matrix_bbox_frame

    # Take screenshots over 2 seconds (time for matrix to reach bottom)
    screenshots = []
    num_captures = 30
    capture_interval = 2.0 / num_captures

    logger.debug(f"Capturing {num_captures} screenshots over 2.0s for matrix detection...")

    for i in range(num_captures):
        screenshot = get_frame_screenshot()
        if screenshot is None:
            logger.error("Failed to get frame screenshot")
            continue

        # Crop to matrix region
        region = screenshot.crop((x1, y1, x2, y2))
        screenshots.append(np.array(region))

        if i < num_captures - 1:
            time.sleep(capture_interval)

    if not screenshots:
        raise ValueError("No screenshots captured")

    # Stack all screenshots and find brightest points
    stacked = np.stack(screenshots, axis=0)  # Shape: (num_captures, height, width, 3)

    # Filter: Remove red/blue, keep only green in 150-200 range
    green_mask = (
        (stacked[:, :, :, 0] < 50)  # Low red
        & (stacked[:, :, :, 1] >= 150)
        & (stacked[:, :, :, 1] <= 200)  # Green 150-200
        & (stacked[:, :, :, 2] < 50)  # Low blue
    )

    # Find brightest green pixels across all captures
    green_brightness = np.where(green_mask, stacked[:, :, :, 1], 0)
    max_brightness = np.max(green_brightness, axis=0)  # Max across time

    # Look for the target color (0, 174, 0) - scan from bottom to top
    height = max_brightness.shape[0]

    for row in range(height - 1, -1, -1):  # Bottom to top
        if np.any(max_brightness[row, :] >= 174):  # Found bright green
            lowest_y = y1 + row
            logger.info(f"Matrix bottom found at frame Y: {lowest_y}")
            return lowest_y

    raise ValueError("No matrix green (174) detected in region")


# Usage example:
if __name__ == "__main__":
    # Define the matrix region in FRAME coordinates
    # This should be the full_bbox from your frame data
    matrix_bbox_frame = (50, 25, 150, 100)  # Example frame coordinates

    try:
        bottom_y = find_matrix_bottom_bound(matrix_bbox_frame)
        logger.info(f"Matrix bottom detected at frame Y: {bottom_y}")
    except ValueError as e:
        logger.error(f"Detection failed: {e}")
