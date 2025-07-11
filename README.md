# Widget Automation Tool

## Overview

The Widget Automation Tool is designed to automate mouse movements and clicks for various minigames, reducing the physical strain on users. The tool captures the screen to identify the current minigame and performs the necessary actions to complete it automatically.

## Features

- Screen capture to analyze specific regions for text recognition.
- Simulated mouse movements and clicks to interact with the game.
- Optical character recognition (OCR) to read text from the screen.
- A user-friendly GUI for selecting and managing minigames.
- Configurable settings for screen dimensions and mouse speed.

## Project Structure

```
widget-automation-tool
├── src
│   ├── main.py            # Entry point of the application
│   ├── screen_capture.py   # Functions for capturing the screen
│   ├── mouse_control.py    # Functions to simulate mouse actions
│   ├── text_recognition.py  # OCR functions for text extraction
│   ├── game_logic.py       # Logic for determining active minigame
│   └── gui
│       ├── __init__.py     # Initializes the GUI package
│       └── menu.py         # GUI for minigame selection
├── config
│   ├── settings.json       # Configuration settings for the application
│   └── minigames.json      # List of available minigames and actions
├── requirements.txt        # Project dependencies
├── setup.py                # Packaging information
└── README.md               # Project documentation
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/widget-automation-tool.git
   ```
2. Navigate to the project directory:
   ```bash
   cd widget-automation-tool
   ```
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

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
