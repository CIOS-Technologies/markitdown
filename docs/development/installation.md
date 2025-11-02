# Installation Guide

This guide covers various installation methods for MarkItDown, from basic setup to advanced configurations with optional dependencies.

## 🚀 Prerequisites

### System Requirements

- **Python 3.10+** - MarkItDown requires Python 3.10 or higher
- **Operating System** - Windows, macOS, or Linux
- **Memory** - 4GB+ RAM recommended for large documents
- **Storage** - 100MB+ for core package + dependencies

### Python Environment

```bash
# Check Python version
python --version
# Should be 3.10.x or higher

# If using Python 2.x or < 3.10, upgrade Python
# Recommended: Use pyenv or conda for Python management
```

## 📦 Installation Methods

### Method 1: PyPI Installation (Recommended)

#### Basic Installation

```bash
# Install core package only
pip install markitdown
```

#### With Optional Dependencies

```bash
# Install with all optional dependencies (recommended for full functionality)
pip install 'markitdown[all]'

# Install specific feature groups
pip install 'markitdown[pdf, docx, pptx]'          # Office documents
pip install 'markitdown[pdf, audio-transcription]' # PDF + audio
pip install 'markitdown[az-doc-intel]'             # Azure Document Intelligence
pip install 'markitdown[youtube-transcription]'    # YouTube transcripts
```

#### Feature Groups Available

| Feature Group | Dependencies | Description |
|---------------|---------------|-------------|
| `all` | All dependencies | Complete functionality |
| `pptx` | `python-pptx` | PowerPoint files |
| `docx` | `mammoth`, `lxml` | Word documents |
| `xlsx` | `pandas`, `openpyxl` | Excel files |
| `xls` | `pandas`, `xlrd` | Legacy Excel files |
| `pdf` | `pdfminer.six` | PDF files |
| `outlook` | `olefile` | Outlook messages |
| `audio-transcription` | `pydub`, `SpeechRecognition` | Audio transcription |
| `youtube-transcription` | `youtube-transcript-api` | YouTube transcripts |
| `az-doc-intel` | `azure-ai-documentintelligence`, `azure-identity` | Azure Document Intelligence |

### Method 2: Development Installation

#### From Source

```bash
# Clone repository
git clone https://github.com/microsoft/markitdown.git
cd markitdown

# Navigate to main package
cd packages/markitdown

# Install in development mode
pip install -e '.[all]'
```

#### Using Hatch (Recommended for Development)

```bash
# Install hatch
pip install hatch

# Clone repository
git clone https://github.com/microsoft/markitdown.git
cd markitdown/packages/markitdown

# Create development environment
hatch shell

# Install with all dependencies
hatch run pip install -e '.[all]'
```

#### Using UV (Fast Package Manager)

```bash
# Install uv
pip install uv

# Clone repository
git clone https://github.com/microsoft/markitdown.git
cd markitdown

# Create virtual environment
uv venv --python=3.12 .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package
uv pip install -e 'packages/markitdown[all]'
```

### Method 3: Docker Installation

#### Using Pre-built Image

```bash
# Pull latest image
docker pull mcr.microsoft.com/markitdown:latest

# Run conversion
docker run --rm -i mcr.microsoft.com/markitdown:latest < input.pdf > output.md

# With volume mounting
docker run --rm -v $(pwd):/workdir mcr.microsoft.com/markitdown:latest \
  markitdown /workdir/document.pdf -o /workdir/output.md
```

#### Building from Source

```bash
# Clone repository
git clone https://github.com/microsoft/markitdown.git
cd markitdown

# Build Docker image
docker build -t markitdown:latest .

# Run container
docker run --rm -i markitdown:latest < input.pdf > output.md
```

## 🔧 Environment Setup

### Virtual Environment Setup

#### Using venv

```bash
# Create virtual environment
python -m venv markitdown-env

# Activate (Linux/macOS)
source markitdown-env/bin/activate

# Activate (Windows)
markitdown-env\Scripts\activate

# Install MarkItDown
pip install 'markitdown[all]'
```

#### Using Conda

```bash
# Create conda environment
conda create -n markitdown python=3.12
conda activate markitdown

# Install MarkItDown
pip install 'markitdown[all]'

# Save environment (optional)
conda env export > environment.yml
```

#### Using Virtualenvwrapper

```bash
# Create environment
mkvirtualenv markitdown -p python3.12

# Install MarkItDown
pip install 'markitdown[all]'

# Deactivate when done
deactivate
```

## ⚙️ Configuration

### Environment Variables

```bash
# Azure Document Intelligence (optional)
export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://your-resource.cognitiveservices.azure.com/"
export AZURE_DOCUMENT_INTELLIGENCE_KEY="your-api-key"

# OpenAI API (for LLM integration)
export OPENAI_API_KEY="your-openai-api-key"

# Plugin paths (optional)
export MARKITDOWN_PLUGIN_PATH="/path/to/custom/plugins"
```

### Shell Configuration

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
# MarkItDown aliases
alias md="markitdown"
alias md-azure="markitdown -d"

