from typing import BinaryIO, Union, Optional
import base64
import mimetypes
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


def get_advanced_image_prompt(context_before: Optional[str] = None, context_after: Optional[str] = None) -> str:
    """Generate advanced prompt for image description with context awareness."""
    system_context = """You are an expert at analyzing business charts, diagrams, and visualizations for SaaS metrics and business analytics.

Your task is to create detailed, accessible text descriptions that will replace images in a text-only document.

IMPORTANT: SKIP the following types of images by responding with exactly "SKIP: [reason]":
- Navigation elements (buttons, menus, breadcrumbs, headers, footers)
- UI elements (icons, logos, decorative graphics, social media buttons)
- Call-to-action buttons or link graphics
- Page layout elements (dividers, backgrounds, borders)
- Non-content images

ONLY describe content-relevant visualizations such as:
- Charts (Line, Bar, Area, Pie, etc.)
- Graphs and plots
- Tables with data
- Diagrams (flowcharts, schematics, concept maps)
- Formulas and equations
- Screenshots of actual data/dashboards (not UI chrome)
- Infographics with business information

For valid content visualizations, the description MUST:
1. Start by identifying the TYPE (Line Graph, Bar Chart, Area Chart, Table, Diagram, Formula, Dashboard, etc.)
   - Be specific: "Line Graph" not just "Graph"
   - For cumulative metrics, note this explicitly
2. Describe what is being measured or visualized
3. Explain the key patterns, trends, or insights visible
4. Include specific data points, axes labels, and important values when present
5. Be comprehensive enough for someone listening via text-to-speech to fully understand

CRITICAL FORMATTING RULES:
- Write in the SAME LANGUAGE as the document text
- Do NOT include image URLs or file paths in your description
- Do NOT use phrases like "the image shows" - describe directly
- Write in clear, professional language

The surrounding document context is provided to help you understand what the visualization illustrates."""

    # Build user prompt with context
    context_parts = []
    if context_before:
        context_parts.append(f"DOCUMENT CONTEXT BEFORE:\n{context_before[:800]}")
    if context_after:
        context_parts.append(f"DOCUMENT CONTEXT AFTER:\n{context_after[:800]}")
    
    context_text = "\n\n".join(context_parts) if context_parts else ""
    
    user_prompt = f"""Analyze this image and determine if it's a content-relevant visualization or a UI/navigation element.

{context_text}

If it's a UI element, button, logo, or navigation graphic, respond with "SKIP: [brief reason]".

If it's a business chart, graph, table, diagram, or formula, provide a comprehensive description.
IMPORTANT: Write in the same language as the document text above. Do NOT include any URLs or image paths."""

    return system_context + "\n\n" + user_prompt


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
        Image description or None if failed
    """
    if not GEMINI_AVAILABLE:
        return None
    
    if client is None:
        return None
    
    try:
        # Read image data
        cur_pos = file_stream.tell()
        image_data = file_stream.read()
        file_stream.seek(cur_pos)
        
        # Load image with PIL
        img = Image.open(io.BytesIO(image_data))
        
        # Prepare prompt
        if prompt is None or prompt.strip() == "":
            if use_advanced_prompt:
                full_prompt = get_advanced_image_prompt(context_before, context_after)
            else:
                full_prompt = "Write a detailed caption for this image."
        else:
            # If custom prompt provided but context exists, append it
            if context_before or context_after:
                context_parts = []
                if context_before:
                    context_parts.append(f"Context before: {context_before[:400]}")
                if context_after:
                    context_parts.append(f"Context after: {context_after[:400]}")
                context_text = "\n\n".join(context_parts)
                full_prompt = f"{prompt}\n\n{context_text}"
            else:
                full_prompt = prompt
        
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
            
            description = response.text.strip()
            logger.debug(f"Received response from Gemini API for {image_filename} ({len(description)} chars)")
        except Exception as api_error:
            logger.warning(f"Gemini API call failed for {image_filename}: {str(api_error)}")
            raise
        
        # Check if Gemini skipped this image
        if description.upper().startswith("SKIP:"):
            return None
        
        return description
        
    except Exception as e:
        # Silently fail and return None (errors are handled gracefully)
        return None


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
) -> Union[None, str]:
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
        Image description or None if failed
    """
    if not GEMINI_AVAILABLE:
        return None
    
    if client is None:
        return None
    
    try:
        # Read image data
        cur_pos = file_stream.tell()
        image_data = file_stream.read()
        file_stream.seek(cur_pos)
        
        # Load image with PIL
        img = Image.open(io.BytesIO(image_data))
        
        # Prepare prompt
        if prompt is None or prompt.strip() == "":
            if use_advanced_prompt:
                full_prompt = get_advanced_image_prompt(context_before, context_after)
            else:
                full_prompt = "Write a detailed caption for this image."
        else:
            # If custom prompt provided but context exists, append it
            if context_before or context_after:
                context_parts = []
                if context_before:
                    context_parts.append(f"Context before: {context_before[:400]}")
                if context_after:
                    context_parts.append(f"Context after: {context_after[:400]}")
                context_text = "\n\n".join(context_parts)
                full_prompt = f"{prompt}\n\n{context_text}"
            else:
                full_prompt = prompt
        
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
            
            description = response.text.strip()
            logger.debug(f"Received async response from Gemini API for {image_filename} ({len(description)} chars)")
        except Exception as api_error:
            logger.warning(f"Gemini API async call failed for {image_filename}: {str(api_error)}")
            raise
        
        # Check if Gemini skipped this image
        if description.upper().startswith("SKIP:"):
            return None
        
        return description
        
    except Exception as e:
        # Silently fail and return None (errors are handled gracefully)
        logger.debug(f"Error in async image captioning for {stream_info.filename}: {e}")
        return None

