"""
f = frame
g = grid
s = screen
"""

import logging
from typing import Tuple
from .cache_manager import get_cache_manager, PIXEL_ART_GRID_WIDTH, PIXEL_ART_GRID_HEIGHT

logger = logging.getLogger(__name__)

# Refactoring note: Remove Grid from entire project
# Order of Operations:  Frame % -> Frame Coords -> Screen Coords


def conv_grid_to_screen_coords(grid_x: int, grid_y: int) -> Tuple[int, int]:
    """
    Convert grid coordinates to screen coordinates for clicking.

    Takes grid coordinates and returns the center pixel of that grid cell in screen coordinates.

    Args:
        grid_x: Grid X coordinate (0 to 191)
        grid_y: Grid Y coordinate (0 to 127)

    Returns:
        Tuple of (screen_x, screen_y) coordinates for clicking
    """
    try:
        window_manager = get_cache_manager()
        frame_area = window_manager.get_frame_area()

        if not frame_area:
            logger.warning("No valid frame area or pixel size for grid conversion")
            return (0, 0)

        # Clamp grid coordinates to valid range
        grid_x = max(0, min(PIXEL_ART_GRID_WIDTH - 1, grid_x))
        grid_y = max(0, min(PIXEL_ART_GRID_HEIGHT - 1, grid_y))

        # Calculate pixel center within the grid cell
        pixel_x = (grid_x + 0.5) * pixel_size
        pixel_y = (grid_y + 0.5) * pixel_size

        # Convert to screen coordinates
        screen_x = int(frame_area["x"] + pixel_x)
        screen_y = int(frame_area["y"] + pixel_y)

        return (screen_x, screen_y)

    except Exception as e:
        logger.error(f"Error converting grid to screen coordinates: {e}")
        return (0, 0)


def conv_screen_to_grid_bbox(bbox: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
    """
    Convert a screen bounding box to grid coordinates.

    Args:
        bbox: Tuple of (screen_x1, screen_y1, screen_x2, screen_y2)

    Returns:
        Tuple of (grid_x1, grid_y1, grid_x2, grid_y2)
    """
    screen_x1, screen_y1, screen_x2, screen_y2 = bbox
    window_manager = get_cache_manager()
    frame_area = window_manager.get_frame_area()
    pixel_size = window_manager.get_pixel_size()

    if not frame_area or not pixel_size:
        logger.warning("No valid frame area or pixel size for screen to grid bbox conversion")
        return (0, 0, 0, 0)

    # Convert screen coordinates to grid coordinates
    grid_x1 = int((screen_x1 - frame_area["x"]) / pixel_size)
    grid_y1 = int((screen_y1 - frame_area["y"]) / pixel_size)
    grid_x2 = int((screen_x2 - frame_area["x"]) / pixel_size)
    grid_y2 = int((screen_y2 - frame_area["y"]) / pixel_size)

    return (grid_x1, grid_y1, grid_x2, grid_y2)


def conv_screen_to_frame_coords(screen_x: int, screen_y: int) -> Tuple[int, int]:
    """
    Convert screen coordinates to frame area coordinates.

    Takes screen coordinates and returns coordinates relative to the frame area.

    Args:
        screen_x: Screen X coordinate
        screen_y: Screen Y coordinate

    Returns:
        Tuple of (frame_area_x, frame_area_y) coordinates relative to frame area
    """
    window_manager = get_cache_manager()
    frame_area = window_manager.get_frame_area()

    if not frame_area:
        logger.warning("No valid frame area for screen to frame area conversion")
        return (0, 0)

    # Convert screen coordinates to frame area coordinates
    frame_area_x = screen_x - frame_area["x"]
    frame_area_y = screen_y - frame_area["y"]

    # Clamp to frame area bounds
    frame_area_x = max(0, min(frame_area["width"] - 1, frame_area_x))
    frame_area_y = max(0, min(frame_area["height"] - 1, frame_area_y))

    return (frame_area_x, frame_area_y)


def conv_screen_to_frame_bbox(bbox: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
    """
    Convert a screen bounding box to frame area coordinates.

    Args:
        bbox: Tuple of (screen_x1, screen_y1, screen_x2, screen_y2)

    Returns:
        Tuple of (frame_area_x1, frame_area_y1, frame_area_x2, frame_area_y2)
    """
    screen_x1, screen_y1, screen_x2, screen_y2 = bbox
    frame_area_x1, frame_area_y1 = conv_screen_to_frame_coords(screen_x1, screen_y1)
    frame_area_x2, frame_area_y2 = conv_screen_to_frame_coords(screen_x2, screen_y2)

    return (frame_area_x1, frame_area_y1, frame_area_x2, frame_area_y2)


def conv_grid_to_frame_coords(grid_x: int, grid_y: int) -> tuple[int, int]:
    """Convert grid coordinates to frame-relative coordinates for screenshot analysis."""
    # Use the reliable grid_to_screen_coords first
    screen_x, screen_y = conv_grid_to_screen_coords(grid_x, grid_y)
    frame_x, frame_y = conv_screen_to_frame_coords(screen_x, screen_y)

    return (frame_x, frame_y)


def conv_grid_to_frame_bbox(bbox: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
    """
    Convert a grid bounding box to frame area coordinates.

    Args:
        bbox: Tuple of (grid_x1, grid_y1, grid_x2, grid_y2)

    Returns:
        Tuple of (frame_area_x1, frame_area_y1, frame_area_x2, frame_area_y2)
    """
    grid_x1, grid_y1, grid_x2, grid_y2 = bbox
    screen_x1, screen_y1 = conv_grid_to_screen_coords(grid_x1, grid_y1)
    screen_x2, screen_y2 = conv_grid_to_screen_coords(grid_x2, grid_y2)

    return conv_screen_to_frame_bbox((screen_x1, screen_y1, screen_x2, screen_y2))


def conv_frame_to_screen_coords(frame_x: int, frame_y: int) -> Tuple[int, int]:
    """
    Convert frame-relative coordinates to absolute screen coordinates.

    Args:
        frame_x: X coordinate relative to the frame area
        frame_y: Y coordinate relative to the frame area

    Returns:
        Tuple of (screen_x, screen_y) coordinates
    """
    window_manager = get_cache_manager()
    frame_area = window_manager.get_frame_area()
    if not frame_area:
        logger.warning("No valid frame area for frame to screen conversion")
        return (0, 0)
    screen_x = frame_area["x"] + frame_x
    screen_y = frame_area["y"] + frame_y
    return (screen_x, screen_y)


def conv_frame_to_screen_bbox(bbox: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
    """
    Convert a frame area bounding box to screen coordinates.

    Args:
        bbox: Tuple of (frame_area_x1, frame_area_y1, frame_area_x2, frame_area_y2)

    Returns:
        Tuple of (screen_x1, screen_y1, screen_x2, screen_y2)
    """
    frame_x1, frame_y1, frame_x2, frame_y2 = bbox
    screen_x1, screen_y1 = conv_frame_to_screen_coords(frame_x1, frame_y1)
    screen_x2, screen_y2 = conv_frame_to_screen_coords(frame_x2, frame_y2)
    return (screen_x1, screen_y1, screen_x2, screen_y2)
