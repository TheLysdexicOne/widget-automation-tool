"""
Screenshot Gallery Widget - Displays screenshots in a grid layout
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGridLayout, QPushButton, QFrame, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from typing import List
from pathlib import Path


class ScreenshotGalleryWidget(QWidget):
    """Widget for displaying screenshot gallery with delete functionality."""

    screenshot_clicked = pyqtSignal(str)  # Emits UUID of clicked screenshot

    def __init__(self, screenshots: List[str], screenshots_dir: Path, parent=None):
        super().__init__(parent)
        self.screenshots = screenshots
        self.screenshots_dir = screenshots_dir
        self.marked_for_deletion = set()

        self._setup_ui()

    def _setup_ui(self):
        """Setup gallery UI."""
        layout = QGridLayout(self)

        # Display screenshots in a grid
        row, col = 0, 0
        max_cols = 3

        for screenshot_uuid in self.screenshots:
            screenshot_widget = self._create_screenshot_widget(screenshot_uuid)
            layout.addWidget(screenshot_widget, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        if not self.screenshots:
            no_screenshots_label = QLabel("No screenshots available")
            no_screenshots_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_screenshots_label, 0, 0)

    def _create_screenshot_widget(self, screenshot_uuid: str) -> QWidget:
        """Create widget for individual screenshot."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box)
        widget.setMaximumSize(120, 100)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Find screenshot file
        screenshot_path = None
        for file_path in self.screenshots_dir.glob(f"*{screenshot_uuid}*"):
            screenshot_path = file_path
            break

        # Screenshot thumbnail
        if screenshot_path and screenshot_path.exists():
            pixmap = QPixmap(str(screenshot_path))
            thumbnail = pixmap.scaled(
                80,
                60,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            screenshot_label = QLabel()
            screenshot_label.setPixmap(thumbnail)
            screenshot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            screenshot_label.mousePressEvent = lambda ev, uuid=screenshot_uuid: self._on_screenshot_clicked(uuid)
            layout.addWidget(screenshot_label)
        else:
            # Missing file placeholder
            placeholder = QLabel("Missing\nFile")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: red;")
            layout.addWidget(placeholder)

        # Delete button (X)
        delete_button = QPushButton("×")
        delete_button.setMaximumSize(20, 20)
        delete_button.setStyleSheet(
            """
            QPushButton {
                background-color: red;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: darkred;
            }
        """
        )
        delete_button.clicked.connect(lambda: self._on_delete_clicked(screenshot_uuid, widget))

        # Position delete button in top-right corner
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(delete_button)
        layout.insertLayout(0, button_layout)

        return widget

    def _on_screenshot_clicked(self, screenshot_uuid: str):
        """Handle screenshot thumbnail click."""
        self.screenshot_clicked.emit(screenshot_uuid)

    def _on_delete_clicked(self, screenshot_uuid: str, widget: QWidget):
        """Handle delete button click."""
        if screenshot_uuid in self.marked_for_deletion:
            # Unmark for deletion
            self.marked_for_deletion.remove(screenshot_uuid)
            widget.setStyleSheet("")
        else:
            # Mark for deletion
            self.marked_for_deletion.add(screenshot_uuid)
            widget.setStyleSheet("background-color: rgba(255, 0, 0, 50);")

    def get_screenshots_to_delete(self) -> List[str]:
        """Get list of screenshot UUIDs marked for deletion."""
        return list(self.marked_for_deletion)
