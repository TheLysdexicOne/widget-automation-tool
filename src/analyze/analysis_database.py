"""
Database management for border analysis results
Handles JSON storage and pickle conversion for frame detection
"""

import json
import pickle
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime


class AnalysisDatabase:
    """Manages storage and retrieval of border analysis results"""

    def __init__(self):
        # Set up directories according to user requirements
        project_root = Path(__file__).parent.parent.parent
        self.analysis_dir = project_root / "config" / "analysis"
        self.data_dir = project_root / "config" / "data"
        self.reports_dir = project_root / "logs" / "reports"

        # Create directories
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamped filename for analysis storage
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.json_file = self.analysis_dir / f"border_analysis_{timestamp}.json"

        self.data = {"metadata": {"created": datetime.now().isoformat(), "version": "1.0"}, "analyses": {}}

    def save_analysis(self, analysis_result: Dict[str, Any]) -> None:
        """Save analysis result for a frame"""
        frame_id = analysis_result.get("frame_id", "unknown")
        self.data["analyses"][frame_id] = analysis_result
        self._save_json()

        # Also save current active files to config/data
        self._save_active_detection_files()

    def get_analysis(self, frame_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis result for a frame"""
        return self.data["analyses"].get(frame_id)

    def get_all_analyses(self) -> Dict[str, Any]:
        """Get all analysis results"""
        return self.data["analyses"]

    def _save_json(self) -> None:
        """Save data to JSON file"""
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def _save_active_detection_files(self) -> None:
        """Save current active detection files to config/data"""
        if not self.data["analyses"]:
            return

        # Save JSON version for human readability
        active_json_file = self.data_dir / "frame_detection.json"
        with open(active_json_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

        # Save pickle version for detection system
        active_pickle_file = self.data_dir / "frame_detection.pkl"
        detection_data = {}
        for frame_id, analysis in self.data["analyses"].items():
            detection_data[frame_id] = {
                "frame_name": analysis.get("frame_name", frame_id),
                "combined_signature": analysis.get("combined_signature"),
                "left_signature": analysis.get("left_border", {}).get("signature"),
                "right_signature": analysis.get("right_border", {}).get("signature"),
                "uniqueness_score": analysis.get("uniqueness_score", 0.0),
            }

        with open(active_pickle_file, "wb") as f:
            pickle.dump(detection_data, f)

    def _calculate_signature_similarity(self, sig1: str, sig2: str) -> float:
        """Calculate similarity between two signatures"""
        if sig1 == sig2:
            return 0.0  # Identical signatures = 0 uniqueness
        return 1.0  # Different signatures = high uniqueness

    def calculate_uniqueness_scores(self) -> Dict[str, float]:
        """Calculate uniqueness scores for all analyzed frames"""
        analyses = self.data["analyses"]
        frame_ids = list(analyses.keys())
        uniqueness_scores = {}

        for frame_id in frame_ids:
            frame_analysis = analyses[frame_id]
            frame_signature = frame_analysis.get("combined_signature", "")

            # Compare with all other frames
            similarities = []
            for other_frame_id in frame_ids:
                if frame_id == other_frame_id:
                    continue

                other_analysis = analyses[other_frame_id]
                other_signature = other_analysis.get("combined_signature", "")

                similarity = self._calculate_signature_similarity(frame_signature, other_signature)
                similarities.append(similarity)

            # Average uniqueness (higher = more unique)
            avg_uniqueness = sum(similarities) / len(similarities) if similarities else 1.0
            uniqueness_scores[frame_id] = avg_uniqueness

            # Update the frame analysis with uniqueness score
            analyses[frame_id]["uniqueness_score"] = avg_uniqueness

        # Save updated data
        self._save_json()

        return uniqueness_scores

    def get_uniqueness_report(self) -> str:
        """Generate a report of frame uniqueness"""
        if not self.data["analyses"]:
            return "No analysis data available"

        uniqueness_scores = self.calculate_uniqueness_scores()

        # Sort by uniqueness score (most unique first)
        sorted_scores = sorted(uniqueness_scores.items(), key=lambda x: x[1], reverse=True)

        report = []
        report.append("Frame Uniqueness Report")
        report.append("=" * 50)

        for frame_id, score in sorted_scores:
            frame_data = self.data["analyses"][frame_id]
            frame_name = frame_data.get("frame_name", frame_id)

            # Determine status based on score
            if score > 0.7:
                status = "HIGHLY UNIQUE"
            elif score > 0.3:
                status = "MODERATELY UNIQUE"
            else:
                status = "SIMILAR TO OTHERS"

            report.append(f"{frame_name:<20} | Score: {score:.3f} | {status}")

        return "\n".join(report)

    def export_to_pickle(self, filename: Optional[str] = None) -> Path:
        """Export analysis data to pickle format for frame detection"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"frame_detection_export_{timestamp}.pkl"

        pickle_file = self.reports_dir / filename

        # Create optimized data structure for frame detection
        detection_data = {}
        for frame_id, analysis in self.data["analyses"].items():
            detection_data[frame_id] = {
                "frame_name": analysis.get("frame_name", frame_id),
                "combined_signature": analysis.get("combined_signature"),
                "left_signature": analysis.get("left_border", {}).get("signature"),
                "right_signature": analysis.get("right_border", {}).get("signature"),
                "uniqueness_score": analysis.get("uniqueness_score", 0.0),
            }

        with open(pickle_file, "wb") as f:
            pickle.dump(detection_data, f)

        return pickle_file

    def export_report(self, report_content: str, filename: Optional[str] = None) -> Path:
        """Export report to logs/reports directory"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_report_{timestamp}.txt"

        report_file = self.reports_dir / filename

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)

        return report_file
