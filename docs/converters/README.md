# Document Converters Reference

MarkItDown includes 23+ specialized converters that handle different file formats. Each converter inherits from the `DocumentConverter` base class and follows a consistent interface.

## 📋 Supported Formats Overview

| Category | Converter | File Types | Dependencies | Priority | Special Features |
|----------|-----------|------------|--------------|----------|------------------|
| **Documents** | PDF Converter | `.pdf` | `pdfminer.six` | 50 | Text extraction, layout preservation |
| **Documents** | DOCX Converter | `.docx`, `.dotx` | `mammoth`, `lxml` | 50 | Style preservation, image extraction |
| **Documents** | PPTX Converter | `.pptx`, `.pptm` | `python-pptx` | 50 | Slide structure, LLM image descriptions |
| **Documents** | XLSX Converter | `.xlsx`, `.xlsm` | `pandas`, `openpyxl` | 50 | Multiple sheets, formula display |
| **Documents** | XLS Converter | `.xls` | `pandas`, `xlrd` | 50 | Legacy Excel format support |
| **Documents** | EPUB Converter | `.epub` | `ebooklib` | 50 | E-book structure, metadata |
| **Documents** | MSG Converter | `.msg` | `olefile` | 50 | Outlook messages, attachments |
| **Media** | Image Converter | `.jpg`, `.png`, `.gif`, etc. | `pillow` | 50 | EXIF metadata, OCR, LLM descriptions |
| **Media** | Audio Converter | `.wav`, `.mp3`, `.m4a` | `pydub`, `SpeechRecognition` | 50 | Speech transcription, metadata |
| **Web** | HTML Converter | `.html`, `.htm` | `beautifulsoup4`, `markdownify` | 50 | Structure preservation, link handling |
| **Web** | Wikipedia Converter | Wikipedia URLs | `requests` | 50 | Article extraction, citation formatting |
| **Web** | YouTube Converter | YouTube URLs | `youtube-transcript-api` | 50 | Video transcription, metadata |
| **Web** | Bing SERP Converter | Bing search URLs | `requests` | 50 | Search result parsing |
| **Web** | RSS Converter | RSS/Atom feeds | `requests` | 50 | Feed item extraction |
| **Data** | CSV Converter | `.csv`, `.tsv` | `pandas` | 50 | Table formatting, delimiter detection |
| **Data** | Jupyter Converter | `.ipynb` | `nbformat`, `nbconvert` | 50 | Code and output formatting |
| **Data** | Plain Text Converter | `.txt`, `.md`, code files | `charset-normalizer` | 100 | Syntax highlighting, encoding detection |
| **Archive** | ZIP Converter | `.zip` | `zipfile` | 50 | Batch processing, recursive conversion |
| **Special** | Doc Intel Converter | Various formats | `azure-ai-documentintelligence` | 45 | Azure AI enhancement, OCR |
| **Special** | Data URI Converter | `data:` URIs | `python-magic` | 50 | Inline data handling |

## 🗂️ Document Converters

### PDF Converter (`_pdf_converter.py`)

**Supported Formats**: `.pdf`
**Dependencies**: `pdfminer.six`
**Priority**: 50

**Features**:
- Text extraction with layout preservation
- Table detection and formatting
- Metadata extraction (title, author, creation date)
- Handling of embedded images
- Cross-platform compatibility

**Usage**:
```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("document.pdf")
print(result.text_content)
```

**Limitations**:
- Text-only extraction (no OCR for scanned PDFs)
- Complex layouts may not be perfectly preserved
- Encrypted PDFs require password handling

### DOCX Converter (`_docx_converter.py`)

**Supported Formats**: `.docx`, `.dotx`
**Dependencies**: `mammoth`, `lxml`
**Priority**: 50

**Features**:
- Style preservation (bold, italic, headings)
- List and table conversion
- Image extraction with alt text
- Comment and footnote handling
- Clean HTML-to-Markdown conversion

**Advanced Usage**:
```python
# Custom style mapping
md = MarkItDown()
result = md.convert("document.docx")
# Preserves document structure with Markdown formatting
```

### PPTX Converter (`_pptx_converter.py`)

**Supported Formats**: `.pptx`, `.pptm`
**Dependencies**: `python-pptx`
**Priority**: 50

**Features**:
- Slide-by-slide conversion
- Speaker notes extraction
- Image processing with LLM descriptions
- Table and chart conversion
- Animation and transition metadata

