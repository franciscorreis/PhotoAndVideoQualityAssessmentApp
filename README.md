# Video Quality Assessment Application

A comprehensive desktop application for subjective and objective video quality assessment, designed to evaluate video quality through user ratings and automated analysis using objective metrics and AI-powered insights.

## Purpose

This application enables researchers and developers to:

- **Conduct subjective video quality tests**: Compare distorted videos against a reference video and collect user ratings
- **Calculate objective quality metrics**: Automatically compute PSNR (Peak Signal-to-Noise Ratio) and SSIM (Structural Similarity Index) metrics
- **Generate comprehensive reports**: Create detailed analysis reports with statistical correlations, regression models, and AI-powered insights
- **Export results**: Save results in CSV format and generate visualizations (graphs and PDF reports)

The application supports two main modes:
1. **Simple Subjective Assessment** (`app.py`): Quick video comparison using VLC player
2. **Comprehensive Quality Testing** (`video_quality_test.py`): Full-featured testing with objective metrics and AI analysis

## Features

- 🎥 **Side-by-side video comparison** with synchronized playback
- 📊 **Objective metrics calculation** (PSNR, SSIM)
- 📈 **Statistical analysis** with correlation coefficients and regression models
- 🤖 **AI-powered analysis** using Google Gemini AI
- 📄 **Report generation** in Markdown and PDF formats
- 📉 **Visualization** with graphs and charts
- 🔀 **Randomized video order** to prevent bias
- 💾 **CSV export** for further analysis

## Requirements

### System Requirements

- **macOS** (tested on macOS 10.14+)
- **Python 3.7+**
- **VLC Media Player** (for `app.py`)

### Python Dependencies

All dependencies are listed in `requirements.txt`:
- `opencv-python` - Video processing
- `Pillow` - Image handling
- `numpy` - Numerical computations
- `matplotlib` - Plotting and visualization
- `scipy` - Statistical analysis
- `scikit-image` - Image quality metrics
- `pandas` - Data manipulation
- `reportlab` - PDF generation
- `python-dotenv` - Environment variable management
- `google-generativeai` - Gemini AI integration
- `python-vlc` - VLC player integration (for `app.py`)

## Installation

### Step 1: Install VLC Media Player

**macOS:**
```bash
brew install --cask vlc
```

