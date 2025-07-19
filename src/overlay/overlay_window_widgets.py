"""
Widget-based overlay window for target application monitoring and screenshot functionality.
Uses hybrid approach: custom painting for compact circle, widgets for expanded interface.
"""

import json
import uuid
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QLabel,
    QFrame,
    QScrollArea,
    QGridLayout,
    QLineEdit,
    QTextEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QApplication,
)
from PyQt6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    QRect,
    QPoint,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QColor,
    QFont,
    QPixmap,
    QPaintEvent,
    QMouseEvent,
)
import pyautogui

from core.window_manager import WindowManager


class MinigameDataDialog(QDialog):
    """Dialog for adding/editing minigame data when taking screenshots."""

    def __init__(self, parent=None, minigames: list = None):
        super().__init__(parent)
        self.minigames = minigames or []
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Minigame Data Entry")
        self.setModal(True)
        self.resize(400, 300)

        layout = QVBoxLayout()

        # Minigame selection
        minigame_layout = QHBoxLayout()
        minigame_layout.addWidget(QLabel("Minigame:"))

        self.minigame_combo = QComboBox()
        self.minigame_combo.addItem("Create New Minigame", None)
        for mg in self.minigames:
            self.minigame_combo.addItem(mg.get("name", "Unnamed"), mg)
        minigame_layout.addWidget(self.minigame_combo)

        layout.addLayout(minigame_layout)

        # Name input (for new minigames)
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        layout.addWidget(self.description_input)

        # Frame type selection
        frame_layout = QHBoxLayout()
        frame_layout.addWidget(QLabel("Frame Type:"))

        self.frame_type_combo = QComboBox()
        self.frame_type_combo.addItems(
            ["background", "ui_element", "sprite", "text_region", "full_screen"]
        )
        frame_layout.addWidget(self.frame_type_combo)

        layout.addLayout(frame_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

        # Connect signals
        self.minigame_combo.currentIndexChanged.connect(self._on_minigame_changed)

    def _on_minigame_changed(self):
        """Update name field when minigame selection changes."""
        current_data = self.minigame_combo.currentData()
        if current_data:
            self.name_input.setText(current_data.get("name", ""))
            self.name_input.setEnabled(False)
        else:
            self.name_input.clear()
            self.name_input.setEnabled(True)

    def get_data(self) -> Dict[str, Any]:
        """Get the entered data."""
        return {
            "minigame": self.minigame_combo.currentData(),
            "name": self.name_input.text(),
            "description": self.description_input.toPlainText(),
            "frame_type": self.frame_type_combo.currentText(),
            "is_new_minigame": self.minigame_combo.currentData() is None,
        }


class ExpandedOverlayWidget(QWidget):
    """Widget-based expanded overlay interface."""

    screenshot_requested = pyqtSignal(dict)  # Emits minigame data

    def __init__(self, parent=None, window_manager: WindowManager = None):
        super().__init__(parent)
        self.window_manager = window_manager
        self.minigames_data = self._load_minigames()

        self.setStyleSheet(
            """
            QWidget {
                background-color: rgba(20, 20, 30, 240);
                color: #e0e0e0;
                border-radius: 10px;
            }
            QPushButton {
                background-color: #4a4a5a;
                border: 1px solid #666;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a5a6a;
            }
            QPushButton:pressed {
                background-color: #3a3a4a;
            }
            QComboBox {
                background-color: #4a4a5a;
                border: 1px solid #666;
                border-radius: 5px;
                padding: 5px;
            }
            QLabel {
                color: #e0e0e0;
                font-weight: bold;
            }
        """
        )

        self.setup_ui()

    def _load_minigames(self) -> Dict[str, Any]:
        """Load minigames configuration."""
        config_path = Path("config/minigames.json")
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"frames": [], "minigames": []}

    def _save_minigames(self):
        """Save minigames configuration."""
        config_path = Path("config/minigames.json")
        try:
            with open(config_path, "w") as f:
                json.dump(self.minigames_data, f, indent=2)
        except Exception as e:
            print(f"Error saving minigames: {e}")

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Title
        title = QLabel("Widget Automation Tool")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #ffffff; margin-bottom: 10px;"
        )
        layout.addWidget(title)

        # Screenshot section
        screenshot_frame = QFrame()
        screenshot_frame.setFrameStyle(QFrame.Shape.Box)
        screenshot_frame.setStyleSheet(
            "border: 1px solid #666; border-radius: 5px; padding: 10px;"
        )

        screenshot_layout = QVBoxLayout()

        # Screenshot button with dropdown menu
        screenshot_btn_layout = QHBoxLayout()

        self.screenshot_btn = QPushButton("📷 Take Screenshot")
        self.screenshot_btn.clicked.connect(self._take_screenshot)
        screenshot_btn_layout.addWidget(self.screenshot_btn)

        self.screenshot_menu = QComboBox()
        self.screenshot_menu.addItems(
            ["Add New Minigame", "Attach to Existing", "Edit Minigames"]
        )
        screenshot_btn_layout.addWidget(self.screenshot_menu)

        screenshot_layout.addLayout(screenshot_btn_layout)

        screenshot_frame.setLayout(screenshot_layout)
        layout.addWidget(screenshot_frame)

        # Status section
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Shape.Box)
        status_frame.setStyleSheet(
            "border: 1px solid #666; border-radius: 5px; padding: 10px;"
        )

        status_layout = QVBoxLayout()

        self.status_label = QLabel("Status: Ready")
        status_layout.addWidget(self.status_label)

        self.coords_label = QLabel("Mouse: (0, 0)")
        status_layout.addWidget(self.coords_label)

        self.playable_label = QLabel("Playable Area: 0%, 0%")
        status_layout.addWidget(self.playable_label)

        status_frame.setLayout(status_layout)
        layout.addWidget(status_frame)

        # Minigames section
        minigames_frame = QFrame()
        minigames_frame.setFrameStyle(QFrame.Shape.Box)
        minigames_frame.setStyleSheet(
            "border: 1px solid #666; border-radius: 5px; padding: 10px;"
        )

        minigames_layout = QVBoxLayout()

        minigames_title = QLabel(
            f"Minigames ({len(self.minigames_data.get('minigames', []))})"
        )
        minigames_layout.addWidget(minigames_title)

        # Quick stats
        frames_count = len(self.minigames_data.get("frames", []))
        stats_label = QLabel(f"Frames Collected: {frames_count}")
        minigames_layout.addWidget(stats_label)

        minigames_frame.setLayout(minigames_layout)
        layout.addWidget(minigames_frame)

        layout.addStretch()  # Push everything to top

        self.setLayout(layout)

    def _take_screenshot(self):
        """Handle screenshot button click."""
        action = self.screenshot_menu.currentText()

        if action == "Edit Minigames":
            self._edit_minigames()
            return

        # Show dialog for minigame data entry
        dialog = MinigameDataDialog(self, self.minigames_data.get("minigames", []))

        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()

            # Take screenshot
            try:
                screenshot = pyautogui.screenshot()
                screenshot_id = str(uuid.uuid4())
                screenshot_path = f"analysis_output/screenshot_{screenshot_id}.png"
                screenshot.save(screenshot_path)

                # Create frame data
                frame_data = {
                    "id": screenshot_id,
                    "timestamp": QTimer().currentTime().toString(),
                    "screenshot_path": screenshot_path,
                    "frame_type": data["frame_type"],
                    "description": data["description"],
                    "minigame_name": data["name"],
                }

                # Add to frames
                if "frames" not in self.minigames_data:
                    self.minigames_data["frames"] = []
                self.minigames_data["frames"].append(frame_data)

                # If new minigame, create it
                if data["is_new_minigame"] and data["name"]:
                    new_minigame = {
                        "name": data["name"],
                        "window_title": "WidgetInc",
                        "game_type": "vision_based",
                        "frame_ids": [screenshot_id],
                    }

                    if "minigames" not in self.minigames_data:
                        self.minigames_data["minigames"] = []
                    self.minigames_data["minigames"].append(new_minigame)

                # Save changes
                self._save_minigames()

                # Update UI
                self.setup_ui()  # Refresh the interface

                self.status_label.setText(f"Screenshot saved: {screenshot_id[:8]}...")

                # Emit signal with data
                self.screenshot_requested.emit(frame_data)

            except Exception as e:
                self.status_label.setText(f"Error taking screenshot: {e}")

    def _edit_minigames(self):
        """Open minigames configuration for editing."""
        # For now, just show a simple message
        self.status_label.setText("Minigames editor - coming soon!")

    def update_coordinates(self, x: int, y: int):
        """Update coordinate display."""
        self.coords_label.setText(f"Mouse: ({x}, {y})")

        # Calculate playable area percentage if window manager available
        if self.window_manager:
            try:
                playable_bounds = self.window_manager.get_playable_area_bounds()
                if playable_bounds:
                    px, py, pw, ph = playable_bounds
                    if px <= x <= px + pw and py <= y <= py + ph:
                        x_percent = ((x - px) / pw) * 100
                        y_percent = ((y - py) / ph) * 100
                        self.playable_label.setText(
                            f"Playable Area: {x_percent:.1f}%, {y_percent:.1f}%"
                        )
                    else:
                        self.playable_label.setText("Playable Area: Outside bounds")
                else:
                    self.playable_label.setText("Playable Area: Not detected")
            except Exception:
                self.playable_label.setText("Playable Area: Error")


