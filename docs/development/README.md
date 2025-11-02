# Development Guide

This guide covers everything you need to know to contribute to the MarkItDown project, from setting up your development environment to submitting pull requests.

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** - MarkItDown requires Python 3.10 or higher
- **Git** - For version control
- **Hatch** - Build system (recommended) or alternative Python packaging tools

### Environment Setup

```bash
# Clone the repository
git clone https://github.com/microsoft/markitdown.git
cd markitdown

# Navigate to main package
cd packages/markitdown

# Install hatch and create development environment
pip install hatch
hatch shell

# Alternative: Using uv
uv venv --python=3.12 .venv
source .venv/bin/activate
pip install -e '.[all]'
```

### Run Tests

```bash
# Run all tests
hatch test

# Run specific test file
hatch test tests/test_module_misc.py

# Run with coverage
hatch test --cover

# Run pre-commit checks
pre-commit run --all-files
```

## 🏗️ Project Structure

### Repository Layout

```
markitdown/
├── packages/
│   ├── markitdown/              # Main conversion engine
│   │   ├── src/markitdown/      # Source code
│   │   ├── tests/               # Test suite
│   │   ├── pyproject.toml       # Project configuration
│   │   └── README.md            # Package-specific README
│   ├── markitdown-mcp/          # MCP server
│   └── markitdown-sample-plugin/ # Plugin template
├── docs/                        # Documentation
├── .github/                     # GitHub workflows
├── .devcontainer/               # Development container
├── CODE_OF_CONDUCT.md           # Community guidelines
├── SECURITY.md                  # Security policy
└── README.md                    # Main project README
```

### Source Code Organization

```
src/markitdown/
├── __init__.py                  # Public API exports
├── _markitdown.py              # Main orchestrator class
├── _base_converter.py          # Converter base class
├── _stream_info.py             # Stream processing
├── _exceptions.py              # Exception definitions
├── _uri_utils.py               # URI parsing utilities
├── __main__.py                 # CLI entry point
├── converters/                 # Converter implementations
│   ├── __init__.py            # Converter registry
│   ├── _pdf_converter.py      # PDF conversion
│   ├── _docx_converter.py     # Word document conversion
│   ├── _pptx_converter.py     # PowerPoint conversion
│   └── ...                    # Other converters
└── converter_utils/            # Shared converter utilities
    ├── _exiftool.py           # EXIF metadata extraction
    ├── _llm_caption.py        # LLM integration
    ├── _markdownify.py        # HTML to Markdown conversion
    └── _transcribe_audio.py   # Audio transcription
```

## 🛠️ Development Workflow

### 1. Create a Feature Branch

```bash
# Create and checkout a new branch
git checkout -b feature/my-new-converter

# Or for bug fixes
git checkout -b fix/issue-description
```

### 2. Make Your Changes

- Add your converter implementation
- Write comprehensive tests
- Update documentation
- Follow code style guidelines

### 3. Run Tests and Checks

```bash
# Run the full test suite
hatch test

# Run pre-commit hooks
pre-commit run --all-files

# Type checking (optional)
hatch run types:check
```

### 4. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with clear message
git commit -m "feat: add new converter for XYZ format

- Implement XYZConverter class
- Add comprehensive test coverage
- Update documentation
- Add entry point registration

Closes #123"
```

### 5. Submit Pull Request

```bash
# Push to your fork
git push origin feature/my-new-converter

# Create pull request on GitHub
```

## 🧪 Testing

### Test Structure

```
tests/
├── test_module_misc.py          # General module tests
├── test_module_vectors.py       # Vector-based regression tests
├── test_cli_misc.py            # CLI interface tests
├── test_cli_vectors.py         # CLI regression tests
├── _test_vectors.py            # Test vector utilities
└── test_data/                  # Test data and fixtures
    ├── vectors/                # Known input/output pairs
    ├── samples/                # Sample files
    └── temp/                   # Temporary test files
```

### Writing Tests

#### Unit Tests

```python
# tests/test_my_converter.py
import unittest
import io
from markitdown import MarkItDown
from markitdown._stream_info import StreamInfo
from markitdown.converters._my_converter import MyConverter

