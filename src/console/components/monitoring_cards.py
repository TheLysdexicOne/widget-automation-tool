"""
Monitoring card components for the monitoring tab.
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel


class MonitoringCard(QFrame):
    """A card widget for monitoring information."""

    def __init__(self, title, subtitle="", parent=None):
        super().__init__(parent)
        self.title = title
        self.subtitle = subtitle
        self._setup_ui()

    def _setup_ui(self):
        """Setup the card UI."""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            """
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                padding: 10px;
            }
        """
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        layout.addWidget(title_label)

        # Subtitle (if provided)
        if self.subtitle:
            subtitle_label = QLabel(self.subtitle)
            subtitle_label.setStyleSheet("font-size: 12px; color: #666;")
            layout.addWidget(subtitle_label)
