"""
Widget creation utilities.
Centralizes common widget creation patterns following KISS principles.
"""

import logging
from typing import Callable, Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QColor, QFont
from utility.status_manager import ApplicationState

logger = logging.getLogger(__name__)


def create_floating_button(
    parent: QWidget,
    width: int = 40,
    height: int = 30,
    click_handler: Optional[Callable] = None,
    icon_text: str = "📷",
) -> QWidget:
    """
    Create a floating button widget with standard styling.

    Args:
        parent: Parent widget
        width: Button width
        height: Button height
        click_handler: Function to handle mouse press events
        icon_text: Text/emoji to display on button

    Returns:
        Configured button widget
    """
    button = QWidget()
    button.setParent(None)  # Make it top-level
    button.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
    button.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    button.setFixedSize(width, height)

    # Standard button styling
    button.setStyleSheet(
        """
        QWidget {
            background-color: rgba(60, 60, 70, 200);
            border: 1px solid rgba(100, 100, 110, 255);
            border-radius: 6px;
            color: #e0e0e0;
        }
        QWidget:hover {
            background-color: rgba(80, 80, 90, 220);
        }
    """
    )

    # Add click handling if provided
    if click_handler:
        button.mousePressEvent = lambda event: _handle_button_click(event, click_handler)

    # Add paint event for icon
    button.paintEvent = lambda event: _paint_button_icon(button, icon_text)

    return button


def _handle_button_click(event, click_handler):
    """Handle button click events."""
    if event.button() == Qt.MouseButton.LeftButton:
        click_handler(event)


def _paint_button_icon(button: QWidget, icon_text: str):
    """Paint button icon."""
    painter = QPainter(button)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Draw icon
    painter.setPen(QPen(QColor(200, 200, 200), 1))
    painter.setFont(QFont("Arial", 12))

    # Center the text
    text_x = (button.width() - 20) // 2 + 8  # Rough centering
    text_y = button.height() - 10
    painter.drawText(text_x, text_y, icon_text)


def ensure_widget_on_top(widget: QWidget):
    """Ensure widget stays on top of other windows."""
    if widget and widget.isVisible():
        widget.raise_()
        widget.activateWindow()


def position_widget_relative(widget: QWidget, reference_widget: QWidget, offset_x: int = 0, offset_y: int = 0):
    """Position widget relative to reference widget."""
    if not widget or not reference_widget:
        return

    ref_geometry = reference_widget.geometry()
    new_x = ref_geometry.x() + offset_x
    new_y = ref_geometry.y() + offset_y

    widget.move(new_x, new_y)


def get_status_color(state: ApplicationState) -> QColor:
    """Centralized state-to-color mapping utility."""
    color_map = {
        ApplicationState.ACTIVE: QColor(0, 255, 0),  # Bright green - performing automation
        ApplicationState.READY: QColor(144, 238, 144),  # Light green - ready, waiting for user
        ApplicationState.ATTENTION: QColor(255, 165, 0),  # Orange - no automation programmed
        ApplicationState.INACTIVE: QColor(128, 128, 128),  # Gray - no automation available
        ApplicationState.ERROR: QColor(255, 0, 0),  # Red - application error
    }
    return color_map.get(state, QColor(128, 128, 128))
