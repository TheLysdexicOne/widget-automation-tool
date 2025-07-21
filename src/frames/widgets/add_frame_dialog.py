"""
Add Frame Dialog - Temporary Placeholder
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel


class AddFrameDialog(QDialog):
    """Temporary placeholder for add frame dialog."""

    def __init__(self, screenshot, playable_coords, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Add Frame - Under construction"))
        self.setLayout(layout)

    def get_frame_data(self):
        return {}
