"""
Frames Management Package

A comprehensive system for frame (scene/minigame) detection and management.
This package handles frame creation, screenshot management, region selection,
and database operations with pixel art grid snapping.

Key Components:
- FramesManager: Combined UI manager and dialog for frames functionality
- DatabaseManagement: Core database and file management utility
- ScreenshotManagerDialog: Advanced screenshot management with primary selection
- RegionsViewerDialog: Visual region overlay and inspection
- GridSelectionWidget: Interactive region selection with grid snapping

Following project standards: KISS, no duplicated calculations, modular design.
"""

from .frames_manager import FramesManager
from .utility.database_management import DatabaseManagement

__all__ = [
    "FramesManager",
    "DatabaseManagement",
]
