"""Gemini tests moved out of test_module_misc.py.

These tests belong to the fork. They used to live in the upstream misc module.
Keeping them here means the next upstream sync can take that file as-is.
The original test bodies are unchanged. A later test covers SKIP: answers.
"""

import os
from unittest.mock import MagicMock

import pytest

from markitdown import MarkItDown

# Don't run the gemini tests without a key and the client library
skip_gemini = False if os.environ.get("GEMINI_API_KEY") else True
try:
    import google.generativeai as genai
except ModuleNotFoundError:
    skip_gemini = True

TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test_files")


@pytest.mark.skipif(
    skip_gemini,
    reason="do not run gemini tests without a key",
)
def test_markitdown_gemini_client_creation() -> None:
    """Test that Gemini client can be created from API key."""
    from markitdown.converters._llm_providers import create_gemini_client
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")
    
    client = create_gemini_client(api_key)
    assert client is not None
    assert hasattr(client, "genai_module")


@pytest.mark.skipif(
    skip_gemini,
    reason="do not run gemini tests without a key",
)
def test_markitdown_gemini_provider_detection() -> None:
    """Test that provider detection correctly identifies Gemini clients."""
    from markitdown.converters._llm_providers import detect_provider, create_gemini_client
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")
    
    gemini_client = create_gemini_client(api_key)
    assert gemini_client is not None
    
    provider = detect_provider(gemini_client)
    assert provider == "gemini"


@pytest.mark.skipif(
    skip_gemini,
    reason="do not run gemini tests without a key",
)
def test_markitdown_gemini_image_caption() -> None:
    """Test Gemini image captioning with a real image file."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")
    
    markitdown = MarkItDown(gemini_api_key=api_key, llm_model="gemini-2.5-flash")
    
    # Test with image file - conversion should not raise exceptions
    # Note: Image converter may return empty if both exiftool metadata and LLM description fail
    # This test primarily verifies that Gemini integration doesn't crash
    result = markitdown.convert(os.path.join(TEST_FILES_DIR, "test_llm.jpg"))
    
    # Verify conversion completed without exceptions
    assert result is not None
    assert isinstance(result.text_content, str)
    
    # If we got content, verify it has meaningful structure
    # Some images may not have metadata or LLM may fail, so empty content is acceptable
    if len(result.text_content) > 0:
        # Should have either metadata fields or description if content exists
        assert (
            "Description:" in result.text_content 
            or "ImageSize:" in result.text_content
            or "Title:" in result.text_content
            or len(result.text_content.split()) > 5
        ), f"Expected meaningful content: {result.text_content[:300]}"


@pytest.mark.skipif(
    skip_gemini,
    reason="do not run gemini tests without a key",
)
def test_markitdown_gemini_image_caption_with_custom_prompt() -> None:
    """Test Gemini image captioning with a custom prompt."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")
    
    custom_prompt = "Describe this image focusing on colors and shapes."
    markitdown = MarkItDown(
        gemini_api_key=api_key,
        llm_model="gemini-2.5-flash",
        llm_prompt=custom_prompt
    )
    
    result = markitdown.convert(os.path.join(TEST_FILES_DIR, "test_llm.jpg"))
    
    # Verify description was generated
    assert "Description:" in result.text_content or len(result.text_content) > 100


@pytest.mark.skipif(
    skip_gemini,
    reason="do not run gemini tests without a key",
)
def test_markitdown_gemini_pdf_image_extraction() -> None:
    """Test PDF image extraction and description with Gemini."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")
    
    # Check if pymupdf4llm is available (should be if pdf dependencies are installed)
    try:
        import pymupdf4llm
    except ImportError:
        pytest.skip("pymupdf4llm not installed - install with 'pip install markitdown[pdf]' or 'pip install markitdown[all]'")
    
    markitdown = MarkItDown(gemini_api_key=api_key, llm_model="gemini-2.5-flash")
    
    # Test with PDF that has images
    test_pdf = os.path.join(TEST_FILES_DIR, "test_image.pdf")
    if not os.path.exists(test_pdf):
        pytest.skip("test_image.pdf not found")
    
    result = markitdown.convert(test_pdf)
    
    # Verify PDF was converted
    assert len(result.text_content) > 0
    
    # Check if AI descriptions were generated (if PDF had extractable images)
    # The marker indicates Gemini processed images
    has_ai_descriptions = "**[AI-Generated Image Description]**" in result.text_content
    
    if has_ai_descriptions:
        # Verify description content
        desc_marker_index = result.text_content.find("**[AI-Generated Image Description]**")
        # Should have substantial content after marker
        assert desc_marker_index >= 0
        # Description should be meaningful (not just a few words)
        desc_section = result.text_content[desc_marker_index:desc_marker_index + 500]
        assert len(desc_section.split()) > 10


@pytest.mark.skipif(
    skip_gemini,
    reason="do not run gemini tests without a key",
)
def test_markitdown_gemini_pptx_with_context() -> None:
    """Test Gemini integration with PPTX files using slide context."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")
    
    markitdown = MarkItDown(gemini_api_key=api_key, llm_model="gemini-2.5-flash")
    
    result = markitdown.convert(os.path.join(TEST_FILES_DIR, "test.pptx"))
    
    # Verify PPTX was converted
    assert len(result.text_content) > 0
    
    # Verify content structure is maintained
    assert "Slide" in result.text_content or "#" in result.text_content


