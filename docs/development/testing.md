# Testing Guide

This guide covers comprehensive testing strategies for the MarkItDown project, including unit tests, integration tests, and contribution guidelines for maintaining code quality.

## 🧪 Test Structure Overview

### Test Categories

```
tests/
├── test_module_misc.py          # General module functionality tests
├── test_module_vectors.py       # Vector-based regression tests
├── test_cli_misc.py            # CLI interface tests
├── test_cli_vectors.py         # CLI regression tests
├── _test_vectors.py            # Test vector utilities
└── test_data/                  # Test data and fixtures
    ├── vectors/                # Known input/output pairs
    ├── samples/                # Sample files for testing
    └── temp/                   # Temporary test files
```

### Test Types

1. **Unit Tests** - Individual component testing
2. **Integration Tests** - End-to-end workflow testing
3. **Vector Tests** - Regression testing with known outputs
4. **CLI Tests** - Command-line interface validation
5. **Performance Tests** - Resource usage and speed testing

## 🚀 Running Tests

### Basic Test Execution

```bash
# Navigate to main package directory
cd packages/markitdown

# Run all tests
hatch test

# Run specific test file
hatch test tests/test_module_misc.py

# Run with verbose output
hatch test -v

# Run with coverage
hatch test --cover
```

### Test Commands Reference

```bash
# Run tests with specific Python version
hatch test --python=3.12

# Run tests in parallel
hatch test --parallel

# Run only unit tests (skip CLI tests)
hatch test tests/test_module_*.py

# Run only CLI tests
hatch test tests/test_cli_*.py

# Run tests with specific pattern
hatch test -k "test_pdf"
```

### Pre-commit Testing

```bash
# Run all pre-commit checks
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
pre-commit run flake8 --all-files
```

## 📊 Test Coverage

### Coverage Analysis

```bash
# Generate coverage report
hatch test --cover

# Generate HTML coverage report
hatch test --cover --cover-html

# Show coverage summary
coverage report

# Show coverage for specific file
coverage report src/markitdown/_markitdown.py
```

### Coverage Targets

- **Overall Coverage**: Target >90%
- **Core Modules**: Target >95%
- **Converter Modules**: Target >85%

### Coverage Configuration

```toml
# pyproject.toml
[tool.coverage.run]
source_pkgs = ["markitdown", "tests"]
branch = true
parallel = true
omit = [
    "src/markitdown/__about__.py",
]

[tool.coverage.report]
exclude_lines = [
    "no cov",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

## 🔧 Test Data Management

### Test Vector Files

Test vectors contain known input/output pairs for regression testing:

```
test_data/vectors/
├── pdf/
│   ├── input1.pdf
│   ├── expected1.md
│   └── metadata1.json
├── docx/
│   ├── document.docx
│   ├── expected.md
│   └── metadata.json
└── images/
    ├── chart.png
    ├── expected.md
    └── metadata.json
```

### Adding Test Vectors

1. **Create test input file** in appropriate format
2. **Generate expected output** using current implementation
3. **Create metadata file** with test parameters
4. **Add to test registry** in `_test_vectors.py`

```python
# _test_vectors.py
VECTOR_TEST_CASES = [
    TestCase(
        input_path="test_data/vectors/pdf/sample.pdf",
        expected_output_path="test_data/vectors/pdf/expected.md",
        metadata_path="test_data/vectors/pdf/metadata.json",
        converter_class=PdfConverter,
        description="Basic PDF text extraction",
        tolerance=0.95  # 95% similarity tolerance
    ),
]
```

### Test Data Best Practices

- **Use minimal files** for faster testing
- **Include edge cases** (empty files, corrupted files)
- **Variety of formats** (different PDF versions, etc.)
- **Realistic content** but not copyrighted material
- **Consistent naming** convention

## 📝 Writing Tests

### Unit Test Template

```python
# tests/test_my_converter.py
import unittest
import tempfile
import os
from markitdown import MarkItDown
from markitdown._stream_info import StreamInfo
from markitdown.converters._my_converter import MyConverter

