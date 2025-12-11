"""
LLM Provider abstraction layer for supporting multiple LLM providers (OpenAI, Gemini).
"""

from typing import BinaryIO, Union, Optional, Any
from .._stream_info import StreamInfo

# Try to patch httpx BEFORE importing genai, so the patch is in place when genai creates its client
# This ensures the connection pool is configured correctly for parallel requests
# We do this in a try-except to avoid breaking imports if httpx isn't available
_httpx_patched = False
try:
    import httpx
    if not hasattr(httpx, '_markitdown_limits_patched'):
        # Store original __init__ methods
        if not hasattr(httpx.Client, '_original_init'):
            httpx.Client._original_init = httpx.Client.__init__
        if not hasattr(httpx.AsyncClient, '_original_init'):
            httpx.AsyncClient._original_init = httpx.AsyncClient.__init__
        
        # Patch httpx.Client to use higher connection limits by default
        # Also override any explicit limits that are too low
        def patched_client_init(self, *args, **kwargs):
            # Always set high connection limits, even if limits are explicitly provided
            # This ensures google.generativeai gets high limits even if it passes explicit low limits
            kwargs['limits'] = httpx.Limits(
                max_connections=20,
                max_keepalive_connections=20
            )
            return httpx.Client._original_init(self, *args, **kwargs)
        
        def patched_async_client_init(self, *args, **kwargs):
            # Always set high connection limits, even if limits are explicitly provided
            kwargs['limits'] = httpx.Limits(
                max_connections=20,
                max_keepalive_connections=20
            )
            return httpx.AsyncClient._original_init(self, *args, **kwargs)
        
        httpx.Client.__init__ = patched_client_init
        httpx.AsyncClient.__init__ = patched_async_client_init
        httpx._markitdown_limits_patched = True
        _httpx_patched = True
except ImportError:
    # httpx not available, skip patching
    pass
except Exception:
    # If patching fails, continue - genai might not use httpx
    # Don't let this break the module import
    # We can't use logging here as it might not be configured yet
    pass

# Try to detect provider availability
OPENAI_AVAILABLE = False
GEMINI_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    pass

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    pass


def detect_provider(client: Any) -> str:
    """
    Detect which LLM provider the client is for.
    
    Args:
        client: LLM client instance
        
    Returns:
        "openai", "gemini", or "unknown"
    """
    if client is None:
        return "unknown"
    
    # Check for OpenAI client
    if hasattr(client, "chat") and hasattr(client.chat, "completions"):
        return "openai"
    
    # Check for Gemini client wrapper (has genai_module attribute)
    if hasattr(client, "genai_module"):
        return "gemini"
    
    # Check for Gemini GenerativeModel directly
    client_type = str(type(client))
    if "generative" in client_type.lower() or "gemini" in client_type.lower():
        return "gemini"
    
    # Try to detect by type name (heuristic)
    client_type = str(type(client))
    if "openai" in client_type.lower():
        return "openai"
    if "gemini" in client_type.lower() or "generativeai" in client_type.lower():
        return "gemini"
    
    return "unknown"


