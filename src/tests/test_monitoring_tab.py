#!/usr/bin/env python3
"""
Test script to verify the monitoring tab functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from console.tabs.monitoring_tab import MonitoringTab
import time

class MockApp:
    """Mock application for testing."""
    def __init__(self):
        self.target_hwnd = 460996  # Current WidgetInc window
        
def test_playable_area_detection():
    """Test playable area detection functionality."""
    print("Testing playable area detection...")
    
    # Create a mock app
    app = MockApp()
    
    # Create the monitoring tab
    tab = MonitoringTab(app)
    
    # Test playable area detection
    try:
        playable_rect = tab.get_playable_area()
        if playable_rect:
            print(f"✓ Playable area detected: {playable_rect}")
            print(f"  Size: {playable_rect['width']}x{playable_rect['height']}")
            print(f"  Position: ({playable_rect['x']}, {playable_rect['y']})")
            print(f"  Aspect ratio: {playable_rect['width']/playable_rect['height']:.3f}")
            
            # Test 192x128 background coordinates
            if hasattr(tab, 'get_background_coordinates'):
                bg_coords = tab.get_background_coordinates()
                if bg_coords:
                    print(f"✓ Background coordinates: {bg_coords}")
                    print(f"  Grid size: {bg_coords['grid_width']}x{bg_coords['grid_height']}")
                    print(f"  Pixel size: {bg_coords['pixel_width']}x{bg_coords['pixel_height']}")
                else:
                    print("✗ Background coordinates not available")
            else:
                print("✗ get_background_coordinates method not found")
        else:
            print("✗ Playable area not detected")
    except Exception as e:
        print(f"✗ Error testing playable area: {e}")

if __name__ == "__main__":
    test_playable_area_detection()