**LLM Integration**:
```python
from openai import OpenAI
from markitdown import MarkItDown

client = OpenAI()
md = MarkItDown(llm_client=client, llm_model="gpt-4o")
result = md.convert("presentation.pptx")
# Images will be described by the LLM
```

### XLSX/XLS Converters (`_xlsx_converter.py`, `_xls_converter.py`)

**Supported Formats**: `.xlsx`, `.xlsm`, `.xls`
**Dependencies**: `pandas`, `openpyxl` (XLSX), `xlrd` (XLS)
**Priority**: 50

**Features**:
- Multiple sheet processing
- Formula display and calculation results
- Data type preservation
- Table formatting with Markdown
- Named ranges and references

**Example Output**:
```markdown
## Sheet1

| Column A | Column B | Formula |
|----------|----------|---------|
| 10       | 20       | =A1+B1  |
| 30       | 40       | =A2+B2  |
```

## 🎨 Media Converters

### Image Converter (`_image_converter.py`)

**Supported Formats**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.webp`
**Dependencies**: `pillow`
**Priority**: 50

**Features**:
- EXIF metadata extraction
- OCR text recognition (when available)
- LLM-powered image descriptions
- Basic image information (dimensions, format)
- Alt text generation

**LLM Integration** (Gemini recommended):
```python
# With Gemini (recommended - automatic context awareness)
md = MarkItDown(
    gemini_api_key="your-gemini-api-key",
    llm_model="gemini-2.5-flash"
)
result = md.convert("chart.png")

# Or with OpenAI
md = MarkItDown(
    llm_client=client,
    llm_model="gpt-4o",
    llm_prompt="Describe this image in detail for accessibility"
)
result = md.convert("chart.png")
```

**Output Example**:
```markdown
![Image Description](data:image/jpeg;base64,...)

*Image: Bar chart showing quarterly revenue growth*

