#!/usr/bin/env python3
"""
Test script for frames management system.
Verifies the frames system can initialize and handle basic operations.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_frames_system():
    print("🧪 Testing Frames Management System")
    print("=" * 50)

    try:
        from utility.frames_manager import FramesManager

        # Test frames manager initialization
        project_root = Path(__file__).parent
        frames_manager = FramesManager(project_root)
        print("✅ FramesManager initialized successfully")

        # Test database loading
        frames_list = frames_manager.get_frame_list()
        print(f"✅ Loaded {len(frames_list)} existing frames")

        # Test database structure
        print(f"✅ Database path: {frames_manager.frames_db_path}")
        print(f"✅ Screenshots dir: {frames_manager.screenshots_dir}")

        # Check if directories exist
        if frames_manager.frames_db_path.parent.exists():
            print("✅ Frames directory exists")
        if frames_manager.screenshots_dir.exists():
            print("✅ Screenshots directory exists")

        print("\n🎉 Frames system test completed successfully!")
        print("Ready to use FRAMES button in overlay application.")

    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_frames_system()
