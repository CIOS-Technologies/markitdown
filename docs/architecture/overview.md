# Architecture Overview

MarkItDown follows a modular, extensible architecture designed for efficient document conversion with clean separation of concerns and robust plugin support.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        MarkItDown API                        │
├─────────────────────────────────────────────────────────────┤
│  MarkItDown Class (markitdown/_markitdown.py)                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Stream Info   │  │ File Detection  │  │  Converter      │ │
│  │  (_stream_info) │  │    (magika)     │  │  Registry       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Document Converters                       │
├─────────────────────────────────────────────────────────────┤
│  DocumentConverter (Base Class - _base_converter.py)        │
│                              │                             │
│  ┌─────────────┬─────────────┬─────────────┬─────────────────┐ │
│  │ Document    │ Media       │ Web         │ Data            │ │
│  │ Converters  │ Converters  │ Converters  │ Converters      │ │
│  │ (PDF, DOCX) │ (Image,     │ (HTML,      │ (CSV, JSON)     │ │
│  │             │ Audio)      │ YouTube)    │                 │ │
│  └─────────────┴─────────────┴─────────────┴─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Plugin Ecosystem                          │
├─────────────────────────────────────────────────────────────┤
│  Plugin Discovery (entry_points)                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Sample Plugin   │  │ Third-party     │  │ Custom          │ │
│  │ (Template)      │  │ Plugins         │  │ Converters      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Core Components

### 1. MarkItDown Orchestrator (`_markitdown.py`)

The main orchestrator class that coordinates the entire conversion process:

**Key Responsibilities:**
- File type detection using Magika
- Converter selection and routing
- Stream management and processing
- Error handling and graceful degradation
- Plugin discovery and management

**Core Methods:**
```python
def convert(self, source: Union[str, Path, BinaryIO]) -> DocumentConverterResult
def convert_stream(self, stream: BinaryIO, stream_info: StreamInfo) -> DocumentConverterResult
```

**Priority System:**
- `PRIORITY_SPECIFIC_FILE_FORMAT` (50): High-priority, format-specific converters
- `PRIORITY_GENERIC_FILE_FORMAT` (100): Lower-priority, generic converters

### 2. DocumentConverter Base Class (`_base_converter.py`)

Abstract base class defining the converter interface:

```python
class DocumentConverter:
    def convert(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any
    ) -> DocumentConverterResult:
        raise NotImplementedError
```

**All converters inherit from this base class**, ensuring consistent interface and behavior.

### 3. StreamInfo (`_stream_info.py`)

Handles stream processing and file metadata extraction:

