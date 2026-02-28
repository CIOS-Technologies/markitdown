#!/bin/bash
# Quick test script to verify MarkItDown setup for process_pdf.py

echo "🔍 Testing MarkItDown Setup..."
echo ""

# Check if venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated!"
    echo "   Run: source .venv/bin/activate"
    exit 1
else
    echo "✓ Virtual environment activated: $VIRTUAL_ENV"
fi

# Check if markitdown is importable
echo -n "Testing MarkItDown import... "
python -c "from markitdown import MarkItDown; print('✓ OK')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "✗ FAILED"
    echo "   Run: pip install -e 'packages/markitdown[all]'"
    exit 1
fi

# Check if PDF converter is available
echo -n "Testing PDF converter... "
python -c "from markitdown.converters._pdf_converter import PdfConverter; print('✓ OK')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "✗ FAILED"
    echo "   PDF dependencies may be missing. Run: pip install 'markitdown[pdf]'"
    exit 1
fi

# Check if process_pdf.py exists
if [ -f "process_pdf.py" ]; then
    echo "✓ process_pdf.py found"
else
    echo "✗ process_pdf.py not found in current directory"
    exit 1
fi

# Check if test PDF exists
if [ -f "packages/markitdown/tests/test_files/test.pdf" ]; then
    echo "✓ Test PDF found"
    TEST_PDF="packages/markitdown/tests/test_files/test.pdf"
elif [ -f "Manuale di neuropsicologia.pdf" ]; then
    echo "✓ Found PDF in root directory"
    TEST_PDF="Manuale di neuropsicologia.pdf"
else
    echo "⚠️  No test PDF found (optional)"
    TEST_PDF=""
fi

echo ""
echo "✅ Setup looks good!"
echo ""
echo "You can now run:"
echo "  python process_pdf.py <your_pdf_file>"
if [ -n "$TEST_PDF" ]; then
    echo ""
    echo "Or test with:"
    echo "  python process_pdf.py $TEST_PDF"
fi



