# Build System Guide

This guide covers the Hatch build system used in MarkItDown, including package configuration, dependency management, and distribution processes.

## 🏗️ Build System Overview

MarkItDown uses [Hatch](https://hatch.pypa.io/) as its primary build system. Hatch is a modern, extensible Python project manager that handles:

- **Environment Management** - Isolated development environments
- **Dependency Management** - Optional dependencies and feature groups
- **Build Process** - Package creation and distribution
- **Testing Integration** - Test running and coverage
- **Publishing** - Automated PyPI releases

## 📦 Project Structure

### Monorepo Layout

```
markitdown/
├── packages/
│   ├── markitdown/              # Main package
│   │   ├── pyproject.toml       # Package configuration
│   │   ├── src/markitdown/      # Source code
│   │   └── tests/               # Test suite
│   ├── markitdown-mcp/          # MCP server package
│   └── markitdown-sample-plugin/ # Sample plugin
├── docs/                        # Documentation
└── scripts/                     # Build utilities
```

### Package Configuration

Each package has its own `pyproject.toml` configuration:

```toml
# packages/markitdown/pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "markitdown"
dynamic = ["version"]
description = 'Utility tool for converting various files to Markdown'
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
keywords = ["document", "conversion", "markdown", "llm"]
authors = [
    { name = "Adam Fourney", email = "adamfo@microsoft.com" },
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
]
dependencies = [
    "beautifulsoup4",
    "requests",
    "markdownify",
    "magika~=0.6.1",
    "charset-normalizer",
    "defusedxml",
    "onnxruntime<=1.20.1; sys_platform == 'win32'",
]

[project.optional-dependencies]
all = [
    "python-pptx",
    "mammoth~=1.11.0",
    "pandas",
    "openpyxl",
    "xlrd",
    "lxml",
    "pdfminer.six",
    "olefile",
    "pydub",
    "SpeechRecognition",
    "youtube-transcript-api~=1.0.0",
    "azure-ai-documentintelligence",
    "azure-identity"
]
# ... other feature groups

[project.urls]
Documentation = "https://github.com/microsoft/markitdown#readme"
Issues = "https://github.com/microsoft/markitdown/issues"
Source = "https://github.com/microsoft/markitdown"

[project.scripts]
markitdown = "markitdown.__main__:main"

[tool.hatch.version]
path = "src/markitdown/__about__.py"

[tool.hatch.envs.default]
features = ["all"]

[tool.hatch.envs.hatch-test]
features = ["all"]
extra-dependencies = [
    "openai",
]

[tool.hatch.envs.types]
features = ["all"]
extra-dependencies = [
    "openai",
    "mypy>=1.0.0",
]

[tool.hatch.build.targets.sdist]
only-include = ["src/markitdown"]
```

## 🚀 Development Environment Setup

### Using Hatch

```bash
# Navigate to package directory
cd packages/markitdown

# Create development environment
hatch env create

# Activate environment
hatch shell

# Or run commands in environment
hatch run python --version
hatch run pip list
```

### Environment Configuration

```toml
# pyproject.toml
[tool.hatch.envs.default]
description = "Default development environment"
features = ["all"]
dependencies = [
    "black",      # Code formatting
    "isort",      # Import sorting
    "flake8",     # Linting
    "mypy",       # Type checking
]

[tool.hatch.envs.test]
description = "Testing environment"
features = ["all"]
extra-dependencies = [
    "pytest>=6.0.0",
    "pytest-cov",
    "pytest-xdist",
]

[tool.hatch.envs.docs]
description = "Documentation environment"
dependencies = [
    "mkdocs>=1.4.0",
    "mkdocs-material>=8.0.0",
    "mkdocstrings[python]>=0.18.0",
]
```

### Custom Scripts

```toml
# pyproject.toml
[tool.hatch.scripts]
fmt = [
    "black src tests",
    "isort src tests"
]
lint = [
    "flake8 src tests",
    "mypy src"
]
test = "pytest tests/ --cov=src/markitdown"
test-fast = "pytest tests/ -x -v"
docs = "mkdocs serve"
build-docs = "mkdocs build"
```

Usage:

```bash
# Run custom scripts
hatch run fmt
hatch run lint
hatch run test
hatch run docs
```

## 📚 Dependency Management

### Core Dependencies

Core dependencies are always installed:

```toml
[project]
dependencies = [
    "beautifulsoup4",      # HTML parsing
    "requests",            # HTTP requests
    "markdownify",         # HTML to Markdown
    "magika~=0.6.1",      # File type detection
    "charset-normalizer",  # Character encoding
    "defusedxml",          # Safe XML parsing
    "onnxruntime<=1.20.1; sys_platform == 'win32'",  # Windows OCR
]
```

### Optional Dependencies

Optional dependencies are organized by feature:

```toml
[project.optional-dependencies]
# Complete installation
all = [
    "python-pptx",
    "mammoth~=1.11.0",
    "pandas",
    "openpyxl",
    "xlrd",
    "lxml",
    "pdfminer.six",
    "olefile",
    "pydub",
    "SpeechRecognition",
    "youtube-transcript-api~=1.0.0",
    "azure-ai-documentintelligence",
    "azure-identity"
]

# Document processing
documents = [
    "python-pptx",         # PowerPoint
    "mammoth~=1.11.0",     # Word documents
    "pdfminer.six",        # PDF files
    "olefile",             # Outlook messages
]

# Spreadsheet processing
spreadsheets = [
    "pandas",
    "openpyxl",            # Modern Excel
    "xlrd",                # Legacy Excel
]

# Media processing
media = [
    "pydub",               # Audio processing
    "SpeechRecognition",   # Speech-to-text
]

# Web content
web = [
    "youtube-transcript-api~=1.0.0",  # YouTube transcripts
]

# Azure integration
azure = [
    "azure-ai-documentintelligence",
    "azure-identity"
]
```

### Development Dependencies

```toml
[tool.hatch.envs.hatch-test]
features = ["all"]
extra-dependencies = [
    "pytest>=6.0.0",
    "pytest-cov",
    "pytest-xdist",
    "openai",              # For LLM integration tests
]

[tool.hatch.envs.types]
features = ["all"]
extra-dependencies = [
    "openai",
    "mypy>=1.0.0",
    "types-requests",
    "types-beautifulsoup4",
]
```

## 🔧 Build Process

### Local Development Build

```bash
# Navigate to package directory
cd packages/markitdown

# Build source and wheel distributions
hatch build

# Build specific target
hatch build -t wheel    # Wheel only
hatch build -t sdist    # Source distribution only

# Clean build artifacts
hatch clean
```

### Version Management

MarkItDown uses dynamic versioning from `__about__.py`:

```python
# src/markitdown/__about__.py
__version__ = "0.0.7"
__version_tuple__ = (0, 0, 7)
```

Version configuration:

```toml
[tool.hatch.version]
path = "src/markitdown/__about__.py"

# Or use Git tags for versioning
[tool.hatch.version]
source = "vcs"
tag-pattern = "^(?P<version>\\d+\\.\\d+\\.\\d+)$"
```

### Build Configuration

```toml
[tool.hatch.build.targets.sdist]
only-include = ["src/markitdown"]
include = [
    "/src/markitdown/**/*.py",
    "/src/markitdown/py.typed",
]

[tool.hatch.build.targets.wheel]
packages = ["src/markitdown"]
```

## 🚀 Distribution and Publishing

### Local Installation Testing

```bash
# Build package
hatch build

# Install from built distribution
pip install dist/markitdown-*.whl --force-reinstall

# Test installation
python -c "import markitdown; print(markitdown.__version__)"

# Test CLI
markitdown --version
```

### Test PyPI Publishing

```bash
# Install Twine
pip install twine

# Build package
hatch build

# Check package
twine check dist/*

# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ markitdown
```

### Production Publishing

Automated through GitHub Actions:

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install Hatch
      run: pip install hatch

    - name: Build package
      run: |
        cd packages/markitdown
        hatch build

    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: |
        pip install twine
        twine upload packages/markitdown/dist/*
```

## 🔧 Advanced Configuration

### Cross-Package Dependencies

For packages that depend on each other:

```toml
# packages/markitdown-mcp/pyproject.toml
[project]
dependencies = [
    "markitdown>=0.0.7",  # Dependency on main package
    "mcp>=1.0.0",
]

[tool.hatch.envs.test]
extra-dependencies = [
    "markitdown @ file://../markitdown",  # Local development dependency
]
```

### Custom Build Hooks

```python
# scripts/build_hooks.py
import os
import subprocess
from pathlib import Path

def pre_build_hook(config):
    """Custom pre-build hook."""
    print("Running pre-build hook...")

    # Generate version file
    version = get_version_from_git()
    write_version_file(version)

    # Run tests
    subprocess.run(["hatch", "test"], check=True)

def post_build_hook(config):
    """Custom post-build hook."""
    print("Running post-build hook...")

    # Validate built package
    validate_package()

# pyproject.toml
[tool.hatch.build.hooks]
pre-build = "scripts.build_hooks:pre_build_hook"
post-build = "scripts.build_hooks:post_build_hook"
```

### Environment Matrix Testing

```bash
# Test across multiple Python versions
for version in 3.10 3.11 3.12; do
    echo "Testing Python $version"
    hatch env create --python=$version
    hatch run python=$version -m pytest tests/
done

# Test across different dependency combinations
hatch env create --feature=documents
hatch run -e documents pytest tests/

hatch env create --feature=media
hatch run -e media pytest tests/
```

## 🔍 Build Troubleshooting

### Common Build Issues

#### Dependency Conflicts

```bash
# Check for conflicts
hatch dep show

# Resolve conflicts by updating pyproject.toml
# Use compatible version ranges
dependencies = [
    "requests>=2.25.0,<3.0.0",
    "beautifulsoup4>=4.9.0,<5.0.0",
]
```

#### Build Failures

```bash
# Clean build artifacts
hatch clean
rm -rf dist/ build/ *.egg-info/

# Rebuild
hatch build --verbose

# Check build logs
hatch build --verbose 2>&1 | tee build.log
```

#### Version Issues

```bash
# Check version source
hatch version show

# Set version manually
hatch version set 0.0.8

# Or update __about__.py directly
echo '__version__ = "0.0.8"' > src/markitdown/__about__.py
```

### Performance Optimization

#### Parallel Testing

```bash
# Run tests in parallel
hatch run pytest -n auto tests/

# Configure parallel execution
[tool.hatch.envs.test]
extra-dependencies = [
    "pytest-xdist",
]

[tool.pytest.ini_options]
addopts = "-n auto"
```

#### Incremental Builds

```bash
# Use Hatch's incremental build features
hatch build --incremental

# Or use build caching
export HATCH_CACHE_DIR=/path/to/cache
hatch build
```

## 📊 Build Metrics and Monitoring

### Build Performance Tracking

```python
# scripts/build_metrics.py
import time
import subprocess
from pathlib import Path

def track_build_performance():
    """Track build performance metrics."""
    start_time = time.time()

    # Run build
    result = subprocess.run(
        ["hatch", "build"],
        capture_output=True,
        text=True
    )

    build_time = time.time() - start_time

    # Calculate package size
    dist_dir = Path("dist")
    total_size = sum(f.stat().st_size for f in dist_dir.rglob("*") if f.is_file())

    metrics = {
        "build_time": build_time,
        "package_size": total_size,
        "success": result.returncode == 0,
        "artifacts": list(dist_dir.rglob("*"))
    }

    print(f"Build Metrics:")
    print(f"  Time: {build_time:.2f}s")
    print(f"  Size: {total_size / 1024 / 1024:.2f}MB")
    print(f"  Success: {metrics['success']}")

    return metrics

if __name__ == "__main__":
    track_build_performance()
```

### Dependency Analysis

```bash
# Analyze dependency tree
hatch dep tree

# Check for unused dependencies
pip install pipdeptree
hatch run pipdeptree

# Security vulnerability scan
pip install safety
hatch run safety check
```

## 🔄 Continuous Integration Build

### GitHub Actions Build Configuration

```yaml
# .github/workflows/build.yml
name: Build and Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  build:
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

    - name: Install Hatch
      run: pip install hatch

    - name: Cache Hatch environments
      uses: actions/cache@v3
      with:
        path: ~/.local/share/hatch
        key: ${{ runner.os }}-hatch-${{ hashFiles('**/pyproject.toml') }}
        restore-keys: |
          ${{ runner.os }}-hatch-

    - name: Build package
      run: |
        cd packages/markitdown
        hatch build

    - name: Run tests
      run: |
        cd packages/markitdown
        hatch test

    - name: Upload build artifacts
      uses: actions/upload-artifact@v3
      with:
        name: dist-${{ matrix.os }}-${{ matrix.python-version }}
        path: packages/markitdown/dist/
```

### Pre-release Build Validation

```bash
# scripts/validate_release.sh
#!/bin/bash
set -e

echo "🔍 Validating release build..."

# Clean environment
hatch clean
rm -rf dist/

# Build package
echo "📦 Building package..."
hatch build

# Check package integrity
echo "✅ Checking package integrity..."
python -m twine check dist/*

# Test installation
echo "🧪 Testing installation..."
pip install dist/markitdown-*.whl --force-reinstall

# Test basic functionality
echo "🔧 Testing basic functionality..."
python -c "
import markitdown
md = markitdown.MarkItDown()
print('✅ Import successful')
print(f'Version: {markitdown.__version__}')
"

# Test CLI
echo "💻 Testing CLI..."
markitdown --version

echo "✅ Release validation complete!"
```

## 📚 Best Practices

### 1. Dependency Management

- **Pin critical dependencies** for reproducible builds
- **Use version ranges** for compatibility
- **Group optional dependencies** logically
- **Document optional features** clearly

### 2. Build Optimization

- **Use incremental builds** for faster development
- **Cache dependencies** in CI/CD pipelines
- **Parallel test execution** where possible
- **Clean build artifacts** regularly

### 3. Version Management

- **Use semantic versioning** (MAJOR.MINOR.PATCH)
- **Update version automatically** from Git tags
- **Document breaking changes** in release notes
- **Maintain backward compatibility** when possible

### 4. Release Process

- **Automate releases** through CI/CD
- **Test thoroughly** before publishing
- **Validate packages** before upload
- **Monitor post-release** issues

This build system guide provides comprehensive coverage of the Hatch-based build process used in MarkItDown, enabling efficient development, testing, and distribution workflows.