class TestMyConverter(unittest.TestCase):
    def setUp(self):
        self.converter = MyConverter()
        self.md = MarkItDown()

    def test_basic_conversion(self):
        """Test basic file conversion."""
        # Create test data
        test_data = b"test content"
        stream = io.BytesIO(test_data)
        stream_info = StreamInfo(stream=stream, filename="test.xyz")

        # Convert
        result = self.converter.convert(stream, stream_info)

        # Assertions
        self.assertIsInstance(result.text_content, str)
        self.assertGreater(len(result.text_content), 0)
        self.assertEqual(result.metadata['converter'], 'MyConverter')

    def test_error_handling(self):
        """Test error handling for invalid input."""
        invalid_data = b"invalid content"
        stream = io.BytesIO(invalid_data)
        stream_info = StreamInfo(stream=stream, filename="invalid.xyz")

        # Should raise appropriate exception
        with self.assertRaises(ValueError):
            self.converter.convert(stream, stream_info)

    def test_integration(self):
        """Test integration with MarkItDown."""
        # Test using the main API
        result = self.md.convert("test_files/sample.xyz")
        self.assertIsInstance(result.text_content, str)

if __name__ == '__main__':
    unittest.main()
```

#### Vector Tests

Vector tests ensure consistent output for known inputs:

```python
# Add to _test_vectors.py
VECTOR_TEST_CASES = [
    TestCase(
        input_path="test_data/vectors/my_format/input.xyz",
        expected_output_path="test_data/vectors/my_format/expected.md",
        converter_class=MyConverter,
        description="My format basic conversion"
    ),
]
```

#### CLI Tests

```python
# tests/test_cli_my_converter.py
import subprocess
import tempfile
import os

