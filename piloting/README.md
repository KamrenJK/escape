# Data Analysis Environment Setup

This folder contains tools for offline data analysis of experimental sessions.

## Quick Start

### 1. Setup Python Environment

Run the automated setup script:
```bash
cd piloting
./setup_env.sh
```

Or manually install dependencies:

#### Option A: Using venv
```bash
# Create virtual environment
python3 -m venv piloting_env

# Activate environment
source piloting_env/bin/activate  # On macOS/Linux
# or
piloting_env\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

#### Option B: Using conda
```bash
# Create conda environment
conda create -n piloting_env python=3.10

# Activate environment
conda activate piloting_env

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch Jupyter Notebook

```bash
# Make sure environment is activated
jupyter notebook data_analysis.ipynb
```

### 3. Configure Data Path

In the notebook, update the `FOLDER_NAME` variable to point to your data folder:
```python
FOLDER_NAME = "your_session_folder_name"  # Replace with actual folder in /data
```

## Files

- `data_analysis.ipynb` - Main analysis notebook
- `requirements.txt` - Python package dependencies
- `setup_env.sh` - Automated environment setup script
- `README.md` - This file

## Features

### Data Loading
- Automatic detection of file types (JSON, CSV, NPY, NPZ)
- Structured data organization
- Comprehensive data information display

### Visualizations
- Trial timeline plots
- Performance metrics (success rate, reaction times)
- 2D trajectory visualization
- Time series plots
- Statistical summaries

### Analysis Tools
- Block-wise performance analysis
- Cumulative success tracking
- Distribution analysis
- Custom analysis section for specific needs

## Data Information Provided

When you load data, the notebook automatically reports:

1. **File Inventory**: List of all files found in the specified folder
2. **Data Structure**: 
   - DataFrames: columns, shape, data types, sample rows
   - Arrays: shape, dtype, basic statistics
   - Dictionaries: keys and nested structure
3. **Statistical Summaries**: Mean, std, min, max, percentiles
4. **Categorical Analysis**: Unique values and distributions

## Troubleshooting

If you encounter import errors:
```bash
# Verify environment is activated
which python  # Should show path to piloting_env

# Reinstall requirements
pip install --upgrade -r requirements.txt

# For Jupyter kernel issues
python -m ipykernel install --user --name=piloting_env
```

## Next Steps

1. Place your data in folders under `/data` directory
2. Run the notebook and specify your folder name
3. Review automatically generated plots
4. Use the custom analysis section for specific analyses
5. Export results using the provided export functions