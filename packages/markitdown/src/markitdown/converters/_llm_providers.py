"""
LLM Provider abstraction layer for supporting multiple LLM providers (OpenAI, Gemini).
"""

from typing import BinaryIO, Union, Optional, Any
from .._stream_info import StreamInfo

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
        genai.configure(api_key=api_key)
        
        # Return a wrapper that provides the genai module interface
        class GeminiClientWrapper:
            def __init__(self):
                self.genai_module = genai
        return GeminiClientWrapper()
    except Exception:
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

