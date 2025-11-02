# Quick Start Guide

Get up and running with MarkItDown in minutes. This guide covers the most common use cases and provides practical examples for converting various document formats.

## 🚀 Installation

### Basic Installation

```bash
# Install with all optional dependencies
pip install 'markitdown[all]'

# Install specific format support
pip install 'markitdown[pdf, docx, pptx]'

# Install from source
git clone https://github.com/microsoft/markitdown.git
cd markitdown
pip install -e 'packages/markitdown[all]'
```

### Verify Installation

```bash
# Check version
markitdown --version

# List available plugins
markitdown --list-plugins
```

## 💻 Command Line Usage

### Basic Conversion

```bash
# Convert PDF to Markdown
markitdown document.pdf > output.md

# Specify output file
markitdown document.pdf -o output.md

# Convert from stdin
cat document.docx | markitdown > output.md
```

### Advanced Options

```bash
# Enable plugins
markitdown document.docx --use-plugins -o output.md

# Use Azure Document Intelligence
markitdown scan.pdf -d -e "https://your-resource.cognitiveservices.azure.com/"

# Convert multiple files
markitdown file1.pdf file2.docx file3.pptx

# Process directory
markitdown documents/*.pdf
```

## 🐍 Python API Usage

### Basic Example

```python
from markitdown import MarkItDown

# Initialize converter
md = MarkItDown()

# Convert document
result = md.convert("document.pdf")

# Access results
print("Content:", result.text_content)
print("Title:", result.title)
print("Metadata:", result.metadata)
```

### Batch Processing

```python
from pathlib import Path
import glob

# Initialize with plugins
md = MarkItDown(enable_plugins=True)

# Process all PDFs in directory
for pdf_file in glob.glob("documents/*.pdf"):
    try:
        result = md.convert(pdf_file)

        # Save to corresponding .md file
        output_path = pdf_file.replace(".pdf", ".md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.text_content)

        print(f"✅ Converted: {pdf_file}")
    except Exception as e:
        print(f"❌ Failed: {pdf_file} - {e}")
```

## 📄 Format-Specific Examples

### PDF Documents

```python
from markitdown import MarkItDown

md = MarkItDown()

# Basic PDF conversion
result = md.convert("research_paper.pdf")
print(result.text_content)

# With Azure Document Intelligence for better OCR
md_azure = MarkItDown(
    docintel_endpoint="https://your-resource.cognitiveservices.azure.com/",
    docintel_key="your-api-key"
)
result = md_azure.convert("scanned_document.pdf")
```

### Word Documents

```python
# Convert DOCX with style preservation
result = md.convert("report.docx")

# Access document metadata
print(f"Title: {result.title}")
print(f"Converter used: {result.metadata.get('converter')}")
```

### PowerPoint Presentations

```python
# Basic PPTX conversion
result = md.convert("presentation.pptx")

# With LLM for image descriptions (Gemini recommended)
md_with_gemini = MarkItDown(
    gemini_api_key="your-gemini-api-key",
    llm_model="gemini-2.5-flash"
)
result = md_with_gemini.convert("presentation.pptx")

# Or with OpenAI
from openai import OpenAI
client = OpenAI()
md_with_openai = MarkItDown(
    llm_client=client,
    llm_model="gpt-4o",
    llm_prompt="Describe this slide content in detail"
)
result = md_with_openai.convert("presentation.pptx")
```

### Excel Spreadsheets

```python
# Convert Excel with multiple sheets
result = md.convert("financial_data.xlsx")

# The result includes all sheets formatted as Markdown tables
print(result.text_content)
```

### Images

```python
# Convert image with OCR and metadata
result = md.convert("chart.png")

# With Gemini (recommended for images - automatic context awareness)
md_gemini = MarkItDown(
    gemini_api_key="your-gemini-api-key",
    llm_model="gemini-2.5-flash"
)
result = md_gemini.convert("chart.png")

# Or with OpenAI
md_openai = MarkItDown(
    llm_client=client,
    llm_model="gpt-4o",
    llm_prompt="Analyze this chart and describe key insights"
)
result = md_openai.convert("chart.png")

print(result.text_content)
# Includes: image description, EXIF metadata, OCR text (if any)
```

### Audio Files

```python
# Transcribe audio file
result = md.convert("meeting.mp3")

print(result.text_content)
# Contains transcribed speech with timestamps
```

## 🌐 Web Content Examples

### HTML Pages

```python
# Convert web page
result = md.convert("https://example.com/article.html")
print(result.text_content)

# Convert local HTML file
result = md.convert("local_page.html")
```

