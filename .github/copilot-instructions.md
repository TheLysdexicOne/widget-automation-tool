---
## applyTo: "_.py_"
---

# Project general coding standards

## Aesthetics

- Industrialesque

## Main Principles

- "KISS" = "Keep It Simple, Stupid!"
- "DRY" = Don't Repeat Yourself!
- Explicit is better than implicit
- Keep the code clean, maintainable, and efficient

## Main Principles 2

- Make it Work
- Make it Right
- Make it Fast

## Don't Reinvent The Wheel

- Don't duplicate calculation functions
- Every time a calculation is duplicated, the risk of error increases
- If a calculation is duplicated, then it creates more places to edit said calculation
- If there is a module that does what we want, suggest it or use it

## Execution

- always use "start.bat" or "start_debug.bat" for starting the application
- Use the venv for any module installation
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

## File Roles

- Keep all database manipulation functions in database_management.py | class DatabaseManagement
- Keep all screenshot manipulation functions in screenshot_management.py | Class ScreenshotManagement

## STATUS INDICATOR

- ACTIVE = "performing automation"
- READY = "The tool recognizes the current screen/minigame and is waitin for user to activate."
- ATTENTION (name can be something more relevant) = "The tool recognizes the current screen/minigame, but there is no automation programmed."
- INACTIVE = "The tool does not recognize the current screen/minigame, therefore there is no automation available on this screen."
- ERROR = "Something wrong with application or target window cannot be found"
