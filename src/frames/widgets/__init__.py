"""
Frames Widgets - UI Components

UI widgets and dialogs for frames management.
Widgets are being created incrementally.

Following project standards: KISS, no duplicated calculations, modular design.
"""

from .edit_frame_dialog import EditFrameDialog
from .grid_selection_widget import GridSelectionWidget
from .regions_viewer_dialog import RegionsViewerDialog
from .screenshot_gallery_widget import ScreenshotGalleryWidget

__all__ = [
    "EditFrameDialog",
    "GridSelectionWidget",
    "RegionsViewerDialog",
    "ScreenshotGalleryWidget",
]
