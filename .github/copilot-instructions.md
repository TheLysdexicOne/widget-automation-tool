---
## applyTo: "_.py_"
---

# General

- Only the user is to alter this file
- AI is allowed to alter \*ai-gen.md or \*ai-generated.md
- Only perform tasks explicitly as told unless permission is granted for creativity
- Always activate the virtual environment before running any commands
  - Do not use ".\venv.bat"
- Put all imports at the top of each file
- Avoid "code vomit" (cluttering code with excessive try: except or "log every action")
- Don't need to take into account every aspect of failure, let the application fail, we can debug when it does
- I'm an amateur coder and these are amateur projects
- This is an unserious project, a project for fun
- Use ImageGrab.grab(bbox=..., all_screens=True) for screenshots

# Widget Automation Tool: AI-Generated Development Instructions

## Project Overview

A comprehensive automation overlay for WidgetInc minigames with manual frame selection and automated execution.

## Architecture Goals

### Phase 1: Manual Selection + Automation (Current Focus)

- **Comprehensive Automation Overlay**: Manual frame selection via dropdown/buttons
- **Individual Frame Automators**: Plugin-like automation modules for each minigame
- **Industrial Aesthetic**: Clean, functional, minimal UI design
- **Immediate Value**: No complex detection - user selects, automation executes

## Core Principles

- **KISS over Complexity**: Manual selection beats unreliable detection
- **User Control**: Player knows the context, automation executes perfectly
- **Modular Design**: Each frame automation is independent and testable
- **Industrial Design**: Functional, minimal, efficient interfaces

## Code Structure Standards

- **Separation of Concerns**: Overlay UI ↔ Automation Engine ↔ Frame Automators
- **Plugin Architecture**: Easy to add new frame automations
- **Shared Utilities**: Database, logging, window utils remain common
- **DRY Principle**: Extract common automation patterns to engine

## Development Workflow

- **Make it Work**: Get basic automation working for one frame type
- **Make it Right**: Extract common patterns, clean up code structure
- **Make it Fast**: Optimize automation speed and reliability
- **Industrial Aesthetic**: Clean, functional, minimal design throughout

## Testing Strategy

- **pytest-qt**: For overlay UI interactions and automation controls
- **Unit Tests**: For individual frame automation logic
- **Integration Tests**: For full automation workflows
- **Coverage Goals**: Focus on automation reliability over perfect coverage

## Key Design Decisions

- **Aesthetics**: Base PyQt6 as much as possible - no special css unless explicitly requested by user or absolutley necessary
- **Manual Frame Selection**: User chooses frame type via dropdown/buttons
- **No Complex Detection**: Eliminates unreliable automated frame recognition
- **Real-time Feedback**: Progress bars, status indicators, visual confirmation
- **Modular Automations**: Each frame type has dedicated automation module
- **Clean Exit Strategy**: Proper cleanup, stop buttons, emergency stops

## File Organization

```
src/
├── applications/
│   └── automation_overlay.py    # Main automation hub application
├── automation/
│   ├── frame_automators/        # Individual frame automation modules
│   ├── automation_engine.py     # Common automation utilities
│   └── automation_controller.py # Orchestrates automation execution
├── gui/
│   └── overlay_controls.py      # Automation overlay UI components
├── utility/                     # Shared utilities (database, logging, etc.)
└── config/                      # Configuration and frame definitions
```

# Code Style & Error Handling

## Clarity Over Cleverness

- **Clear, concise, and to the point**: Prefer simple, readable code over clever one-liners
- **Obvious naming**: Variables and functions should be self-documenting
- **Minimal abstraction**: Don't abstract until you need to repeat code 3+ times
- **Direct approach**: If something needs to happen, make it happen directly

## Error Handling Philosophy

- **Fail fast on data corruption**: If core data is invalid (wrong array length, missing required fields), crash immediately with `sys.exit()`
- **Valid errors worth catching**: File not found, network issues, user input validation
- **Invalid errors to ignore**: Don't catch errors that indicate broken logic or corrupted data
- **No defensive programming**: Don't code around problems that shouldn't exist

## Examples of Good vs Bad Error Handling

### Good (Fail Fast):

```python
if len(button_data) != 3:
    logger.error(f"Invalid button data for {button_name}: {button_data}")
    sys.exit("Exiting due to invalid database")
```

### Bad (Defensive):

```python
try:
    if len(button_data) == 3:
        grid_x, grid_y, color = button_data
    else:
        logger.warning("Invalid button data, using defaults")
        grid_x, grid_y, color = 0, 0, "red"  # WHY?!
except Exception as e:
    logger.error(f"Button processing failed: {e}")
    continue  # Skip broken data and pretend it's fine
```

## Function Design

- **Single responsibility**: One function, one job
- **Minimal parameters**: If a function needs lots of data, it should get it itself
- **No parameter passing for the sake of it**: `grid_to_screen_coordinates(x, y)` not `grid_to_screen_coordinates(x, y, playable_area, window_info, config)`
- **Internal dependencies**: Let functions handle their own requirements

## Keep It Simple

- **Don't anticipate problems**: Write code for the happy path, fix issues when they actually happen
- **Crash is better than corrupt**: Better to crash and debug than silently produce wrong results
- **User will report actual issues**: Don't code around theoretical edge cases
