#!/usr/bin/env python3
"""
Simple test for the Debug GUI standalone
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from debug_gui import create_debug_gui


def test_debug_gui_standalone():
    """Test just the Debug GUI"""
    print("Starting Debug GUI test...")

    # Create debug GUI
    debug_gui = create_debug_gui()

    # Add some test logs
    debug_gui.log("INFO", "Debug GUI standalone test started")
    debug_gui.log("SUCCESS", "All components loaded successfully")
    debug_gui.log("WARNING", "This is a test warning")
    debug_gui.log("ERROR", "This is a test error")
    debug_gui.log("DEBUG", "This is a debug message")

    # Update some status
    debug_gui.update_status("Application Status", "TESTING")
    debug_gui.update_status("WidgetInc Status", "SIMULATED")
    debug_gui.update_status("Current Minigame", "Iron Mine")
    debug_gui.update_status("Last Detection", "12:34:56")

    # Update some stats
    debug_gui.update_stats("Detections Today", "42")
    debug_gui.update_stats("Automation Runs", "15")
    debug_gui.update_stats("Uptime", "02:15:30")
    debug_gui.update_stats("Errors", "0")

    print("Debug GUI is now running!")
    print("Test the following features:")
    print("1. Console tab - view different log levels")
    print("2. Settings tab - change debug settings")
    print("3. Monitoring tab - view status and statistics")
    print("4. Controls tab - test manual controls")
    print("5. Try Ctrl+R to test reload")
    print("6. Use the menu bar options")
    print("Close the window to exit.")

    # Run the GUI
    debug_gui.run()

    print("Debug GUI test completed!")


if __name__ == "__main__":
    test_debug_gui_standalone()
