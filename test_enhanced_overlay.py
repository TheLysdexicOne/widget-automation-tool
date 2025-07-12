#!/usr/bin/env python3
"""
Test script for the enhanced overlay with click recording
"""

import time
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from enhanced_overlay import EnhancedOverlay


def test_overlay():
    """Test the enhanced overlay functionality"""
    print("Testing Enhanced Overlay with Click Recording...")

    # Create overlay instance
    overlay = EnhancedOverlay()

    print("Overlay created successfully!")
    print("Features:")
    print("- Click recording functionality")
    print("- Improved cursor tracking")
    print("- Better UI layout with larger dimensions")
    print("- Copy to clipboard for recorded clicks")
    print("- Enhanced debug mode with better spacing")
    print()
    print("To test:")
    print("1. Hover over the overlay to expand it")
    print("2. Enable 'Debug Mode' checkbox")
    print("3. Enable 'Enable cursor tracking' checkbox")
    print("4. The overlay should now show cursor position in real-time")
    print("5. Click around to record clicks")
    print("6. Use '[Copy to Clipboard]' button to copy recorded clicks")
    print()
    print("Press Ctrl+C to stop the overlay")

    try:
        overlay.root.mainloop()
    except KeyboardInterrupt:
        print("\nOverlay stopped by user")

    print("Test completed!")


if __name__ == "__main__":
    test_overlay()
