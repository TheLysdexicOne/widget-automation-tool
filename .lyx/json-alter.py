import json
from pathlib import Path


def main():
    db_path = Path(r"c:\Projects\widget-automation-tool\src\config\frames_database.json")
    altered_path = db_path.parent / "frames_database_altered.json"

    with db_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    for frame in data.get("frames", []):
        frame["regions"] = {"text": frame.get("text", []), "interact": []}
        frame.pop("text", None)

    with altered_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    main()