**Features:**
- Binary stream management with position tracking
- File type detection using Magika ML
- MIME type and encoding detection
- URI parsing (file://, data://, http://)
- Character set normalization

**Key Methods:**
```python
def get_filetype() -> str
def get_mimetype() -> str
def get_encoding() -> str
```

## 🔧 Converter Architecture

### Converter Categories

1. **Document Converters**
   - `_pdf_converter.py` - PDF text extraction with pdfminer.six
   - `_docx_converter.py` - Word documents via mammoth
   - `_pptx_converter.py` - PowerPoint with image LLM descriptions
   - `_xlsx_converter.py` / `_xls_converter.py` - Excel files via pandas

2. **Media Converters**
   - `_image_converter.py` - Images with OCR and LLM descriptions
   - `_audio_converter.py` - Audio files with speech transcription
   - `_transcribe_audio.py` - Speech recognition engine

3. **Web Content Converters**
   - `_html_converter.py` - HTML to structured Markdown
   - `_wikipedia_converter.py` - Wikipedia article extraction
   - `_youtube_converter.py` - YouTube video transcription
   - `_bing_serp_converter.py` - Bing search results parsing
   - `_rss_converter.py` - RSS feed processing

4. **Data Converters**
   - `_csv_converter.py` - CSV files with table formatting
   - `_ipynb_converter.py` - Jupyter notebook conversion
   - `_plain_text_converter.py` - Text files and code

5. **Archive Converters**
   - `_zip_converter.py` - ZIP file batch processing

6. **Special Converters**
   - `_epub_converter.py` - EPUB e-book processing
   - `_outlook_msg_converter.py` - Outlook message parsing
   - `_doc_intel_converter.py` - Azure Document Intelligence

### Converter Implementation Pattern

Each converter follows a consistent pattern:

```python
class SpecificConverter(DocumentConverter):
    def __init__(self, *args, **kwargs):
        # Initialize converter-specific dependencies

    def convert(
        self,
        stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any
    ) -> DocumentConverterResult:
        # 1. Validate file type
        # 2. Process content
        # 3. Generate Markdown output
        # 4. Return DocumentConverterResult
```

## 🔌 Plugin System Architecture

### Plugin Discovery

Plugins are discovered via Python entry points:

```python
# pyproject.toml
[project.entry-points."markitdown.converter"]
my_converter = "my_plugin.converter:MyConverter"
```

### Plugin Interface

Plugins implement the same `DocumentConverter` interface:

```python
class MyConverter(DocumentConverter):
    def convert(self, stream: BinaryIO, stream_info: StreamInfo, **kwargs):
        # Custom conversion logic
        return DocumentConverterResult(...)
```

### Plugin Management

- **Enabled by default**: Core converters are always available
- **Optional plugins**: Must be explicitly enabled with `enable_plugins=True`
- **Discovery**: Automatic discovery via entry points
- **Priority**: Plugins can specify priority for converter selection

## 🌊 Stream Processing Architecture

### Stream Management

MarkItDown uses a stream-based architecture to avoid temporary files:

```python
# Efficient binary stream processing
with open(file_path, "rb") as stream:
    result = markitdown.convert_stream(stream, stream_info)
```

### Memory Efficiency

- **Position tracking**: Streams maintain position for multiple reads
- **Lazy loading**: Converters load dependencies on demand
- **Chunked processing**: Large files processed in chunks when possible

## 🎯 Priority-Based Converter Selection

### Selection Algorithm

1. **File Type Detection**: Use Magika to determine file type
2. **Converter Filtering**: Find converters supporting the detected type
3. **Priority Sorting**: Sort by priority (lower number = higher priority)
4. **Plugin Integration**: Include enabled plugins in selection
5. **Fallback Handling**: Graceful degradation if all converters fail

### Priority Levels

```python
PRIORITY_SPECIFIC_FILE_FORMAT = 50  # Format-specific converters
PRIORITY_GENERIC_FILE_FORMAT = 100  # Generic/fallback converters
```

## 🛡️ Error Handling Architecture

### Exception Hierarchy

```python
MarkItDownException (Base)
├── MissingDependencyException
├── FailedConversionAttempt
├── FileConversionException
└── UnsupportedFormatException
```

### Graceful Degradation

- **Converter fallback**: Try multiple converters for the same file type
- **Partial success**: Extract what's possible from damaged files
- **Detailed errors**: Provide specific error messages for debugging
- **Logging**: Comprehensive logging for troubleshooting

## 🚀 Performance Optimizations

### Lazy Loading
- Converters import dependencies only when needed
- Optional dependencies reduce memory footprint
- Plugin loading on-demand

### Efficient Processing
- Binary streams avoid memory duplication
- Magika ML-based file type detection
- Minimal temporary file creation

### Caching Strategy
- File type detection results cached
- Converter instances reused
- Plugin discovery results cached

## 🧪 Testing Architecture

### Test Categories

1. **Unit Tests** (`test_module_*.py`)
   - Individual converter testing
   - API method validation
   - Error condition testing

2. **Integration Tests** (`test_cli_*.py`)
   - CLI interface testing
   - End-to-end conversion workflows
   - Plugin integration testing

3. **Vector Tests** (`test_*_vectors.py`)
   - Regression testing with known inputs/outputs
   - Format-specific validation
   - Cross-platform compatibility

### Test Data Organization

```
tests/
├── test_data/
│   ├── vectors/          # Known input/output pairs
│   ├── samples/          # Sample files for testing
│   └── temp/            # Temporary test files
```

## 📦 Package Structure

### Main Package (`packages/markitdown/`)

```
src/markitdown/
├── __init__.py           # Public API exports
├── _markitdown.py        # Main orchestrator class
├── _base_converter.py    # Converter base class
├── _stream_info.py       # Stream processing
├── _exceptions.py        # Exception definitions
├── _uri_utils.py         # URI parsing utilities
├── __main__.py          # CLI entry point
├── converters/          # Converter implementations
└── converter_utils/     # Shared converter utilities
```

### MCP Package (`packages/markitdown-mcp/`)

```
src/markitdown_mcp/
├── server.py            # MCP server implementation
├── transport.py         # MCP transport layer
└── handlers/            # MCP request handlers
```

### Plugin Package (`packages/markitdown-sample-plugin/`)

```
src/markitdown_sample_plugin/
├── converter.py         # Sample converter implementation
└── setup.py            # Plugin setup configuration
```

## 🔄 Extension Points

### Custom Converters

1. **Inherit from DocumentConverter**
2. **Implement convert() method**
3. **Register via entry points**
4. **Handle specific file types**

### Custom Stream Processors

1. **Extend StreamInfo class**
2. **Add custom file type detection**
3. **Implement URI scheme handlers**
4. **Add encoding detection**

### Integration Hooks

1. **LLM integration**: Custom image description models
2. **Cloud services**: Azure, AWS, GCP integrations
3. **Database integration**: Direct database document processing
4. **API integration**: REST API document sources

This architecture provides a solid foundation for reliable, extensible document conversion with clean separation of concerns and comprehensive error handling.