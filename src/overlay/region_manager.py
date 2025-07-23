"""
Region Manager Dialogs and Widgets
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QScrollArea, QHBoxLayout, QPushButton, QWidget
from PyQt6.QtGui import QFont, QPixmap, QPainter, QPen, QBrush, QColor
from PyQt6.QtCore import Qt
from pathlib import Path
from typing import Dict


class RegionManager(QDialog):
    """Dialog for viewing text regions overlaid on primary screenshot."""

    def __init__(self, screenshot_path: Path, frame_data: Dict, parent=None):
        super().__init__(parent)
        self.screenshot_path = screenshot_path
        self.frame_data = frame_data
        self.setWindowTitle("Regions Viewer")
        # self.setModal(True)  # Make modeless
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.resize(900, 700)
        self._setup_ui()

    def _setup_ui(self):
        """Setup regions viewer UI with synced dropdown."""
        from PyQt6.QtWidgets import QComboBox
        from utility.frame_selection_model import FrameSelectionModel

        layout = QVBoxLayout(self)

        # Top: Title and dropdown
        top_layout = QHBoxLayout()
        title_label = QLabel("Managing Regions")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        top_layout.addWidget(title_label)

        self.dropdown = QComboBox()
        self.dropdown.setMinimumWidth(220)
        self.dropdown.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.dropdown.setEnabled(True)
        self.dropdown.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        top_layout.addWidget(self.dropdown)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # Populate dropdown from FrameSelectionModel
        self.frame_model = FrameSelectionModel.instance()
        self._populate_dropdown()
        self.dropdown.currentIndexChanged.connect(self._on_dropdown_changed)
        self.frame_model.selection_changed.connect(self._on_external_selection_changed)

        # Create a widget to display the screenshot with regions
        self.regions_widget = RegionsDisplayWidget(self.screenshot_path, self.frame_data)
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.regions_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Regions information
        self.info_layout = QVBoxLayout()
        self.info_label = QLabel("Text Regions:")
        self.info_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.info_layout.addWidget(self.info_label)
        layout.addLayout(self.info_layout)
        self._update_info()

        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

    def _populate_dropdown(self):
        self.dropdown.blockSignals(True)
        self.dropdown.clear()
        frames = self.frame_model.get_frames_list()
        for frame in frames:
            self.dropdown.addItem(f"{frame.get('id', '??')}: {frame.get('name', 'Unnamed')}", frame)
        # Set current selection
        selected = self.frame_model.get_selected_frame()
        if selected:
            for i in range(self.dropdown.count()):
                if self.dropdown.itemData(i) == selected:
                    self.dropdown.setCurrentIndex(i)
                    break
        self.dropdown.blockSignals(False)

    def _on_dropdown_changed(self, idx):
        frame = self.dropdown.itemData(idx)
        if frame:
            self.frame_model.set_selected_frame(frame)
            self._update_for_frame(frame)

    def _on_external_selection_changed(self, frame):
        self._populate_dropdown()
        self._update_for_frame(frame)

    def _update_for_frame(self, frame):
        self.frame_data = frame.copy()
        self.screenshot_path = self._get_primary_screenshot_path(frame)
        self.regions_widget.frame_data = self.frame_data
        self.regions_widget.screenshot_path = self.screenshot_path
        self.regions_widget.update()
        self._update_info()

    def _get_primary_screenshot_path(self, frame):
        screenshots = frame.get("screenshots", [])
        if screenshots:
            return Path("assets/screenshots") / f"{frame.get('name', 'Unnamed').replace(' ', '_')}_{screenshots[0]}.png"
        return Path()

    def _update_info(self):
        # Clear and repopulate info layout
        while self.info_layout.count() > 1:
            item = self.info_layout.takeAt(1)
            if item is not None:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        text_regions = self.frame_data.get("regions", {}).get("text", [])
        if text_regions:
            for i, region in enumerate(text_regions):
                region_info = region.get("region", {})
                text_info = region.get("text", "")
                info_text = f'Region {i + 1}: "{text_info}" at ({region_info.get("x", 0)}, {region_info.get("y", 0)}) {region_info.get("width", 0)}x{region_info.get("height", 0)}'
                self.info_layout.addWidget(QLabel(info_text))
        else:
            self.info_layout.addWidget(QLabel("No text regions defined"))


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
