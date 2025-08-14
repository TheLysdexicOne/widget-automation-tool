"""
Analyze Module - Frame Border Analysis Tools

This module provides standalone tools for analyzing frame borders to generate
unique identification signatures for frame detection.

Components:
- frame_analyzer.py: Main PyQt6 application for border analysis
- border_analysis_engine.py: Core image processing engine
- analysis_database.py: Data storage and management
- analysis.py: Similarity analysis tool

File Organization:
- Analysis data → config/analysis/
- Reports → logs/reports/
- Active detection files → config/data/

Usage:
    python src/analyze/frame_analyzer.py
    python src/analyze/analysis.py

Following project standards: KISS, DRY, standalone operation.
"""

from .border_analysis_engine import BorderAnalysisEngine
from .analysis_database import AnalysisDatabase
from .analysis import SimilarityAnalyzer

__all__ = ["BorderAnalysisEngine", "AnalysisDatabase", "SimilarityAnalyzer"]
