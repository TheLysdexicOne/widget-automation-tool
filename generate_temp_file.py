#!/usr/bin/env python3
"""
Quick script to generate frames_temp.json without window dependency.
"""

import json
import os
import sys

# Add src to path
sys.path.append("src")


def mock_grid_to_screen_coordinates(grid_x, grid_y, playable_area=None):
    """Mock coordinate conversion for testing."""
    if not playable_area:
        playable_area = {"x": 100, "y": 100, "width": 960, "height": 640}

    # Calculate pixel size
    pixel_size_x = playable_area["width"] / 192  # PIXEL_ART_GRID_WIDTH
    pixel_size_y = playable_area["height"] / 128  # PIXEL_ART_GRID_HEIGHT
    pixel_size = min(pixel_size_x, pixel_size_y)

    # Calculate screen coordinates
    screen_x = int(playable_area["x"] + (grid_x + 0.5) * pixel_size)
    screen_y = int(playable_area["y"] + (grid_y + 0.5) * pixel_size)

    return (screen_x, screen_y)


def convert_buttons_mock(buttons_data):
    """Convert button grid coordinates to screen coordinates."""
    converted = {}
    playable_area = {"x": 100, "y": 100, "width": 960, "height": 640}

    for button_name, button_data in buttons_data.items():
        if len(button_data) != 3:
            print(f"Invalid button data for {button_name}: {button_data}")
            continue

        grid_x, grid_y, color = button_data
        screen_coords = mock_grid_to_screen_coordinates(grid_x, grid_y, playable_area)

        converted[button_name] = {"grid": (grid_x, grid_y), "screen": screen_coords, "color": color}
        print(f"Button {button_name}: Grid ({grid_x}, {grid_y}) -> Screen {screen_coords}")

    return converted


def main():
    print("Generating frames_temp.json...")

    # Load frames database
    with open("src/config/frames_database.json", "r") as f:
        data = json.load(f)
        frames_data = data["frames"]

    print(f"Loaded {len(frames_data)} frames")

    frames_with_coords = []

    for frame in frames_data:
        frame_copy = frame.copy()

        if "buttons" in frame and frame["buttons"]:
            frame_name = frame.get("name", "unknown")
            button_count = len(frame["buttons"])
            print(f"Processing frame: {frame_name} with {button_count} buttons")

            converted_buttons = convert_buttons_mock(frame["buttons"])
            frame_copy["buttons_converted"] = converted_buttons

        frames_with_coords.append(frame_copy)

    # Create output directory
    os.makedirs("data", exist_ok=True)

    # Create the temporary data structure
    temp_data = {
        "frames": frames_with_coords,
        "generated_at": "mock_generation",
        "playable_area": {"x": 100, "y": 100, "width": 960, "height": 640},
    }

    # Write to file
    with open("data/frames_temp.json", "w", encoding="utf-8") as f:
        json.dump(temp_data, f, indent=2)

    print("✅ frames_temp.json generated successfully!")
    file_size = os.path.getsize("data/frames_temp.json")
    print(f"File size: {file_size} bytes")

    # Show sample data
    print("\nSample generated data:")
    for frame in temp_data["frames"]:
        if "buttons_converted" in frame and frame["buttons_converted"]:
            frame_name = frame.get("name", "unknown")
            print(f"  Frame: {frame_name}")
            for btn_name, btn_data in list(frame["buttons_converted"].items())[:2]:
                print(f"    {btn_name}: {btn_data}")
            break


if __name__ == "__main__":
    main()
