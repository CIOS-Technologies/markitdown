"""Shared image-description pipeline.

PdfConverter calls describe_images_in_markdown after it has markdown and a
list of image files. This module does not import PyMuPDF. The PDF engine
still decides which files to pass in (today: a *.png glob).

Three fixes live here, on top of the moved PDF pipeline:

- Each file keeps its own mimetype and extension on every path, including
  the subprocess payload.
- Context lookup uses the last path segment, the same rule as the replacer.
  "img1.png" does not match "img10.png".
- An image inside a markdown table cell keeps its link. The description
  block is inserted after that table, in document order.
"""

import asyncio
import io
import json
import logging
import mimetypes
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Optional

from .._stream_info import StreamInfo
from ._llm_providers import caption_image, detect_provider

logger = logging.getLogger(__name__)

# Same block the PDF converter has always written. Outside a table the
# original image link is appended to this block. Inside a table the link
# stays in the cell and only this block is added after the table.
_DESCRIPTION_HEADING = "**[AI-Generated Image Description]**"

# A pipe row, and the dash row that makes the block a real markdown table.
_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
_TABLE_SEPARATOR = re.compile(r"^\s*\|(?:\s*:?-+:?\s*\|)+\s*$")
_IMAGE_REF = re.compile(r"!\[([^\]]*)\]\(([^\)]+)\)")


def describe_images_in_markdown(
    markdown: str,
    image_files: list[Path],
    *,
    llm_client,
    llm_model,
    **kwargs,
) -> str:
    """Describe image_files and insert the text into markdown.

    Returns the original markdown when nothing was described. The block
    format matches the previous PdfConverter output.
    """
    if not image_files:
        return markdown

    descriptions = process_images_parallel(
        image_files,
        markdown,
        llm_client,
        llm_model,
        **kwargs,
    )
    logger.info(
        "Completed image processing: "
        f"{len(descriptions)}/{len(image_files)} images described successfully"
    )
    if not descriptions:
        return markdown
    return replace_images_with_descriptions(markdown, descriptions)


def image_file_stream_info(img_path: Path) -> StreamInfo:
    """Build StreamInfo from the file name.

    The type comes from the suffix (.jpg -> image/jpeg). We do not label
    every file as image/png.
    """
    extension = img_path.suffix or None
    guessed, _ = mimetypes.guess_type(img_path.name)
    mimetype = guessed or "application/octet-stream"
    return StreamInfo(
        extension=extension,
        filename=img_path.name,
        mimetype=mimetype,
    )


def _last_segment(path: str) -> str:
    """File name at the end of a markdown image path.

    Backslashes count as separators. The comparison is the whole name,
    so a shorter name cannot match a longer one.
    """
    cleaned = path.strip().replace("\\", "/")
    return cleaned.split("/")[-1]


def _description_block(description: str) -> str:
    return f"\n\n{_DESCRIPTION_HEADING}\n\n{description}\n\n"


def _table_spans(markdown_text: str) -> list[tuple[int, int]]:
    """Character spans [start, end) of pipe tables.

    A table is a run of pipe rows that includes a separator row
    (| --- | --- |). The end index is the first character after the table,
    so an insert there sits on the following line.
    """
    spans: list[tuple[int, int]] = []
    offset = 0
    block_start: Optional[int] = None
    block_has_separator = False

    def close(end: int) -> None:
        nonlocal block_start, block_has_separator
        if block_start is not None and block_has_separator:
            spans.append((block_start, end))
        block_start = None
        block_has_separator = False

    for line in markdown_text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        if _TABLE_ROW.match(body) and body.count("|") >= 2:
            if block_start is None:
                block_start = offset
            if _TABLE_SEPARATOR.match(body):
                block_has_separator = True
        else:
            close(offset)
        offset += len(line)
    close(offset)
    return spans


