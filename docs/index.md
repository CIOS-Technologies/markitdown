# MarkItDown Documentation

**MarkItDown** is a sophisticated Python utility for converting various document formats to Markdown, specifically designed for LLM consumption and text analysis pipelines. It preserves important document structure while providing token-efficient output optimized for AI workflows.

## 🚀 Quick Overview

MarkItDown converts 15+ document formats to structured Markdown with support for:
- **Documents**: PDF, DOCX, PPTX, XLSX/XLS, EPUB, MSG (Outlook)
- **Web Content**: HTML, Wikipedia, YouTube transcripts, Bing SERPs, RSS feeds
- **Media**: Images (with OCR + LLM descriptions), Audio (speech transcription)
- **Data**: CSV, JSON, XML, Jupyter notebooks
- **Archives**: ZIP files with batch processing
- **Advanced**: Azure Document Intelligence, custom LLM integration, MCP server

## 📋 Key Features

- 🎯 **LLM-Optimized**: Token-efficient Markdown output that mainstream LLMs understand natively
- 🔧 **Extensible**: Plugin architecture for third-party converters
- 🌊 **Stream Processing**: Efficient binary stream handling with no temporary files
- 🤖 **AI Integration**: LLM-powered image descriptions and Azure Document Intelligence
- ⚡ **Parallel Processing**: Multi-worker parallel image processing for fast PDF conversion
- 🐳 **Production Ready**: Docker support, comprehensive testing, enterprise-grade quality
- 🔌 **MCP Server**: Model Context Protocol support for LLM applications

## 📚 Documentation Structure

### Getting Started
- [**Quick Start**](examples/quick-start.md) - Basic usage examples and common workflows
- [**CLI Reference**](api/cli.md) - Command-line interface documentation
- [**PDF Processing Script**](../process_pdf.py) - Standalone script for PDF conversion with parallel image processing

### Core Documentation
- [**Architecture Overview**](architecture/overview.md) - System design and component relationships
- [**API Reference**](api/README.md) - Python API documentation and usage patterns
- [**Converter Reference**](converters/README.md) - All supported formats and converter details

### Advanced Topics
- [**Plugin Development**](plugins/README.md) - Creating custom converters and extensions
- [**Azure Integration**](api/azure-doc-intel.md) - Document Intelligence setup and usage
- [**LLM Integration**](api/llm-integration.md) - Custom model integration for media processing
- [**MCP Server**](api/mcp-server.md) - Model Context Protocol server implementation

### Development
- [**Development Setup**](development/README.md) - Contributing guidelines and development workflow
- [**Installation Guide**](development/installation.md) - Setup instructions and dependency management
- [**Testing Guide**](development/testing.md) - Running and writing tests
- [**Build System**](development/build.md) - Hatch build system and packaging
- [**Docker Deployment**](development/docker.md) - Containerized deployment and production setup
- [**Publishing Package**](development/publishing.md) - Building and publishing pip packages

## 🎯 Common Use Cases

### Basic Document Conversion
```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("document.pdf")
print(result.text_content)
```

### Advanced Features
```python
# With OpenAI LLM integration for images
from openai import OpenAI
client = OpenAI()
md = MarkItDown(llm_client=client, llm_model="gpt-4o")

# With Gemini LLM integration for images (recommended)
md = MarkItDown(gemini_api_key="your-gemini-api-key", llm_model="gemini-2.5-flash")

# With parallel image processing (up to 20 workers by default)
result = md.convert("document.pdf", max_image_workers=20)

# With Azure Document Intelligence
md = MarkItDown(docintel_endpoint="your-endpoint")

# Enable plugins
md = MarkItDown(enable_plugins=True)
```

### Command Line Usage
```bash
# Basic conversion
markitdown document.pdf -o output.md

# With plugins
markitdown document.docx --use-plugins

# Azure Document Intelligence
markitdown scan.pdf -d -e "endpoint"
```

## 📊 Supported Formats

| Category | Formats | Special Features |
|----------|---------|------------------|
| **Documents** | PDF, DOCX, PPTX, XLSX/XLS, EPUB | Preserve structure, tables, links |
| **Media** | Images, Audio | OCR, transcription, AI descriptions (OpenAI/Gemini) |
| **Web** | HTML, Wikipedia, YouTube, RSS | Live content fetching |
| **Data** | CSV, JSON, XML, IPYNB | Structured data extraction |
| **Archives** | ZIP | Batch processing of contents |
| **Messaging** | Outlook MSG | Email metadata and content |

## 🔧 Configuration Options

MarkItDown supports various configuration options:
- **Optional Dependencies**: Install only needed converters (`[pdf]`, `[docx]`, `[all]`)
- **Plugin System**: Enable/disable third-party converters
- **LLM Integration**: OpenAI and Google Gemini support for image descriptions
- **Azure Integration**: Enhanced OCR and structure extraction
- **Priority System**: Control converter selection behavior

## 🏗️ Architecture Highlights

- **Modular Design**: 23 specialized converters with clean inheritance
- **Stream Processing**: No temporary files, efficient memory usage
- **Priority-Based Routing**: Intelligent converter selection
- **Error Handling**: Graceful degradation with detailed exceptions
- **Type Detection**: Magika ML-based content recognition

## 📦 Package Structure

```
markitdown/
├── packages/
│   ├── markitdown/              # Main conversion engine
│   ├── markitdown-mcp/          # MCP server implementation
│   └── markitdown-sample-plugin/ # Plugin development template
└── docs/                        # This documentation
```

## 🚀 Next Steps

1. **New Users**: Start with [Installation Guide](development/installation.md) and [Quick Start](examples/quick-start.md)
2. **Developers**: See [API Reference](api/README.md) and [Plugin Development](plugins/README.md)
3. **Advanced Users**: Explore [Azure Integration](api/azure-doc-intel.md) and [LLM Integration](api/llm-integration.md)
4. **Container Users**: See [Docker Deployment](development/docker.md) for containerized setups
5. **Contributors**: Read [Development Setup](development/README.md) and [Testing Guide](development/testing.md)

## 📄 Additional Resources

- [GitHub Repository](https://github.com/microsoft/markitdown) - Source code and issues
- [PyPI Package](https://pypi.org/project/markitdown/) - Package distribution
- [MCP Server](https://github.com/microsoft/markitdown/tree/main/packages/markitdown-mcp) - LLM integration
- [Sample Plugins](https://github.com/microsoft/markitdown/tree/main/packages/markitdown-sample-plugin) - Extension examples

---

*MarkItDown is built by the [AutoGen Team](https://github.com/microsoft/autogen) at Microsoft, designed to bridge the gap between complex document formats and AI-powered text analysis.*