class TestMyConverter(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.converter = MyConverter()
        self.md = MarkItDown()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_basic_conversion(self):
        """Test basic file conversion."""
        # Create test input
        test_content = b"test content for conversion"
        test_file = os.path.join(self.temp_dir, "test.xyz")
        with open(test_file, "wb") as f:
            f.write(test_content)

        # Convert
        result = self.converter.convert(
            open(test_file, "rb"),
            StreamInfo(stream=open(test_file, "rb"), filename="test.xyz")
        )

        # Assertions
        self.assertIsInstance(result.text_content, str)
        self.assertGreater(len(result.text_content), 0)
        self.assertEqual(result.metadata["converter"], "MyConverter")

    def test_error_handling(self):
        """Test error handling for invalid input."""
        invalid_content = b"invalid content that causes error"
        test_file = os.path.join(self.temp_dir, "invalid.xyz")
        with open(test_file, "wb") as f:
            f.write(invalid_content)

        stream = open(test_file, "rb")
        stream_info = StreamInfo(stream=stream, filename="invalid.xyz")

        # Should raise appropriate exception
        with self.assertRaises(ValueError):
            self.converter.convert(stream, stream_info)

    def test_integration_with_markitdown(self):
        """Test integration with main MarkItDown class."""
        test_file = os.path.join(self.temp_dir, "test.xyz")
        with open(test_file, "wb") as f:
            f.write(b"test content")

        result = self.md.convert(test_file)
        self.assertIsInstance(result.text_content, str)

    def test_converter_priority(self):
        """Test converter priority registration."""
        self.assertEqual(self.converter.priority, 50)
        self.assertIn(".xyz", self.converter.supported_file_types)

if __name__ == "__main__":
    unittest.main()
```

### Parameterized Tests

```python
# tests/test_parameterized.py
import unittest
from markitdown import MarkItDown

class TestParameterizedConverters(unittest.TestCase):
    def setUp(self):
        self.md = MarkItDown()

    def test_text_formats(self):
        """Test various text format conversions."""
        test_cases = [
            ("simple.txt", "Hello World"),
            ("document.md", "# Title\n\nContent"),
            ("data.json", '{"key": "value"}'),
            ("config.xml", "<root><item>test</item></root>"),
        ]

        for filename, content in test_cases:
            with self.subTest(filename=filename):
                # Create temporary file
                with tempfile.NamedTemporaryFile(
                    mode='w', suffix=filename, delete=False
                ) as f:
                    f.write(content)
                    temp_file = f.name

                try:
                    result = self.md.convert(temp_file)
                    self.assertIsInstance(result.text_content, str)
                    self.assertGreater(len(result.text_content), 0)
                finally:
                    os.unlink(temp_file)

    @parameterized.expand([
        ("pdf", "test.pdf"),
        ("docx", "test.docx"),
        ("pptx", "test.pptx"),
    ])
    def test_document_formats(self, format_type, filename):
        """Test document format conversions."""
        # Implementation similar to above
        pass
```

### Mock Tests

```python
# tests/test_with_mocks.py
import unittest
from unittest.mock import Mock, patch, MagicMock
from markitdown import MarkItDown

class TestWithMocks(unittest.TestCase):
    @patch('markitdown.converters._pdf_converter.pdfminer')
    def test_pdf_conversion_with_mock(self, mock_pdfminer):
        """Test PDF conversion with mocked dependencies."""
        # Setup mock
        mock_pdfminer.extract_text.return_value = "Extracted PDF text"

        # Test
        md = MarkItDown()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"mock pdf content")
            temp_file = f.name

        try:
            result = md.convert(temp_file)
            self.assertIn("Extracted PDF text", result.text_content)
        finally:
            os.unlink(temp_file)

    def test_llm_integration_with_mock(self):
        """Test LLM integration with mocked client."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices[0].message.content = "Image description"
        mock_client.chat.completions.create.return_value = mock_response

        md = MarkItDown(llm_client=mock_client, llm_model="gpt-4o")

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"mock image content")
            temp_file = f.name

        try:
            result = md.convert(temp_file)
            mock_client.chat.completions.create.assert_called_once()
            self.assertIn("Image description", result.text_content)
        finally:
            os.unlink(temp_file)
```

## 🔍 Integration Testing

### End-to-End Test Template

```python
# tests/test_integration.py
import unittest
import tempfile
import os
from markitdown import MarkItDown
from markitdown._exceptions import *

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.md = MarkItDown()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_workflow(self):
        """Test complete document processing workflow."""
        # Create test document
        test_content = """# Test Document

This is a test document with various content types.

## Section 1
Some text content.

