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

## Cleanup

- Always clean up linter warnings

## Execution

- Always use the virtual environment
- Always launch via start\*.bat files
- gui = GUI = MainWindow or main_window.py and associated classes

## Testing

- pytest-qt for gui testing
