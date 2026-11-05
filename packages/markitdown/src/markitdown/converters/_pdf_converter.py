import sys
import io
import tempfile
import os
import logging
from pathlib import Path

from typing import BinaryIO, Any, Dict


from .._base_converter import DocumentConverter, DocumentConverterResult
from .._stream_info import StreamInfo
from .._exceptions import MissingDependencyException, MISSING_DEPENDENCY_MESSAGE
from ._image_descriptions import (
    describe_images_in_markdown,
    extract_image_context,
    replace_images_with_descriptions,
)

# Set up logging for PDF conversion
logger = logging.getLogger(__name__)


# Try loading optional (but in this case, required) dependencies
# Save reporting of any exceptions for later
_dependency_exc_info = None
try:
    import pymupdf4llm
    import tempfile
    from pathlib import Path
except ImportError:
    # Preserve the error and stack trace for later
    _dependency_exc_info = sys.exc_info()

# Optional: enable PyMuPDF Layout for better multi-column and layout detection.
# When pymupdf.layout is imported before pymupdf4llm, to_markdown() uses the
# Layout code path, which improves reading order on multi-column pages.
# See: https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/
_layout_imported = False
if _dependency_exc_info is None:
    try:
        import pymupdf.layout  # noqa: F401
        _layout_imported = True
        logging.getLogger(__name__).debug(
            "pymupdf.layout imported for improved PDF multi-column/layout handling"
        )
    except ImportError:
        pass


ACCEPTED_MIME_TYPE_PREFIXES = [
    "application/pdf",
    "application/x-pdf",
]

ACCEPTED_FILE_EXTENSIONS = [".pdf"]

# pymupdf4llm.to_markdown() parameters that can be passed through from convert(**kwargs).
# Used to tune layout/reading order (e.g. margins, page_chunks) for multi-column PDFs.
# See https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/api.html
PYMUPDF4LLM_KWARGS = {
    "margins", "page_chunks", "page_separators", "table_strategy",
    "detect_bg_color", "page_width", "page_height", "header", "footer",
    "fontsize_limit", "force_text", "write_images", "image_path", "image_format",
    "dpi", "pages", "show_progress",
}
# Our own kwargs - never forward these to pymupdf4llm
PDF_CONVERTER_KWARGS = {"llm_client", "llm_model", "max_image_workers", "llm_prompt", "llm_use_advanced_prompt"}