# Function for batch conversion
md-batch() {
    for file in "$@"; do
        markitdown "$file" -o "${file%.*}.md"
    done
}
```

## 🧪 Verification

### Verify Installation

```bash
# Check version
markitdown --version

# Test basic conversion
echo "# Test Markdown" > test.md
markitdown test.md

# List available plugins
markitdown --list-plugins
```

### Python API Test

```python
# Create test script
python -c "
from markitdown import MarkItDown
md = MarkItDown()
result = md.convert_string('# Test Content')
print('✅ Installation successful!')
print(result.text_content)
"
```

### Feature Test

```python
# Test specific features
python -c "
from markitdown import MarkItDown
import tempfile
import os

# Test basic functionality
md = MarkItDown()

# Create temporary test file
with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
    f.write('# Test Document\n\nThis is a test.')
    temp_file = f.name

try:
    result = md.convert(temp_file)
    print('✅ Basic conversion works')

    # Test with plugins
    md_plugins = MarkItDown(enable_plugins=True)
    result = md_plugins.convert(temp_file)
    print('✅ Plugin system works')

finally:
    os.unlink(temp_file)

print('✅ All tests passed!')
"
```

## 🔌 Plugin Installation

### Installing Sample Plugin

```bash
# Navigate to sample plugin directory
cd packages/markitdown-sample-plugin

# Install in development mode
pip install -e .

# Test plugin
markitdown --list-plugins
```

### Installing Third-party Plugins

```bash
# Install from PyPI
pip install markitdown-custom-plugin

# Install from local directory
pip install -e /path/to/plugin

# Install from Git repository
pip install git+https://github.com/user/markitdown-plugin.git
```

### Verifying Plugin Installation

```bash
# List all available plugins
markitdown --list-plugins

# Test plugin functionality
markitdown sample_file.extension --use-plugins
```

## 🐛 Troubleshooting

### Common Issues

#### Python Version Incompatible

```bash
# Check Python version
python --version

# If < 3.10, upgrade Python or use pyenv
pyenv install 3.12.0
pyenv local 3.12.0
```

#### Permission Denied

```bash
# Use user installation
pip install --user 'markitdown[all]'

# Or use sudo (not recommended)
sudo pip install 'markitdown[all]'
```

#### Missing Dependencies

```bash
# Install specific feature group
pip install 'markitdown[pdf]'

# Upgrade pip and setuptools
pip install --upgrade pip setuptools

# Clean installation
pip uninstall markitdown
pip install 'markitdown[all]'
```

#### Import Errors

```bash
# Check installation
python -c "import markitdown; print(markitdown.__version__)"

# Reinstall if necessary
pip uninstall markitdown
pip install 'markitdown[all]'
```

#### Platform-specific Issues

**Windows:**

```bash
# Ensure Python is in PATH
echo %PATH%

# Use PowerShell if cmd has issues
powershell -c "pip install 'markitdown[all]'"
```

**macOS:**

```bash
# Install Xcode command line tools if needed
xcode-select --install

# Use Homebrew Python if system Python is old
brew install python@3.12
```

**Linux:**

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install python3-dev python3-pip build-essential

# Install system dependencies (CentOS/RHEL)
sudo yum install python3-devel python3-pip gcc
```

### Getting Help

```bash
# Get help for CLI
markitdown --help

# Check logs for errors
markitdown document.pdf --verbose

# Python debugging
python -c "
import markitdown
import logging
logging.basicConfig(level=logging.DEBUG)
# Your code here
"
```

## 🚀 Next Steps

After successful installation:

1. **Try the Quick Start Guide** - [examples/quick-start.md](../examples/quick-start.md)
2. **Read the API Documentation** - [api/README.md](../api/README.md)
3. **Explore Converters** - [converters/README.md](../converters/README.md)
4. **Set Up Development Environment** - [development/README.md](README.md)

## 📊 Installation Sizes

| Installation Type | Approximate Size | Features |
|-------------------|------------------|----------|
| `markitdown` (core only) | ~15MB | Basic text formats |
| `markitdown[office]` | ~50MB | PDF, DOCX, PPTX, XLSX |
| `markitdown[media]` | ~80MB | + Audio, Image processing |
| `markitdown[all]` | ~150MB | All features including Azure |

## 🔄 Upgrading

### Upgrade to Latest Version

```bash
# Upgrade package
pip install --upgrade 'markitdown[all]'

# Check version after upgrade
markitdown --version
```

### Upgrade from Source

```bash
# Pull latest changes
git pull origin main

# Reinstall
pip install -e 'packages/markitdown[all]'
```

### Breaking Changes

When upgrading between major versions:

1. **Check release notes** on GitHub
2. **Backup current environment**
3. **Test in development environment first**
4. **Update code for API changes if any**

---

**Need Help?**
- Check the [GitHub Issues](https://github.com/microsoft/markitdown/issues)
- Review the [Troubleshooting Guide](#troubleshooting)
- Join the community discussions