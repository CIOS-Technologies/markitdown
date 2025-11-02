# Plugin Development Guide

MarkItDown supports a flexible plugin system that allows developers to create custom document converters for unsupported file formats or specialized processing needs.

## 🔌 Plugin Architecture Overview

### Plugin Discovery

Plugins are discovered using Python's entry points mechanism. When MarkItDown initializes, it scans for registered converters and makes them available alongside the built-in converters.

### Plugin Interface

All plugins must implement the `DocumentConverter` interface:

```python
from markitdown._base_converter import DocumentConverter
from markitdown._stream_info import StreamInfo
from markitdown import DocumentConverterResult
import io
from typing import Any

class MyPluginConverter(DocumentConverter):
    def __init__(self):
        super().__init__()
        self.supported_file_types = [".custom", ".special"]
        self.priority = 50  # Lower number = higher priority

    def convert(
        self,
        stream: io.BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any
    ) -> DocumentConverterResult:
        """Convert document to Markdown."""
        # Implementation here
        pass
```

## 🛠️ Creating a Plugin

### Step 1: Project Structure

Create a new Python package for your plugin:

```
my-markitdown-plugin/
├── pyproject.toml
├── src/
│   └── my_markitdown_plugin/
│       ├── __init__.py
│       └── converter.py
└── README.md
```

### Step 2: Implement the Converter

```python
# src/my_markitdown_plugin/converter.py
from markitdown._base_converter import DocumentConverter
from markitdown._stream_info import StreamInfo
from markitdown import DocumentConverterResult
import io
import json
from typing import Any

class JsonConverter(DocumentConverter):
    """Convert JSON files to readable Markdown."""

    def __init__(self):
        super().__init__()
        self.supported_file_types = [".json"]
        self.priority = 50

    def convert(
        self,
        stream: io.BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any
    ) -> DocumentConverterResult:
        """Convert JSON to Markdown table/list format."""
        try:
            # Read JSON content
            content = stream.read().decode('utf-8')
            data = json.loads(content)

            # Convert to Markdown
            markdown_content = self._json_to_markdown(data)

            return DocumentConverterResult(
                text_content=markdown_content,
                title=getattr(data, 'title', 'JSON Document'),
                metadata={
                    'converter': 'JsonConverter',
                    'format': 'JSON',
                    'size': len(content)
                }
            )

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

    def _json_to_markdown(self, data: Any, level: int = 0) -> str:
        """Convert JSON data to Markdown format."""
        indent = "  " * level

        if isinstance(data, dict):
            result = []
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    result.append(f"{indent}**{key}:**")
                    result.append(self._json_to_markdown(value, level + 1))
                else:
                    result.append(f"{indent}**{key}:** {value}")
            return "\n".join(result)

        elif isinstance(data, list):
            result = []
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    result.append(f"{indent}{i + 1}.")
                    result.append(self._json_to_markdown(item, level + 1))
                else:
                    result.append(f"{indent}{i + 1}. {item}")
            return "\n".join(result)

        else:
            return f"{indent}{data}"
```

### Step 3: Register the Plugin

Create the `pyproject.toml` file:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-markitdown-plugin"
version = "0.1.0"
description = "Custom JSON converter for MarkItDown"
authors = [{name = "Your Name", email = "your.email@example.com"}]
license = {text = "MIT"}
requires-python = ">=3.10"
dependencies = ["markitdown"]

[project.entry-points."markitdown.converter"]
json_converter = "my_markitdown_plugin.converter:JsonConverter"
```

### Step 4: Package Metadata

```python
# src/my_markitdown_plugin/__init__.py
__version__ = "0.1.0"
__author__ = "Your Name"

from .converter import JsonConverter

__all__ = ["JsonConverter"]
```

## 📦 Installation and Usage

### Installing the Plugin

```bash
# Install from local directory
pip install -e /path/to/my-markitdown-plugin

# Install from PyPI (if published)
pip install my-markitdown-plugin
```

### Using the Plugin

```python
from markitdown import MarkItDown

# Enable plugins
md = MarkItDown(enable_plugins=True)

# Convert JSON file
result = md.convert("data.json")
print(result.text_content)
```

### CLI Usage

```bash
# List available plugins
markitdown --list-plugins