def create_gemini_client(api_key: Optional[str] = None) -> Optional[Any]:
    """
    Create and return a Gemini client instance.
    
    Args:
        api_key: Gemini API key (if None, tries to get from environment)
        
    Returns:
        Gemini client or None if unavailable
    """
    if not GEMINI_AVAILABLE:
        return None
    
    try:
        import google.generativeai as genai
        import os
        
        if api_key is None:
            api_key = os.getenv("GEMINI_API_KEY")
        
        if api_key is None:
            return None
        
        # Configure Gemini
        # IMPORTANT: genai.configure() sets up a global HTTP client (httpx) with connection pool
        # The httpx client is created with default limits when genai.configure() is called
        # We need to configure httpx limits BEFORE calling genai.configure()
        # 
        # Check if genai is already configured (client already created)
        genai_already_configured = hasattr(genai, '_client') and genai._client is not None
        
        # httpx should already be patched at module import time (see top of file)
        # But if genai was already configured before our module was imported, we need to handle it
        try:
            import httpx
            httpx_patched = hasattr(httpx, '_markitdown_limits_patched')
        except ImportError:
            httpx_patched = False
        
        # If genai was already configured, try to clear and reconfigure with patched httpx
        if genai_already_configured:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Gemini was already configured - attempting to reconfigure with higher connection limits")
            try:
                # Clear the existing client if possible
                if hasattr(genai, '_client'):
                    genai._client = None
            except Exception as e:
                logger.debug(f"Could not clear existing genai client: {e}")
        
        genai.configure(api_key=api_key)
        
        # Log configuration status
        import logging
        logger = logging.getLogger(__name__)
        try:
            import httpx
            httpx_patched = hasattr(httpx, '_markitdown_limits_patched')
        except ImportError:
            httpx_patched = False
        
        if httpx_patched:
            if genai_already_configured:
                logger.info("Reconfigured Gemini - httpx.Client patched for 20 concurrent connections")
            else:
                logger.info("Gemini configured - httpx.Client patched for 20 concurrent connections")
            
            # Try to verify the actual httpx client limits
            try:
                import httpx
                if hasattr(genai, '_client') and genai._client is not None:
                    client = genai._client
                    if isinstance(client, httpx.Client):
                        if hasattr(client, '_limits'):
                            limits = client._limits
                            logger.info(f"Gemini httpx client limits: max_connections={limits.max_connections}, max_keepalive={limits.max_keepalive_connections}")
                        elif hasattr(client, '_transport') and hasattr(client._transport, '_pool'):
                            pool = client._transport._pool
                            if hasattr(pool, '_max_connections'):
                                logger.info(f"Gemini httpx pool max_connections: {pool._max_connections}")
            except Exception as e:
                logger.debug(f"Could not verify httpx client limits: {e}")
        else:
            logger.warning("httpx.Client not patched - connection pool may use default limits (~2-5 connections)")
        
        # Return a wrapper that provides the genai module interface
        class GeminiClientWrapper:
            def __init__(self):
                self.genai_module = genai
        return GeminiClientWrapper()
    except Exception as e:
        # Log the error but don't break the module import
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create Gemini client: {e}", exc_info=True)
        return None


def caption_image(
    file_stream: BinaryIO,
    stream_info: StreamInfo,
    *,
    client: Any,
    model: str,
    prompt: Optional[str] = None,
    context_before: Optional[str] = None,
    context_after: Optional[str] = None,
    use_advanced_prompt: bool = True,
) -> Union[None, str]:
    """
    Unified interface for image captioning across different LLM providers.
    
    Args:
        file_stream: Binary image stream
        stream_info: Stream metadata
        client: LLM client (OpenAI or Gemini)
        model: Model name
        prompt: Custom prompt
        context_before: Text context before image
        context_after: Text context after image
        use_advanced_prompt: Whether to use advanced prompt (Gemini only)
        
    Returns:
        Image description or None if failed
    """
    provider = detect_provider(client)
    
    if provider == "openai":
        from ._llm_caption import llm_caption
        # OpenAI doesn't support context yet, so ignore context_before/context_after
        return llm_caption(
            file_stream=file_stream,
            stream_info=stream_info,
            client=client,
            model=model,
            prompt=prompt,
        )
    
    elif provider == "gemini":
        from ._gemini_caption import gemini_caption
        return gemini_caption(
            file_stream=file_stream,
            stream_info=stream_info,
            client=client,
            model=model,
            prompt=prompt,
            context_before=context_before,
            context_after=context_after,
            use_advanced_prompt=use_advanced_prompt,
        )
    
    else:
        # Unknown provider, try OpenAI format as fallback
        try:
            from ._llm_caption import llm_caption
            return llm_caption(
                file_stream=file_stream,
                stream_info=stream_info,
                client=client,
                model=model,
                prompt=prompt,
            )
        except Exception:
            return None