def extract_image_context(
    markdown_text: str, image_filename: str
) -> tuple[Optional[str], Optional[str]]:
    """Text before and after the image whose last path segment equals image_filename.

    Up to 800 characters on each side. No match returns (None, None).
    """
    for match in _IMAGE_REF.finditer(markdown_text):
        # Exact name only. A substring such as img1.png inside img10.png
        # or chart.png inside mychart.png is a different image.
        if _last_segment(match.group(2)) != image_filename:
            continue
        match_start = match.start()
        match_end = match.end()
        context_before = markdown_text[max(0, match_start - 800) : match_start].strip()
        context_after = markdown_text[match_end : match_end + 800].strip()
        return context_before, context_after
    return None, None


def replace_images_with_descriptions(
    markdown_text: str, image_descriptions: dict[str, str]
) -> str:
    """Insert description blocks next to the images they describe.

    Outside a table the block is written, then the original link, which is
    the PDF behaviour. Inside a table the link stays in the cell. The blocks
    for that table are written after the table's last line, in the order
    the images appear.
    """
    if not image_descriptions:
        return markdown_text

    spans = _table_spans(markdown_text)

    def table_end_for(pos: int) -> Optional[int]:
        for start, end in spans:
            if start <= pos < end:
                return end
        return None

    # start index -> (end index, replacement text) for images that are not in a table
    in_place: dict[int, tuple[int, str]] = {}
    # index just after a table -> description blocks, in document order
    insertions: dict[int, list[str]] = {}

    for match in _IMAGE_REF.finditer(markdown_text):
        filename = _last_segment(match.group(2))
        if filename not in image_descriptions:
            continue
        block = _description_block(image_descriptions[filename])
        table_end = table_end_for(match.start())
        if table_end is None:
            in_place[match.start()] = (match.end(), block + match.group(0))
        else:
            insertions.setdefault(table_end, []).append(block)

    if not in_place and not insertions:
        return markdown_text

    parts: list[str] = []
    cursor = 0
    for pos in sorted(set(in_place) | set(insertions)):
        parts.append(markdown_text[cursor:pos])
        parts.extend(insertions.get(pos, []))
        if pos in in_place:
            end, text = in_place[pos]
            parts.append(text)
            cursor = end
        else:
            cursor = pos
    parts.append(markdown_text[cursor:])
    return "".join(parts)


def build_subprocess_payload(
    image_files: list[Path],
    markdown_text: str,
    *,
    api_key: str,
    llm_model: str,
    max_workers: int,
    llm_prompt: Optional[str],
    use_advanced_prompt: bool,
) -> dict:
    """JSON body for _image_description_worker.py.

    Each image carries its mimetype and extension. The advanced-prompt flag
    is in config so the worker does not assume True.
    """
    images_data = []
    for img_path in image_files:
        context_before, context_after = extract_image_context(
            markdown_text, img_path.name
        )
        info = image_file_stream_info(img_path)
        images_data.append(
            {
                "path": str(img_path),
                "context_before": context_before[:800] if context_before else None,
                "context_after": context_after[:800] if context_after else None,
                "mimetype": info.mimetype,
                "extension": info.extension,
            }
        )
    return {
        "images": images_data,
        "config": {
            "api_key": api_key,
            "model": llm_model,
            "max_workers": max_workers,
            "prompt": llm_prompt,
            "use_advanced_prompt": use_advanced_prompt,
        },
    }


