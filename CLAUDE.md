# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MarkItDown is a Python utility for converting various document formats to Markdown. It's designed for LLM consumption and supports PDF, PowerPoint, Word, Excel, Images, Audio, HTML, text-based formats, ZIP files, YouTube URLs, EPubs, and more.

## Architecture

This is a multi-package Python project using the [hatch](https://hatch.pypa.io/) build system:

- `packages/markitdown/` - Main package with the core conversion engine
- `packages/markitdown-mcp/` - MCP (Model Context Protocol) server implementation
- `packages/markitdown-sample-plugin/` - Sample plugin for third-party extensions

### Core Architecture

The main MarkItDown class follows a converter pattern with these key components:

- **MarkItDown** (`_markitdown.py`) - Main orchestrator class that handles file type detection and converter routing
- **DocumentConverter** (`_base_converter.py`) - Abstract base class for all converters
- **Converters** (`converters/`) - 20+ format-specific converters implementing DocumentConverter
- **StreamInfo** (`_stream_info.py`) - Handles stream processing and file type detection using magika

### Converter System

Each converter in `converters/` implements:
- `DocumentConverter.convert()` method that takes a stream and returns `DocumentConverterResult`
- Priority-based system (PRIORITY_SPECIFIC_FILE_FORMAT vs PRIORITY_GENERIC_FILE_FORMAT)
- Automatic format detection using magika and MIME types
- Plugin support for third-party converters

## Development Commands

### Environment Setup

```bash
# From project root
cd packages/markitdown

# Install hatch and create environment
pip install hatch
hatch shell

# Or use uv
uv venv --python=3.12 .venv
source .venv/bin/activate
pip install -e '.[all]'
```

### Testing

```bash
cd packages/markitdown

# Run all tests
hatch test

# Run specific test file
hatch test tests/test_module_misc.py

# Run with coverage
hatch test --cover

# Run pre-commit checks
pre-commit run --all-files
```

### Build and Installation

```bash
# Install in development mode with all dependencies
pip install -e 'packages/markitdown[all]'

# Build packages
hatch build

# Install specific feature groups
pip install 'markitdown[pdf, docx, pptx]'
```

## Code Structure

### Key Files

- `src/markitdown/__init__.py` - Public API and exports
- `src/markitdown/_markitdown.py` - Main MarkItDown orchestrator class
- `src/markitdown/__main__.py` - CLI entry point
- `src/markitdown/_base_converter.py` - Converter base class
- `src/markitdown/converters/__init__.py` - Converter registry

### Adding New Converters

1. Create a new file in `src/markitdown/converters/_your_converter.py`
2. Inherit from `DocumentConverter`
3. Implement `convert()` method returning `DocumentConverterResult`
4. Add to imports in `src/markitdown/converters/__init__.py`
5. Add to main imports in `src/markitdown/_markitdown.py`

### Dependencies and Feature Groups

The project uses optional dependencies organized by feature groups in `pyproject.toml`:
- `[all]` - All optional dependencies
- `[pdf]`, `[docx]`, `[pptx]`, `[xlsx]` - Document formats
- `[audio-transcription]`, `[youtube-transcription]` - Media processing
- `[az-doc-intel]` - Azure Document Intelligence

## Plugin System

- Plugins are discovered via entry points
- Sample plugin in `packages/markitdown-sample-plugin/`
- Enable plugins with `markitdown --use-plugins` or `MarkItDown(enable_plugins=True)`
- Plugin development follows the same DocumentConverter pattern

## Testing Strategy

- Unit tests for individual converters in `tests/`
- Integration tests using test vectors in `tests/test_*_vectors.py`
- CLI tests in `tests/test_cli_*.py`
- Uses hatch's test runner with pytest
- Test files include various document formats for conversion validation

## Important Notes

- Python 3.10+ required
- Stream-based processing (no temporary files created)
- Supports both file paths and binary streams
- Plugin architecture for extensibility
- Optional Azure Document Intelligence integration
- LLM integration for image descriptions in PPTX and image files