---
## applyTo: "_.py_"
---

# Widget Automation Tool: Copilot Instructions (AI-Optimized)

## General Coding Standards

- **Aesthetics:** Favor an "industrialesque" look in UI and code structure.
- **Principles:**
  - KISS (Keep It Simple, Stupid)
  - DRY (Don't Repeat Yourself)
  - Explicit is better than implicit
  - Clean, maintainable, and efficient code
  - Make it Work → Make it Right → Make it Fast
- **No Reinventing the Wheel:**
  - Use existing modules/utilities when possible
  - Never duplicate calculation or utility functions
  - Suggest or use external libraries if they fit the need

## File & Module Roles

- **database_management.py:** All database logic (class: `DatabaseManagement`)
- **screenshot_management.py:** All screenshot logic (class: `ScreenshotManagement`)
- **update_manager.py:** Global update notification system (singleton: `UpdateManager`)
- **update_poller.py:** Polling utility for update signals (`UpdatePoller`)
- **status_manager.py:** Application state logic (`StatusManager`, `ApplicationState`)
- **/tests:** All tests live here. One-time tests should be deleted after use.
- **Never reference or use files in any `/old/` folder.**

## Execution & Environment

- Always use `.venv` for Python modules and installation
- Use `start.bat` or `start_debug.bat` to launch the app (never run main.py directly)
- Use Powershell 7 commands in the terminal
- Standalone apps (ending in `_app`) must not depend on other apps, but can use shared helpers

## Error Handling & Logging

- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- Clean up debug code after use
- Log to `logs/` directory

## UI/UX

- QSS stylesheets are loaded at app startup and apply globally
- The app may be positioned with negative coordinates (multi-monitor setups)
- Remove temporary debug UI when done

## Status Indicator (ApplicationState)

- ACTIVE: "performing automation"
- READY: "tool recognizes current screen/minigame, waiting for user"
- ATTENTION: "screen recognized, but no automation programmed"
- INACTIVE: "screen not recognized, no automation available"
- ERROR: "application or target window error"

## Tests

- All tests in `/tests` folder
- Do not move/delete files prefixed with `lyx__.`
- Remove one-time or obsolete tests promptly

## Miscellaneous

- Place all AI-generated summaries in `/documents/summaries`
- If a new file replaces an old one, move the old file to `/old` (never reference `/old` in production)
- Never use `_old` or `_new` in production filenames

## AI Prompting Efficiency

- Be explicit about file roles and boundaries
- Use and reference the correct utility (update_manager, update_poller, status_manager) for their intended purpose
- When in doubt, prefer clarity and maintainability over cleverness
- Always check for and use existing helpers/utilities before writing new code
- Keep code and prompts focused, direct, and DRY