### Wikipedia Articles

```python
# Extract Wikipedia article
result = md.convert("https://en.wikipedia.org/wiki/Artificial_intelligence")
print(result.text_content)
# Includes article content, references, and proper citation formatting
```

### YouTube Videos

```python
# Get YouTube transcript
result = md.convert("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
print(result.text_content)
# Contains transcript with video metadata
```

## 📦 Archive Processing

### ZIP Files

```python
# Process all supported files in ZIP archive
result = md.convert("document_archive.zip")

# The result contains concatenated Markdown from all files
print(result.text_content)
```

## 🔧 Advanced Usage Patterns

### Custom Error Handling

```python
from markitdown import MarkItDown
from markitdown._exceptions import (
    UnsupportedFormatException,
    FileConversionException,
    MissingDependencyException
)

def safe_convert(file_path: str, md: MarkItDown) -> str:
    """Convert with comprehensive error handling."""
    try:
        result = md.convert(file_path)
        return result.text_content

    except UnsupportedFormatException:
        return f"# Unsupported Format\n\nFile '{file_path}' is not supported."

    except MissingDependencyException as e:
        return f"# Missing Dependency\n\n{e}\n\nInstall with: pip install markitdown[required-features]"

    except FileConversionException as e:
        return f"# Conversion Failed\n\nError converting '{file_path}': {e}"

    except Exception as e:
        return f"# Unexpected Error\n\nError processing '{file_path}': {e}"

# Usage
md = MarkItDown(enable_plugins=True)
content = safe_convert("unknown_file.xyz", md)
print(content)
```

### Stream Processing

```python
import io
from markitdown import MarkItDown, StreamInfo

def convert_from_data(data: bytes, filename: str) -> str:
    """Convert from binary data instead of file."""
    md = MarkItDown()

    # Create stream from data
    stream = io.BytesIO(data)

    # Create stream info
    stream_info = StreamInfo(stream=stream, filename=filename)

    # Convert
    result = md.convert_stream(stream, stream_info)
    return result.text_content

# Usage with downloaded content
import requests

response = requests.get("https://example.com/document.pdf")
content = convert_from_data(response.content, "document.pdf")
print(content)
```

### Configuration Management

```python
from markitdown import MarkItDown
import os

class MarkItDownConfig:
    """Configuration management for MarkItDown."""

    def __init__(self):
        self.enable_plugins = os.getenv("MARKITDOWN_ENABLE_PLUGINS", "false").lower() == "true"
        self.docintel_endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        self.docintel_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        self.llm_model = os.getenv("MARKITDOWN_LLM_MODEL", "gpt-4o")

    def create_markitdown(self, openai_client=None):
        """Create configured MarkItDown instance."""
        kwargs = {
            "enable_plugins": self.enable_plugins,
        }

        if self.docintel_endpoint:
            kwargs["docintel_endpoint"] = self.docintel_endpoint
        if self.docintel_key:
            kwargs["docintel_key"] = self.docintel_key
        if openai_client:
            kwargs["llm_client"] = openai_client
            kwargs["llm_model"] = self.llm_model

        return MarkItDown(**kwargs)

# Usage
config = MarkItDownConfig()
md = config.create_markitdown()
```

## 📊 Working with Results

### Document Information

```python
result = md.convert("document.pdf")

# Basic information
print(f"Title: {result.title}")
print(f"Content length: {len(result.text_content)} characters")

# Metadata
if result.metadata:
    print("\nMetadata:")
    for key, value in result.metadata.items():
        print(f"  {key}: {value}")

# References (if any)
if result.references:
    print("\nReferences:")
    for ref in result.references:
        print(f"  - {ref}")

# Errors/warnings
if result.errors:
    print("\nWarnings:")
    for error in result.errors:
        print(f"  - {error}")
```

### Content Processing

```python
import re

def process_markdown(content: str) -> dict:
    """Extract structured information from Markdown content."""

    # Extract headings
    headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)

    # Extract links
    links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)

    # Extract tables
    tables = re.findall(r'\|(.+)\|\n\|[-\s\|]+\|\n((?:\|.+\|\n?)*)', content)

    # Count words
    word_count = len(content.split())

    return {
        "headings": [{"level": len(h[0]), "text": h[1]} for h in headings],
        "links": [{"text": l[0], "url": l[1]} for l in links],
        "table_count": len(tables),
        "word_count": word_count,
        "content": content
    }

# Usage
result = md.convert("research_paper.pdf")
processed = process_markdown(result.text_content)

print(f"Document Analysis:")
print(f"  Headings: {len(processed['headings'])}")
print(f"  Links: {len(processed['links'])}")
print(f"  Tables: {processed['table_count']}")
print(f"  Word count: {processed['word_count']}")
```

