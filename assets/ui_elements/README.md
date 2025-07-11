# UI Element Templates

Place your UI element template images in this directory for static UI-based minigames.

## File Naming Convention

Use descriptive names for UI elements:

- `start_button.png`
- `play_button.png`
- `pause_button.png`
- `settings_icon.png`
- `close_button.png`
- `target_area.png`

## Image Requirements

- **Format**: PNG recommended (supports transparency)
- **Size**: Keep templates reasonably small but clear
- **Quality**: High-contrast images work best for detection
- **Background**: Crop closely around the UI element

## Example Structure

```
ui_elements/
├── start_button.png
├── play_button.png
├── pause_button.png
├── settings_icon.png
├── close_button.png
└── target_area.png
```

## Usage

These templates will be used by the UIDetector class to find and click UI elements automatically within the WidgetInc application window.