# Use plugins in CLI
markitdown data.json --use-plugins
```

## 🎯 Advanced Plugin Development

### Custom Dependencies

Your plugin can have its own dependencies:

```toml
[project]
dependencies = [
    "markitdown",
    "pandas>=1.0.0",
    "requests>=2.25.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=6.0.0",
    "black>=21.0.0"
]
```

### Configuration Options

Make your plugin configurable:

```python
class ConfigurableConverter(DocumentConverter):
    def __init__(self, max_depth: int = 10, include_metadata: bool = True):
        super().__init__()
        self.supported_file_types = [".yaml", ".yml"]
        self.priority = 50
        self.max_depth = max_depth
        self.include_metadata = include_metadata

    def convert(self, stream: io.BinaryIO, stream_info: StreamInfo, **kwargs):
        # Access configuration
        max_depth = kwargs.get('max_depth', self.max_depth)
        include_metadata = kwargs.get('include_metadata', self.include_metadata)

        # Convert with configuration
        pass
```

### Error Handling

Implement robust error handling:

```python
from markitdown._exceptions import FailedConversionAttempt

class RobustConverter(DocumentConverter):
    def convert(self, stream: io.BinaryIO, stream_info: StreamInfo, **kwargs):
        try:
            # Primary conversion method
            return self._primary_convert(stream, stream_info)
        except Exception as e:
            try:
                # Fallback method
                return self._fallback_convert(stream, stream_info)
            except Exception:
                # Raise specific exception
                raise FailedConversionAttempt(f"Conversion failed: {e}")
```

### Testing Your Plugin

Create comprehensive tests:

```python
# tests/test_converter.py
import unittest
import io
from my_markitdown_plugin.converter import JsonConverter
from markitdown._stream_info import StreamInfo

class TestJsonConverter(unittest.TestCase):
    def setUp(self):
        self.converter = JsonConverter()

    def test_simple_json(self):
        json_data = '{"name": "test", "value": 123}'
        stream = io.BytesIO(json_data.encode('utf-8'))
        stream_info = StreamInfo(stream=stream, filename="test.json")

        result = self.converter.convert(stream, stream_info)

        self.assertIn("**name:** test", result.text_content)
        self.assertIn("**value:** 123", result.text_content)
        self.assertEqual(result.metadata['converter'], 'JsonConverter')

    def test_nested_json(self):
        json_data = '{"user": {"name": "John", "age": 30}, "tags": ["a", "b"]}'
        stream = io.BytesIO(json_data.encode('utf-8'))
        stream_info = StreamInfo(stream=stream, filename="nested.json")

        result = self.converter.convert(stream, stream_info)

        self.assertIn("**user:**", result.text_content)
        self.assertIn("**name:** John", result.text_content)
        self.assertIn("1. a", result.text_content)

    def test_invalid_json(self):
        json_data = '{"invalid": json}'
        stream = io.BytesIO(json_data.encode('utf-8'))
        stream_info = StreamInfo(stream=stream, filename="invalid.json")

        with self.assertRaises(ValueError):
            self.converter.convert(stream, stream_info)

if __name__ == '__main__':
    unittest.main()