def process_images_parallel(
    image_files: list[Path],
    markdown_text: str,
    llm_client: Any,
    llm_model: str,
    **kwargs: Any,
) -> dict[str, str]:
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
    logger.info(
        f"Parallel processing configuration: max_image_workers={max_workers}, total_images={total_images}"
    )

    # Check if we should use async (for Gemini) or fall back to threads (for OpenAI)
    provider = detect_provider(llm_client)

    # Check if gevent is active (monkey-patched) - asyncio conflicts with gevent
    gevent_active = False
    try:
        import gevent.monkey

        gevent_active = gevent.monkey.is_module_patched("socket")
        if gevent_active:
            logger.info(
                "Detected gevent monkey-patching - will use gevent pool for parallel processing"
            )
    except ImportError:
        pass

    # Check if there's already a running event loop (e.g., in Jupyter, async web frameworks)
    try:
        loop = asyncio.get_running_loop()
        if loop is not None:
            logger.info(
                "Detected running event loop - using threaded processing to avoid conflicts"
            )
            gevent_active = True  # Treat as conflict, use threads
    except RuntimeError:
        pass  # No running loop, asyncio.run() is safe

    if provider == "gemini" and not gevent_active:
        # Use async for Gemini - true parallelism without connection pool limits
        logger.info(
            f"Using async processing for Gemini API (true parallelism with {max_workers} concurrent requests)"
        )
        try:
            return asyncio.run(
                _process_images_async(
                    image_files,
                    markdown_text,
                    llm_client,
                    llm_model,
                    max_workers,
                    **kwargs,
                )
            )
        except Exception as e:
            logger.warning(
                f"Async processing failed ({e}), falling back to threaded processing"
            )
            return _process_images_threaded(
                image_files,
                markdown_text,
                llm_client,
                llm_model,
                max_workers,
                **kwargs,
            )
    elif gevent_active:
        # When gevent is active, use a separate subprocess for image processing
        # This bypasses gevent monkey-patching completely and ensures true parallelism
        logger.info(
            "Using subprocess worker for Gemini API to bypass gevent limitations"
        )
        return _process_images_subprocess(
            image_files,
            markdown_text,
            llm_client,
            llm_model,
            max_workers,
            **kwargs,
        )
    else:
        # Fall back to ThreadPoolExecutor for other providers
        logger.info(
            f"Using ThreadPoolExecutor for {provider} API with {max_workers} workers"
        )
        return _process_images_threaded(
            image_files,
            markdown_text,
            llm_client,
            llm_model,
            max_workers,
            **kwargs,
        )


