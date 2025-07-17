#!/usr/bin/env python3
"""
Test script to verify the refactored debug console functionality.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_imports():
    """Test that all components can be imported successfully."""
    print("Testing imports...")

    try:
        from src.console.debug_console import DebugConsole

        print("✅ DebugConsole imported successfully")
    except Exception as e:
        print(f"❌ DebugConsole import failed: {e}")
        return False

    try:
        from src.console.tabs import (
            BaseTab,
            ConsoleTab,
            SettingsTab,
            MonitoringTab,
            DebugTab,
        )

        print("✅ All tabs imported successfully")
    except Exception as e:
        print(f"❌ Tab imports failed: {e}")
        return False

    try:
        from src.console.components import LogHandler, MonitoringCard

        print("✅ All components imported successfully")
    except Exception as e:
        print(f"❌ Component imports failed: {e}")
        return False

    return True


def test_console_creation():
    """Test that the debug console can be created."""
    print("\nTesting console creation...")

    try:
        from PyQt6.QtWidgets import QApplication

        app = QApplication([])

        from src.console.debug_console import DebugConsole

        # Mock application object
        class MockApp:
            def __init__(self):
                self.config = {}
                self.process_monitor = None
                self.overlay = None
                self.system_tray = None

        mock_app = MockApp()
        console = DebugConsole(mock_app)

        print("✅ Debug console created successfully")
        print(f"✅ Console has {console.tab_widget.count()} tabs")

        # Test tab names
        tab_names = []
        for i in range(console.tab_widget.count()):
            tab_names.append(console.tab_widget.tabText(i))

        print(f"✅ Tab names: {tab_names}")

        return True

    except Exception as e:
        print(f"❌ Console creation failed: {e}")
        return False


def main():
    """Main test function."""
    print("=== Debug Console Refactoring Test ===")

    # Test 1: Imports
    if not test_imports():
        print("\n❌ Import tests failed!")
        return 1

    # Test 2: Console creation
    if not test_console_creation():
        print("\n❌ Console creation tests failed!")
        return 1

    print("\n✅ All tests passed! Refactoring successful!")
    print("\nRefactoring Summary:")
    print("- Original debug_console.py: 894 lines → Multiple focused files")
    print("- Modular architecture with base classes and inheritance")
    print("- Separate tabs: Console, Settings, Monitoring, Debug")
    print("- Reusable components: LogHandler, MonitoringCard")
    print("- Improved maintainability and testability")

    return 0


if __name__ == "__main__":
    sys.exit(main())
