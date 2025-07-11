#!/usr/bin/env python3
"""
Test runner for widget automation tool
"""

import sys
import os
import unittest
import signal

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\nReceived interrupt signal. Exiting gracefully...")
    sys.exit(0)


# Set up signal handler
signal.signal(signal.SIGINT, signal_handler)


def check_environment():
    """Check if we're running in the correct environment"""
    try:
        import psutil
        import pyautogui
        import cv2

        return True
    except ImportError as e:
        print(f"Missing required packages: {e}")
        print("\nPlease run the tests using the virtual environment:")
        print(
            "C:/Projects/Misc/widget-automation-tool/.venv/Scripts/python.exe tests/run_tests.py"
        )
        print("\nOr activate the virtual environment first:")
        print(".venv\\Scripts\\activate")
        print("python tests/run_tests.py")
        return False


def run_overlay_tests():
    """Run overlay GUI tests"""
    if not check_environment():
        return

    while True:
        try:
            print("\nRunning Overlay GUI Tests")
            print("=" * 50)

            # Import test modules
            from test_overlay import test_overlay
            from simple_overlay_test import SimpleOverlayTest

            print("Available tests:")
            print("1. Full Overlay Test (requires WidgetInc)")
            print("2. Simple Overlay Test (standalone)")
            print("3. Run all tests")
            print("0. Exit")

            choice = input("\nEnter your choice (0-3): ").strip()

            if choice == "0":
                break
            elif choice == "1":
                print("\nRunning Full Overlay Test...")
                print(
                    "Instructions: Hover over the red circle, click to pin/unpin, watch status changes."
                )
                print("Press Ctrl+C to return to menu or close window to exit test.")
                try:
                    test_overlay()
                except KeyboardInterrupt:
                    print("\nTest interrupted - returning to menu")
                    continue
            elif choice == "2":
                print("\nRunning Simple Overlay Test...")
                print(
                    "Instructions: Hover over the red circle, click to pin/unpin, watch status changes."
                )
                print("Press Ctrl+C to return to menu or close window to exit test.")
                try:
                    overlay = SimpleOverlayTest()
                    overlay.run()
                except KeyboardInterrupt:
                    print("\nTest interrupted - returning to menu")
                    continue
            elif choice == "3":
                print("\nRunning all tests...")
                print("Press Ctrl+C to return to menu.")
                try:
                    print("Starting Simple Overlay Test...")
                    overlay = SimpleOverlayTest()
                    overlay.run()

                    print("Starting Full Overlay Test...")
                    test_overlay()
                except KeyboardInterrupt:
                    print("\nTest interrupted - returning to menu")
                    continue
            else:
                print("Invalid choice. Please enter 0-3.")

        except KeyboardInterrupt:
            print("\nReturning to main menu")
            break
        except Exception as e:
            print(f"Error running test: {e}")
            input("Press Enter to continue...")
            continue


def run_unit_tests():
    """Run unit tests"""
    if not check_environment():
        return

    print("Running Unit Tests")
    print("=" * 50)

    # Discover and run unit tests
    loader = unittest.TestLoader()
    suite = loader.discover("tests", pattern="test_*.py")

    if suite.countTestCases() == 0:
        print("No unit tests found.")
        return

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        print("\nAll tests passed!")
    else:
        print(
            f"\nTests failed: {len(result.failures)} failures, {len(result.errors)} errors"
        )


def main():
    """Main test runner"""
    while True:
        try:
            print("\nWidget Automation Tool - Test Runner")
            print("=" * 50)

            print("Test categories:")
            print("1. GUI/Overlay Tests")
            print("2. Unit Tests")
            print("3. All Tests")
            print("0. Exit")

            choice = input("\nEnter your choice (0-3): ").strip()

            if choice == "0":
                break
            elif choice == "1":
                run_overlay_tests()
            elif choice == "2":
                run_unit_tests()
            elif choice == "3":
                print("\nRunning all tests...")
                try:
                    run_unit_tests()
                    input("\nPress Enter to continue with GUI tests...")
                    run_overlay_tests()
                except KeyboardInterrupt:
                    print("\nTest sequence interrupted - returning to main menu")
                    continue
            else:
                print("Invalid choice. Please enter 0-3.")

        except KeyboardInterrupt:
            print("\nExiting test runner")
            break
        except Exception as e:
            print(f"Error in test runner: {e}")
            input("Press Enter to continue...")
            continue

    print("Goodbye!")


if __name__ == "__main__":
    main()
