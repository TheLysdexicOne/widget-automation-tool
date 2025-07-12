#!/usr/bin/env python3
"""
Test the new Debug GUI + Simplified Overlay architecture
"""

import sys
import os
import time
import threading

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from debug_gui import create_debug_gui
from simplified_overlay import create_simplified_overlay


def test_debug_gui_architecture():
    """Test the new architecture with debug GUI and simplified overlay"""
    print("=" * 60)
    print("Testing Debug GUI + Simplified Overlay Architecture")
    print("=" * 60)

    # Create debug GUI
    debug_gui = create_debug_gui()

    # Show debug GUI
    debug_gui.log("INFO", "Debug GUI started")
    debug_gui.log("INFO", "Testing new architecture...")

    # Simulate some activity
    def simulate_activity():
        """Simulate application activity"""
        time.sleep(2)
        debug_gui.log("INFO", "Simulating minigame detection...")
        debug_gui.update_status("Current Minigame", "Iron Mine")
        debug_gui.update_status("Last Detection", "12:34:56")
        debug_gui.update_stats("Detections Today", "5")

        time.sleep(3)
        debug_gui.log("SUCCESS", "Minigame automation started")
        debug_gui.update_status("Current Minigame", "Iron Mine (Running)")
        debug_gui.update_stats("Automation Runs", "1")

        time.sleep(5)
        debug_gui.log("INFO", "Automation completed")
        debug_gui.update_status("Current Minigame", "None")

        time.sleep(2)
        debug_gui.log("INFO", "Ready for next detection")
        debug_gui.log("INFO", "Test completed successfully!")

    # Start simulation in background
    sim_thread = threading.Thread(target=simulate_activity, daemon=True)
    sim_thread.start()

    print("\n🚀 Architecture Test Started!")
    print("\nFeatures to test:")
    print("1. Debug GUI with console logging")
    print("2. Settings management in Debug GUI")
    print("3. Real-time status updates")
    print("4. Statistics tracking")
    print("5. Ctrl+R reload functionality")
    print("\n📋 What you'll see:")
    print("- Debug GUI window with tabs for Console, Settings, Monitoring, Controls")
    print("- Simulated minigame detection and automation")
    print("- Real-time logging and statistics")
    print("\n🔧 Test the features:")
    print("- Switch between Debug GUI tabs")
    print("- Change settings in the Settings tab")
    print("- Watch the Console tab for real-time logs")
    print("- Check the Monitoring tab for status updates")
    print("- Use Controls tab for manual actions")
    print("- Try Ctrl+R to reload (in Debug GUI)")
    print("\nClose the Debug GUI window to exit the test.")
    print("=" * 60)

    # Run debug GUI (main thread)
    try:
        debug_gui.run()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")

    print("\n✅ Architecture test completed!")
    print("The new architecture separates concerns:")
    print("- Debug GUI: Full debugging interface")
    print("- Simplified Overlay: Clean status display")
    print("- Better organization and usability")


if __name__ == "__main__":
    test_debug_gui_architecture()
