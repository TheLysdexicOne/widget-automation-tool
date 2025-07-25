import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QScrollArea, QVBoxLayout, QWidget, QPushButton, QMenu
from PyQt6.QtCore import Qt


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
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setGeometry(100, 100, 200, 1250)

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

        # Create title widget
        self.title_label = QLabel("WIDGETS", self)
        from PyQt6.QtWidgets import QSizePolicy

        self.title_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                font-weight: bold;
                color: #2c3e50;
                padding: 4px;
            }
        """)

        # Main content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(8)
        content_layout.setContentsMargins(0, 0, 0, 0)

        for tier in sorted(tiers.keys()):
            # Tier header
            tier_label = QLabel(f"TIER {tier}")
            tier_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tier_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 4px 0 2px 4px;")
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
        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(scroll)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def create_frame_button(self, frame):
        """Create a button for a frame with automation status styling."""
        name = frame.get("name", "Unknown")
        automation = frame.get("automation", 0)
        frame_id = frame.get("id", "")

        btn = QPushButton(name)
        btn.setToolTip(f"ID: {frame_id}\nAutomation: {'Available' if automation else 'Not Implemented'}")

        # Style based on automation status
        if automation:
            btn.setStyleSheet("""
                QPushButton {
                    font-family: 'NotoMono', 'monospace'; 
                    font-size: 12px;
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 4px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #2ecc71;
                }
                QPushButton:pressed {
                    background-color: #1e8449;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    font-family: 'NotoMono', 'monospace'; 
                    font-size: 12px;
                    background-color: #95a5a6;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 4px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #7f8c8d;
                }
                QPushButton:pressed {
                    background-color: #5d6d7e;
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
