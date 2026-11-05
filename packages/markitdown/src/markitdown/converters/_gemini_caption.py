from typing import BinaryIO, Optional, Union
from dataclasses import dataclass
import logging
from PIL import Image
import io
import asyncio
from .._stream_info import StreamInfo

# Set up logging for Gemini captioning
logger = logging.getLogger(__name__)

# Try to import Gemini SDK
GEMINI_AVAILABLE = False
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    pass


@dataclass(frozen=True)
class CaptionOutcome:
    """What one caption call produced.

    skipped is a model answer of the form "SKIP: reason".
    failed is an exception or an empty answer. They are not the same.
    """

    status: str
    description: Optional[str] = None
    reason: Optional[str] = None


# Same rules for the advanced prompt, the short prompt, and the OpenAI path.
# Decorative images are the only ones we drop. A screenshot or mockup is content.
_SKIP_RULE = """Skip ONLY decorative images. For those, respond with exactly "SKIP: [reason]".
Skip: logos, icons, bullet markers, dividers, backgrounds, borders, and purely decorative stock photos.
Describe every other image. Screenshots, UI mockups, wireframes, org charts, slides, and photos that carry information are content, not decoration."""

_QUALITY_RULES = """The description MUST:
1. Start by naming the TYPE (screenshot, mockup, wireframe, chart, diagram, table, photo, org chart, slide, or another specific type).
2. For a screenshot or mockup, name the screen and what it shows, including the visible text and values that matter.
3. For a chart or diagram, include the patterns and the important labels and values.
4. Use the SAME LANGUAGE as the document text.
5. Do NOT use phrases like "the image shows".
6. Do NOT include image URLs or file paths.
7. Write in clear, professional language."""


def _context_block(
    context_before: Optional[str],
    context_after: Optional[str],
    *,
    limit: int,
) -> str:
    """Surrounding document text, already clipped."""
    parts = []
    if context_before:
        parts.append(f"DOCUMENT CONTEXT BEFORE:\n{context_before[:limit]}")
    if context_after:
        parts.append(f"DOCUMENT CONTEXT AFTER:\n{context_after[:limit]}")
    return "\n\n".join(parts)


def get_advanced_image_prompt(context_before: Optional[str] = None, context_after: Optional[str] = None) -> str:
    """Full prompt. Same skip policy as the short prompt, with more guidance."""
    context_text = _context_block(context_before, context_after, limit=800)
    return f"""You write detailed descriptions that replace images in a text-only document.

{_SKIP_RULE}

{_QUALITY_RULES}
Be specific and complete enough that a reader who cannot see the image still understands it.

{context_text}

Describe the image, or reply "SKIP: [brief reason]" when it is only decorative.
Write in the same language as the document text above. Do NOT include any URLs or image paths."""


def get_short_image_prompt(context_before: Optional[str] = None, context_after: Optional[str] = None) -> str:
    """Shorter prompt. The skip list and the quality rules match the advanced prompt."""
    context_text = _context_block(context_before, context_after, limit=800)
    return f"""Describe this image for a text-only document.

{_SKIP_RULE}

{_QUALITY_RULES}

{context_text}"""


def compose_image_prompt(
    prompt: Optional[str],
    context_before: Optional[str],
    context_after: Optional[str],
    use_advanced_prompt: bool,
) -> str:
    """Pick the prompt for one caption call.

    A caller-supplied prompt is kept. Surrounding text is appended, which is
    what the Gemini path already did. The default prompts share one policy.
    """
    if prompt is not None and prompt.strip():
        extra = _context_block(context_before, context_after, limit=400)
        if extra:
            # Custom prompts used a "Context before" label. Keep that shape.
            lines = []
            if context_before:
                lines.append(f"Context before: {context_before[:400]}")
            if context_after:
                lines.append(f"Context after: {context_after[:400]}")
            return prompt + "\n\n" + "\n\n".join(lines)
        return prompt
    if use_advanced_prompt:
        return get_advanced_image_prompt(context_before, context_after)
    return get_short_image_prompt(context_before, context_after)


def classify_model_text(text: Optional[str], filename: str) -> CaptionOutcome:
    """Turn the model text into described, skipped, or failed.

    A skip is logged at INFO with the file name and the model's reason.
    An empty answer is a failure, not a skip.
    """
    name = filename or "unknown"
    if text is None or not str(text).strip():
        return CaptionOutcome("failed", reason="empty response")
    stripped = str(text).strip()
    if stripped.upper().startswith("SKIP:"):
        reason = stripped.split(":", 1)[1].strip() or "unspecified"
        logger.info(f"Skipped image {name}: {reason}")
        return CaptionOutcome("skipped", reason=reason)
    return CaptionOutcome("described", description=stripped)


def gemini_caption(
    file_stream: BinaryIO,
    stream_info: StreamInfo,
    *,
    client,
    model: str = "gemini-2.5-flash",
    prompt: Optional[str] = None,
    context_before: Optional[str] = None,
    context_after: Optional[str] = None,
    use_advanced_prompt: bool = True,
) -> Union[None, str]:
    """Description text, or None when the image was skipped or the call failed.

    The outcome, including a skip reason, is available from gemini_caption_outcome.
    """
    outcome = gemini_caption_outcome(
        file_stream,
        stream_info,
        client=client,
        model=model,
        prompt=prompt,
        context_before=context_before,
        context_after=context_after,
        use_advanced_prompt=use_advanced_prompt,
    )
    if outcome.status == "described":
        return outcome.description
    return None