Or download from [VLC official website](https://www.videolan.org/vlc/).

### Step 2: Set Up Environment Variables

Create a `.env` file in the `macos` directory with your Gemini API key:

```bash
cd macos
touch .env
```

Add the following line to `.env`:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

**Getting a Gemini API Key:**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy the key and paste it in your `.env` file

**Note:** The Gemini API key is optional. The application will work without it, but AI-powered analysis features will be disabled.

### Step 3: Run Setup Script

Run the setup script to verify requirements and install dependencies:

```bash
python setup.py
```

This script will:
- ✓ Check if VLC is installed
- ✓ Install all Python dependencies from `requirements.txt`
- ✓ Verify the setup is complete

### Step 4: Verify Installation

After running `setup.py`, you should see:
```
✓ VLC encontrado no sistema
✓ Dependências instaladas com sucesso
✓ Setup completo! Pode executar: python video_quality_test.py
```

## Usage

### Running the Comprehensive Quality Test Application

To run the main application with full features:

```bash
python video_quality_test.py
```

**Main Menu:**
The application starts with a main menu offering two options:

1. **Criar Teste** (Create Test) - Conduct a new subjective video quality test
2. **Criar Resultado** (Create Result) - Calculate results and analysis from existing tests

### Workflow: Creating a Test

1. **Select "Criar Teste"** from the main menu
2. **Test Setup Screen**:
   - Enter a test name
   - Select one reference video
   - Select one or more distorted/test videos
   - Click "Iniciar Teste" (Start Test)
3. **Video Comparison**: For each test video:
   - Videos play side-by-side automatically
   - Rate the quality difference (0-10 scale)
   - Click "Next" to continue
4. **Save Results**: After completing all videos:
   - Results are saved automatically as CSV in `tests/nomedoteste/results_TIMESTAMP.csv`
   - Each test is saved in its own folder (no accumulation)
   - Returns to main menu

### Workflow: Creating Results

1. **Select "Criar Resultado"** from the main menu
2. **Result Setup Screen**:
   - Enter a result name
   - Add one or more CSV files from previous tests (from `tests/` folder)
   - Select the reference video
   - Select the distorted videos
   - Click "Gerar Análise" (Generate Analysis)
3. **Analysis Generation**:
   - Combines multiple test CSVs
   - Calculates MOS (Mean Opinion Score) as the average of all ratings for each video
   - Generates comprehensive analysis with:
     - Objective metrics (PSNR, SSIM)
     - Statistical correlations
     - Regression models
     - Visualizations (graphs)
     - AI-powered analysis (if Gemini key is configured)
   - Saves all results in `results/nomeresultado/`

### Running the Simple Subjective Assessment

For a simpler interface using VLC player:

```bash
python app.py
```

**Note:** This version uses VLC for playback and may have different features than `video_quality_test.py`.

## Project Structure

The application organizes files in two main directories:

### Tests Directory (`tests/`)

Each test is saved in its own folder:
```
tests/
└── nomedoteste/
    └── results_YYYYMMDD_HHMMSS.csv
```

- **Location**: `tests/nomedoteste/results_TIMESTAMP.csv`
- **Content**: Raw test data with individual ratings
- **Format**: CSV with columns: `nome_do_teste`, `reference_filename`, `distorted_filename`, `trial_index`, `rating_0_10`, `timestamp`
- **Note**: Each test is independent and saved in a separate folder

### Results Directory (`results/`)

Analysis results are saved in organized folders:
```
results/
└── nomeresultado/
    ├── dados_YYYYMMDD_HHMMSS.pdf          # Data report with statistics
    ├── analise_YYYYMMDD_HHMMSS.md          # AI-generated analysis (Markdown)
    ├── analise_YYYYMMDD_HHMMSS.pdf         # AI-generated analysis (PDF)
    ├── analysis_YYYYMMDD_HHMMSS_analysis.md # Detailed analysis report
    └── figures/                             # Visualization graphs
        ├── psnr_vs_mos.png                 # PSNR vs Mean Opinion Score
        ├── ssim_vs_mos.png                 # SSIM vs Mean Opinion Score
        └── mos_vs_psnr_comparison.png      # Comparison visualization
```

- **Location**: `results/nomeresultado/`
- **Content**: Combined analysis from multiple tests
- **MOS Calculation**: Mean Opinion Score is calculated as the average of all ratings from selected tests for each video

## Configuration

### Environment Variables

The application uses a `.env` file for configuration:

```env
GEMINI_API_KEY=your_api_key_here
```

### VLC Configuration (macOS)

If you encounter VLC-related issues on macOS, you may need to set environment variables:

```bash
export DYLD_LIBRARY_PATH=/Applications/VLC.app/Contents/MacOS/lib
export VLC_PLUGIN_PATH=/Applications/VLC.app/Contents/MacOS/plugins
```

## Troubleshooting

### VLC Not Found

**Error:** "VLC não encontrado" or "VLC Media Player não foi encontrado"

**Solution:**
1. Install VLC: `brew install --cask vlc`
2. Or download from [videolan.org](https://www.videolan.org/vlc/)
3. Ensure VLC is in `/Applications/VLC.app`

### Gemini API Key Issues

**Error:** "GEMINI_API_KEY não encontrada no .env"

**Solution:**
1. Create a `.env` file in the `macos` directory
2. Add: `GEMINI_API_KEY=your_key_here`
3. The application will work without it, but AI analysis will be skipped

### Import Errors

**Error:** ModuleNotFoundError

**Solution:**
```bash
pip install -r requirements.txt
```

Or run `python setup.py` again.

### Video Playback Issues

- Ensure video files are in supported formats (MP4, AVI, MKV, MOV, M4V, HEVC)
- Check that video codecs are supported by OpenCV/VLC
- Try converting videos to a standard format (H.264 MP4)

## File Structure

```
macos/
├── app.py                    # Simple subjective assessment app (VLC-based)
├── video_quality_test.py     # Comprehensive quality testing application
├── setup.py                  # Setup and dependency installation script
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
├── tests/                    # Directory for individual test results
│   └── nomedoteste/          # Each test in its own folder
│       └── results_*.csv     # Test CSV files
├── results/                   # Directory for analysis results
│   └── nomeresultado/        # Each result analysis in its own folder
│       ├── dados_*.pdf       # Data reports
│       ├── analise_*.pdf     # AI analysis reports
│       └── figures/          # Visualization graphs
└── README.md                 # This file
```

## Key Concepts

### Mean Opinion Score (MOS)

MOS is calculated as the average of all subjective ratings for each video across multiple tests:

- **Single Test**: Each test collects individual ratings (0-10 scale)
- **Multiple Tests**: When creating results, select multiple test CSVs
- **MOS Calculation**: For each video, MOS = average of all ratings from all selected tests
- **Example**: If 3 users rated a video as 7, 8, and 9, the MOS = (7+8+9)/3 = 8.0

This ensures that MOS represents the collective opinion of multiple evaluators, which is essential for reliable subjective quality assessment.

## License

This project is developed for academic research purposes at UBI (Universidade da Beira Interior).

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify all dependencies are installed
3. Ensure VLC is properly installed
4. Check that your `.env` file is configured correctly

## Contributing

This is an academic research project. For contributions or modifications, please contact the project maintainers.

