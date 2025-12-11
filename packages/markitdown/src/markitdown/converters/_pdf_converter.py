import sys
import io
import tempfile
import os
import re
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from typing import BinaryIO, Any, Optional, List, Dict


from .._base_converter import DocumentConverter, DocumentConverterResult
from .._stream_info import StreamInfo
from .._exceptions import MissingDependencyException, MISSING_DEPENDENCY_MESSAGE
from ._llm_providers import caption_image

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


ACCEPTED_MIME_TYPE_PREFIXES = [
    "application/pdf",
    "application/x-pdf",
]

ACCEPTED_FILE_EXTENSIONS = [".pdf"]


class PdfConverter(DocumentConverter):
    """
    Converts PDFs to Markdown using pymupdf4llm.
    Provides better markdown structure (headings, links) than pdfminer.
    Supports image extraction and AI-powered descriptions via Gemini.
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
        
        # Create temporary directory for extracted images
        with tempfile.TemporaryDirectory() as image_dir:
            try:
                # Extract markdown and images using pymupdf4llm
                markdown_text = pymupdf4llm.to_markdown(
                    tmp_path,
                    write_images=True,  # Extract images
                    image_path=str(image_dir),  # Save location
                    image_format="png"
                )
                
                # Check if LLM client is available for image descriptions
                llm_client = kwargs.get("llm_client")
                llm_model = kwargs.get("llm_model")
                
                if llm_client is not None and llm_model is not None:
                    # Find all extracted images
                    image_files = sorted(Path(image_dir).glob("*.png"))
                    
                    if image_files:
                        total_images = len(image_files)
                        logger.info(f"Found {total_images} images in PDF. Starting image description generation...")
                        
                        # Remove llm_client and llm_model from kwargs to avoid duplicate arguments
                        # when passing to _process_images_parallel
                        filtered_kwargs = {k: v for k, v in kwargs.items() 
                                         if k not in ('llm_client', 'llm_model')}
                        
                        # Process images in parallel with adaptive rate limiting
                        image_descriptions = self._process_images_parallel(
                            image_files,
                            markdown_text,
                            llm_client,
                            llm_model,
                            **filtered_kwargs
                        )
                        
                        logger.info(f"Completed image processing: {len(image_descriptions)}/{total_images} images described successfully")
                        
                        # Replace image markdown references with descriptions
                        if image_descriptions:
                            markdown_text = self._replace_images_with_descriptions(
                                markdown_text, image_descriptions
                            )
                
                return DocumentConverterResult(
                    markdown=markdown_text,
                )
            finally:
                # Clean up temporary PDF file
                try:
                    Path(tmp_path).unlink()
                except Exception:
                    pass
    
    def _process_images_parallel(
        self,
        image_files: List[Path],
        markdown_text: str,
        llm_client: Any,
        llm_model: str,
        **kwargs: Any
    ) -> Dict[str, str]:
        """
        Process images in parallel using worker pool with adaptive rate limiting.
        
        Args:
            image_files: List of image file paths
            markdown_text: The markdown content for context extraction
            llm_client: LLM client instance
            llm_model: LLM model name
            **kwargs: Additional options (max_image_workers, llm_prompt, etc.)
            
        Returns:
            Dictionary mapping image filenames to descriptions
        """
        total_images = len(image_files)
        max_workers = kwargs.get("max_image_workers", 20)
        
        # Prepare all image tasks upfront
        image_tasks = []
        for idx, img_path in enumerate(image_files, 1):
            context_before, context_after = self._extract_image_context(
                markdown_text, img_path.name
            )
            image_tasks.append({
                'idx': idx,
                'img_path': img_path,
                'context_before': context_before[:800] if context_before else None,
                'context_after': context_after[:800] if context_after else None,
            })
        
        image_descriptions = {}
        current_workers = max_workers
        consecutive_errors = 0
        max_consecutive_errors = 3  # Reduce workers after 3 consecutive errors
        min_workers = 1  # Minimum workers (1 = sequential processing)
        
        # Process all images with current worker count
        # If we encounter rate limiting errors, we'll log them for monitoring
        with ThreadPoolExecutor(max_workers=current_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(
                    self._process_single_image,
                    task['idx'],
                    total_images,
                    task['img_path'],
                    task['context_before'],
                    task['context_after'],
                    llm_client,
                    llm_model,
                    kwargs
                ): task
                for task in image_tasks
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                image_name = task['img_path'].name
                idx = task['idx']
                
                try:
                    description = future.result()
                    if description:
                        image_descriptions[image_name] = description
                        logger.info(f"Successfully generated description for image {idx}/{total_images}: {image_name} ({len(description)} chars)")
                        consecutive_errors = 0  # Reset error counter on success
                    else:
                        logger.debug(f"Image {idx}/{total_images} skipped or failed: {image_name}")
                        consecutive_errors = 0  # Skipped images don't count as errors
                        
                except Exception as e:
                    # Track consecutive errors for monitoring
                    consecutive_errors += 1
                    error_msg = str(e).lower()
                    is_rate_limit = any(keyword in error_msg for keyword in ['rate limit', '429', 'quota', 'too many requests'])
                    
                    logger.warning(f"Failed to process image {idx}/{total_images} ({image_name}): {str(e)}")
                    
                    # Log warning if rate limiting detected (for monitoring/debugging)
                    if is_rate_limit and consecutive_errors >= max_consecutive_errors:
                        logger.warning(
                            f"Detected {consecutive_errors} consecutive errors (possible rate limiting). "
                            f"Consider reducing max_image_workers from {current_workers} to {max(min_workers, current_workers // 2)} "
                            f"if this persists."
                        )
        
        return image_descriptions
    
    def _process_single_image(
        self,
        idx: int,
        total_images: int,
        img_path: Path,
        context_before: Optional[str],
        context_after: Optional[str],
        llm_client: Any,
        llm_model: str,
        kwargs: dict
    ) -> Optional[str]:
        """
        Process a single image (worker function for parallel processing).
        
        Args:
            idx: Image index (1-based)
            total_images: Total number of images
            img_path: Path to image file
            context_before: Text context before image
            context_after: Text context after image
            llm_client: LLM client instance
            llm_model: LLM model name
            kwargs: Additional options
            
        Returns:
            Image description or None if failed/skipped
        """
        try:
            logger.info(f"Processing image {idx}/{total_images}: {img_path.name}")
            
            # Read image file
            with open(img_path, 'rb') as img_file:
                img_stream = io.BytesIO(img_file.read())
            
            # Create stream info for image
            img_stream_info = StreamInfo(
                extension='.png',
                mimetype='image/png',
                filename=img_path.name
            )
            
            # Generate description using LLM
            logger.debug(f"Calling LLM API for image {idx}/{total_images}: {img_path.name}")
            description = caption_image(
                img_stream,
                img_stream_info,
                client=llm_client,
                model=llm_model,
                prompt=kwargs.get("llm_prompt"),
                context_before=context_before,
                context_after=context_after,
                use_advanced_prompt=kwargs.get("llm_use_advanced_prompt", True),
            )
            
            return description
            
        except Exception as e:
            # Re-raise exception to be handled by caller
            raise
    
    def _extract_image_context(self, markdown_text: str, image_filename: str) -> tuple[Optional[str], Optional[str]]:
        """
        Extract context (text before and after) an image reference in markdown.
        
        Args:
            markdown_text: The markdown content
            image_filename: Name of the image file to find
            
        Returns:
            Tuple of (context_before, context_after)
        """
        # Find image references in markdown (format: ![alt](path/to/image.png))
        # Pattern matches markdown image syntax
        pattern = rf'!\[([^\]]*)\]\([^\)]*{re.escape(image_filename)}\)'
        
        match = re.search(pattern, markdown_text)
        if not match:
            return None, None
        
        match_start = match.start()
        match_end = match.end()
        
        # Get text before image (up to 800 chars)
        context_before = markdown_text[max(0, match_start - 800):match_start].strip()
        
        # Get text after image (up to 800 chars)
        context_after = markdown_text[match_end:match_end + 800].strip()
        
        return context_before, context_after
    
    def _replace_images_with_descriptions(self, markdown_text: str, image_descriptions: Dict[str, str]) -> str:
        """
        Replace image markdown references with AI-generated descriptions.
        
        Args:
            markdown_text: The markdown content with image references
            image_descriptions: Dictionary mapping image filenames to descriptions
            
        Returns:
            Updated markdown text with descriptions
        """
        for image_filename, description in image_descriptions.items():
            # Pattern to match image markdown: ![alt](path/to/image.png)
            # Escape the filename to handle any special regex characters
            escaped_filename = re.escape(image_filename)
            pattern = rf'!\[([^\]]*)\]\([^\)]*{escaped_filename}\)'
            
            # Build replacement text
            replacement_text = f"\n\n**[AI-Generated Image Description]**\n\n{description}\n\n"
            
            # Create a replacer function that captures the replacement text
            # This avoids closure issues in the loop
            def make_replacer(repl):
                return lambda m: repl
            
            # Use the replacer to safely replace, treating replacement as literal text
            markdown_text = re.sub(pattern, make_replacer(replacement_text), markdown_text)
        
        return markdown_text