**EXIF Metadata**:
- Dimensions: 1920x1080
- Format: JPEG
- Created: 2024-01-15
```

### Audio Converter (`_audio_converter.py`)

**Supported Formats**: `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`
**Dependencies**: `pydub`, `SpeechRecognition`
**Priority**: 50

**Features**:
- Speech-to-text transcription
- Audio metadata extraction
- Multiple format support
- Language detection
- Timestamp generation

**Usage**:
```python
result = md.convert("meeting.mp3")
print(result.text_content)  # Transcribed text
```

## 🌐 Web Content Converters

### HTML Converter (`_html_converter.py`)

**Supported Formats**: `.html`, `.htm`, web URLs
**Dependencies**: `beautifulsoup4`, `markdownify`
**Priority**: 50

**Features**:
- Clean HTML to Markdown conversion
- Link and image reference handling
- Table and list preservation
- Script and style removal
- Meta tag extraction

**Advanced Features**:
- Relative link resolution
- Image alt text preservation
- Table of contents generation
- Semantic HTML structure preservation

### Wikipedia Converter (`_wikipedia_converter.py`)

**Supported Formats**: Wikipedia URLs
**Dependencies**: `requests`
**Priority**: 50

**Features**:
- Full article extraction
- Reference and citation formatting
- Infobox data extraction
- Category and link preservation
- Section hierarchy maintenance

**Example**:
```python
result = md.convert("https://en.wikipedia.org/wiki/Artificial_intelligence")
# Returns structured Markdown with proper citations
```

### YouTube Converter (`_youtube_converter.py`)

**Supported Formats**: YouTube video URLs
**Dependencies**: `youtube-transcript-api`
**Priority**: 50

**Features**:
- Video transcript extraction
- Metadata (title, description, duration)
- Channel information
- Upload date and view count
- Multiple language support

**Usage**:
```python
result = md.convert("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
# Returns transcript with video metadata
```

## 📊 Data Converters

### CSV Converter (`_csv_converter.py`)

**Supported Formats**: `.csv`, `.tsv`, custom delimiters
**Dependencies**: `pandas`
**Priority**: 50

**Features**:
- Automatic delimiter detection
- Header row identification
- Data type inference
- Table formatting
- Large file handling

**Customization**:
```python
# CSV files are automatically formatted as Markdown tables
# Handles various delimiters and encodings
result = md.convert("data.csv")
```

### Jupyter Converter (`_ipynb_converter.py`)

**Supported Formats**: `.ipynb`
**Dependencies**: `nbformat`, `nbconvert`
**Priority**: 50

**Features**:
- Code cell extraction with syntax highlighting
- Output preservation (text, images, HTML)
- Markdown cell integration
- Cell execution count
- Kernel information

**Output Structure**:
```markdown
## Jupyter Notebook

### Cell 1: Code [python]
```python
import pandas as pd
df = pd.read_csv('data.csv')
print(df.head())
```

**Output**:
```
   column1  column2
0       1       2
1       3       4
```
```

## 📦 Archive Converters

### ZIP Converter (`_zip_converter.py`)

**Supported Formats**: `.zip`
**Dependencies**: `zipfile` (built-in)
**Priority**: 50

**Features**:
- Recursive file processing
- Nested archive handling
- File type filtering
- Batch conversion
- Compression ratio metadata

**Usage**:
```python
result = md.convert("archive.zip")
# Processes all supported files within the archive
```

## 🔧 Special Converters

### Azure Document Intelligence Converter (`_doc_intel_converter.py`)

**Supported Formats**: PDF, images, documents
**Dependencies**: `azure-ai-documentintelligence`, `azure-identity`
**Priority**: 45 (higher than standard converters)

**Features**:
- Advanced OCR capabilities
- Layout analysis
- Form field extraction
- Table structure detection
- Handwriting recognition

**Setup**:
```python
md = MarkItDown(
    docintel_endpoint="https://your-resource.cognitiveservices.azure.com/",
    docintel_key="your-api-key"  # or use Azure AD authentication
)
result = md.convert("scan.pdf")
```

### Data URI Converter

**Supported Formats**: `data:` URIs
**Dependencies**: `python-magic`
**Priority**: 50

**Features**:
- Inline data processing
- MIME type detection
- Base64 decoding
- Embedded file handling

## 🎯 Converter Selection Process

### Priority System

Converters are selected based on priority:
1. **Priority 45**: Azure Document Intelligence (highest)
2. **Priority 50**: Format-specific converters
3. **Priority 100**: Generic converters (fallback)

### Selection Algorithm

```python
def select_converter(stream_info: StreamInfo) -> DocumentConverter:
    # 1. Get file type from Magika
    file_type = stream_info.get_filetype()

    # 2. Filter converters by supported types
    compatible_converters = [
        c for c in self._converters
        if file_type in c.supported_file_types
    ]

    # 3. Sort by priority (lower number = higher priority)
    compatible_converters.sort(key=lambda c: c.priority)

    # 4. Try converters in order
    for converter in compatible_converters:
        try:
            return converter.convert(stream, stream_info)
        except Exception:
            continue
```

## 🛠️ Custom Converter Development

### Basic Converter Template

```python
from markitdown._base_converter import DocumentConverter
from markitdown._stream_info import StreamInfo
from markitdown import DocumentConverterResult
import io

class MyCustomConverter(DocumentConverter):
    def __init__(self):
        super().__init__()
        self.supported_file_types = [".custom"]
        self.priority = 50

    def convert(
        self,
        stream: io.BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any
    ) -> DocumentConverterResult:
        # 1. Read content
        content = stream.read()

        # 2. Process content
        markdown_content = self._process_content(content)

        # 3. Return result
        return DocumentConverterResult(
            markdown_content,
            title="Custom Document",
            metadata={"converter": "MyCustomConverter"}
        )

    def _process_content(self, content: bytes) -> str:
        # Custom processing logic
        return content.decode("utf-8")
```

### Registration

1. **Entry Point Registration** (for plugins):
```toml
[project.entry-points."markitdown.converter"]
my_converter = "my_package.converter:MyCustomConverter"
```

2. **Direct Registration** (for internal use):
```python
from markitdown import MarkItDown

md = MarkItDown()
md.register_converter(MyCustomConverter())
```

## 📋 Dependencies by Feature Group

### Document Processing
- `pdfminer.six` - PDF text extraction
- `mammoth` - DOCX processing
- `python-pptx` - PowerPoint processing
- `pandas`, `openpyxl`, `xlrd` - Excel processing
- `ebooklib` - EPUB processing
- `olefile` - Outlook MSG processing

### Media Processing
- `pillow` - Image processing
- `pydub` - Audio processing
- `SpeechRecognition` - Speech-to-text

### Web Processing
- `beautifulsoup4` - HTML parsing
- `markdownify` - HTML to Markdown
- `requests` - HTTP requests
- `youtube-transcript-api` - YouTube transcripts

### Advanced Features
- `azure-ai-documentintelligence` - Azure Document Intelligence
- `azure-identity` - Azure authentication
- `openai` - LLM integration

This converter system provides comprehensive format support while maintaining a clean, extensible architecture for adding new document types.