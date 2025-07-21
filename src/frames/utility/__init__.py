"""
Frames Utility Package

Core utility classes and functions for frames management:
- FramesManagement: Core data operations and database management
- Helper functions for frame processing

Following project standards: KISS, no duplicated calculations, modular design.
"""

from .frames_management import FramesManagement

__all__ = [
    "FramesManagement",
]