def _process_images_subprocess(
    image_files: list[Path],
    markdown_text: str,
    llm_client: Any,
    llm_model: str,
    max_workers: int,
    **kwargs: Any,
) -> dict[str, str]:
    """
    Process images using a separate subprocess to bypass gevent limitations.
    """
    # Try to get API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Try to extract from client if possible
        try:
            if hasattr(llm_client, "api_key"):
                api_key = llm_client.api_key
        except Exception:
            pass

    if not api_key:
        logger.warning(
            "Could not find GEMINI_API_KEY for subprocess worker. Falling back to threaded processing."
        )
        return _process_images_threaded(
            image_files, markdown_text, llm_client, llm_model, max_workers, **kwargs
        )

    total_images = len(image_files)
    logger.info(
        f"Preparing subprocess worker for {total_images} images with {max_workers} workers"
    )

    worker_input = build_subprocess_payload(
        image_files,
        markdown_text,
        api_key=api_key,
        llm_model=llm_model,
        max_workers=max_workers,
        llm_prompt=kwargs.get("llm_prompt"),
        use_advanced_prompt=kwargs.get("llm_use_advanced_prompt", True),
    )

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump(worker_input, f)
        input_path = f.name

    output_path = input_path + ".out"

    try:
        # Locate worker script. It stays next to this package so the
        # subprocess can import markitdown the same way as before.
        import markitdown.converters

        package_dir = Path(markitdown.converters.__file__).parent
        worker_script = package_dir / "_image_description_worker.py"

        if not worker_script.exists():
            logger.error(f"Worker script not found at {worker_script}")
            return _process_images_threaded(
                image_files,
                markdown_text,
                llm_client,
                llm_model,
                max_workers,
                **kwargs,
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
            universal_newlines=True,
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
            return _process_images_threaded(
                image_files,
                markdown_text,
                llm_client,
                llm_model,
                max_workers,
                **kwargs,
            )

        # Read results
        if os.path.exists(output_path):
            with open(output_path, "r") as f:
                descriptions = json.load(f)
            logger.info(
                f"Subprocess completed successfully. Received {len(descriptions)} descriptions."
            )
            return descriptions
        else:
            logger.error("Subprocess did not produce output file")
            return {}

    except Exception as e:
        logger.error(f"Error running subprocess worker: {e}", exc_info=True)
        return _process_images_threaded(
            image_files, markdown_text, llm_client, llm_model, max_workers, **kwargs
        )
    finally:
        # Cleanup temp files
        if os.path.exists(input_path):
            os.unlink(input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)


async def _process_images_async(
    image_files: list[Path],
    markdown_text: str,
    llm_client: Any,
    llm_model: str,
    max_workers: int,
    **kwargs: Any,
) -> dict[str, str]:
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
    use_advanced_prompt = kwargs.get("llm_use_advanced_prompt", True)

    # Prepare all image tasks upfront
    image_tasks = []
    for idx, img_path in enumerate(image_files, 1):
        context_before, context_after = extract_image_context(
            markdown_text, img_path.name
        )
        image_tasks.append(
            {
                "idx": idx,
                "img_path": img_path,
                "context_before": context_before[:800] if context_before else None,
                "context_after": context_after[:800] if context_after else None,
            }
        )

    # Create semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(max_workers)
    image_descriptions: dict[str, str] = {}

    async def process_single_image_async(task: dict) -> tuple[str, Optional[str]]:
        """Process a single image asynchronously."""
        async with semaphore:
            idx = task["idx"]
            img_path = task["img_path"]
            context_before = task["context_before"]
            context_after = task["context_after"]

            start_time = time.time()
            try:
                logger.info(
                    f"[Async] START Processing image {idx}/{total_images}: {img_path.name} at {time.time():.3f}"
                )

                # Read image file
                logger.debug(f"[Async] Reading image file: {img_path.name}")
                with open(img_path, "rb") as img_file:
                    img_stream = io.BytesIO(img_file.read())
                logger.debug(
                    f"[Async] Image file read: {img_path.name} ({len(img_stream.getvalue())} bytes)"
                )

                # Type comes from the file, not a fixed PNG label.
                img_stream_info = image_file_stream_info(img_path)

                # Call async caption function
                logger.debug(f"[Async] Calling gemini_caption_async for: {img_path.name}")
                description = await gemini_caption_async(
                    img_stream,
                    img_stream_info,
                    client=llm_client,
                    model=llm_model,
                    prompt=kwargs.get("llm_prompt"),
                    context_before=context_before,
                    context_after=context_after,
                    use_advanced_prompt=use_advanced_prompt,
                )
                logger.debug(
                    f"[Async] Received response from gemini_caption_async for: {img_path.name}"
                )

                duration = time.time() - start_time
                if description:
                    logger.info(
                        f"[Async] COMPLETED image {idx}/{total_images} in {duration:.2f}s: {img_path.name} ({len(description)} chars)"
                    )
                else:
                    logger.debug(
                        f"[Async] SKIPPED image {idx}/{total_images} in {duration:.2f}s: {img_path.name}"
                    )

                return img_path.name, description

            except Exception as e:
                duration = time.time() - start_time
                logger.warning(
                    f"[Async] ERROR processing image {idx}/{total_images} in {duration:.2f}s: {img_path.name} - {str(e)}"
                )
                return img_path.name, None

    # Process all images concurrently
    logger.info(
        f"Starting async processing of {len(image_tasks)} images with {max_workers} concurrent requests..."
    )
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
            logger.info(
                f"Successfully processed image {completed_count}/{total_images}: {image_name}"
            )

    total_duration = time.time() - start_time
    logger.info(
        f"Completed async processing: {len(image_descriptions)}/{total_images} images described in {total_duration:.2f}s"
    )

    return image_descriptions


def _process_images_threaded(
    image_files: list[Path],
    markdown_text: str,
    llm_client: Any,
    llm_model: str,
    max_workers: int,
    **kwargs: Any,
) -> dict[str, str]:
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
        context_before, context_after = extract_image_context(
            markdown_text, img_path.name
        )
        image_tasks.append(
            {
                "idx": idx,
                "img_path": img_path,
                "context_before": context_before[:800] if context_before else None,
                "context_after": context_after[:800] if context_after else None,
            }
        )

    image_descriptions: dict[str, str] = {}
    current_workers = max_workers
    consecutive_errors = 0
    max_consecutive_errors = 3
    min_workers = 1

    # Process all images with current worker count
    logger.info(
        f"Creating ThreadPoolExecutor with {current_workers} workers for {total_images} images"
    )
    with ThreadPoolExecutor(
        max_workers=current_workers, thread_name_prefix="ImageWorker"
    ) as executor:
        # Submit all tasks at once
        logger.info(
            f"Submitting {len(image_tasks)} image processing tasks to executor with {current_workers} workers..."
        )
        submit_start = time.time()
        future_to_task = {
            executor.submit(
                _process_single_image,
                task["idx"],
                total_images,
                task["img_path"],
                task["context_before"],
                task["context_after"],
                llm_client,
                llm_model,
                kwargs,
            ): task
            for task in image_tasks
        }
        submit_duration = time.time() - submit_start
        logger.info(
            f"All {len(future_to_task)} tasks submitted in {submit_duration:.3f}s. Waiting for completion..."
        )

        # Log active thread count
        active_threads = threading.active_count()
        logger.info(
            f"Active threads after submission: {active_threads} (expected: {current_workers + 1} main thread)"
        )

        # Note: If you see fewer threads than expected, it may be due to:
        # 1. Gemini API client connection pool limits (default may be ~5)
        # 2. API rate limiting
        # 3. ThreadPoolExecutor not creating all workers immediately
        # The executor will create threads as needed, but API/client limits may prevent true parallelism

        # Collect results as they complete
        completed_count = 0
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            image_name = task["img_path"].name
            idx = task["idx"]

            completed_count += 1
            try:
                description = future.result()
                if description:
                    image_descriptions[image_name] = description
                    logger.info(
                        f"Successfully generated description for image {idx}/{total_images} ({completed_count}/{total_images} completed): {image_name} ({len(description)} chars)"
                    )
                    consecutive_errors = 0  # Reset error counter on success
                else:
                    logger.debug(
                        f"Image {idx}/{total_images} ({completed_count}/{total_images} completed) skipped or failed: {image_name}"
                    )
                    consecutive_errors = 0  # Skipped images don't count as errors

            except Exception as e:
                # Track consecutive errors for monitoring
                consecutive_errors += 1
                error_msg = str(e).lower()
                is_rate_limit = any(
                    keyword in error_msg
                    for keyword in ["rate limit", "429", "quota", "too many requests"]
                )

                logger.warning(
                    f"Failed to process image {idx}/{total_images} ({image_name}): {str(e)}"
                )

                # Log warning if rate limiting detected (for monitoring/debugging)
                if is_rate_limit and consecutive_errors >= max_consecutive_errors:
                    logger.warning(
                        f"Detected {consecutive_errors} consecutive errors (possible rate limiting). "
                        f"Consider reducing max_image_workers from {current_workers} to {max(min_workers, current_workers // 2)} "
                        f"if this persists."
                    )

    return image_descriptions


def _process_single_image(
    idx: int,
    total_images: int,
    img_path: Path,
    context_before: Optional[str],
    context_after: Optional[str],
    llm_client: Any,
    llm_model: str,
    kwargs: dict,
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
    thread_id = threading.current_thread().ident
    thread_name = threading.current_thread().name
    start_time = time.time()
    try:
        # Log when thread actually starts processing (not just when task is submitted)
        logger.info(
            f"[Thread {thread_id} ({thread_name})] START Processing image {idx}/{total_images}: {img_path.name} at {time.time():.3f}"
        )

        # Read image file
        with open(img_path, "rb") as img_file:
            img_stream = io.BytesIO(img_file.read())

        # Type comes from the file, not a fixed PNG label.
        img_stream_info = image_file_stream_info(img_path)

        # Generate description using LLM
        logger.debug(
            f"[Thread {thread_id}] Calling LLM API for image {idx}/{total_images}: {img_path.name}"
        )
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
        logger.debug(
            f"[Thread {thread_id}] COMPLETED image {idx}/{total_images} in {total_duration:.2f}s (API: {api_duration:.2f}s): {img_path.name}"
        )

        return description

    except Exception:
        # Re-raise exception to be handled by caller
        raise