class OverlayWindowWidgets(QWidget):
    """
    Hybrid overlay window using widgets for expanded interface.
    Compact mode uses custom painting, expanded mode uses PyQt6 widgets.
    """

    def __init__(self, window_manager, app=None):
        super().__init__()
        self.window_manager = window_manager
        self.app = app  # Reference to main application for target window info
        self.logger = logging.getLogger(__name__)

        # State
        self.is_expanded = False
        self.compact_size = 60
        self.expanded_size = (350, 450)
        self.border_width = 3

        # Animation
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Expanded widget (hidden initially)
        self.expanded_widget = ExpandedOverlayWidget(self, window_manager)
        self.expanded_widget.hide()

        # Timer for updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(100)  # 10 FPS

        self.setup_window()

    def setup_window(self):
        """Initialize the overlay window."""
        # Window flags for overlay behavior
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Start in compact mode
        self.resize(self.compact_size, self.compact_size)
        self.position_overlay()

    def position_overlay(self):
        """Position overlay in top-right corner of target window."""
        if self.app and self.app.current_target_window:
            try:
                # Get window rectangle
                window = self.app.current_target_window
                self.logger.debug(
                    f"Target window: left={window.left}, top={window.top}, width={window.width}, height={window.height}"
                )

                # Calculate position in top-right corner
                overlay_width = self.width()
                overlay_height = self.height()

                x = window.left + window.width - overlay_width - 10
                y = window.top + 30  # Account for title bar

                # Ensure overlay stays within screen bounds
                screen = QApplication.primaryScreen().geometry()
                x = max(0, min(x, screen.width() - overlay_width))
                y = max(0, min(y, screen.height() - overlay_height))

                self.logger.debug(
                    f"Calculated position: ({x}, {y}), overlay size: {overlay_width}x{overlay_height}, screen: {screen.width()}x{screen.height()}"
                )
                self.move(x, y)
                self.logger.debug(f"Final positioned overlay at ({x}, {y})")
            except Exception as e:
                self.logger.error(f"Error positioning overlay: {e}")
                # Fallback to center of screen
                screen = QApplication.primaryScreen().geometry()
                x = screen.width() // 2 - self.width() // 2
                y = screen.height() // 2 - self.height() // 2
                self.move(x, y)
                self.logger.debug(f"Fallback position: ({x}, {y})")
        else:
            self.logger.debug("No target window available for positioning")

    def paintEvent(self, event: QPaintEvent):
        """Custom painting for compact mode only."""
        if not self.is_expanded:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Get status info
            status_info = self._get_status_info()

            # Determine colors based on status
            if status_info["target_found"]:
                bg_color = QColor(0, 100, 0, 200)  # Green
                border_color = QColor(0, 150, 0)
            else:
                bg_color = QColor(100, 0, 0, 200)  # Red
                border_color = QColor(150, 0, 0)

            # Draw circle background
            painter.setBrush(QBrush(bg_color))
            painter.setPen(QPen(border_color, self.border_width))

            circle_rect = QRect(
                self.border_width,
                self.border_width,
                self.compact_size - 2 * self.border_width,
                self.compact_size - 2 * self.border_width,
            )
            painter.drawEllipse(circle_rect)

            # Draw status text
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))

            if status_info["target_found"]:
                painter.drawText(circle_rect, Qt.AlignmentFlag.AlignCenter, "●")
            else:
                painter.drawText(circle_rect, Qt.AlignmentFlag.AlignCenter, "×")

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse clicks to toggle expanded/compact mode."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_expanded()
        super().mousePressEvent(event)

    def _toggle_expanded(self):
        """Toggle between expanded and compact modes."""
        if self.is_expanded:
            self._collapse()
        else:
            self._expand()

    def _expand(self):
        """Expand to widget-based interface."""
        self.is_expanded = True

        # Setup layout with expanded widget
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.expanded_widget)
        self.setLayout(layout)

        # Show expanded widget
        self.expanded_widget.show()

        # Animate to expanded size
        current_pos = self.pos()
        new_width, new_height = self.expanded_size

        # Adjust position to keep in top-right
        new_x = current_pos.x() - (new_width - self.compact_size)
        new_y = current_pos.y()

        target_geometry = QRect(new_x, new_y, new_width, new_height)

        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(target_geometry)
        self.animation.start()

    def _collapse(self):
        """Collapse to compact circle mode."""
        self.is_expanded = False

        # Hide expanded widget
        self.expanded_widget.hide()

        # Remove layout
        if self.layout():
            self.layout().deleteLater()

        # Animate to compact size
        current_pos = self.pos()
        new_x = current_pos.x() + (self.expanded_size[0] - self.compact_size)
        new_y = current_pos.y()

        target_geometry = QRect(new_x, new_y, self.compact_size, self.compact_size)

        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(target_geometry)
        self.animation.start()

    def _update_display(self):
        """Update display information."""
        if not self.is_expanded:
            self.update()  # Trigger repaint for compact mode
        else:
            # Update expanded widget with current mouse position
            try:
                pos = pyautogui.position()
                self.expanded_widget.update_coordinates(pos.x, pos.y)
            except Exception as e:
                self.logger.error(f"Error updating coordinates: {e}")

    def _get_status_info(self) -> Dict[str, Any]:
        """Get current status information."""
        target_found = (
            self.app
            and self.app.current_target_window
            and hasattr(self.app.current_target_window, "isActive")
        )

        return {
            "target_found": target_found,
        }
