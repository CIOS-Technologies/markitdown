#!/usr/bin/env python3
"""
Standalone script to process PDF files with MarkItDown and save to Markdown.

Usage:
    python process_pdf.py input.pdf [--output output.md] [--workers 20] [--gemini-key KEY]
    python process_pdf.py input.pdf --page-chunks --margins 0   # better multi-column layout
    python process_pdf.py input.pdf --no-header-footer           # strip headers/footers (needs pdf-layout)

Features:
    - Parallel image processing (up to 20 workers by default)
    - Progress logging
    - Automatic output file naming
    - Gemini API integration for image descriptions

For local development:
    1. Activate virtual environment: source .venv/bin/activate
    2. Install in editable mode: pip install -e 'packages/markitdown[all]'
    3. Run: python process_pdf.py input.pdf
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add local package path for development (if running from markitdown root)
_script_dir = Path(__file__).parent.absolute()
_local_package_path = _script_dir / "packages" / "markitdown" / "src"
if _local_package_path.exists() and str(_local_package_path) not in sys.path:
    sys.path.insert(0, str(_local_package_path))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

try:
    from markitdown import MarkItDown
except ImportError:
    logger.error(
        "MarkItDown not found. Please install it:\n"
        "  For production: pip install 'markitdown[all]'\n"
        "  For development: pip install -e 'packages/markitdown[all]'\n"
        "  (Make sure virtual environment is activated: source .venv/bin/activate)"
    )
    sys.exit(1)


def process_pdf(
    pdf_path: str,
    output_path: Optional[str] = None,
    max_workers: int = 20,
    gemini_api_key: Optional[str] = None,
    image_dir: Optional[str] = None,
    page_chunks: bool = False,
    margins: Optional[float] = None,
    no_header_footer: bool = False,
) -> bool:
    """
    Process a PDF file and save the result to Markdown.

    Args:
        pdf_path: Path to the PDF file
        output_path: Output Markdown file path (auto-generated if None)
        max_workers: Maximum number of parallel workers for image processing
        gemini_api_key: Gemini API key (or use GEMINI_API_KEY env var)
        image_dir: If set, extracted PDF images are saved here (for inspection); otherwise a temp dir is used and deleted.
        page_chunks: If True, pass page_chunks=True to the PDF converter for per-page chunks (can improve multi-column order).
        margins: If set, pass margins=N to the PDF converter (e.g. 0 for tighter layout on multi-column PDFs).
        no_header_footer: If True, pass header=False, footer=False to strip page headers/footers (requires PyMuPDF Layout).
    """
    # Validate input file
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        logger.error(f"PDF file not found: {pdf_path}")
        return False
    
    if not pdf_file.is_file():
        logger.error(f"Path is not a file: {pdf_path}")
        return False
    
    logger.info(f"Processing PDF: {pdf_path}")
    logger.info(f"File size: {pdf_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Determine output path
    if output_path is None:
        output_path = pdf_file.with_suffix('.md')
    else:
        output_path = Path(output_path)
    
    logger.info(f"Output will be saved to: {output_path}")
    
    # Get Gemini API key
    if gemini_api_key is None:
        gemini_api_key = os.environ.get('GEMINI_API_KEY')
    
    # Initialize MarkItDown
    if gemini_api_key:
        logger.info("Initializing MarkItDown with Gemini API for image descriptions...")
        md = MarkItDown(
            gemini_api_key=gemini_api_key,
            llm_model="gemini-2.5-flash"
        )
        logger.info(f"Parallel image processing enabled: {max_workers} workers")
    else:
        logger.warning(
            "No Gemini API key found. Image descriptions will be disabled.\n"
            "Set GEMINI_API_KEY environment variable or use --gemini-key option."
        )
        md = MarkItDown()
        max_workers = 1  # No parallel processing without LLM
    
    try:
        # Build PDF converter options (passed through to pymupdf4llm / PyMuPDF Layout).
        convert_kwargs: dict = {"max_image_workers": max_workers}
        if image_dir:
            convert_kwargs["image_path"] = image_dir
        if page_chunks:
            convert_kwargs["page_chunks"] = True
        if margins is not None:
            convert_kwargs["margins"] = margins
        if no_header_footer:
            convert_kwargs["header"] = False
            convert_kwargs["footer"] = False

        # Convert PDF
        logger.info("Starting PDF conversion...")
        result = md.convert(str(pdf_file), **convert_kwargs)
        
        # Save result
        logger.info(f"Saving result to {output_path}...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result.text_content)
        
        # Log statistics
        content_length = len(result.text_content)
        word_count = len(result.text_content.split())
        
        logger.info("=" * 60)
        logger.info("Conversion completed successfully!")
        logger.info(f"Output file: {output_path}")
        logger.info(f"Content length: {content_length:,} characters")
        logger.info(f"Word count: {word_count:,} words")
        
        if result.title:
            logger.info(f"Document title: {result.title}")
        
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing PDF: {e}", exc_info=True)
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Process PDF files with MarkItDown and save to Markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (auto-generates output.md)
  python process_pdf.py document.pdf
  
  # Specify output file
  python process_pdf.py document.pdf --output result.md
  
  # Custom worker count
  python process_pdf.py document.pdf --workers 10
  
  # With Gemini API key
  python process_pdf.py document.pdf --gemini-key YOUR_API_KEY
  
  # Using environment variable for API key
  export GEMINI_API_KEY=your_key
  python process_pdf.py document.pdf

  # Better layout for multi-column PDFs
  python process_pdf.py document.pdf --page-chunks --margins 0
  python process_pdf.py document.pdf --no-header-footer
        """
    )
    
    parser.add_argument(
        'pdf_file',
        help='Path to the PDF file to process'
    )
    
    parser.add_argument(
        '-o', '--output',
        dest='output',
        help='Output Markdown file path (default: same as input with .md extension)'
    )
    
    parser.add_argument(
        '-w', '--workers',
        dest='workers',
        type=int,
        default=20,
        help='Maximum number of parallel workers for image processing (default: 20)'
    )
    
    parser.add_argument(
        '--gemini-key',
        dest='gemini_key',
        help='Gemini API key (or set GEMINI_API_KEY environment variable)'
    )

    parser.add_argument(
        '--image-dir',
        dest='image_dir',
        help='Directory to save extracted PDF images (for inspection). If not set, images are stored in a temp dir and deleted after conversion.'
    )

    parser.add_argument(
        '--page-chunks',
        dest='page_chunks',
        action='store_true',
        help='Use per-page chunks for conversion (can improve reading order on multi-column PDFs).'
    )
    parser.add_argument(
        '--margins',
        dest='margins',
        type=float,
        default=None,
        metavar='N',
        help='Set margins for layout (e.g. 0 for tighter multi-column reading). Only passed if set.'
    )
    parser.add_argument(
        '--no-header-footer',
        dest='no_header_footer',
        action='store_true',
        help='Strip page headers and footers (requires PyMuPDF Layout: pip install markitdown[pdf-layout]).'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging (DEBUG level)'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    # Process PDF
    success = process_pdf(
        pdf_path=args.pdf_file,
        output_path=args.output,
        max_workers=args.workers,
        gemini_api_key=args.gemini_key,
        image_dir=args.image_dir,
        page_chunks=args.page_chunks,
        margins=args.margins,
        no_header_footer=args.no_header_footer,
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()



