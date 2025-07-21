"""
Attach Frame Dialog - Temporary Placeholder
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel


class AttachToFrameDialog(QDialog):
    """Temporary placeholder for attach frame dialog."""

    def __init__(self, screenshot, frames_list, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Attach Frame - Under construction"))
        self.setLayout(layout)

    def get_selected_frame(self):
        return None
