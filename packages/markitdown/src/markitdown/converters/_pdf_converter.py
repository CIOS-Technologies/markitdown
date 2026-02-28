import sys
import io
import tempfile
import os
import re
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import asyncio

from typing import BinaryIO, Any, Optional, List, Dict


from .._base_converter import DocumentConverter, DocumentConverterResult
from .._stream_info import StreamInfo
from .._exceptions import MissingDependencyException, MISSING_DEPENDENCY_MESSAGE
from ._llm_providers import caption_image, detect_provider

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
                # Extract markdown and images using pymupdf4llm
                raw_result = pymupdf4llm.to_markdown(tmp_path, **to_md_kwargs)
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
                    else:
                        logger.info("PDF converter - No images found in PDF, skipping image description generation")
                else:
                    logger.warning(f"PDF converter - LLM not available (llm_client={llm_client is not None}, llm_model={llm_model is not None}), skipping image description generation")
                
                return DocumentConverterResult(
                    markdown=markdown_text,
                )
        finally:
            # Clean up temporary PDF file
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass
            # Clean up temp image dir only if we created it (not user-provided image_path)
            if image_dir_cleanup is not None:
                try:
                    image_dir_cleanup.cleanup()
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
        logger.info(f"Parallel processing configuration: max_image_workers={max_workers}, total_images={total_images}")
        
        # Check if we should use async (for Gemini) or fall back to threads (for OpenAI)
        provider = detect_provider(llm_client)
        
        # Check if gevent is active (monkey-patched) - asyncio conflicts with gevent
        gevent_active = False
        try:
            import gevent.monkey
            gevent_active = gevent.monkey.is_module_patched('socket')
            if gevent_active:
                logger.info("Detected gevent monkey-patching - will use gevent pool for parallel processing")
        except ImportError:
            pass
        
        # Check if there's already a running event loop (e.g., in Jupyter, async web frameworks)
        try:
            loop = asyncio.get_running_loop()
            if loop is not None:
                logger.info("Detected running event loop - using threaded processing to avoid conflicts")
                gevent_active = True  # Treat as conflict, use threads
        except RuntimeError:
            pass  # No running loop, asyncio.run() is safe
        
        if provider == "gemini" and not gevent_active:
            # Use async for Gemini - true parallelism without connection pool limits
            logger.info(f"Using async processing for Gemini API (true parallelism with {max_workers} concurrent requests)")
            try:
                return asyncio.run(self._process_images_async(
                    image_files, markdown_text, llm_client, llm_model, max_workers, **kwargs
                ))
            except Exception as e:
                logger.warning(f"Async processing failed ({e}), falling back to threaded processing")
                return self._process_images_threaded(
                    image_files, markdown_text, llm_client, llm_model, max_workers, **kwargs
                )
        elif gevent_active:
            # When gevent is active, use a separate subprocess for image processing
            # This bypasses gevent monkey-patching completely and ensures true parallelism
            logger.info(f"Using subprocess worker for Gemini API to bypass gevent limitations")
            return self._process_images_subprocess(
                image_files, markdown_text, llm_client, llm_model, max_workers, **kwargs
            )
        else:
            # Fall back to ThreadPoolExecutor for other providers
            logger.info(f"Using ThreadPoolExecutor for {provider} API with {max_workers} workers")
            return self._process_images_threaded(
                image_files, markdown_text, llm_client, llm_model, max_workers, **kwargs
            )
    
    def _process_images_subprocess(
        self,
        image_files: List[Path],
        markdown_text: str,
        llm_client: Any,
        llm_model: str,
        max_workers: int,
        **kwargs: Any
    ) -> Dict[str, str]:
        """
        Process images using a separate subprocess to bypass gevent limitations.
        """
        import json
        import subprocess
        import tempfile
        import os
        
        # Try to get API key
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            # Try to extract from client if possible
            try:
                if hasattr(llm_client, "api_key"):
                     api_key = llm_client.api_key
            except:
                pass
        
        if not api_key:
            logger.warning("Could not find GEMINI_API_KEY for subprocess worker. Falling back to threaded processing.")
            return self._process_images_threaded(
                image_files, markdown_text, llm_client, llm_model, max_workers, **kwargs
            )

        total_images = len(image_files)
        logger.info(f"Preparing subprocess worker for {total_images} images with {max_workers} workers")
        
        # Prepare input data
        images_data = []
        for img_path in image_files:
            context_before, context_after = self._extract_image_context(
                markdown_text, img_path.name
            )
            images_data.append({
                'path': str(img_path),
                'context_before': context_before[:800] if context_before else None,
                'context_after': context_after[:800] if context_after else None,
            })
            
        worker_input = {
            'images': images_data,
            'config': {
                'api_key': api_key,
                'model': llm_model,
                'max_workers': max_workers,
                'prompt': kwargs.get('llm_prompt')
            }
        }
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(worker_input, f)
            input_path = f.name
            
        output_path = input_path + ".out"
        
        try:
            # Locate worker script
            import markitdown.converters
            package_dir = Path(markitdown.converters.__file__).parent
            worker_script = package_dir / "_image_description_worker.py"
            
            if not worker_script.exists():
                logger.error(f"Worker script not found at {worker_script}")
                return self._process_images_threaded(
                    image_files, markdown_text, llm_client, llm_model, max_workers, **kwargs
                )
            
            logger.info(f"Spawning subprocess: {sys.executable} {worker_script}")
            
            # Run subprocess with real-time logging
            # We use Popen to stream stderr (where logs go) to our logger
            process = subprocess.Popen(
                [sys.executable, str(worker_script), input_path, output_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            # Stream logs from subprocess stderr
            # The worker script configures logging to stderr by default
            if process.stderr:
                for line in process.stderr:
                    line = line.strip()
                    if line:
                        # Forward worker logs to our logger
                        # Check if it looks like a log line with timestamp, if so, strip it to avoid double timestamp
                        # But simplest is just to log it
                        if "ERROR" in line:
                            logger.error(f"[Worker] {line}")
                        elif "WARNING" in line:
                            logger.warning(f"[Worker] {line}")
                        else:
                            logger.info(f"[Worker] {line}")
                            
            # Wait for process to complete
            return_code = process.wait()
            
            if return_code != 0:
                stdout_content = process.stdout.read() if process.stdout else ""
                logger.error(f"Subprocess failed with return code {return_code}")
                logger.error(f"Stdout: {stdout_content}")
                return self._process_images_threaded(
                    image_files, markdown_text, llm_client, llm_model, max_workers, **kwargs
                )
                
            # Read results
            if os.path.exists(output_path):
                with open(output_path, 'r') as f:
                    descriptions = json.load(f)
                logger.info(f"Subprocess completed successfully. Received {len(descriptions)} descriptions.")
                return descriptions
            else:
                logger.error("Subprocess did not produce output file")
                return {}
                
        except Exception as e:
            logger.error(f"Error running subprocess worker: {e}", exc_info=True)
            return self._process_images_threaded(
                image_files, markdown_text, llm_client, llm_model, max_workers, **kwargs
            )
        finally:
            # Cleanup temp files
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    async def _process_images_async(
        self,
        image_files: List[Path],
        markdown_text: str,
        llm_client: Any,
        llm_model: str,
        max_workers: int,
        **kwargs: Any
    ) -> Dict[str, str]:
        """
        Process images asynchronously using asyncio for true parallelism.
        
        Args:
            image_files: List of image file paths
            markdown_text: The markdown content for context extraction
            llm_client: LLM client instance
            llm_model: LLM model name
            max_workers: Maximum number of concurrent requests
            **kwargs: Additional options
            
        Returns:
            Dictionary mapping image filenames to descriptions
        """
        from ._gemini_caption import gemini_caption_async
        
        total_images = len(image_files)
        
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
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_workers)
        image_descriptions = {}
        
        async def process_single_image_async(task: dict) -> tuple[str, Optional[str]]:
            """Process a single image asynchronously."""
            async with semaphore:
                idx = task['idx']
                img_path = task['img_path']
                context_before = task['context_before']
                context_after = task['context_after']
                
                import time
                start_time = time.time()
                try:
                    logger.info(f"[Async] START Processing image {idx}/{total_images}: {img_path.name} at {time.time():.3f}")
                    
                    # Read image file
                    logger.debug(f"[Async] Reading image file: {img_path.name}")
                    with open(img_path, 'rb') as img_file:
                        img_stream = io.BytesIO(img_file.read())
                    logger.debug(f"[Async] Image file read: {img_path.name} ({len(img_stream.getvalue())} bytes)")
                    
                    # Create stream info for image
                    img_stream_info = StreamInfo(
                        extension='.png',
                        filename=img_path.name,
                        mimetype='image/png'
                    )
                    
                    # Call async caption function
                    logger.debug(f"[Async] Calling gemini_caption_async for: {img_path.name}")
                    description = await gemini_caption_async(
                        img_stream,
                        img_stream_info,
                        client=llm_client,
                        model=llm_model,
                        prompt=kwargs.get('llm_prompt'),
                        context_before=context_before,
                        context_after=context_after,
                        use_advanced_prompt=kwargs.get('llm_use_advanced_prompt', True)
                    )
                    logger.debug(f"[Async] Received response from gemini_caption_async for: {img_path.name}")
                    
                    duration = time.time() - start_time
                    if description:
                        logger.info(f"[Async] COMPLETED image {idx}/{total_images} in {duration:.2f}s: {img_path.name} ({len(description)} chars)")
                    else:
                        logger.debug(f"[Async] SKIPPED image {idx}/{total_images} in {duration:.2f}s: {img_path.name}")
                    
                    return img_path.name, description
                    
                except Exception as e:
                    duration = time.time() - start_time
                    logger.warning(f"[Async] ERROR processing image {idx}/{total_images} in {duration:.2f}s: {img_path.name} - {str(e)}")
                    return img_path.name, None
        
        # Process all images concurrently
        logger.info(f"Starting async processing of {len(image_tasks)} images with {max_workers} concurrent requests...")
        import time
        start_time = time.time()
        
        # Create all tasks
        tasks = [process_single_image_async(task) for task in image_tasks]
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        completed_count = 0
        for result in results:
            completed_count += 1
            if isinstance(result, Exception):
                logger.warning(f"Task failed with exception: {result}")
                continue
            
            image_name, description = result
            if description:
                image_descriptions[image_name] = description
                logger.info(f"Successfully processed image {completed_count}/{total_images}: {image_name}")
        
        total_duration = time.time() - start_time
        logger.info(f"Completed async processing: {len(image_descriptions)}/{total_images} images described in {total_duration:.2f}s")
        
        return image_descriptions
    
    def _process_images_threaded(
        self,
        image_files: List[Path],
        markdown_text: str,
        llm_client: Any,
        llm_model: str,
        max_workers: int,
        **kwargs: Any
    ) -> Dict[str, str]:
        """
        Process images using ThreadPoolExecutor (fallback for non-Gemini providers).
        
        Args:
            image_files: List of image file paths
            markdown_text: The markdown content for context extraction
            llm_client: LLM client instance
            llm_model: LLM model name
            max_workers: Maximum number of worker threads
            **kwargs: Additional options
            
        Returns:
            Dictionary mapping image filenames to descriptions
        """
        total_images = len(image_files)
        
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
        max_consecutive_errors = 3
        min_workers = 1
        
        # Process all images with current worker count
        logger.info(f"Creating ThreadPoolExecutor with {current_workers} workers for {total_images} images")
        with ThreadPoolExecutor(max_workers=current_workers, thread_name_prefix="ImageWorker") as executor:
            # Submit all tasks at once
            logger.info(f"Submitting {len(image_tasks)} image processing tasks to executor with {current_workers} workers...")
            import time
            submit_start = time.time()
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
            submit_duration = time.time() - submit_start
            logger.info(f"All {len(future_to_task)} tasks submitted in {submit_duration:.3f}s. Waiting for completion...")
            
            # Log active thread count
            active_threads = threading.active_count()
            logger.info(f"Active threads after submission: {active_threads} (expected: {current_workers + 1} main thread)")
            
            # Note: If you see fewer threads than expected, it may be due to:
            # 1. Gemini API client connection pool limits (default may be ~5)
            # 2. API rate limiting
            # 3. ThreadPoolExecutor not creating all workers immediately
            # The executor will create threads as needed, but API/client limits may prevent true parallelism
            
            # Collect results as they complete
            completed_count = 0
            import time
            start_collection = time.time()
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                image_name = task['img_path'].name
                idx = task['idx']
                
                completed_count += 1
                try:
                    description = future.result()
                    if description:
                        image_descriptions[image_name] = description
                        logger.info(f"Successfully generated description for image {idx}/{total_images} ({completed_count}/{total_images} completed): {image_name} ({len(description)} chars)")
                        consecutive_errors = 0  # Reset error counter on success
                    else:
                        logger.debug(f"Image {idx}/{total_images} ({completed_count}/{total_images} completed) skipped or failed: {image_name}")
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
        import threading
        import time
        thread_id = threading.current_thread().ident
        thread_name = threading.current_thread().name
        start_time = time.time()
        try:
            # Log when thread actually starts processing (not just when task is submitted)
            logger.info(f"[Thread {thread_id} ({thread_name})] START Processing image {idx}/{total_images}: {img_path.name} at {time.time():.3f}")
            
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
            logger.debug(f"[Thread {thread_id}] Calling LLM API for image {idx}/{total_images}: {img_path.name}")
            api_start = time.time()
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
            api_duration = time.time() - api_start
            total_duration = time.time() - start_time
            logger.debug(f"[Thread {thread_id}] COMPLETED image {idx}/{total_images} in {total_duration:.2f}s (API: {api_duration:.2f}s): {img_path.name}")
            
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
        Descriptions are inserted in document order and the original image link
        is kept immediately after each description so they stay adjacent.

        Args:
            markdown_text: The markdown content with image references
            image_descriptions: Dictionary mapping image filenames to descriptions

        Returns:
            Updated markdown text with descriptions (and original links kept after each)
        """
        if not image_descriptions:
            return markdown_text

        # Match any markdown image: ![alt](path). Path can contain / or \.
        image_ref_pattern = re.compile(r'!\[([^\]]*)\]\(([^\)]+)\)')
        parts = []
        last_end = 0

        for match in image_ref_pattern.finditer(markdown_text):
            full_match = match.group(0)
            path = match.group(2).strip()
            # Filename is the last path component (avoids matching "img.png" inside "myimg.png")
            filename = path.replace("\\", "/").split("/")[-1]

            if filename not in image_descriptions:
                continue

            description = image_descriptions[filename]
            # Insert description block then keep the original image link so they stay together
            replacement = (
                f"\n\n**[AI-Generated Image Description]**\n\n{description}\n\n"
                + full_match
            )

            parts.append(markdown_text[last_end : match.start()])
            parts.append(replacement)
            last_end = match.end()

        parts.append(markdown_text[last_end:])
        return "".join(parts)
