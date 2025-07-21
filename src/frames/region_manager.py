"""
Region Manager Dialogs and Widgets
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QScrollArea, QHBoxLayout, QPushButton, QWidget
from PyQt6.QtGui import QFont, QPixmap, QPainter, QPen, QBrush, QColor
from PyQt6.QtCore import Qt
from pathlib import Path
from typing import Dict


class RegionsViewerDialog(QDialog):
    """Dialog for viewing text regions overlaid on primary screenshot."""

    def __init__(self, screenshot_path: Path, frame_data: Dict, parent=None):
        super().__init__(parent)
        self.screenshot_path = screenshot_path
        self.frame_data = frame_data

        self.setWindowTitle("Regions Viewer")
        self.setModal(True)
        self.resize(900, 700)
        self._setup_ui()

    def _setup_ui(self):
        """Setup regions viewer UI."""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel(f"Text Regions for: {self.frame_data.get('name', 'Unnamed Frame')}")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)

        # Create a widget to display the screenshot with regions
        self.regions_widget = RegionsDisplayWidget(self.screenshot_path, self.frame_data)
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.regions_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Regions information
        info_layout = QVBoxLayout()
        info_label = QLabel("Text Regions:")
        info_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        info_layout.addWidget(info_label)

        text_regions = self.frame_data.get("regions", {}).get("text", [])
        if text_regions:
            for i, region in enumerate(text_regions):
                region_info = region.get("region", {})
                text_info = region.get("text", "")
                info_text = f'Region {i + 1}: "{text_info}" at ({region_info.get("x", 0)}, {region_info.get("y", 0)}) {region_info.get("width", 0)}x{region_info.get("height", 0)}'
                info_layout.addWidget(QLabel(info_text))
        else:
            info_layout.addWidget(QLabel("No text regions defined"))

        layout.addLayout(info_layout)

        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)


class RegionsDisplayWidget(QWidget):
    """Widget to display screenshot with text regions overlaid."""

    def __init__(self, screenshot_path: Path, frame_data: Dict, parent=None):
        super().__init__(parent)
        self.screenshot_path = screenshot_path
        self.frame_data = frame_data
        self.scale_factor = 0.8  # Scale down for viewing

        # Load screenshot
        self.pixmap = QPixmap(str(screenshot_path))
        if not self.pixmap.isNull():
            # Scale the pixmap
            self.scaled_pixmap = self.pixmap.scaled(
                int(self.pixmap.width() * self.scale_factor),
                int(self.pixmap.height() * self.scale_factor),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setFixedSize(self.scaled_pixmap.size())
        else:
            self.scaled_pixmap = QPixmap()
            self.setFixedSize(400, 300)

    def paintEvent(self, event):
        """Paint the screenshot with regions overlaid."""
        painter = QPainter(self)

        # Draw screenshot
        if not self.scaled_pixmap.isNull():
            painter.drawPixmap(0, 0, self.scaled_pixmap)

        # Draw text regions
        text_regions = self.frame_data.get("regions", {}).get("text", [])
        colors = [
            QColor(0, 255, 255, 120),  # Cyan
            QColor(255, 165, 0, 120),  # Orange
            QColor(0, 255, 0, 120),  # Green
        ]

        for i, region in enumerate(text_regions):
            region_info = region.get("region", {})
            if not region_info:
                continue

            # Scale region coordinates
            x = int(region_info.get("x", 0) * self.scale_factor)
            y = int(region_info.get("y", 0) * self.scale_factor)
            width = int(region_info.get("width", 0) * self.scale_factor)
            height = int(region_info.get("height", 0) * self.scale_factor)

            # Draw region box
            color = colors[i % len(colors)]
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color))
            painter.drawRect(x, y, width, height)

            # Draw region label
            text = region.get("text", f"Region {i + 1}")
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawText(x + 5, y + 15, text)
