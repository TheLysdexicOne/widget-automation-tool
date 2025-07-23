import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import pytest
from PyQt6.QtWidgets import QApplication
from overlay.screenshot_manager import ScreenshotManagerDialog


@pytest.fixture(scope="module")
def app():
    import sys

    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def test_screenshot_manager_initializes(app):
    # Minimal frame_data and dummy frames_manager
    frame_data = {"name": "TestFrame", "screenshots": []}

    class DummyFramesManager:
        screenshots_dir = None

    dlg = ScreenshotManagerDialog(frame_data, DummyFramesManager(), None)
    assert dlg.windowTitle().startswith("Screenshot Manager")
    assert dlg.isModal()
    assert hasattr(dlg, "current_screenshots")
    assert hasattr(dlg, "staged_screenshots")