## 🔍 Common Use Cases

### Research Paper Processing

```python
def process_research_paper(pdf_path: str) -> dict:
    """Extract structured information from research paper."""
    md = MarkItDown()

    # Convert PDF
    result = md.convert(pdf_path)
    content = result.text_content

    # Extract sections
    sections = {}
    current_section = "Introduction"
    current_content = []

    for line in content.split('\n'):
        if line.startswith('#'):
            # Save previous section
            if current_content:
                sections[current_section] = '\n'.join(current_content)

            # Start new section
            current_section = line.lstrip('# ').strip()
            current_content = []
        else:
            current_content.append(line)

    # Save last section
    if current_content:
        sections[current_section] = '\n'.join(current_content)

    return {
        "title": result.title,
        "sections": sections,
        "metadata": result.metadata,
        "full_content": content
    }

# Usage
paper = process_research_paper("research_paper.pdf")
print(f"Paper Title: {paper['title']}")
print(f"Sections: {list(paper['sections'].keys())}")
```

### Meeting Notes Processing

```python
def process_meeting_audio(audio_path: str) -> str:
    """Convert meeting audio to structured notes."""
    md = MarkItDown()

    # Transcribe audio
    result = md.convert(audio_path)
    transcript = result.text_content

    # Add meeting note structure
    structured_notes = f"""# Meeting Notes

## Transcript
{transcript}

## Metadata
- **Source**: {audio_path}
- **Converted**: {result.metadata.get('conversion_time', 'Unknown')}
- **Duration**: {result.metadata.get('duration', 'Unknown')}

---
*Generated by MarkItDown*
"""

    return structured_notes

# Usage
notes = process_meeting_audio("team_meeting.mp3")
with open("meeting_notes.md", "w") as f:
    f.write(notes)
```

### Document Archive Migration

```python
def migrate_document_archive(source_dir: str, target_dir: str):
    """Convert all documents in directory to Markdown."""
    import os
    from pathlib import Path

    md = MarkItDown(enable_plugins=True)

    # Create target directory
    Path(target_dir).mkdir(parents=True, exist_ok=True)

    # Supported extensions
    supported_exts = {'.pdf', '.docx', '.pptx', '.xlsx', '.txt', '.html', '.md'}

    for root, dirs, files in os.walk(source_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1].lower()

            if file_ext in supported_exts:
                try:
                    # Convert document
                    result = md.convert(file_path)

                    # Create output path
                    rel_path = os.path.relpath(file_path, source_dir)
                    output_path = os.path.join(target_dir, rel_path.replace(file_ext, '.md'))

                    # Create output directory
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)

                    # Save result
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(result.text_content)

                    print(f"✅ Converted: {file_path} -> {output_path}")

                except Exception as e:
                    print(f"❌ Failed: {file_path} - {e}")

# Usage
migrate_document_archive("old_documents/", "markdown_archive/")
```

## 🚀 Performance Tips

### Efficient Batch Processing

```python
from concurrent.futures import ThreadPoolExecutor
import time

def convert_file(file_path: str, md: MarkItDown) -> tuple:
    """Convert single file with error handling."""
    try:
        start_time = time.time()
        result = md.convert(file_path)
        conversion_time = time.time() - start_time

        return file_path, result.text_content, conversion_time, None
    except Exception as e:
        return file_path, None, 0, str(e)

def batch_convert_parallel(file_paths: list, max_workers: int = 4):
    """Convert multiple files in parallel."""
    md = MarkItDown(enable_plugins=True)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(convert_file, path, md) for path in file_paths]

        results = []
        for future in futures:
            file_path, content, conv_time, error = future.result()
            results.append({
                "file": file_path,
                "content": content,
                "conversion_time": conv_time,
                "error": error
            })

    return results

# Usage
import glob
files = glob.glob("documents/*.pdf")
results = batch_convert_parallel(files)

# Print summary
successful = sum(1 for r in results if not r["error"])
failed = len(results) - successful
total_time = sum(r["conversion_time"] for r in results)

print(f"Conversion Summary:")
print(f"  Successful: {successful}")
print(f"  Failed: {failed}")
print(f"  Total time: {total_time:.2f}s")
print(f"  Average time per file: {total_time/len(results):.2f}s")
```

This quick start guide provides practical examples for the most common MarkItDown use cases, helping you get productive quickly with the library.