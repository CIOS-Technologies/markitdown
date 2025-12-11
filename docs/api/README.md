# API Reference

This section provides comprehensive documentation for the MarkItDown Python API and command-line interface.

## 🐍 Python API

### Core Classes

#### MarkItDown Class

The main orchestrator class for document conversion.

```python
from markitdown import MarkItDown

# Basic initialization
md = MarkItDown()

# With plugins enabled
md = MarkItDown(enable_plugins=True)

# With Azure Document Intelligence
md = MarkItDown(
    docintel_endpoint="https://your-resource.cognitiveservices.azure.com/",
    docintel_key="your-api-key"
)

# With LLM integration
from openai import OpenAI
client = OpenAI()
md = MarkItDown(
    llm_client=client,
    llm_model="gpt-4o",
    llm_prompt="Describe this image in detail"
)
```

**Constructor Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_plugins` | `bool` | `False` | Enable third-party plugins |
| `docintel_endpoint` | `str` | `None` | Azure Document Intelligence endpoint |
| `docintel_key` | `str` | `None` | Azure Document Intelligence API key |
| `llm_client` | `Any` | `None` | LLM client for image descriptions (OpenAI or Gemini) |
| `llm_model` | `str` | `None` | LLM model name |
| `llm_prompt` | `str` | `None` | Custom prompt for LLM descriptions |
| `gemini_api_key` | `str` | `None` | Google Gemini API key (alternative to llm_client) |

**convert() Method Parameters** (passed via `**kwargs`):

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_image_workers` | `int` | `20` | Maximum parallel workers for PDF image processing (1 = sequential) |
| `llm_prompt` | `str` | `None` | Custom prompt for LLM image descriptions |
| `llm_use_advanced_prompt` | `bool` | `True` | Use advanced context-aware prompts for images |

#### Main Methods

##### convert()

Convert a document to Markdown.

```python
def convert(
    self,
    source: Union[str, Path, BinaryIO],
    **kwargs: Any
) -> DocumentConverterResult:
    """Convert a document to Markdown.

    Args:
        source: File path, Path object, or binary stream
        **kwargs: Additional options passed to converters:
            - max_image_workers (int): Maximum parallel workers for PDF image processing (default: 20)
            - llm_prompt (str): Custom prompt for LLM image descriptions
            - llm_use_advanced_prompt (bool): Use advanced context-aware prompts (default: True)

    Returns:
        DocumentConverterResult with converted content and metadata

    Raises:
        FileConversionException: If conversion fails
        UnsupportedFormatException: If file type not supported
    """
```

**Usage Examples**:

```python
# Convert from file path
result = md.convert("document.pdf")
print(result.text_content)

# Convert from Path object
from pathlib import Path
result = md.convert(Path("presentation.pptx"))

# Convert from binary stream
with open("image.jpg", "rb") as stream:
    result = md.convert(stream)

# PDF with parallel image processing
md = MarkItDown(gemini_api_key="your-key", llm_model="gemini-2.5-flash")
result = md.convert("document.pdf", max_image_workers=20)  # Process 20 images in parallel
```

##### convert_stream()

Convert from a binary stream with explicit stream information.

```python
def convert_stream(
    self,
    stream: BinaryIO,
    stream_info: StreamInfo
) -> DocumentConverterResult:
    """Convert from a binary stream.

    Args:
        stream: Binary stream to convert
        stream_info: Stream information including file type

    Returns:
        DocumentConverterResult with converted content
    """
```

**Usage**:

```python
from markitdown import StreamInfo
import io

# Create stream from data
data = b"Hello, World!"
stream = io.BytesIO(data)

# Create stream info
stream_info = StreamInfo(stream=stream, filename="hello.txt")

# Convert
result = md.convert_stream(stream, stream_info)
```

### Result Classes

#### DocumentConverterResult

Contains the result of a document conversion.

```python
@dataclass
class DocumentConverterResult:
    """Result of document conversion."""

    text_content: str                    # Converted Markdown content
    title: Optional[str] = None          # Document title
    metadata: Dict[str, Any] = None      # Additional metadata
    references: List[str] = None         # Reference links/citations
    errors: List[str] = None             # Conversion errors/warnings
```

