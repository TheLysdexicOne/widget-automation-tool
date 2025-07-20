#!/usr/bin/env python3
"""
Test script to debug screenshot capture
"""

import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PIL import ImageGrab
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt6.QtGui import QPixmap


def test_screenshot():
    """Test screenshot capture methods."""
    print("Testing screenshot capture...")

    # Initialize QApplication for QPixmap testing
    app = QApplication(sys.argv)

    # Test 1: Full screen capture
    try:
        screenshot = ImageGrab.grab()
        print(f"Full screen screenshot size: {screenshot.size}")

        # Save to file
        test_path = Path("test_screenshot.png")
        screenshot.save(test_path)
        print(f"Screenshot saved to: {test_path}")

        # Test loading as QPixmap
        pixmap = QPixmap(str(test_path))
        print(f"QPixmap size: {pixmap.width()}x{pixmap.height()}")

        # Check if image is black/empty
        bbox = screenshot.getbbox()
        if bbox is None:
            print("WARNING: Screenshot appears to be empty/black")
        else:
            print(f"Screenshot bounding box: {bbox}")

        return True, app

    except Exception as e:
        print(f"Error in screenshot test: {e}")
        return False, app


def show_screenshot():
    """Show screenshot in a window."""
    app = QApplication(sys.argv)

    # Load the screenshot
    test_path = Path("test_screenshot.png")
    if not test_path.exists():
        print("No test screenshot found. Run test_screenshot() first.")
        return

    # Create window and show screenshot
    window = QMainWindow()
    window.setWindowTitle("Screenshot Test")

    label = QLabel()
    pixmap = QPixmap(str(test_path))

    # Scale down for display
    from PyQt6.QtCore import Qt

    scaled_pixmap = pixmap.scaled(
        800,
        600,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )

    label.setPixmap(scaled_pixmap)
    window.setCentralWidget(label)

    window.show()

    print("Showing screenshot window. Close window to continue.")
    app.exec()


if __name__ == "__main__":
    success, app = test_screenshot()
    if success:
        print("\nScreenshot test successful!")
        show_screenshot()
    else:
        print("Screenshot test failed!")
