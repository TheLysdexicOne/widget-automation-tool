#!/usr/bin/env python3
"""
Demo script showing the enhanced overlay click recording functionality
"""

import time
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from enhanced_overlay import EnhancedOverlay


def demo_click_recording():
    """Demo the click recording functionality"""
    print("=== Enhanced Overlay Click Recording Demo ===")
    print()

    # Create overlay instance
    overlay = EnhancedOverlay()

    # Enable debug mode and cursor tracking by default
    overlay.debug_mode = True
    overlay.enable_cursor_tracking = True
    overlay.enable_click_recording = True

    print("Demo Features Enabled:")
    print("✓ Debug Mode")
    print("✓ Cursor Tracking")
    print("✓ Click Recording")
    print()
    print("What you can do:")
    print("1. The overlay will appear on screen")
    print("2. Hover over it to expand and see all settings")
    print("3. Real-time cursor position tracking")
    print("4. Click anywhere to record clicks")
    print("5. View recent clicks in the overlay")
    print("6. Click '[Copy to Clipboard]' to copy recorded clicks as Python code")
    print()
    print("Overlay Features:")
    print("- Larger overlay size (400x300+)")
    print("- Better spacing and layout")
    print("- Debug menu no longer cut off")
    print("- Enhanced cursor tracking with coordinate display")
    print("- Click recording with button type detection")
    print("- Clipboard integration for automation scripts")
    print()
    print("Press Ctrl+C to stop the demo")
    print()

    try:
        overlay.root.mainloop()
    except KeyboardInterrupt:
        print("\nDemo stopped by user")

        # Show recorded clicks if any
        if overlay.recorded_clicks:
            print(f"\nRecorded {len(overlay.recorded_clicks)} clicks:")
            for i, click in enumerate(overlay.recorded_clicks):
                print(
                    f"  {i+1}. Position: ({click['x']}, {click['y']}) - Button: {click['button']}"
                )
        else:
            print("\nNo clicks were recorded")

    print("Demo completed!")


if __name__ == "__main__":
    demo_click_recording()
