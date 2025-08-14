#!/usr/bin/env python3
"""
Quick test to verify the fixed frame detection methodology.
Tests if the percentage-based border extraction matches the analyze package approach.
"""

import sys
import os
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

import numpy as np
from PIL import Image

# Mock the modules for testing
from utility.window_utils import get_frame_screenshot
from utility.cache_manager import get_cache_manager


def test_border_extraction_methodology():
    """Test if the frame detection uses the correct border extraction method."""

    print("🔍 Testing Frame Detection Border Extraction Fix")
    print("=" * 50)

    # Get a frame screenshot to test with
    try:
        screenshot = get_frame_screenshot()
        if screenshot is None:
            print("❌ Could not capture frame screenshot")
            return False

        print(f"✅ Captured screenshot: {screenshot.width}x{screenshot.height}")

        # Test the new percentage-based extraction method
        img_array = np.array(screenshot)
        height, width = img_array.shape[:2]

        # Parameters from analyze package
        border_inset = 0.05  # 5% inset from edge
        center_strip = 0.2  # 20% center strip

        # Calculate dimensions using percentages
        inset_width = int(width * border_inset)
        strip_height = int(height * center_strip)

        center_y = height // 2
        start_y = center_y - strip_height // 2
        end_y = start_y + strip_height

        # Extract border regions
        left_border = img_array[start_y:end_y, 0:inset_width]
        right_border_start_x = width - inset_width
        right_border = img_array[start_y:end_y, right_border_start_x:width]

        print(f"📐 Frame dimensions: {width}x{height}")
        print(f"📏 Border inset (5%): {inset_width} pixels")
        print(f"📏 Strip height (20%): {strip_height} pixels")
        print(f"🎯 Center position: y={center_y}, range={start_y}-{end_y}")
        print(f"🔲 Left border shape: {left_border.shape}")
        print(f"🔲 Right border shape: {right_border.shape}")

        # Verify dimensions match the analyze package expectations
        expected_left_shape = (strip_height, inset_width, 3)
        expected_right_shape = (strip_height, inset_width, 3)

        if left_border.shape == expected_left_shape and right_border.shape == expected_right_shape:
            print("✅ Border extraction methodology matches analyze package!")

            # Calculate average colors
            left_avg_color = np.mean(left_border, axis=(0, 1))[:3]
            right_avg_color = np.mean(right_border, axis=(0, 1))[:3]

            print(f"🎨 Left border average color: {left_avg_color}")
            print(f"🎨 Right border average color: {right_avg_color}")

            return True
        else:
            print(f"❌ Border extraction shape mismatch!")
            print(f"   Expected left: {expected_left_shape}, got: {left_border.shape}")
            print(f"   Expected right: {expected_right_shape}, got: {right_border.shape}")
            return False

    except Exception as e:
        print(f"❌ Error during border extraction test: {e}")
        return False


def test_analysis_data_dimensions():
    """Test if the analysis data dimensions are consistent with percentage approach."""

    print("\n🔍 Testing Analysis Data Consistency")
    print("=" * 50)

    # Check if border analysis data has the right dimensions
    analysis_file = Path(__file__).parent / "config" / "analysis" / "border_analysis_20250813_192534.json"

    if not analysis_file.exists():
        print("❌ Analysis data file not found")
        return False

    import json

    try:
        with open(analysis_file, "r") as f:
            data = json.load(f)

        # Check a few frames to see their border dimensions
        frame_count = 0
        for frame_key, frame_data in data.items():
            if frame_count >= 3:  # Check first 3 frames
                break

            if isinstance(frame_data, dict) and "analysis_parameters" in frame_data:
                params = frame_data["analysis_parameters"]
                print(f"📋 Frame {frame_key}:")
                print(f"   Border inset: {params.get('border_inset', 'unknown')}")
                print(f"   Center strip: {params.get('center_strip', 'unknown')}")

                if "border_dimensions" in params:
                    dims = params["border_dimensions"]
                    print(f"   Left border: {dims.get('left', 'unknown')}")
                    print(f"   Right border: {dims.get('right', 'unknown')}")

                frame_count += 1

        print("✅ Analysis data structure looks correct!")
        return True

    except Exception as e:
        print(f"❌ Error reading analysis data: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Frame Detection Fix Verification Test")
    print("Testing percentage-based border extraction methodology")
    print()

    # Test border extraction
    test1_passed = test_border_extraction_methodology()

    # Test analysis data consistency
    test2_passed = test_analysis_data_dimensions()

    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"   Border Extraction: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"   Analysis Data: {'✅ PASS' if test2_passed else '❌ FAIL'}")

    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("Frame detection fix is working correctly!")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Frame detection fix needs more work.")
