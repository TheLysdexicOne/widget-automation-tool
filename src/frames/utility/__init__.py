"""
Frames Utility Package

Core utility classes and functions for frames management:
- DatabaseManagement: Core data operations and database management
- Helper functions for frame processing

Following project standards: KISS, no duplicated calculations, modular design.
"""

from .database_management import DatabaseManagement

__all__ = [
    "DatabaseManagement",
]
