"""
Utility module for common functionality.
Centralizes reusable components following KISS principles.
"""

from .logging_utils import get_smart_logger, log_position_change, log_state_change
from .window_utils import calculate_overlay_position

__all__ = [
    "calculate_overlay_position",
    "get_smart_logger",
    "log_position_change",
    "log_state_change",
]