**Usage**:

```python
result = md.convert("document.pdf")

print("Content:", result.text_content)
print("Title:", result.title)
print("Metadata:", result.metadata)
print("References:", result.references)
print("Errors:", result.errors)
```

### Stream Information

#### StreamInfo Class

Provides information about the input stream.

```python
class StreamInfo:
    """Information about the input stream."""

    def __init__(
        self,
        stream: BinaryIO,
        filename: Optional[str] = None,
        uri: Optional[str] = None
    ):
        """Initialize stream information.

        Args:
            stream: Binary stream
            filename: Original filename (optional)
            uri: URI for remote resources (optional)
        """

    def get_filetype(self) -> str:
        """Get detected file type using Magika."""

    def get_mimetype(self) -> str:
        """Get MIME type."""

    def get_encoding(self) -> str:
        """Get character encoding."""
```

### Exception Classes

#### Exception Hierarchy

```python
class MarkItDownException(Exception):
    """Base exception for MarkItDown."""
    pass

class MissingDependencyException(MarkItDownException):
    """Raised when required dependency is missing."""
    pass

class FailedConversionAttempt(MarkItDownException):
    """Raised when conversion attempt fails."""
    pass

class FileConversionException(MarkItDownException):
    """Raised when file conversion fails completely."""
    pass

class UnsupportedFormatException(MarkItDownException):
    """Raised when file format is not supported."""
    pass
```

**Error Handling Example**:

```python
from markitdown import MarkItDown, UnsupportedFormatException, FileConversionException

md = MarkItDown()

try:
    result = md.convert("document.pdf")
    print(result.text_content)
except UnsupportedFormatException:
    print("File format not supported")
except FileConversionException as e:
    print(f"Conversion failed: {e}")
except MissingDependencyException as e:
    print(f"Missing dependency: {e}")
```

### Advanced Usage Patterns

#### Batch Processing

```python
from pathlib import Path
import glob

md = MarkItDown()

# Process multiple files
for file_path in glob.glob("documents/*.pdf"):
    try:
        result = md.convert(file_path)
        output_path = file_path.replace(".pdf", ".md")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.text_content)

        print(f"Converted: {file_path} -> {output_path}")
    except Exception as e:
        print(f"Failed to convert {file_path}: {e}")
```

#### Custom Error Handling

```python
from markitdown import MarkItDown
from markitdown._exceptions import *

class CustomConverter:
    def __init__(self):
        self.md = MarkItDown(enable_plugins=True)
        self.success_count = 0
        self.error_count = 0

    def convert_with_retry(self, file_path: str, max_retries: int = 3):
        """Convert with retry logic."""
        for attempt in range(max_retries):
            try:
                result = self.md.convert(file_path)
                self.success_count += 1
                return result
            except FailedConversionAttempt:
                if attempt == max_retries - 1:
                    self.error_count += 1
                    raise
                continue
            except (UnsupportedFormatException, MissingDependencyException):
                self.error_count += 1
                raise

    def get_stats(self):
        return {
            "success": self.success_count,
            "errors": self.error_count,
            "total": self.success_count + self.error_count
        }
```

#### Streaming Large Files

```python
import io
from markitdown import MarkItDown, StreamInfo

md = MarkItDown()

def process_large_file(file_path: str, chunk_size: int = 8192):
    """Process large files in chunks."""
    with open(file_path, "rb") as f:
        # Create stream info
        stream_info = StreamInfo(stream=f, filename=file_path)

        # Reset stream position
        f.seek(0)

        # Convert
        result = md.convert_stream(f, stream_info)
        return result
```

## 💻 Command Line Interface

### Basic Usage

```bash
# Basic conversion
markitdown input.pdf > output.md

# Specify output file
markitdown input.pdf -o output.md

# Convert from stdin
cat input.pdf | markitdown > output.md
```

### Advanced Options

#### Plugin Support

