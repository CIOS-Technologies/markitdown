# Testing process_pdf.py Script Locally

## Quick Setup (One-time)

### 1. Activate Virtual Environment

```bash
cd /home/denter/user/work/markitdown
source .venv/bin/activate
```

### 2. Install MarkItDown in Editable Mode (if not already done)

```bash
pip install -e 'packages/markitdown[all]'
```

This installs the package in "editable" mode, so any changes you make to the source code will be immediately available.

### 3. Verify Installation

```bash
python -c "from markitdown import MarkItDown; print('✓ MarkItDown imported successfully')"
```

## Running the Script

### Basic Usage

```bash
# Make sure venv is activated
source .venv/bin/activate

# Run the script
python process_pdf.py test.pdf

# Or with a test PDF from the test files
python process_pdf.py packages/markitdown/tests/test_files/test.pdf
```

### With Options

```bash
# Specify output file
python process_pdf.py test.pdf --output result.md

# Custom worker count
python process_pdf.py test.pdf --workers 10

# With Gemini API key
python process_pdf.py test.pdf --gemini-key YOUR_API_KEY

# Or use environment variable
export GEMINI_API_KEY=your_key
python process_pdf.py test.pdf

# Verbose logging
python process_pdf.py test.pdf --verbose
```

## Testing with a Real PDF

If you have a PDF file in the markitdown directory (like `Manuale di neuropsicologia.pdf`):

```bash
source .venv/bin/activate
python process_pdf.py "Manuale di neuropsicologia.pdf"
```

This will create `Manuale di neuropsicologia.md` with all images processed in parallel.

## What to Expect

The script will show progress logs like:

```
2024-01-15 10:30:45 - INFO - Processing PDF: test.pdf
2024-01-15 10:30:45 - INFO - File size: 2.45 MB
2024-01-15 10:30:45 - INFO - Output will be saved to: test.md
2024-01-15 10:30:45 - INFO - Initializing MarkItDown with Gemini API for image descriptions...
2024-01-15 10:30:45 - INFO - Parallel image processing enabled: 20 workers
2024-01-15 10:30:45 - INFO - Starting PDF conversion...
2024-01-15 10:30:46 - INFO - Found 15 images in PDF. Starting image description generation...
2024-01-15 10:30:46 - INFO - Processing image 1/15: image-001.png
...
2024-01-15 10:30:58 - INFO - Completed image processing: 15/15 images described successfully
2024-01-15 10:30:58 - INFO - Conversion completed successfully!
```

## Troubleshooting

### "MarkItDown not found"

**Solution**: Make sure you've activated the virtual environment and installed the package:

```bash
source .venv/bin/activate
pip install -e 'packages/markitdown[all]'
```

### "No module named 'pymupdf4llm'"

**Solution**: Install PDF dependencies:

```bash
pip install 'markitdown[pdf]'
# Or install all dependencies
pip install 'markitdown[all]'
```

### Script works but no image descriptions

**Solution**: Make sure you have a Gemini API key:

```bash
export GEMINI_API_KEY=your_key
python process_pdf.py test.pdf
```

Or pass it as an argument:

```bash
python process_pdf.py test.pdf --gemini-key your_key
```

## Development Workflow

1. **Make changes** to `packages/markitdown/src/markitdown/converters/_pdf_converter.py`
2. **Test immediately** (no reinstall needed with editable install):
   ```bash
   source .venv/bin/activate
   python process_pdf.py test.pdf
   ```
3. **Changes are live** - the editable install means your code changes are immediately available

## Next Steps

Once you've tested locally and everything works:

1. Commit the changes to the repository
2. Update the ai_personality project to use the updated markitdown
3. Test in the ai_personality environment