```

## 🚀 Publishing Your Plugin

### Prepare for Publication

1. **Update Metadata**:
```toml
[project]
name = "my-markitdown-plugin"
version = "0.1.0"
description = "A custom converter for MarkItDown"
readme = "README.md"
license = {text = "MIT"}
authors = [{name = "Your Name", email = "your.email@example.com"}]
keywords = ["markitdown", "converter", "json"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

[project.urls]
Homepage = "https://github.com/yourusername/my-markitdown-plugin"
Repository = "https://github.com/yourusername/my-markitdown-plugin"
Issues = "https://github.com/yourusername/my-markitdown-plugin/issues"
```

2. **Build the Package**:
```bash
pip install build
python -m build
```

3. **Publish to PyPI**:
```bash
pip install twine
twine upload dist/*
```

### Documentation

Create comprehensive documentation:

```markdown
# My MarkItDown Plugin

A custom JSON converter for MarkItDown that converts JSON files to readable Markdown format.

## Features

- Converts JSON objects and arrays to structured Markdown
- Preserves data hierarchy with indentation
- Handles nested structures
- Provides metadata about the conversion

## Installation

```bash
pip install my-markitdown-plugin
```

## Usage

### Python API

```python
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=True)
result = md.convert("data.json")
print(result.text_content)
```

### CLI

```bash
markitdown data.json --use-plugins
```

## Example

**Input JSON:**
```json
{
  "user": {
    "name": "John Doe",
    "age": 30,
    "hobbies": ["reading", "coding"]
  },
  "active": true
}
```

**Output Markdown:**
```markdown
**user:**
  **name:** John Doe
  **age:** 30
  **hobbies:**
    1. reading
    2. coding
**active:** true
```
```

## 🔧 Plugin Development Best Practices

### 1. Follow Naming Conventions

- Use descriptive converter names
- Follow Python package naming conventions
- Use semantic versioning

### 2. Handle Edge Cases

```python
def convert(self, stream: io.BinaryIO, stream_info: StreamInfo, **kwargs):
    # Validate stream
    if not stream.readable():
        raise ValueError("Stream is not readable")

    # Reset stream position
    stream.seek(0)

    # Handle empty files
    content = stream.read()
    if not content:
        return DocumentConverterResult(
            text_content="# Empty Document\n\nNo content found.",
            title="Empty Document"
        )

    # Process content
    # ...
```

### 3. Provide Metadata

```python
return DocumentConverterResult(
    text_content=markdown_content,
    title=document_title,
    metadata={
        'converter': 'MyConverter',
        'version': '1.0.0',
        'processing_time': processing_time,
        'file_size': len(content),
        'features': extracted_features
    }
)
```

### 4. Use Appropriate Priority

```python
class MyConverter(DocumentConverter):
    def __init__(self):
        super().__init__()
        self.supported_file_types = [".special"]
        self.priority = 45  # Higher priority than default (50)
        # Use lower priority if your converter is a fallback
```

### 5. Support Streaming

```python
def convert(self, stream: io.BinaryIO, stream_info: StreamInfo, **kwargs):
    # Process in chunks for large files
    chunk_size = 8192
    content_chunks = []

    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        content_chunks.append(chunk)

    content = b''.join(content_chunks)
    # Process content...
```

## 🐛 Debugging Plugins

### Enable Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
md = MarkItDown(enable_plugins=True)
```

### Test Plugin Registration

```python
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=True)

# List all available converters
for converter in md._converters:
    print(f"Converter: {converter.__class__.__name__}")
    print(f"  Priority: {getattr(converter, 'priority', 'N/A')}")
    print(f"  Types: {getattr(converter, 'supported_file_types', 'N/A')}")
```

### Manual Plugin Testing

```python
# Test plugin directly
from my_markitdown_plugin.converter import JsonConverter
from markitdown._stream_info import StreamInfo
import io

converter = JsonConverter()
json_data = '{"test": "data"}'
stream = io.BytesIO(json_data.encode('utf-8'))
stream_info = StreamInfo(stream=stream, filename="test.json")

result = converter.convert(stream, stream_info)
print(result.text_content)
```

## 📚 Sample Plugin Templates

### Simple Text Converter

```python
class SimpleTextConverter(DocumentConverter):
    """Convert plain text files with basic formatting."""

    def __init__(self):
        super().__init__()
        self.supported_file_types = [".txt"]
        self.priority = 100  # Low priority fallback

    def convert(self, stream: io.BinaryIO, stream_info: StreamInfo, **kwargs):
        content = stream.read().decode('utf-8', errors='replace')

        # Basic formatting
        lines = content.split('\n')
        formatted_lines = []

        for line in lines:
            if line.strip().endswith(':'):
                # Treat as heading
                formatted_lines.append(f"## {line.strip()}")
            else:
                formatted_lines.append(line)

        markdown_content = '\n'.join(formatted_lines)

        return DocumentConverterResult(
            text_content=markdown_content,
            title=stream_info.filename or "Text Document",
            metadata={'converter': 'SimpleTextConverter'}
        )
```

### API Data Converter

```python
import requests

class APIConverter(DocumentConverter):
    """Convert API responses to Markdown."""

    def __init__(self):
        super().__init__()
        self.supported_file_types = [".api"]  # Custom extension
        self.priority = 50

    def convert(self, stream: io.BinaryIO, stream_info: StreamInfo, **kwargs):
        content = stream.read().decode('utf-8')
        api_url = content.strip()

        try:
            response = requests.get(api_url)
            response.raise_for_status()

            # Convert JSON response to Markdown
            data = response.json()
            markdown_content = self._format_api_response(data, api_url)

            return DocumentConverterResult(
                text_content=markdown_content,
                title=f"API Response: {api_url}",
                metadata={
                    'converter': 'APIConverter',
                    'url': api_url,
                    'status_code': response.status_code
                }
            )

        except requests.RequestException as e:
            return DocumentConverterResult(
                text_content=f"# API Error\n\nFailed to fetch {api_url}: {e}",
                title="API Error",
                metadata={'converter': 'APIConverter', 'error': str(e)}
            )
```

This plugin development guide provides comprehensive information for creating, testing, and publishing custom MarkItDown converters, enabling developers to extend the system's capabilities for their specific document processing needs.