def test_markitdown_gemini_provider_detection_openai() -> None:
    """Test that provider detection correctly identifies OpenAI clients."""
    from markitdown.converters._llm_providers import detect_provider
    
    mock_openai_client = MagicMock()
    mock_openai_client.chat = MagicMock()
    mock_openai_client.chat.completions = MagicMock()
    
    provider = detect_provider(mock_openai_client)
    assert provider == "openai"


def test_markitdown_gemini_caption_with_mock() -> None:
    """Test Gemini caption functionality with mocked client."""
    from markitdown.converters._gemini_caption import gemini_caption
    from markitdown._stream_info import StreamInfo
    from unittest.mock import Mock, patch
    import io
    
    # Create a mock Gemini client
    mock_client = Mock()
    mock_genai_module = Mock()
    mock_model = Mock()
    mock_response = Mock()
    mock_response.text = "Test image description: red circle and blue square"
    
    mock_model.generate_content.return_value = mock_response
    mock_genai_module.GenerativeModel.return_value = mock_model
    mock_client.genai_module = mock_genai_module
    
    # Create test image stream
    from PIL import Image as PILImage
    img = PILImage.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    stream_info = StreamInfo(extension='.png', mimetype='image/png')
    
    # Test caption generation
    description = gemini_caption(
        img_bytes,
        stream_info,
        client=mock_client,
        model="gemini-2.5-flash",
        use_advanced_prompt=False  # Use simple prompt for testing
    )
    
    assert description is not None
    assert "Test image description" in description
    mock_model.generate_content.assert_called_once()


def test_gemini_skip_answer_is_logged_with_its_reason(caplog) -> None:
    """A SKIP: body is not a description and not a silent failure."""
    import io
    from unittest.mock import Mock
    from markitdown.converters._gemini_caption import gemini_caption
    from markitdown._stream_info import StreamInfo
    from PIL import Image as PILImage

    mock_client = Mock()
    mock_model = Mock()
    mock_response = Mock()
    mock_response.text = "SKIP: decorative logo"
    mock_model.generate_content.return_value = mock_response
    mock_client.genai_module = Mock()
    mock_client.genai_module.GenerativeModel.return_value = mock_model

    img = PILImage.new("RGB", (8, 8), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    with caplog.at_level("INFO"):
        description = gemini_caption(
            img_bytes,
            StreamInfo(extension=".png", mimetype="image/png", filename="mark.png"),
            client=mock_client,
            model="gemini-2.5-flash",
        )

    assert description is None
    skip_lines = [
        record.message
        for record in caplog.records
        if record.levelname == "INFO" and record.message.startswith("Skipped image ")
    ]
    assert len(skip_lines) == 1
    assert "mark.png" in skip_lines[0]
    assert "decorative logo" in skip_lines[0]


def test_markitdown_gemini_context_extraction() -> None:
    """Test context extraction from PDF markdown."""
    from markitdown.converters._pdf_converter import PdfConverter
    
    converter = PdfConverter()
    
    # Sample markdown with image reference
    markdown_text = """
    This is some text before the image.
    
    ![Chart](images/chart1.png)
    
    This is some text after the image.
    """
    
    context_before, context_after = converter._extract_image_context(markdown_text, "chart1.png")
    
    assert context_before is not None
    assert context_after is not None
    assert "before" in context_before.lower()
    assert "after" in context_after.lower()


def test_markitdown_gemini_image_replacement() -> None:
    """Test replacement of image references with descriptions (description + original link kept)."""
    from markitdown.converters._pdf_converter import PdfConverter

    converter = PdfConverter()

    markdown_text = "![Chart](images/chart1.png)"
    descriptions = {"chart1.png": "This is a bar chart showing quarterly sales data."}

    result = converter._replace_images_with_descriptions(markdown_text, descriptions)

    assert "**[AI-Generated Image Description]**" in result
    assert "bar chart" in result.lower()
    # Converter keeps the original image link after the description so they stay together
    assert "![Chart](images/chart1.png)" in result


@pytest.mark.skipif(
    skip_gemini,
    reason="do not run gemini tests without a key",
)
def test_markitdown_gemini_environment_variable() -> None:
    """Test that Gemini client can be created from environment variable."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")
    
    # Create MarkItDown without explicit API key (should use env var)
    markitdown = MarkItDown(llm_model="gemini-2.5-flash")
    
    # Verify client was created
    assert markitdown._llm_client is not None
    assert markitdown._llm_model == "gemini-2.5-flash"
