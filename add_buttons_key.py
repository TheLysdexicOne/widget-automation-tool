import json
from pathlib import Path


def add_buttons_key_to_frames():
    """Add empty buttons key to frames that don't have one."""

    # Load the frames database
    frames_db_path = Path("config/database/frames_database.json")

    with open(frames_db_path, "r") as f:
        data = json.load(f)

    # Track changes
    frames_updated = 0

    # Process each frame
    for frame in data["frames"]:
        if "buttons" not in frame:
            frame["buttons"] = {"1": []}
            frames_updated += 1
            print(f"Added buttons key to frame {frame['id']} - {frame['name']}")

    # Save the updated data
    with open(frames_db_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nCompleted! Updated {frames_updated} frames.")


if __name__ == "__main__":
    add_buttons_key_to_frames()
