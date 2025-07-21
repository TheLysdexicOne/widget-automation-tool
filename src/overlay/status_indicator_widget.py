"""
Status Indicator Widget - Top of Main Overlay Widget
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPaintEvent
from utility.status_manager import ApplicationState
from utility.widget_utils import get_status_color


class StatusIndicatorWidget(QWidget):
    """Custom widget for status circle and text display."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_state = ApplicationState.READY  # Start with wrong state to force update
        self.setFixedHeight(40)  # Slightly taller than buttons to fit circle and text
        self.setMinimumWidth(160)

        # Transparent background to blend with main overlay
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_state(self, state: ApplicationState):
        """Update the status state and trigger repaint."""
        if self.current_state != state:
            self.current_state = state
            self.update()

    def paintEvent(self, event: QPaintEvent):
        """Paint the status circle and text."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw status circle - fixed 24px diameter in right side
        circle_color = self._get_status_color()
        painter.setBrush(QBrush(circle_color))
        painter.setPen(QPen(circle_color.darker(120), 2))

        # Position circle on right side with margin
        circle_size = 24
        margin = 10
        circle_x = self.width() - circle_size - margin
        circle_y = (self.height() - circle_size) // 2  # Center vertically
        circle_rect = QRect(circle_x, circle_y, circle_size, circle_size)
        painter.drawEllipse(circle_rect)

        # Draw status text - left-aligned, inline with circle center
        painter.setPen(QPen(QColor(200, 200, 200), 1))  # Light gray text
        painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))  # Slightly smaller for widget

        # Position text inline with circle center
        text_y = circle_y + (circle_size // 2)
        text_rect = QRect(10, text_y - 10, self.width() - circle_size - 30, 20)
        status_text = self.current_state.value.upper()
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            status_text,
        )

    def _get_status_color(self) -> QColor:
        """Get color based on current state using centralized mapping."""
        return get_status_color(self.current_state)
