---
## applyTo: "_.py_"
---

# Project general coding standards

## "KISS" Principals

- "KISS" stands for "Keep It Simple, Stupid"
- Keep the code clean and simple as much as possible
- Use modules when it's easier to do so, don't try to reinvent the wheel
- Do not overcomplicate code. If it seems complicated, it's probably complicated.

## Separation of duties

- While the application is initiated with main.py,
- The brains are in src/core
- The brains user display is src/console
- The user experience is src/overlay

## Execution

- Always use the .venv
- Always use Powershell 7 commands in the terminal
- Unless testing for compiling errors, use the "start.bat" or "start_debug.bat" files for executing the application

## Error Handling

- Remember there are log levels in the console portion of this application

## Tests

- All tests should be in src/tests

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
