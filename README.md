# Widget Automation Tool

## Overview

A professional automation tool for Widget Inc. with dual-mode operation, system tray integration, and comprehensive debug capabilities. The tool automates minigame interactions while providing real-time monitoring and development tools.

## Features

- **Dual-Mode Operation**: Normal mode (system tray) or Debug mode (GUI visible)
- **System Tray Integration**: Background operation with quick access menu
- **Professional Debug Console**: 4-tab interface (Console, Settings, Monitoring, Debug)
- **Smart Overlay System**: Hover expansion, pin/unpin, context menu
- **Click Recording**: Development tools for automation scripting
- **Hot Reload**: Ctrl+R to reload application and configurations
- **Real-time Monitoring**: Live status updates and statistics
- **Threading Safety**: Robust error handling and thread management

## Project Structure

```
widget-automation-tool/
├── src/
│   ├── main.py                 # Core application controller
│   ├── overlay_gui.py          # Consolidated overlay system
│   ├── debug_gui.py            # Professional debug interface
│   ├── window_spy.py           # Click recording and cursor tracking
│   ├── widget_inc_manager.py   # Widget Inc. window management
│   ├── minigame_detector.py    # Game detection logic
│   ├── mouse_control.py        # Mouse automation functions
│   ├── screen_capture.py       # Screen capture utilities
│   ├── text_recognition.py     # OCR text extraction
│   ├── game_logic.py           # Game automation logic
│   └── gui/
│       ├── __init__.py
│       └── menu.py
├── config/
│   ├── settings.json           # Application configuration
│   └── minigames.json          # Minigame definitions
├── assets/
│   ├── sprites/                # Game sprites for detection
│   └── ui_elements/            # UI element templates
├── tests/
│   ├── run_tests.py            # Test runner
│   ├── test_overlay.py         # Overlay tests
│   ├── debug_detector.py       # Detector debugging
│   ├── debug_logic.py          # Logic debugging
│   └── debug_overlay_colors.py # Color debugging
├── .venv/                      # Python virtual environment
├── requirements.txt            # Project dependencies
├── setup.py                    # Package configuration
├── run_app.bat                 # Application launcher
├── DEVELOPMENT_LOG.md          # Development history
└── README.md                   # Project documentation
```

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/TheLysdexicOne/widget-automation-tool.git
   cd widget-automation-tool
   ```

2. Create and activate virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Quick Start

```bash
# Normal mode (system tray)
run_app.bat

# Debug mode (GUI visible)
run_app.bat --debug
```

### System Tray Mode

- Application runs in background with system tray icon
- Right-click tray icon for menu options
- Overlay appears on Widget Inc. window

### Debug Mode

- **Console Tab**: Real-time logging with adjustable log levels
- **Settings Tab**: Configuration controls and overlay settings
- **Monitoring Tab**: Live status updates and statistics
- **Debug Tab**: Development tools and click recording

### Development Features

- **Hot Reload**: Press Ctrl+R to reload application and configs
- **Click Recording**: Enable in Debug tab to record mouse actions
- **Window Spy**: Real-time cursor tracking and coordinate display
- **Action Management**: Copy, remove, or clear recorded actions

## Configuration

### Settings (`config/settings.json`)

```json
{
  "widget_inc_window_title": "WidgetInc",
  "check_interval": 1.0,
  "mouse_speed": 1.0,
  "screen_capture_region": [0, 0, 1920, 1080]
}
```

### Minigames (`config/minigames.json`)

```json
{
  "minigames": [
    {
      "name": "Example Game",
      "type": "static_ui",
      "detection_method": "text_recognition",
      "automation_sequence": [...]
    }
  ]
}
```

## Development

### Architecture

- **Main Application**: Handles startup, monitoring, and coordination
- **Overlay System**: Visual feedback and status display
- **Debug Interface**: Development tools and real-time monitoring
- **Window Spy**: Click recording and cursor tracking
- **Detection Engine**: Minigame identification and automation

### Key Components

- **Threading**: Background monitoring with GUI thread safety
- **Error Handling**: Comprehensive error handling and logging
- **Hot Reload**: Dynamic module reloading for development
- **System Integration**: Windows API integration for window management

## Dependencies

- **Core**: `tkinter`, `threading`, `json`, `argparse`
- **System Tray**: `pystray`, `Pillow`
- **Window Management**: `pygetwindow`, `pyautogui`
- **Windows API**: `pywin32`
- **OCR**: `pytesseract` (optional)

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## Support

For issues or questions, please open an issue on GitHub.
git clone https://github.com/yourusername/widget-automation-tool.git

````
2. Navigate to the project directory:
```bash
cd widget-automation-tool
````

3. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python src/main.py
   ```
2. Use the GUI to select a minigame and start the automation process.
3. Press the designated escape key to stop the automation.

## Testing

### Run All Tests

```bash
# Use the test runner (recommended)
python tests/run_tests.py
```

### Individual Tests

```bash
# Simple overlay test (no WidgetInc required)
python tests/simple_overlay_test.py

# Full overlay test (requires WidgetInc)
python tests/test_overlay.py
```

### Test Categories

- **GUI/Overlay Tests**: Test the on-screen overlay functionality
- **Unit Tests**: Test individual components in isolation

See `tests/README.md` for detailed testing documentation.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