class TestMyConverterCLI(unittest.TestCase):
    def test_cli_conversion(self):
        """Test CLI conversion of my format."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as tmp:
            # Write test data
            tmp.write(b"test content")
            tmp_path = tmp.name

        try:
            # Run CLI
            result = subprocess.run(
                ["markitdown", tmp_path],
                capture_output=True,
                text=True
            )

            # Verify
            self.assertEqual(result.returncode, 0)
            self.assertIn("expected output", result.stdout)

        finally:
            # Cleanup
            os.unlink(tmp_path)
```

### Running Tests

```bash
# Run all tests
hatch test

# Run specific test file
hatch test tests/test_my_converter.py

# Run with coverage
hatch test --cover

# Run with verbose output
hatch test -v

# Run specific test method
hatch test tests/test_my_converter.py::TestMyConverter::test_basic_conversion
```

## 📝 Code Style and Quality

### Pre-commit Hooks

The project uses pre-commit hooks to enforce code quality:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Code Formatting

- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting (if configured)

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Run linter
flake8 src/ tests/
```

### Type Hints

MarkItDown uses type hints throughout the codebase:

```python
from typing import Any, Dict, List, Optional, Union, BinaryIO
from pathlib import Path

class MyConverter(DocumentConverter):
    def convert(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any
    ) -> DocumentConverterResult:
        """Convert document to Markdown."""
        pass
```

### Documentation

All public methods and classes should have docstrings:

```python
class MyConverter(DocumentConverter):
    """Converter for XYZ format files.

    This converter processes XYZ format files and converts them to
    structured Markdown, preserving formatting and metadata.

    Attributes:
        supported_file_types: List of supported file extensions
        priority: Converter priority (lower number = higher priority)
    """

    def convert(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any
    ) -> DocumentConverterResult:
        """Convert XYZ file to Markdown.

        Args:
            stream: Binary stream containing file content
            stream_info: Stream information including file type
            **kwargs: Additional conversion options

        Returns:
            DocumentConverterResult with converted content

        Raises:
            ValueError: If file format is invalid
            UnsupportedFormatException: If file type not supported
        """
        pass
```

## 🔧 Adding New Converters

### 1. Create Converter File

```python
# src/markitdown/converters/_my_converter.py
from markitdown._base_converter import DocumentConverter
from markitdown._stream_info import StreamInfo
from markitdown import DocumentConverterResult
import io
from typing import Any

class MyConverter(DocumentConverter):
    """Converter for My Format files."""

    def __init__(self):
        super().__init__()
        self.supported_file_types = [".myf", ".myformat"]
        self.priority = 50

    def convert(
        self,
        stream: io.BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any
    ) -> DocumentConverterResult:
        """Convert My Format file to Markdown."""
        # Implementation here
        pass
```

### 2. Register Converter

Add to `src/markitdown/converters/__init__.py`:

```python
from ._my_converter import MyConverter

# Add to __all__
__all__ = [
    # ... existing converters ...
    "MyConverter",
]
```

Add to `src/markitdown/_markitdown.py` imports:

```python
from .converters import (
    # ... existing imports ...
    MyConverter,
)
```

Add to converter list initialization:

```python
self._converters = [
    # ... existing converters ...
    MyConverter(),
]
```

### 3. Add Dependencies

Update `pyproject.toml`:

```toml
[project.optional-dependencies]
myformat = ["my-format-library>=1.0.0"]
all = [
    # ... existing dependencies ...
    "my-format-library>=1.0.0"
]
```

### 4. Add Tests

Create `tests/test_my_converter.py` with comprehensive test coverage.

### 5. Update Documentation

- Add converter to documentation
- Update supported formats list
- Add usage examples

## 📦 Build and Distribution

### Building the Package

```bash
# Build source and wheel distributions
hatch build

# Build specific package
hatch build -t wheel  # wheel only
hatch build -t sdist  # source distribution only
```

### Local Installation

```bash
# Install in development mode
pip install -e '.[all]'

# Install from built distribution
pip install dist/markitdown-*.whl
```

### Publishing

The project uses automated releases via GitHub Actions. For manual testing:

```bash
# Install publish dependencies
pip install hatch-vcs twine

# Build with version from Git tags
hatch build

# Check package
twine check dist/*

# Upload to test PyPI
twine upload --repository testpypi dist/*

# Upload to PyPI (if permissions)
twine upload dist/*
```

## 🐛 Debugging

### Debug Mode

Enable debug logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

### Common Issues

#### Import Errors

```python
# Check if dependencies are installed
try:
    import required_library
except ImportError:
    raise MissingDependencyException("required_library is required for this converter")
```

#### Stream Issues

```python
# Always reset stream position
stream.seek(0)

# Check if stream is readable
if not stream.readable():
    raise ValueError("Stream is not readable")
```

#### File Type Detection

```python
# Debug file type detection
stream_info = StreamInfo(stream=stream, filename="test.xyz")
print(f"Detected file type: {stream_info.get_filetype()}")
print(f"MIME type: {stream_info.get_mimetype()}")
```

### Performance Profiling

```python
import cProfile
import pstats

# Profile conversion
def profile_conversion(file_path: str):
    md = MarkItDown()

    profiler = cProfile.Profile()
    profiler.enable()

    result = md.convert(file_path)

    profiler.disable()

    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions

    return result
```

## 🤝 Contributing Guidelines

### Code of Conduct

Please read and follow our [Code of Conduct](https://github.com/microsoft/markitdown/blob/main/CODE_OF_CONDUCT.md).

### Issue Reporting

When reporting issues, please include:

- **MarkItDown version**
- **Python version**
- **Operating system**
- **Minimal reproduction case**
- **Expected vs actual behavior**
- **Sample files** (if applicable)

### Pull Request Guidelines

#### Before Submitting

1. **Search existing PRs** - Avoid duplicate work
2. **Update documentation** - Include relevant documentation changes
3. **Add tests** - Ensure test coverage is maintained or improved
4. **Run tests** - All tests must pass
5. **Follow commit message conventions** - Use conventional commit format

#### Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(pdf): add support for encrypted PDFs

- Implement password handling for encrypted PDFs
- Add error handling for invalid passwords
- Update documentation with encryption examples

Closes #123
```

```
fix(docx): resolve issue with table formatting

- Correct table border handling in DOCX converter
- Add regression test for table formatting
- Update test vectors

Fixes #456
```

### Review Process

1. **Automated Checks** - CI/CD pipeline runs tests and quality checks
2. **Code Review** - Maintainers review code for quality and consistency
3. **Integration Testing** - Changes are tested with the full test suite
4. **Approval** - PR must be approved by at least one maintainer
5. **Merge** - PR is merged to main branch

### Release Process

The project follows semantic versioning:

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Releases are automated through GitHub Actions based on Git tags.

## 📚 Additional Resources

### Development Tools

- **Hatch** - Modern Python project management
- **Pre-commit** - Git pre-commit hooks
- **Black** - Code formatting
- **pytest** - Testing framework
- **mypy** - Type checking

### Documentation

- [Hatch Documentation](https://hatch.pypa.io/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [pytest Documentation](https://docs.pytest.org/)

### Community

- [GitHub Discussions](https://github.com/microsoft/markitdown/discussions)
- [GitHub Issues](https://github.com/microsoft/markitdown/issues)
- [Security Policy](https://github.com/microsoft/markitdown/blob/main/SECURITY.md)

This development guide provides comprehensive information for contributing to MarkItDown, ensuring high-quality contributions that follow project standards and best practices.