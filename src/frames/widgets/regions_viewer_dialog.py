"""
Regions Viewer Dialog - Temporary Placeholder
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel


class RegionsViewerDialog(QDialog):
    """Temporary placeholder for regions viewer dialog."""

    def __init__(self, screenshot_path, frame_data, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Regions Viewer - Under construction"))
        self.setLayout(layout)
