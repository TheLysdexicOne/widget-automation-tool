import logging
from typing import Tuple
from .cache_manager import get_cache_manager

logger = logging.getLogger(__name__)

"""
Tiers:
Frame Percent > Frame Coords > Screen Coords

Frame Percent and Frame Coords are use for frame-relative operations. (Think screenshots)
Screen Coords are used for actual clicking and interaction.

This means Frame Percent and Frame Coords are always positive.
Screen Coords can be negative if the frame is off-screen or partially off-screen.

From Frame Percent
===================
conv_frame_percent_to_frame_coords
conv_frame_percent_to_screen_coords

From Frame Coords
===================
conv_frame_coords_to_frame_percent
conv_frame_coords_to_screen_coords


From Screen Coords
===================
conv_screen_coords_to_frame_coords
conv_screen_coords_to_frame_percent

BBOX Conversions
===================
conv_frame_percent_to_screen_bbox

Shorthand Functions
===================
fp = frame percent
fc = frame coords
sc = screen coords
-------------------
fp_to_fc_coord
fp_to_sc_coord
fc_to_fp_coord
fc_to_sc_coord
sc_to_fc_coord
sc_to_fp_coord
fp_to_sc_bbox
===================
"""


######################
# From Frame Percent #
######################
def conv_frame_percent_to_frame_coords(frame_x: float, frame_y: float) -> Tuple[int, int]:
    """
    Convert frame percentage coordinates to frame pixel coordinates.

    Args:
        frame_x: X coordinate as a percentage (0.0 to 1.0)
        frame_y: Y coordinate as a percentage (0.0 to 1.0)

    Returns:
        Tuple of (frame_x, frame_y) in pixel coordinates
    """
    window_manager = get_cache_manager()
    frame_area = window_manager.get_frame_area()
    print(f"Frame area: {frame_area}")

    if not frame_area:
        logger.warning("No valid frame area for conversion")
        return (0, 0)

    pixel_x = int(frame_area["width"] * frame_x)
    pixel_y = int(frame_area["height"] * frame_y)

    return (pixel_x, pixel_y)


def conv_frame_percent_to_screen_coords(frame_x: float, frame_y: float) -> Tuple[int, int]:
    """
    Convert frame percentage coordinates to screen pixel coordinates.

    Args:
        frame_x: X coordinate as a percentage (0.0 to 1.0)
        frame_y: Y coordinate as a percentage (0.0 to 1.0)

    Returns:
        Tuple of (screen_x, screen_y) in pixel coordinates
    """
    window_manager = get_cache_manager()
    frame_area = window_manager.get_frame_area()

    if not frame_area:
        logger.warning("No valid frame area for conversion")
        return (0, 0)

    screen_x = int(frame_area["x"] + frame_area["width"] * frame_x)
    screen_y = int(frame_area["y"] + frame_area["height"] * frame_y)

    return (screen_x, screen_y)


#####################
# From Frame Coords #
#####################


def conv_frame_coords_to_frame_percent(frame_x: int, frame_y: int) -> Tuple[float, float]:
    """
    Convert frame pixel coordinates to frame percentage coordinates.

    Args:
        frame_x: X coordinate in pixels
        frame_y: Y coordinate in pixels

    Returns:
        Tuple of (frame_x, frame_y) as percentages (0.0 to 1.0)
    """
    window_manager = get_cache_manager()
    frame_area = window_manager.get_frame_area()

    if not frame_area:
        logger.warning("No valid frame area for conversion")
        return (0.0, 0.0)

    percent_x = frame_x / frame_area["width"] if frame_area["width"] > 0 else 0.0
    percent_y = frame_y / frame_area["height"] if frame_area["height"] > 0 else 0.0

    return (percent_x, percent_y)


def conv_frame_coords_to_screen_coords(frame_x: int, frame_y: int) -> Tuple[int, int]:
    """
    Convert frame pixel coordinates to screen pixel coordinates.

    Args:
        frame_x: X coordinate in pixels
        frame_y: Y coordinate in pixels

    Returns:
        Tuple of (screen_x, screen_y) in pixel coordinates
    """
    window_manager = get_cache_manager()
    frame_area = window_manager.get_frame_area()

    if not frame_area:
        logger.warning("No valid frame area for conversion")
        return (0, 0)

    screen_x = int(frame_area["x"] + frame_x)
    screen_y = int(frame_area["y"] + frame_y)

    return (screen_x, screen_y)


