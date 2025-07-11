#!/usr/bin/env python3
"""
Debug the string comparison logic
"""


def debug_status_logic():
    """Debug the status color logic"""
    status_text = "INACTIVE"

    print(f"Testing status: '{status_text}'")
    print(f"status_text.upper() = '{status_text.upper()}'")
    print(f"'ACTIVE' in status_text.upper() = {'ACTIVE' in status_text.upper()}")
    print(f"'INACTIVE' in status_text.upper() = {'INACTIVE' in status_text.upper()}")

    # Test the exact logic from the overlay
    if "ACTIVE" in status_text.upper():
        color = "#44FF44"  # Green for active
        reason = "ACTIVE condition matched"
    elif "INACTIVE" in status_text.upper():
        color = "#FF4444"  # Red for inactive
        reason = "INACTIVE condition matched"
    elif "ERROR" in status_text.upper():
        color = "#FFAA00"  # Orange for error
        reason = "ERROR condition matched"
    elif "WAITING" in status_text.upper():
        color = "#4444FF"  # Blue for waiting
        reason = "WAITING condition matched"
    elif "STARTING" in status_text.upper():
        color = "#FF44FF"  # Purple for starting
        reason = "STARTING condition matched"
    else:
        color = "#CCCCCC"  # Gray for unknown states
        reason = "Unknown state"

    print(f"Result: {color} ({reason})")


if __name__ == "__main__":
    debug_status_logic()
