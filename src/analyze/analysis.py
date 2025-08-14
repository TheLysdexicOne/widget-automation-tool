"""
One-off similarity analysis tool for border analysis results
Compares all analyzed frames to identify potential detection conflicts
"""

import json
import glob
from typing import Dict, Any, List, Optional
from pathlib import Path
import numpy as np
from datetime import datetime
import re
import sys


class SimilarityAnalyzer:
    """Analyzes similarity between analyzed frame borders"""

    def __init__(self, analysis_file: Optional[str] = None):
        project_root = Path(__file__).parent.parent.parent
        self.analysis_dir = project_root / "config" / "analysis"
        self.analysis_file = analysis_file
        self.analyses = {}
        self.similarity_results = {}

        # Check if system can handle Unicode emojis
        self.use_emojis = self._check_unicode_support()

    def _check_unicode_support(self) -> bool:
        """Check if system supports Unicode emojis for display"""
        try:
            test_emoji = "✅🚨⚠️"
            test_emoji.encode(sys.stdout.encoding or "utf-8")
            return True
        except (UnicodeEncodeError, LookupError):
            return False

    def _format_status(self, status_type: str) -> str:
        """Format status indicators with emoji fallback"""
        if self.use_emojis:
            status_map = {
                "success": "✅",
                "warning": "🚨",
                "caution": "⚠️",
                "search": "🔍",
                "folder": "📁",
                "error": "❌",
                "info": "💡",
                "report": "📄",
                "rocket": "🚀",
                "chart": "📊",
            }
        else:
            status_map = {
                "success": "[OK]",
                "warning": "[!!!]",
                "caution": "[!]",
                "search": "[?]",
                "folder": "[DIR]",
                "error": "[X]",
                "info": "[i]",
                "report": "[RPT]",
                "rocket": "[*]",
                "chart": "[DATA]",
            }

        return status_map.get(status_type, "")

    def find_analysis_files(self) -> List[Path]:
        """Find all border analysis files"""
        print(f"{self._format_status('search')} Looking for analysis files in: {self.analysis_dir}")
        print(f"{self._format_status('search')} Absolute path: {self.analysis_dir.absolute()}")

        if not self.analysis_dir.exists():
            print(f"{self._format_status('error')} Directory does not exist: {self.analysis_dir}")
            print(f"{self._format_status('folder')} Parent directory exists: {self.analysis_dir.parent.exists()}")
            print(f"{self._format_status('folder')} Config directory exists: {self.analysis_dir.parent.exists()}")
            print(f"{self._format_status('folder')} Project root exists: {self.analysis_dir.parent.parent.exists()}")
            return []

        pattern = str(self.analysis_dir / "border_analysis_*.json")
        files = glob.glob(pattern)

        print(f"{self._format_status('search')} Found {len(files)} analysis files")
        for file in files:
            print(f"  - {Path(file).name}")

        file_paths = [Path(f) for f in files]

        def extract_timestamp(filepath):
            match = re.search(r"border_analysis_(\d{8}_\d{6})\.json", filepath.name)
            return match.group(1) if match else "00000000_000000"

        file_paths.sort(key=extract_timestamp, reverse=True)
        return file_paths

    def select_analysis_file(self) -> Optional[Path]:
        """Select which analysis file to use"""
        if self.analysis_file:
            file_path = self.analysis_dir / self.analysis_file
            if file_path.exists():
                return file_path
            else:
                print(f"{self._format_status('error')} Specified file not found: {file_path}")
                return None

        available_files = self.find_analysis_files()

        if not available_files:
            print(f"{self._format_status('error')} No border analysis files found in: {self.analysis_dir}")
            print(
                f"{self._format_status('info')} Make sure you've run the frame analyzer first to generate analysis files"
            )
            return None

        if len(available_files) == 1:
            print(f"{self._format_status('success')} Found analysis file: {available_files[0].name}")
            return available_files[0]

        print(f"\n{self._format_status('folder')} Found {len(available_files)} analysis files:")
        for i, file_path in enumerate(available_files):
            print(f"  {i + 1}. {file_path.name}")

        print("\nUsing latest file (most recent timestamp)")
        print(f"{self._format_status('success')} Selected: {available_files[0].name}")
        return available_files[0]

    def load_analysis_data(self) -> bool:
        """Load existing border analysis data"""
        try:
            selected_file = self.select_analysis_file()
            if not selected_file:
                return False

            with open(selected_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "analyses" in data:
                self.analyses = data["analyses"]
                print(
                    f"{self._format_status('success')} Loaded {len(self.analyses)} frame analyses from {selected_file.name} (wrapped structure)"
                )
            else:
                self.analyses = {}
                for key, value in data.items():
                    if isinstance(value, dict) and "frame_id" in value:
                        self.analyses[key] = value

                print(
                    f"{self._format_status('success')} Loaded {len(self.analyses)} frame analyses from {selected_file.name} (direct structure)"
                )

            if self.analyses:
                frame_ids = list(self.analyses.keys())[:5]
                print(f"{self._format_status('search')} First few frame IDs: {frame_ids}")

                first_frame = list(self.analyses.values())[0]
                required_keys = ["frame_id", "frame_name", "combined_signature"]
                missing_keys = [key for key in required_keys if key not in first_frame]
                if missing_keys:
                    print(f"{self._format_status('caution')} Warning: Missing keys in frame data: {missing_keys}")
                else:
                    print(f"{self._format_status('success')} Frame data structure validation passed")

            return len(self.analyses) > 0

        except Exception as e:
            print(f"{self._format_status('error')} Error loading analysis data: {e}")
            import traceback

            traceback.print_exc()
            return False

    def calculate_color_similarity(self, color1: List[int], color2: List[int]) -> float:
        """Calculate color similarity using Euclidean distance"""
        if not color1 or not color2:
            return 0.0

        c1 = np.array(color1[:3])
        c2 = np.array(color2[:3])
        distance = np.linalg.norm(c1 - c2)
        max_distance = np.sqrt(3 * 255**2)
        similarity = 1.0 - (distance / max_distance)

        return similarity

    def calculate_signature_similarity(self, sig1: str, sig2: str) -> float:
        """Calculate signature similarity"""
        if sig1 == sig2:
            return 1.0
        return 0.0

    def calculate_edge_similarity(self, edge1: Dict, edge2: Dict) -> float:
        """Calculate edge characteristics similarity"""
        if not edge1 or not edge2:
            return 0.0

        metrics = [
            "edge_density",
            "edge_variance",
            "max_edge_strength",
            "horizontal_tendency",
            "vertical_tendency",
            "edge_ratio",
        ]

        similarities = []
        for metric in metrics:
            if metric in edge1 and metric in edge2:
                val1 = float(edge1[metric])
                val2 = float(edge2[metric])

                if val1 == 0 and val2 == 0:
                    similarities.append(1.0)
                elif val1 == 0 or val2 == 0:
                    similarities.append(0.0)
                else:
                    ratio = min(val1, val2) / max(val1, val2)
                    similarities.append(ratio)

        return float(np.mean(similarities)) if similarities else 0.0

    def calculate_frame_similarity(self, frame1_data: Dict, frame2_data: Dict) -> Dict[str, float]:
        """Calculate comprehensive similarity between two frames"""

        combined_sim = self.calculate_signature_similarity(
            frame1_data.get("combined_signature", ""), frame2_data.get("combined_signature", "")
        )

        left_sig_sim = self.calculate_signature_similarity(
            frame1_data.get("left_border", {}).get("signature", ""),
            frame2_data.get("left_border", {}).get("signature", ""),
        )

        right_sig_sim = self.calculate_signature_similarity(
            frame1_data.get("right_border", {}).get("signature", ""),
            frame2_data.get("right_border", {}).get("signature", ""),
        )

        left_color_sim = self.calculate_color_similarity(
            frame1_data.get("left_border", {}).get("average_color", []),
            frame2_data.get("left_border", {}).get("average_color", []),
        )

        right_color_sim = self.calculate_color_similarity(
            frame1_data.get("right_border", {}).get("average_color", []),
            frame2_data.get("right_border", {}).get("average_color", []),
        )

        left_edge_sim = self.calculate_edge_similarity(
            frame1_data.get("left_border", {}).get("edge_characteristics", {}),
            frame2_data.get("left_border", {}).get("edge_characteristics", {}),
        )

        right_edge_sim = self.calculate_edge_similarity(
            frame1_data.get("right_border", {}).get("edge_characteristics", {}),
            frame2_data.get("right_border", {}).get("edge_characteristics", {}),
        )

        signature_avg = (left_sig_sim + right_sig_sim) / 2
        color_avg = (left_color_sim + right_color_sim) / 2
        edge_avg = (left_edge_sim + right_edge_sim) / 2

        overall_similarity = combined_sim * 0.4 + signature_avg * 0.3 + color_avg * 0.2 + edge_avg * 0.1

        return {
            "overall": overall_similarity,
            "combined_signature": combined_sim,
            "left_signature": left_sig_sim,
            "right_signature": right_sig_sim,
            "left_color": left_color_sim,
            "right_color": right_color_sim,
            "left_edge": left_edge_sim,
            "right_edge": right_edge_sim,
            "average_signature": signature_avg,
            "average_color": color_avg,
            "average_edge": edge_avg,
        }

    def analyze_all_similarities(self) -> Dict[str, Any]:
        """Analyze similarities between all frame pairs"""

        frame_ids = list(self.analyses.keys())
        similarities = {}

        print(f"\n{self._format_status('search')} Analyzing similarities between {len(frame_ids)} frames...")

        for i, frame1_id in enumerate(frame_ids):
            for j, frame2_id in enumerate(frame_ids):
                if i >= j:
                    continue

                frame1_data = self.analyses[frame1_id]
                frame2_data = self.analyses[frame2_id]

                similarity = self.calculate_frame_similarity(frame1_data, frame2_data)

                pair_key = f"{frame1_id} vs {frame2_id}"
                similarities[pair_key] = {
                    "frame1_id": frame1_id,
                    "frame1_name": frame1_data.get("frame_name", frame1_id),
                    "frame2_id": frame2_id,
                    "frame2_name": frame2_data.get("frame_name", frame2_id),
                    "similarity_scores": similarity,
                }

        return similarities

    def generate_report(self, similarities: Dict[str, Any]) -> str:
        """Generate similarity analysis report"""

        report = []
        report.append("=" * 80)
        report.append("FRAME BORDER SIMILARITY ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Comparisons: {len(similarities)}")
        report.append("")

        sorted_pairs = sorted(similarities.items(), key=lambda x: x[1]["similarity_scores"]["overall"], reverse=True)

        high_similarity_pairs = [
            (pair, data) for pair, data in sorted_pairs if data["similarity_scores"]["overall"] > 0.7
        ]

        if high_similarity_pairs:
            report.append(f"{self._format_status('warning')} HIGH SIMILARITY WARNINGS (Potential Detection Conflicts)")
            report.append("-" * 60)
            for pair, data in high_similarity_pairs:
                scores = data["similarity_scores"]
                report.append(f"Frame: {data['frame1_name']} vs {data['frame2_name']}")
                report.append(f"  Overall Similarity: {scores['overall']:.3f}")
                report.append(f"  Combined Signature: {scores['combined_signature']:.3f}")
                report.append(f"  Signature Average: {scores['average_signature']:.3f}")
                report.append(f"  Color Average: {scores['average_color']:.3f}")
                report.append(f"  Edge Average: {scores['average_edge']:.3f}")
                report.append("")
        else:
            report.append(f"{self._format_status('success')} NO HIGH SIMILARITY CONFLICTS DETECTED")
            report.append("")

        exact_matches = [
            (pair, data) for pair, data in sorted_pairs if data["similarity_scores"]["combined_signature"] == 1.0
        ]

        if exact_matches:
            report.append(f"{self._format_status('caution')} EXACT SIGNATURE MATCHES (Identical Frames)")
            report.append("-" * 60)
            for pair, data in exact_matches:
                report.append(f"Frame: {data['frame1_name']} vs {data['frame2_name']}")
                report.append("  -> These frames have identical combined signatures!")
                report.append("")
        else:
            report.append(f"{self._format_status('success')} NO EXACT SIGNATURE MATCHES")
            report.append("")

        report.append(f"{self._format_status('chart')} FULL SIMILARITY COMPARISON TABLE")
        report.append("-" * 80)
        report.append(f"{'Frame 1':<20} {'Frame 2':<20} {'Overall':<8} {'Signature':<9} {'Color':<7} {'Edge':<6}")
        report.append("-" * 80)

        for pair, data in sorted_pairs:
            scores = data["similarity_scores"]
            frame1_name = data["frame1_name"][:18]
            frame2_name = data["frame2_name"][:18]

            report.append(
                f"{frame1_name:<20} {frame2_name:<20} "
                f"{scores['overall']:<8.3f} {scores['average_signature']:<9.3f} "
                f"{scores['average_color']:<7.3f} {scores['average_edge']:<6.3f}"
            )

        report.append("")
        report.append("=" * 80)
        report.append("RECOMMENDATIONS:")
        report.append("")

        if high_similarity_pairs:
            report.append(f"{self._format_status('caution')} ATTENTION REQUIRED:")
            report.append("- Frames with high similarity may cause detection conflicts")
            report.append("- Consider analyzing additional border regions or using different detection methods")
            report.append("- Test frame detection thoroughly with similar frames")

        if exact_matches:
            report.append(f"{self._format_status('warning')} CRITICAL ISSUE:")
            report.append("- Frames with identical signatures will cause detection failures")
            report.append("- These frames must be distinguished by different methods")
            report.append("- Consider using different border regions or additional detection criteria")

        if not high_similarity_pairs and not exact_matches:
            report.append(f"{self._format_status('success')} ANALYSIS LOOKS GOOD:")
            report.append("- All frames have sufficiently unique border signatures")
            report.append("- Frame detection should work reliably")
            report.append("- Proceed with implementing detection algorithms")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

    def save_report(self, report: str, filename: Optional[str] = None) -> None:
        """Save report to file with proper UTF-8 encoding"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"similarity_analysis_{timestamp}.txt"

        # Save to logs/reports directory according to user requirements
        project_root = Path(__file__).parent.parent.parent
        reports_dir = project_root / "logs" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        report_path = reports_dir / filename

        # Force UTF-8 encoding to handle Unicode characters
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"{self._format_status('report')} Report saved to: {report_path}")

    def run_analysis(self) -> bool:
        """Run complete similarity analysis"""

        print(f"{self._format_status('rocket')} Starting Frame Border Similarity Analysis...")

        if not self.load_analysis_data():
            return False

        if len(self.analyses) < 2:
            print(f"{self._format_status('error')} Need at least 2 analyzed frames for comparison")
            return False

        similarities = self.analyze_all_similarities()
        report = self.generate_report(similarities)

        print("\n" + report)
        self.save_report(report)

        return True


def main():
    """Main entry point for similarity analysis"""
    analyzer = SimilarityAnalyzer()

    try:
        success = analyzer.run_analysis()
        if success:
            print(f"\n{analyzer._format_status('success')} Similarity analysis completed successfully!")
        else:
            print(f"\n{analyzer._format_status('error')} Similarity analysis failed!")

    except KeyboardInterrupt:
        print(f"\n{analyzer._format_status('caution')} Analysis interrupted by user")
    except Exception as e:
        print(f"\n{analyzer._format_status('error')} Unexpected error: {e}")


if __name__ == "__main__":
    main()