def _pdf_to_text_fitz_fallback(pdf_path: str) -> str:
    """
    Last-resort PDF text extraction using PyMuPDF (fitz) when pymupdf4llm fails.
    Returns plain text from all pages (no images, no layout). Used when
    pymupdf4llm raises min() iterable argument is empty even with no kwargs.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ValueError("PyMuPDF (fitz) is required for PDF fallback but could not be imported")
    doc = fitz.open(pdf_path)
    try:
        parts = []
        for i in range(len(doc)):
            page = doc.load_page(i)
            parts.append(page.get_text())
        return "\n\n".join(parts)
    finally:
        doc.close()


class PdfConverter(DocumentConverter):
    """
    Converts PDFs to Markdown using pymupdf4llm.
    Provides better markdown structure (headings, links) than pdfminer.
    Supports image extraction and AI-powered descriptions via Gemini.

    Multi-column pages: Reading order is determined by pymupdf4llm (and
    optionally PyMuPDF Layout if available). If column order is wrong on some
    pages, try passing margins=0 or page_chunks=True in convert(**kwargs), or
    ensure pymupdf (with layout support) is installed for improved layout detection.

    Page headers/footers: Only supported when PyMuPDF Layout is used. Pass
    header=False, footer=False in convert(**kwargs) to exclude them (if your
    pymupdf4llm version supports these parameters).

    Keeping extracted images: Pass image_path=/some/dir in convert(**kwargs) to
    save extracted PNGs there (otherwise a temp dir is used and deleted after).
    """

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,  # Options to pass to the converter
    ) -> bool:
        mimetype = (stream_info.mimetype or "").lower()
        extension = (stream_info.extension or "").lower()

        if extension in ACCEPTED_FILE_EXTENSIONS:
            return True

        for prefix in ACCEPTED_MIME_TYPE_PREFIXES:
            if mimetype.startswith(prefix):
                return True

        return False

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,  # Options to pass to the converter
    ) -> DocumentConverterResult:
        # Check the dependencies
        if _dependency_exc_info is not None:
            raise MissingDependencyException(
                MISSING_DEPENDENCY_MESSAGE.format(
                    converter=type(self).__name__,
                    extension=".pdf",
                    feature="pdf",
                )
            ) from _dependency_exc_info[
                1
            ].with_traceback(  # type: ignore[union-attr]
                _dependency_exc_info[2]
            )

        assert isinstance(file_stream, io.IOBase)  # for mypy
        
        # pymupdf4llm.to_markdown() requires a file path, not a stream
        # So we need to write to a temporary file
        file_stream.seek(0)  # Reset to beginning
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file_stream.read())
            tmp_path = tmp_file.name
        
        def _read_pdf_into_fresh_temp():
            """Write stream into a new temp file (for retry after failure)."""
            file_stream.seek(0)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tf:
                tf.write(file_stream.read())
                return tf.name
        
        # Create temporary directory for extracted images (or use image_path if provided)
        image_dir_cleanup = None
        if kwargs.get("image_path"):
            image_dir = Path(kwargs["image_path"])
            image_dir.mkdir(parents=True, exist_ok=True)
            image_dir_str = str(image_dir)
            logger.info(f"PDF converter - Extracted images will be saved to: {image_dir_str}")
        else:
            image_dir_cleanup = tempfile.TemporaryDirectory()
            image_dir_str = image_dir_cleanup.name
        image_dir = image_dir_str
        retry_tmp_path = None  # Set if we retry after empty-iterable error; cleaned in finally
        try:
                # Build options for pymupdf4llm.to_markdown().
                # Pass through allowed layout/format kwargs for multi-column and layout tuning.
                to_md_kwargs: Dict[str, Any] = {
                    "write_images": True,
                    "image_path": str(image_dir),
                    "image_format": "png",
                }
                for key in PYMUPDF4LLM_KWARGS:
                    if key not in PDF_CONVERTER_KWARGS and key in kwargs:
                        to_md_kwargs[key] = kwargs[key]
                # header/footer are only supported when PyMuPDF Layout is used; omit if not accepted
                if kwargs.get("header") is not None or kwargs.get("footer") is not None:
                    to_md_kwargs["header"] = kwargs.get("header", True)
                    to_md_kwargs["footer"] = kwargs.get("footer", True)
                # Only pass kwargs that to_markdown() accepts (avoids TypeError on older pymupdf4llm)
                try:
                    import inspect
                    sig = inspect.signature(pymupdf4llm.to_markdown)
                    allowed = set(sig.parameters)
                    to_md_kwargs = {k: v for k, v in to_md_kwargs.items() if k in allowed}
                except Exception:
                    pass
                # Extract markdown and images using pymupdf4llm.
                # Some PDFs trigger "min() iterable argument is empty" with layout or image options;
                # retry with path-only on a fresh temp file to get at least the text.
                raw_result = None
                try:
                    raw_result = pymupdf4llm.to_markdown(tmp_path, **to_md_kwargs)
                except ValueError as e:
                    if "min()" in str(e) and "empty" in str(e).lower():
                        logger.warning(
                            "pymupdf4llm failed with empty iterable. "
                            "Retrying with path-only on a fresh temp file to extract text."
                        )
                        retry_tmp_path = _read_pdf_into_fresh_temp()
                        try:
                            raw_result = pymupdf4llm.to_markdown(retry_tmp_path)
                        except ValueError as e2:
                            if "min()" in str(e2) and "empty" in str(e2).lower():
                                logger.warning(
                                    "pymupdf4llm retry also failed. Using PyMuPDF (fitz) as last resort for text extraction."
                                )
                                raw_result = _pdf_to_text_fitz_fallback(retry_tmp_path)
                            else:
                                raise
                    else:
                        raise
                # When page_chunks=True, result is list of dicts; normalize to single markdown string
                if isinstance(raw_result, list):
                    markdown_text = "\n\n".join(
                        chunk.get("text", "") for chunk in raw_result if isinstance(chunk, dict)
                    )
                else:
                    markdown_text = raw_result

                # Check if LLM client is available for image descriptions
                llm_client = kwargs.get("llm_client")
                llm_model = kwargs.get("llm_model")
                
                logger.info(f"PDF converter - Checking for image processing: llm_client={llm_client is not None}, llm_model={llm_model}")
                
                if llm_client is not None and llm_model is not None:
                    # Find all extracted images
                    image_files = sorted(Path(image_dir).glob("*.png"))
                    logger.info(f"PDF converter - Found {len(image_files)} image files in {image_dir}")
                    
                    if image_files:
                        total_images = len(image_files)
                        logger.info(f"Found {total_images} images in PDF. Starting image description generation...")
                        
                        # Remove llm_client and llm_model from kwargs to avoid duplicate arguments
                        # when passing to the shared description pipeline.
                        filtered_kwargs = {k: v for k, v in kwargs.items() 
                                         if k not in ('llm_client', 'llm_model')}
                        
                        # The *.png glob stays here. pymupdf4llm writes PDF page
                        # images as PNG. The shared pipeline does not assume PNG.
                        markdown_text = describe_images_in_markdown(
                            markdown_text,
                            image_files,
                            llm_client=llm_client,
                            llm_model=llm_model,
                            **filtered_kwargs,
                        )
                    else:
                        logger.info("PDF converter - No images found in PDF, skipping image description generation")
                else:
                    logger.warning(f"PDF converter - LLM not available (llm_client={llm_client is not None}, llm_model={llm_model is not None}), skipping image description generation")
                
                return DocumentConverterResult(
                    markdown=markdown_text,
                )
        finally:
            # Critical for cloud/containers: always remove temp files and our temp image dir
            # so we don't leave garbage on disk when called from e.g. ai_personality book upload.
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass
            if retry_tmp_path is not None:
                try:
                    Path(retry_tmp_path).unlink(missing_ok=True)
                except Exception:
                    pass
            # Clean up temp image dir only if we created it (not user-provided image_path)
            if image_dir_cleanup is not None:
                try:
                    image_dir_cleanup.cleanup()
                except Exception:
                    pass
    

    def _extract_image_context(self, markdown_text: str, image_filename: str):
        """Delegate to the shared pipeline.

        Fork tests call this name on PdfConverter. The match rule lives in
        _image_descriptions.extract_image_context.
        """
        return extract_image_context(markdown_text, image_filename)

    def _replace_images_with_descriptions(self, markdown_text: str, image_descriptions):
        """Delegate to the shared pipeline.

        Fork tests call this name on PdfConverter. Table-safe replacement
        lives in _image_descriptions.replace_images_with_descriptions.
        """
        return replace_images_with_descriptions(markdown_text, image_descriptions)
