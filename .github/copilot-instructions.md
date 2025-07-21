---
## applyTo: "_.py_"
---

# Project general coding standards

## Aesthetics

- Industrialesque

## Main Principals

- "KISS" = "Keep It Simple, Stupid!"
- "DRY" = Don't Repeat Yourself!
- Explicit is better than implicit
- Keep the code clean, maintainable, and efficient

## Extra Principals

- Make it Work
- Make it Right
- Make it Fast

## Don't Reinvent The Wheel

- Don't duplicate calculation functions
- Every time a calculation is duplicated, the risk of error increases
- If a calculation is duplicated, then it creates more places to edit said calculation
- If there is a module that does what we want, suggest it or use it

## Execution

- Anything \_app should be considered a standalone application and should never rely on another application
- Standalone applications can still use helper functions to reduce risk of error
- Always use the .venv
- Always use Powershell 7 commands in the terminal
- Unless testing for compiling errors, use the "start.bat" or "start_debug.bat" files for executing the application

## Error Handling

- Remember there are log levels in the console portion of this application

## Tests

- All tests should be in tests/
- One-time tests should be deleted after use
- Do not move or delete any files with the prefix lyx\__._

## Old Files

- If a new file is created, move the old file into ./old so that it can be deleted
- Don't ever reference a file in a {folder}/old/ folder
- Don't ever use \_old or \_new in a production file

## MISC

- The application can and will often be left of the center monitor causing negative coordinates - This is valid!
- Clean up debug. If it's only needed for testing one part, remove the debugging when done.
- Place all AI generated "summaries" in /documents/summaries

## Playable Area

### Overview

The playable area is the actual game content area within the WidgetInc.exe window, distinct from the full client window size. This area contains the actual minigames and has specific pixel art scaling properties.

### Key Characteristics

- **Fixed Aspect Ratio**: Always maintains a 3:2 (width:height) ratio regardless of window size
- **Black Border Color**: Areas outside playable bounds are colored `#0c0a10` (RGB: 12, 10, 16)
- **Centered Positioning**: Playable area is always centered within the client window
- **Pixel Art Base**: Background is conceptually 180x120 pixels that scales to fit the playable area

### Border Behavior

- **Landscape Windows** (wider than 3:2): Black bars appear on left and right sides
- **Portrait Windows** (taller than 3:2): Black bars appear on top and bottom
- **Perfect Fit** (exactly 3:2): No black bars needed

### Pixel Art Scaling

- **Background Pixels**: The 192x128 background grid scales to fill the playable area
  - Example: 2160x1440 playable area = 12px per background pixel (2160/180 = 12)
- **Sprite Pixels**: Game sprites render at ~2x higher density than background
  - Example: If background pixel = 12px, sprite pixel ≈ 5-7px depending on antialiasing
- **Perfect Squares**: When calculated correctly, background pixels should be square (same width/height)

### Detection Methods

1. **Pixel Sampling**: Use `pyautogui.pixel(x, y)` to detect black border color `#0c0a10`
2. **Ratio-Based Fallback**: Calculate 3:2 area mathematically when pixel detection fails
3. **Dual Approach**: Always try pixel detection first, fall back to ratio calculation

### Implementation Notes

- Use client window coordinates as the base for all calculations
- Account for window decorations (title bar, borders) when getting client area
- Playable area coordinates are relative to the client window, not screen coordinates
- Mouse percentage calculations should be relative to playable area, not full window

## STATUS INDICATOR

- ACTIVE = performing automation
- READY = "The tool recognizes the current screen/minigame and is waitin for user to activate."
- ATTENTION (name can be something more relevant) = "The tool recognizes the current screen/minigame, but there is no automation programmed."
- INACTIVE = "The tool does not recognize the current screen/minigame, therefore there is no automation available on this screen."
- ERROR = Something wrong with application
