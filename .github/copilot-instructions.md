---
## applyTo: "_.py_"
---

# General

- **Only the user is to alter this file**
- **AI is allowed to alter *ai-gen.md or *ai-generated.md**
- **Always use the venv or start.bat files for execution or installation**

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
