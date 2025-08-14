# Frame Border Analysis Tool

## Overview

The Frame Border Analysis Tool is a standalone application for analyzing the left and right borders of frames to generate unique identification signatures. This tool is designed to help create data for frame detection algorithms by analyzing border patterns, colors, and characteristics.

## Key Features

- **Independent Operation**: Runs separately from the main application
- **Border Analysis**: Analyzes 5% inset borders with 20% center strips
- **Color Analysis**: Extracts average colors, dominant colors, and variance
- **Pattern Detection**: Identifies edge characteristics and patterns
- **Signature Generation**: Creates unique hashes for frame identification
- **Uniqueness Scoring**: Calculates similarity between frames
- **Export Options**: JSON and Pickle format exports

## Border Analysis Regions

```text
Frame Layout:
┌─────────────────────────┐
│ 5%  │    90%     │ 5% │  ← Analyzed borders
├─────┼─────────────┼─────┤
│  L  │             │  R  │  ← Left/Right borders
│  E  │   Content   │  I  │  ← 20% center strip of each border
│  F  │    Area     │  G  │
│  T  │             │  H  │
├─────┼─────────────┼─────┤
│ 5%  │    90%     │ 5% │
└─────────────────────────┘
```

## Usage

### Starting the Tool

1. **Using the launcher script** (recommended):

   ```bash
   analyze.bat
   ```

2. **Direct Python execution**:

   ```bash
   python src/analyze/frame_analyzer.py
   ```

### Prerequisites

- WidgetInc.exe must be running and visible
- Virtual environment activated (done automatically by launcher)
- Frame database must exist at `config/data/frames_database.json`

### Analysis Workflow

1. **Frame Selection**: Choose a frame from the dropdown
2. **Single Analysis**: Click "Analyze Selected Frame" for individual analysis
3. **Batch Analysis**: Click "Analyze All Frames" to process all frames
4. **View Results**: Analysis results appear in the results panel
5. **Calculate Uniqueness**: Use "Calculate Uniqueness Scores" to identify similar frames
6. **Export Data**: Export to JSON or Pickle format for use in detection algorithms

### Understanding Results

#### Border Analysis Output

- **Average Color**: RGB values for border region
- **Dominant Colors**: Most frequent colors in the border
- **Color Variance**: Measure of color diversity
- **Edge Characteristics**: Pattern analysis (density, directionality)
- **Signature**: Unique hash for frame identification

#### Uniqueness Scores

- **0.0 - 0.3**: Highly unique borders (excellent for detection)
- **0.3 - 0.7**: Moderately unique (good for detection)
- **0.7 - 1.0**: Similar to other frames (may need additional analysis)

## File Structure

```text
src/analyze/
├── frame_analyzer.py          # Main PyQt6 application
├── border_analysis_engine.py  # Core image processing
├── analysis_database.py       # Data storage management
└── __init__.py                # Module initialization

config/analysis/               # Generated analysis data
├── border_analysis.json       # JSON database
├── border_signatures.pkl      # Pickle export for detection
└── border_analysis_YYYYMMDD_HHMMSS.json  # Timestamped exports
```

## Technical Details

### Image Processing

- Uses numpy for efficient pixel operations
- Extracts 5% inset borders from left and right edges
- Analyzes 20% center strip to avoid corner artifacts
- Performs color and edge analysis

### Signature Generation

- Creates MD5 hashes from key characteristics
- Combines left/right border signatures with SHA256
- Enables fast frame comparison and identification

### Data Storage

- Primary storage in JSON format for human readability
- Pickle export for efficient runtime frame detection
- Automatic backup creation during saves

## Troubleshooting

### Common Issues

1. **"WidgetInc window not detected"**
   - Ensure WidgetInc.exe is running
   - Make sure the window is visible (not minimized)
   - Check that the window title contains "WidgetInc"

2. **"No frames loaded"**
   - Verify `config/data/frames_database.json` exists
   - Check JSON syntax is valid
   - Ensure frames array contains frame objects

3. **Analysis fails**
   - Check that frame area is properly detected
   - Verify screenshot capture is working
   - Review console output for detailed error messages

### Performance Notes

- Analysis takes 1-3 seconds per frame
- Batch analysis processes frames sequentially
- Large numbers of frames (100+) may take several minutes
- Results are auto-saved during batch processing

## Integration with Frame Detection

The analysis results can be used to enhance frame detection:

1. **Export to Pickle**: Use "Export to Pickle" to create detection database
2. **Load in Detection Code**: Import the pickle file in detection algorithms
3. **Signature Matching**: Compare captured signatures with database
4. **Threshold Tuning**: Adjust similarity thresholds based on uniqueness scores

## Development Notes

Following project coding standards:

- **KISS**: Simple, focused functionality
- **DRY**: Reuses existing cache manager and utilities
- **Independent**: No dependencies on main application
- **Error Handling**: Smart fail-fast with meaningful error messages

The tool leverages existing project infrastructure while maintaining complete independence for analysis workflows.