```bash
# List available plugins
markitdown --list-plugins

# Enable plugins
markitdown input.docx --use-plugins

# Enable specific plugins (if supported)
markitdown input.pdf --plugins my_plugin
```

#### Azure Document Intelligence

```bash
# Enable Azure Document Intelligence
markitdown scan.pdf -d -e "https://your-resource.cognitiveservices.azure.com/"

# With API key
markitdown scan.pdf -d -e "endpoint" -k "api-key"
```

#### Output Options

```bash
# Specify output file
markitdown input.pdf -o output.md

# Suppress warnings
markitdown input.pdf --quiet

# Verbose output
markitdown input.pdf --verbose

# Show version
markitdown --version
```

#### File Processing Options

```bash
# Process multiple files
markitdown file1.pdf file2.docx file3.pptx

# Process files from directory
markitdown documents/*.pdf

# Recursive processing (if supported)
markitdown -r documents/
```

### CLI Help

```bash
# Show main help
markitdown --help

# Show specific command help
markitdown convert --help
```

### CLI Exit Codes

| Exit Code | Meaning |
|-----------|---------|
| 0 | Success |
| 1 | General error |
| 2 | File not found |
| 3 | Unsupported format |
| 4 | Missing dependency |
| 5 | Conversion failed |

## 🔧 Configuration

### Environment Variables

```bash
# Azure Document Intelligence
export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://your-resource.cognitiveservices.azure.com/"
export AZURE_DOCUMENT_INTELLIGENCE_KEY="your-api-key"

# OpenAI API (for LLM integration)
export OPENAI_API_KEY="your-openai-api-key"

# Plugin paths (if applicable)
export MARKITDOWN_PLUGIN_PATH="/path/to/plugins"
```

### Configuration Files

MarkItDown supports configuration via environment variables and command-line parameters. There is no separate configuration file format.

## 📊 Performance Considerations

### Memory Usage

```python
# Stream-based processing for large files
import io

def convert_large_file_efficiently(file_path: str):
    with open(file_path, "rb") as stream:
        # Stream processing avoids loading entire file into memory
        result = md.convert_stream(stream, StreamInfo(stream=stream))
    return result
```

### Caching

```python
# Enable file type detection caching
md = MarkItDown()
# Magika results are cached automatically for performance
```

### Parallel Processing

```python
from concurrent.futures import ThreadPoolExecutor
import glob

def batch_convert_files(file_paths: list, max_workers: int = 4):
    """Convert multiple files in parallel."""
    md = MarkItDown()

    def convert_single(file_path: str):
        try:
            return {"file": file_path, "result": md.convert(file_path), "error": None}
        except Exception as e:
            return {"file": file_path, "result": None, "error": str(e)}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(convert_single, file_paths))

    return results

# Usage
files = glob.glob("documents/*.pdf")
results = batch_convert_files(files)
```

## 🧪 Testing

### Unit Testing

```python
import unittest
from markitdown import MarkItDown
from markitdown._exceptions import UnsupportedFormatException

class TestMarkItDown(unittest.TestCase):
    def setUp(self):
        self.md = MarkItDown()

    def test_pdf_conversion(self):
        result = self.md.convert("test.pdf")
        self.assertIsInstance(result.text_content, str)
        self.assertGreater(len(result.text_content), 0)

    def test_unsupported_format(self):
        with self.assertRaises(UnsupportedFormatException):
            self.md.convert("test.xyz")

if __name__ == "__main__":
    unittest.main()
```

### Integration Testing

```python
def test_end_to_end_conversion():
    """Test complete conversion workflow."""
    import tempfile
    import os

    # Create temporary files
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        # Write test PDF content
        tmp.write(test_pdf_data)
        tmp_path = tmp.name

    try:
        # Convert file
        md = MarkItDown()
        result = md.convert(tmp_path)

        # Verify output
        assert result.text_content
        assert isinstance(result.title, str)
        assert isinstance(result.metadata, dict)

    finally:
        # Cleanup
        os.unlink(tmp_path)
```

This API reference provides comprehensive coverage of the MarkItDown Python API and CLI interface, enabling developers to integrate document conversion capabilities into their applications effectively.