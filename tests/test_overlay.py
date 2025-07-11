#!/usr/bin/env python3
"""
Test script for the overlay GUI
Run this to see the overlay without needing WidgetInc
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

import tkinter as tk
import time
import threading
from overlay_gui import create_overlay


def test_overlay():
    """Test the overlay GUI with different states"""
    # Create hidden root window
    root = tk.Tk()
    root.withdraw()

    # Create overlay
    overlay = create_overlay()
    overlay.show()

    # Flag to control the test
    test_running = True

    def cycle_states():
        """Cycle through different overlay states"""
        states = [
            ("STARTING", "Initializing..."),
            ("WAITING", "Looking for WidgetInc..."),
            ("INACTIVE", "No minigame detected"),
            ("ACTIVE", "Running: Clicker Game"),
            ("ACTIVE", "Running: Sprite Sorter"),
            ("WAITING", "Preparing next game..."),
            ("ERROR", "Connection lost"),
            ("INACTIVE", "Automation complete"),
        ]

        state_index = 0
        while test_running:
            status, detail = states[state_index]
            overlay.update_status(status, detail)
            state_index = (state_index + 1) % len(states)

            # Sleep in small chunks to be responsive to interrupts
            for _ in range(30):  # 3 seconds total
                if not test_running:
                    break
                time.sleep(0.1)

        print("Test complete!")

    def stop_test():
        """Stop the test and close windows"""
        nonlocal test_running
        test_running = False
        overlay.destroy()
        root.quit()

    # Handle window close event
    def on_closing():
        stop_test()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Start state cycling in background
    state_thread = threading.Thread(target=cycle_states, daemon=True)
    state_thread.start()

    # Run GUI with proper exception handling
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nTest interrupted")
        stop_test()
    finally:
        test_running = False
        if overlay:
            overlay.destroy()


if __name__ == "__main__":
    print("Testing Overlay GUI...")
    print("The overlay should appear and cycle through different states.")
    print("Try hovering over it, clicking to pin/unpin, and moving your mouse away.")
    print("Press Ctrl+C or close the window to exit.")

    test_overlay()
