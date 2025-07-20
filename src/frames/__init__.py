"""
Frames Management Package

A comprehensive system for frame (scene/minigame) detection and management.
This package handles frame creation, screenshot management, region selection,
and database operations with pixel art grid snapping.

Key Components:
- FramesManager: Core database and file management
- FramesDialog: Main frames management interface
- ScreenshotManagerDialog: Advanced screenshot management with primary selection
- RegionsViewerDialog: Visual region overlay and inspection
- GridSelectionWidget: Interactive region selection with grid snapping

Following project standards: KISS, no duplicated calculations, modular design.
"""

from .manager import (
    FramesManager,
    FramesDialog,
    FramesMenuSystem,
    ScreenshotManagerDialog,
    RegionsViewerDialog,
    GridSelectionWidget,
    EditFrameDialog,
    AddFrameDialog,
    AttachToFrameDialog,
    ScreenshotGalleryWidget,
    RegionsDisplayWidget,
)

__all__ = [
    "FramesManager",
    "FramesDialog",
    "FramesMenuSystem",
    "ScreenshotManagerDialog",
    "RegionsViewerDialog",
    "GridSelectionWidget",
    "EditFrameDialog",
    "AddFrameDialog",
    "AttachToFrameDialog",
    "ScreenshotGalleryWidget",
    "RegionsDisplayWidget",
]
