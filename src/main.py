import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class CustomTitleBar(QWidget):
    """Custom title bar with minimize and close buttons."""

    def __init__(self, parent):
        super().__init__(parent)
        self.main_window = parent
        self.setFixedHeight(30)

        # Track dragging
        self.dragging = False
        self.drag_position = QPoint()

        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(0)

        # Title label
        self.title_label = QLabel("Widget Automation Tool")

        # Spacer
        layout.addWidget(self.title_label)
        layout.addStretch()

        # Minimize button
        self.minimize_btn = QPushButton("−")
        self.minimize_btn.setFixedSize(30, 30)
        self.minimize_btn.clicked.connect(self.main_window.showMinimized)

        # Close button
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.main_window.close)

        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.close_btn)

    def mousePressEvent(self, event):
        """Start dragging the window."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.main_window.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        """Drag the window."""
        if self.dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.main_window.move(event.globalPosition().toPoint() - self.drag_position)

    def mouseReleaseEvent(self, event):
        """Stop dragging."""
        self.dragging = False


class MainWindow(QMainWindow):
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            widget = self.childAt(pos)

            if isinstance(widget, QPushButton):
                return
            menu = QMenu(self)
            restart_action = menu.addAction("Restart")
            menu.addSeparator()
            exit_action = menu.addAction("Exit")
            global_pos = event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos()
            action = menu.exec(global_pos)
            if action == restart_action:
                self.restart_app()
            elif action == exit_action:
                self.close()
        else:
            super().mousePressEvent(event)

    def restart_app(self):
        import os
        import sys

        # Relaunch the current script
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Widget Automation Tool")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Window
        )
        self.setMinimumSize(100, 200)  # Set a reasonable minimum size

        # Load frames from JSON (adjusted path for our project structure)
        frames_file = Path(__file__).parent / "config" / "frames_database.json"
        try:
            with open(frames_file, "r", encoding="utf-8") as f:
                frames_data = json.load(f)
            frames = frames_data.get("frames", [])
        except FileNotFoundError:
            print(f"Warning: Could not find frames database at {frames_file}")
            frames = []

        # Group frames by tier
        from collections import defaultdict
        import re

        tiers = defaultdict(list)
        for frame in frames:
            match = re.match(r"(\d+)\.\d+", frame.get("id", ""))
            if match:
                tier = int(match.group(1))
            else:
                tier = 0
            tiers[tier].append(frame)

        # Create main widget with custom title bar
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add custom title bar
        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)

        # Create title widget
        self.title_label = QLabel("WIDGETS")
        from PyQt6.QtWidgets import QSizePolicy

        self.title_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Main content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(8)
        content_layout.setContentsMargins(8, 8, 8, 8)

        for tier in sorted(tiers.keys()):
            # Tier header
            tier_label = QLabel(f"TIER {tier}")
            tier_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.addWidget(tier_label)

            # Buttons for this tier
            row_widget = QWidget()
            row_layout = QVBoxLayout(row_widget)
            row_layout.setSpacing(8)
            row_layout.setContentsMargins(8, 0, 0, 0)

            for frame in tiers[tier]:
                btn = self.create_frame_button(frame)
                row_layout.addWidget(btn)
            content_layout.addWidget(row_widget)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content_widget)

        # Layout
        content_container_layout = QVBoxLayout()
        content_container_layout.addWidget(self.title_label)
        content_container_layout.addWidget(scroll)

        content_container = QWidget()
        content_container.setLayout(content_container_layout)

        main_layout.addWidget(content_container)

        self.setCentralWidget(main_widget)

        # Auto-resize width to fit content, allow manual resizing
        self.adjustSize()
        # Set width to fit contents
        content_width = content_container.sizeHint().width() + 15  # Add padding for scroll area and layout
        self.resize(content_width, 600)  # Set reasonable height, auto width
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.move(100, 100)

    def create_frame_button(self, frame):
        """Create a button for a frame with automation status styling."""
        name = frame.get("name", "Unknown")
        automation = frame.get("automation", 0)
        frame_id = frame.get("id", "")

        btn = QPushButton(name)
        btn.setToolTip(f"ID: {frame_id}\nAutomation: {'Available' if automation else 'Not Implemented'}")

        # Only minimal font styling as per copilot instructions
        btn.setStyleSheet("""
            QPushButton {
                font-family: 'Noto Sans', 'Segoe UI';
                font-size: 12px;
            }
        """)

        # Connect button click to automation
        btn.clicked.connect(lambda checked, f=frame: self.start_automation(f))

        return btn

    def start_automation(self, frame):
        """Handle frame automation start."""
        name = frame.get("name", "Unknown")
        automation = frame.get("automation", 0)
        frame_id = frame.get("id", "")

        if automation:
            print(f"🤖 Starting automation for: {name} (ID: {frame_id})")
            # TODO: Implement actual automation logic here
        else:
            print(f"⚠️  Automation not implemented for: {name} (ID: {frame_id})")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        app.quit()
        sys.exit(0)
    except Exception as e:
        print(f"Application error: {e}")
        app.quit()
        sys.exit(1)


if __name__ == "__main__":
    main()
