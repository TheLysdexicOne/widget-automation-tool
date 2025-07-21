"""
Frames Widgets - UI Components

UI widgets and dialogs for frames management.
Widgets are being created incrementally.

Following project standards: KISS, no duplicated calculations, modular design.
"""

from .add_frame_dialog import AddFrameDialog
from .edit_frame_dialog import EditFrameDialog
from .attach_frame_dialog import AttachToFrameDialog
from .frames_dialog import FramesDialog
from .grid_selection_widget import GridSelectionWidget
from .regions_viewer_dialog import RegionsViewerDialog
from .screenshot_gallery_widget import ScreenshotGalleryWidget

__all__ = [
    "AddFrameDialog",
    "EditFrameDialog",
    "AttachToFrameDialog",
    "FramesDialog",
    "GridSelectionWidget",
    "RegionsViewerDialog",
    "ScreenshotGalleryWidget",
]