######################
# From Screen Coords #
######################


def conv_screen_coords_to_frame_coords(screen_x: int, screen_y: int) -> Tuple[int, int]:
    """
    Convert screen pixel coordinates to frame pixel coordinates.

    Args:
        screen_x: X coordinate in pixels
        screen_y: Y coordinate in pixels

    Returns:
        Tuple of (frame_x, frame_y) in pixel coordinates relative to the frame area
    """
    window_manager = get_cache_manager()
    frame_area = window_manager.get_frame_area()

    if not frame_area:
        logger.warning("No valid frame area for conversion")
        return (0, 0)

    frame_x = screen_x - frame_area["x"]
    frame_y = screen_y - frame_area["y"]

    return (frame_x, frame_y)


def conv_screen_coords_to_frame_percent(screen_x: int, screen_y: int) -> Tuple[float, float]:
    """
    Convert screen pixel coordinates to frame percentage coordinates.

    Args:
        screen_x: X coordinate in pixels
        screen_y: Y coordinate in pixels

    Returns:
        Tuple of (frame_x, frame_y) as percentages (0.0 to 1.0)
    """
    window_manager = get_cache_manager()
    frame_area = window_manager.get_frame_area()

    if not frame_area:
        logger.warning("No valid frame area for conversion")
        return (0.0, 0.0)

    frame_x = (screen_x - frame_area["x"]) / frame_area["width"] if frame_area["width"] > 0 else 0.0
    frame_y = (screen_y - frame_area["y"]) / frame_area["height"] if frame_area["height"] > 0 else 0.0

    return (frame_x, frame_y)


####################
# BBOX Conversions #
####################


def conv_frame_percent_to_screen_bbox(bbox: Tuple[float, float, float, float]) -> Tuple[int, int, int, int]:
    """
    Convert a bounding box from frame percentage coordinates to screen pixel coordinates.

    Args:
        bbox: Tuple of (frame_x1, frame_y1, frame_x2, frame_y2) as percentages (0.0 to 1.0)

    Returns:
        Tuple of (screen_x1, screen_y1, screen_x2, screen_y2) in pixel coordinates
    """
    window_manager = get_cache_manager()
    frame_area = window_manager.get_frame_area()

    if not frame_area:
        logger.warning("No valid frame area for bbox conversion")
        return (0, 0, 0, 0)

    screen_x1 = int(frame_area["x"] + frame_area["width"] * bbox[0])
    screen_y1 = int(frame_area["y"] + frame_area["height"] * bbox[1])
    screen_x2 = int(frame_area["x"] + frame_area["width"] * bbox[2])
    screen_y2 = int(frame_area["y"] + frame_area["height"] * bbox[3])

    return (screen_x1, screen_y1, screen_x2, screen_y2)


#######################
# Shorthand Functions #
#######################
def fp_to_fc_coord(frame_x: float, frame_y: float) -> Tuple[int, int]:
    """Convert frame percent to frame coords."""
    return conv_frame_percent_to_frame_coords(frame_x, frame_y)


def fp_to_sc_coord(frame_x: float, frame_y: float) -> Tuple[int, int]:
    """Convert frame percent to screen coords."""
    return conv_frame_percent_to_screen_coords(frame_x, frame_y)


def fc_to_fp_coord(frame_x: int, frame_y: int) -> Tuple[float, float]:
    """Convert frame coords to frame percent."""
    return conv_frame_coords_to_frame_percent(frame_x, frame_y)


def fc_to_sc_coord(frame_x: int, frame_y: int) -> Tuple[int, int]:
    """Convert frame coords to screen coords."""
    return conv_frame_coords_to_screen_coords(frame_x, frame_y)


def sc_to_fc_coord(screen_x: int, screen_y: int) -> Tuple[int, int]:
    """Convert screen coords to frame coords."""
    return conv_screen_coords_to_frame_coords(screen_x, screen_y)


def sc_to_fp_coord(screen_x: int, screen_y: int) -> Tuple[float, float]:
    """Convert screen coords to frame percent."""
    return conv_screen_coords_to_frame_percent(screen_x, screen_y)


def fp_to_sc_bbox(bbox: Tuple[float, float, float, float]) -> Tuple[int, int, int, int]:
    """Convert frame percent bbox to screen bbox."""
    return conv_frame_percent_to_screen_bbox(bbox)
