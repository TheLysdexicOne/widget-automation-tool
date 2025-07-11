#!/usr/bin/env python3
"""
Debug test for overlay color issue
"""

import sys
import os
import tkinter as tk
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from overlay_gui import create_overlay


def debug_overlay_colors():
    """Test overlay colors to debug the issue"""
    print("Debug: Testing overlay colors...")

    # Create hidden root window
    root = tk.Tk()
    root.withdraw()

    # Create overlay
    overlay = create_overlay()
    overlay.show()

    print(f"Debug: Initial status_text = '{overlay.status_text}'")
    print(f"Debug: Initial circle_color = '{overlay.circle_color}'")

    # Test each status explicitly
    statuses_to_test = [
        ("INACTIVE", "Should be red"),
        ("ACTIVE", "Should be green"),
        ("ERROR", "Should be orange"),
        ("WAITING", "Should be blue"),
        ("STARTING", "Should be purple"),
    ]

    for status, description in statuses_to_test:
        print(f"\nDebug: Setting status to '{status}' ({description})")
        overlay.update_status(status, description)
        print(f"Debug: After update - status_text = '{overlay.status_text}'")
        print(f"Debug: After update - circle_color = '{overlay.circle_color}'")
        time.sleep(2)

    # Test the original issue
    print(f"\nDebug: Testing INACTIVE again...")
    overlay.update_status("INACTIVE", "No minigame detected")
    print(f"Debug: Final status_text = '{overlay.status_text}'")
    print(f"Debug: Final circle_color = '{overlay.circle_color}'")

    print("\nDebug: Close the overlay window to exit...")

    # Handle window close
    def on_closing():
        overlay.destroy()
        root.quit()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nDebug: Test interrupted")
    finally:
        overlay.destroy()


if __name__ == "__main__":
    debug_overlay_colors()