## Section 2
- Item 1
- Item 2
- Item 3

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |
"""

        test_file = os.path.join(self.temp_dir, "test.md")
        with open(test_file, "w") as f:
            f.write(test_content)

        # Process document
        result = self.md.convert(test_file)

        # Verify results
        self.assertIsInstance(result.text_content, str)
        self.assertIn("Test Document", result.text_content)
        self.assertIn("Section 1", result.text_content)

        # Test metadata
        self.assertIsInstance(result.metadata, dict)
        if result.title:
            self.assertIsInstance(result.title, str)

    def test_error_recovery_workflow(self):
        """Test error handling and recovery."""
        # Test with non-existent file
        with self.assertRaises(FileNotFoundError):
            self.md.convert("non_existent_file.pdf")

        # Test with unsupported format
        unsupported_file = os.path.join(self.temp_dir, "test.xyz")
        with open(unsupported_file, "w") as f:
            f.write("unsupported content")

        with self.assertRaises(UnsupportedFormatException):
            self.md.convert(unsupported_file)

    def test_plugin_integration(self):
        """Test plugin system integration."""
        md_with_plugins = MarkItDown(enable_plugins=True)

        # Test plugin discovery and loading
        # (Depends on available plugins)
        if hasattr(md_with_plugins, '_plugins'):
            self.assertIsInstance(md_with_plugins._plugins, list)
```

### Performance Tests

```python
# tests/test_performance.py
import unittest
import time
import tempfile
import os
from markitdown import MarkItDown

class TestPerformance(unittest.TestCase):
    def setUp(self):
        self.md = MarkItDown()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_conversion_speed(self):
        """Test conversion speed benchmarks."""
        # Create test files of different sizes
        test_sizes = [1024, 10240, 102400]  # 1KB, 10KB, 100KB

        for size in test_sizes:
            with self.subTest(size=size):
                # Create test file
                test_content = "Test content\n" * (size // 15)
                test_file = os.path.join(self.temp_dir, f"test_{size}.txt")

                with open(test_file, "w") as f:
                    f.write(test_content)

                # Measure conversion time
                start_time = time.time()
                result = self.md.convert(test_file)
                conversion_time = time.time() - start_time

                # Verify reasonable performance
                self.assertLess(conversion_time, 5.0)  # Should complete within 5 seconds
                self.assertGreater(len(result.text_content), size // 2)  # Reasonable output

                # Calculate throughput
                throughput = size / conversion_time
                self.assertGreater(throughput, 1000)  # At least 1KB/second

    def test_memory_usage(self):
        """Test memory usage during conversion."""
        import psutil
        import gc

        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Process several files
        for i in range(10):
            test_file = os.path.join(self.temp_dir, f"test_{i}.txt")
            with open(test_file, "w") as f:
                f.write("Test content " * 1000)

            result = self.md.convert(test_file)
            del result  # Explicit cleanup

        gc.collect()  # Force garbage collection
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (< 100MB)
        self.assertLess(memory_increase, 100 * 1024 * 1024)
```

## 🔧 Test Utilities

### Custom Assertions

```python
# tests/utils.py
import difflib
import re

class MarkitdownTestCase(unittest.TestCase):
    """Custom test case with MarkItDown-specific assertions."""

    def assertMarkdownSimilar(self, expected: str, actual: str, tolerance: float = 0.95):
        """Assert two Markdown strings are similar within tolerance."""
        # Normalize whitespace
        expected_norm = re.sub(r'\s+', ' ', expected.strip())
        actual_norm = re.sub(r'\s+', ' ', actual.strip())

        # Calculate similarity
        similarity = difflib.SequenceMatcher(None, expected_norm, actual_norm).ratio()

        self.assertGreaterEqual(
            similarity, tolerance,
            f"Markdown similarity {similarity:.3f} below threshold {tolerance}"
        )

    def assertConversionSuccess(self, result):
        """Assert conversion result is successful."""
        self.assertIsNotNone(result)
        self.assertIsInstance(result.text_content, str)
        self.assertGreater(len(result.text_content), 0)

    def assertMetadataValid(self, metadata):
        """Assert metadata is valid."""
        self.assertIsInstance(metadata, dict)
        # Check for required metadata fields
        if metadata:
            for key, value in metadata.items():
                self.assertIsInstance(key, str)
```

### Test Data Generators

```python
# tests/generators.py
import tempfile
import os
import json
from pathlib import Path

class TestDataGenerator:
    """Generate test data for various formats."""

    @staticmethod
    def create_text_file(content: str, filename: str = None) -> str:
        """Create temporary text file."""
        if filename is None:
            fd, path = tempfile.mkstemp(suffix=".txt")
            os.close(fd)
        else:
            path = filename

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return path

    @staticmethod
    def create_json_file(data: dict, filename: str = None) -> str:
        """Create temporary JSON file."""
        if filename is None:
            fd, path = tempfile.mkstemp(suffix=".json")
            os.close(fd)
        else:
            path = filename

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return path

    @staticmethod
    def create_markdown_file(title: str, sections: list, filename: str = None) -> str:
        """Create temporary Markdown file."""
        content = f"# {title}\n\n"

        for section in sections:
            content += f"## {section['title']}\n\n"
            content += f"{section['content']}\n\n"

        return TestDataGenerator.create_text_file(content, filename)

# Usage in tests
from tests.generators import TestDataGenerator

class TestMyConverter(unittest.TestCase):
    def test_with_generated_data(self):
        """Test using generated test data."""
        # Create test file
        test_file = TestDataGenerator.create_json_file({
            "title": "Test Document",
            "content": "Test content"
        })

        try:
            result = self.md.convert(test_file)
            self.assertIn("Test Document", result.text_content)
        finally:
            os.unlink(test_file)
```

## 🐛 Debugging Tests

### Test Debugging Techniques

```python
# tests/test_debug.py
import unittest
import logging
import tempfile
import os
from markitdown import MarkItDown

class TestDebug(unittest.TestCase):
    def setUp(self):
        # Enable debug logging
        logging.basicConfig(level=logging.DEBUG)
        self.md = MarkItDown()
        self.temp_dir = tempfile.mkdtemp()

    def test_debug_conversion(self):
        """Debug conversion process."""
        # Create test file
        test_file = os.path.join(self.temp_dir, "debug_test.txt")
        with open(test_file, "w") as f:
            f.write("Debug test content")

        print(f"Test file: {test_file}")
        print(f"File exists: {os.path.exists(test_file)}")
        print(f"File size: {os.path.getsize(test_file)}")

        # Enable detailed logging in MarkItDown
        import markitdown
        markitdown.logger.setLevel(logging.DEBUG)

        try:
            result = self.md.convert(test_file)
            print(f"Conversion successful: {len(result.text_content)} chars")
            print(f"First 100 chars: {result.text_content[:100]}")
        except Exception as e:
            print(f"Conversion failed: {e}")
            print(f"Exception type: {type(e)}")
            raise
```

### Test Output Analysis

```bash
# Run specific test with maximum verbosity
python -m pytest tests/test_module_misc.py::TestPdfConverter::test_pdf_conversion -v -s

# Run with custom output
python -m pytest tests/ -v --tb=short --color=yes

# Generate test report
python -m pytest tests/ --html=test_report.html --self-contained-html
```

## 📋 Continuous Integration

### GitHub Actions Test Configuration

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: [3.10, 3.11, 3.12]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install hatch
        hatch env create

    - name: Run tests
      run: |
        cd packages/markitdown
        hatch test

    - name: Generate coverage report
      run: |
        cd packages/markitdown
        hatch test --cover

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./packages/markitdown/coverage.xml
```

### Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 22.12.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings]

  - repo: local
    hooks:
      - id: run-tests
        name: Run tests
        entry: bash -c 'cd packages/markitdown && hatch test'
        language: system
        pass_filenames: false
```

## 📊 Test Metrics and Reporting

### Test Result Analysis

```python
# scripts/analyze_test_results.py
import subprocess
import json
import re

def run_tests_and_analyze():
    """Run tests and analyze results."""
    # Run tests with JSON output
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/", "--json-report", "--json-report-file=test_results.json"],
        capture_output=True,
        text=True
    )

    # Analyze results
    with open("test_results.json") as f:
        test_results = json.load(f)

    summary = test_results.get("summary", {})

    print(f"Test Summary:")
    print(f"  Total: {summary.get('total', 0)}")
    print(f"  Passed: {summary.get('passed', 0)}")
    print(f"  Failed: {summary.get('failed', 0)}")
    print(f"  Skipped: {summary.get('skipped', 0)}")
    print(f"  Duration: {summary.get('duration', 0):.2f}s")

    # Analyze failing tests
    failed_tests = [test for test in test_results.get("tests", []) if test.get("outcome") == "failed"]
    if failed_tests:
        print(f"\nFailing Tests:")
        for test in failed_tests:
            print(f"  - {test['nodeid']}: {test.get('call', {}).get('crash', {}).get('message', 'Unknown error')}")

if __name__ == "__main__":
    run_tests_and_analyze()
```

## 🚀 Contributing Tests

### Test Contribution Guidelines

When contributing to MarkItDown:

1. **Write tests for new features** - Aim for >90% coverage
2. **Include regression tests** - For bug fixes
3. **Add test vectors** - For new converter functionality
4. **Update documentation** - Include testing instructions
5. **Run full test suite** - Before submitting PR

### Test Naming Conventions

```python
# Use descriptive test names
def test_pdf_conversion_with_tables_and_images(self):
    pass

def test_error_handling_for_corrupted_docx_files(self):
    pass

def test_plugin_discovery_and_registration(self):
    pass
```

### Test Documentation

```python
def test_complex_pdf_conversion(self):
    """Test conversion of PDF with multiple columns, tables, and images.

    This test verifies:
    - Multi-column layout preservation
    - Table extraction accuracy
    - Image metadata extraction
    - Proper heading hierarchy

    Related issue: #123
    """
    # Test implementation
    pass
```

This comprehensive testing guide provides the foundation for maintaining high code quality in the MarkItDown project through systematic testing practices and robust test infrastructure.