def gemini_caption_outcome(
    file_stream: BinaryIO,
    stream_info: StreamInfo,
    *,
    client,
    model: str = "gemini-2.5-flash",
    prompt: Optional[str] = None,
    context_before: Optional[str] = None,
    context_after: Optional[str] = None,
    use_advanced_prompt: bool = True,
) -> CaptionOutcome:
    """
    Generate image caption using Google Gemini Vision API.

    Args:
        file_stream: Binary image stream
        stream_info: Stream metadata
        client: Gemini client (genai.Client instance)
        model: Gemini model name (default: gemini-2.5-flash)
        prompt: Custom prompt (if None, uses advanced prompt)
        context_before: Text context before image in document
        context_after: Text context after image in document
        use_advanced_prompt: If True, use enhanced prompt with context awareness

    Returns:
        described, skipped, or failed. A skip has already been logged.
    """
    if not GEMINI_AVAILABLE:
        return CaptionOutcome("failed", reason="gemini unavailable")

    if client is None:
        return CaptionOutcome("failed", reason="no client")
    
    try:
        # Read image data
        cur_pos = file_stream.tell()
        image_data = file_stream.read()
        file_stream.seek(cur_pos)
        
        # Load image with PIL
        img = Image.open(io.BytesIO(image_data))
        
        full_prompt = compose_image_prompt(
            prompt, context_before, context_after, use_advanced_prompt
        )

        # Get genai module from client wrapper or use directly
        # NOTE: Python modules are singletons, so importing again won't help
        # The issue is that genai.configure() sets up a shared HTTP session with connection pool limits
        # We need to work with the shared module but ensure each thread can make concurrent requests
        if hasattr(client, 'genai_module'):
            genai_module = client.genai_module
        else:
            import google.generativeai as genai_module
        
        # NOTE: Connection pool configuration is attempted in create_gemini_client()
        # The genai module uses a shared HTTP session with connection pool limits
        # If you're seeing only 5 threads active despite 20 workers, it's likely due to:
        # 1. Default connection pool limit in the underlying HTTP client
        # 2. API rate limiting
        # 3. Shared HTTP session across all threads
        # 
        # The connection pool is configured when the client is created, but if the genai
        # module was already configured earlier in the process, that configuration may not apply
        
        # Call Gemini API using google.generativeai
        # Create model and generate content
        # Create a new model instance for each call to ensure thread safety
        image_filename = stream_info.filename or "unknown"
        logger.debug(f"Calling Gemini API (model: {model}) for image: {image_filename}")
        
        # Create model instance - this should be thread-safe when each thread creates its own
        gemini_model = genai_module.GenerativeModel(model)
        
        generation_config = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        try:
            response = gemini_model.generate_content(
                [full_prompt, img],
                generation_config=generation_config
            )
            
            description = (response.text or "").strip()
            logger.debug(f"Received response from Gemini API for {image_filename} ({len(description)} chars)")
        except Exception as api_error:
            logger.warning(f"Gemini API call failed for {image_filename}: {str(api_error)}")
            raise

        return classify_model_text(description, image_filename)

    except Exception as e:
        # The API warning was already logged. This is a failed caption, not a skip.
        logger.debug(f"Error in image captioning for {stream_info.filename}: {e}")
        return CaptionOutcome("failed", reason=str(e))


async def gemini_caption_async(
    file_stream: BinaryIO,
    stream_info: StreamInfo,
    *,
    client,
    model: str = "gemini-2.5-flash",
    prompt: Optional[str] = None,
    context_before: Optional[str] = None,
    context_after: Optional[str] = None,
    use_advanced_prompt: bool = True,
) -> CaptionOutcome:
    """
    Generate image caption using Google Gemini Vision API (async version for true parallelism).
    
    Args:
        file_stream: Binary image stream
        stream_info: Stream metadata
        client: Gemini client (genai.Client instance)
        model: Gemini model name (default: gemini-2.5-flash)
        prompt: Custom prompt (if None, uses advanced prompt)
        context_before: Text context before image in document
        context_after: Text context after image in document
        use_advanced_prompt: If True, use enhanced prompt with context awareness
    
    Returns:
        described, skipped, or failed. A skip has already been logged.
    """
    if not GEMINI_AVAILABLE:
        return CaptionOutcome("failed", reason="gemini unavailable")

    if client is None:
        return CaptionOutcome("failed", reason="no client")
    
    try:
        # Read image data
        cur_pos = file_stream.tell()
        image_data = file_stream.read()
        file_stream.seek(cur_pos)
        
        # Load image with PIL
        img = Image.open(io.BytesIO(image_data))
        
        full_prompt = compose_image_prompt(
            prompt, context_before, context_after, use_advanced_prompt
        )

        # Get genai module from client wrapper or use directly
        if hasattr(client, 'genai_module'):
            genai_module = client.genai_module
        else:
            import google.generativeai as genai_module
        
        # Call Gemini API using async method for true parallelism
        image_filename = stream_info.filename or "unknown"
        logger.debug(f"Calling Gemini API async (model: {model}) for image: {image_filename}")
        
        # Create model instance
        gemini_model = genai_module.GenerativeModel(model)
        
        generation_config = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        try:
            # Use async API for true parallelism
            response = await gemini_model.generate_content_async(
                [full_prompt, img],
                generation_config=generation_config
            )
            
            description = (response.text or "").strip()
            logger.debug(f"Received async response from Gemini API for {image_filename} ({len(description)} chars)")
        except Exception as api_error:
            logger.warning(f"Gemini API async call failed for {image_filename}: {str(api_error)}")
            raise

        return classify_model_text(description, image_filename)

    except Exception as e:
        # The API warning was already logged. This is a failed caption, not a skip.
        logger.debug(f"Error in async image captioning for {stream_info.filename}: {e}")
        return CaptionOutcome("failed", reason=str(e))

