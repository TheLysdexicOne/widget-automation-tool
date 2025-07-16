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
