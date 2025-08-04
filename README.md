# Widget Automation Tool - WIP

A personal project for fun. The main goal is to learn python at a deeper level.

## Disclaimer

A significant portion of this codebase was generated using various LLMs. Mostly for concepts outside of my knowledge or to speed up tedious coding. Very few steps were taken to fully optimize the code unless there was a glaring efficiency issue.

## Introduction

A Python automation tool designed to assist with frame minigames in Widget Inc. This tool provides automated solutions for repetitive tasks within the game's various frame interfaces.

## Overview

Widget Automation Tool creates an overlay interface that detects the Widget Inc game window and provides automation capabilities for different frame minigames. The tool uses computer vision and coordinate-based automation to interact with game elements.

## Features

- Frame-specific automation modules for different minigames
- Real-time coordinate tracking and debugging tools (standalone tracker.exe)
- Multi-monitor support with proper coordinate handling
- Emergency stop functionality for safe operation

## Important Notice

**This tool is intended for personal assistance and practice only.** If Widget Inc introduces competitive leaderboards or ranking systems in the future, please refrain from using automation tools during official competitive play to maintain fair gameplay for all participants.

**This tool is only tested on 1440p monitors.** While steps have been taken to accomodate all window sizes, there is no guarantee they will work on differently scaled monitors. As long as the game is running wider than 3:2, most automation features should work as intended.

## Requirements

- Still work in progress, but at the moment, Python 3.8+

## Installation

1. Clone the repository
2. Run `.\venv.bat` to activate the virtual environment
3. Launch with `python src\main.py` or use `.\start.bat`
