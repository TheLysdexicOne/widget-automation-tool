import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import pytest
from PyQt6.QtWidgets import QApplication
from overlay.frames_manager import FramesManager


@pytest.fixture(scope="module")
def app():
    import sys

    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def test_frames_manager_initializes(app):
    fm = FramesManager(None)
    assert fm.windowTitle() == "Frames Managemer"
    assert fm.isModal()
    assert fm.selected_frame is None or isinstance(fm.selected_frame, dict)
    assert hasattr(fm, "frames_management")
    assert hasattr(fm, "dropdown")
    assert hasattr(fm, "_update_frame_display")


def test_frames_manager_refresh_frames_list(app):
    fm = FramesManager(None)
    fm._refresh_frames_list()
    assert isinstance(fm.frames_list, list)
    assert hasattr(fm, "dropdown")
    # Should not raise
    fm._on_frame_selected()
