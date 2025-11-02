# Azure Document Intelligence Integration

MarkItDown supports Azure Document Intelligence (formerly Form Recognizer) for enhanced document processing capabilities, including advanced OCR, form field extraction, and layout analysis.

## 🌟 Overview

Azure Document Intelligence provides cloud-based API services that use machine learning to extract text, key-value pairs, tables, and structures from documents automatically. When integrated with MarkItDown, it significantly improves conversion quality for:

- **Scanned documents and PDFs**
- **Complex layouts and forms**
- **Handwritten text recognition**
- **Multi-language documents**
- **Tables and structured data**
- **Business cards and invoices**

## 🚀 Setup and Configuration

### Prerequisites

1. **Azure Account** - Active Azure subscription
2. **Document Intelligence Resource** - Created in Azure portal
3. **API Key and Endpoint** - From your Azure resource

### Create Azure Document Intelligence Resource

1. **Sign in to Azure Portal** - [portal.azure.com](https://portal.azure.com)
2. **Create a resource**:
   - Search for "Document Intelligence" or "Form Recognizer"
   - Click "Create"
   - Fill in required fields:
     - **Subscription**: Your Azure subscription
     - **Resource group**: Create new or use existing
     - **Resource name**: Unique name (e.g., "my-doc-intel")
     - **Region**: Choose nearest region
     - **Pricing tier**: F0 (free) or S0 (standard)
3. **Review and create** the resource
4. **Get credentials** from the resource overview page:
   - **Endpoint**: URL like `https://your-resource.cognitiveservices.azure.com/`
   - **Key**: API key (either Key 1 or Key 2)

### Environment Variables

```bash
# Set environment variables
export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://your-resource.cognitiveservices.azure.com/"
export AZURE_DOCUMENT_INTELLIGENCE_KEY="your-api-key-here"
```

### Configuration in Code

```python
from markitdown import MarkItDown

# Method 1: Using environment variables
md = MarkItDown(docintel_enabled=True)

# Method 2: Explicit configuration
md = MarkItDown(
    docintel_endpoint="https://your-resource.cognitiveservices.azure.com/",
    docintel_key="your-api-key"
)

# Method 3: Using Azure AD authentication
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
md = MarkItDown(
    docintel_endpoint="https://your-resource.cognitiveservices.azure.com/",
    docintel_credential=credential
)
```

## 🔌 Integration Methods

### Method 1: Automatic Detection

MarkItDown automatically uses Azure Document Intelligence when enabled and available:

```python
from markitdown import MarkItDown

# Enable with environment variables
md = MarkItDown(docintel_enabled=True)

# Convert any supported document
result = md.convert("scanned_document.pdf")
print(result.text_content)
```

### Method 2: CLI Usage

```bash
# Enable with environment variables
export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://your-resource.cognitiveservices.azure.com/"
export AZURE_DOCUMENT_INTELLIGENCE_KEY="your-key"

# Use Azure Document Intelligence
markitdown document.pdf -d

# Or specify endpoint explicitly
markitdown document.pdf -d -e "https://your-resource.cognitiveservices.azure.com/" -k "your-key"
```

### Method 3: Selective Usage

```python
from markitdown import MarkItDown

# Create instances with and without Azure
md_standard = MarkItDown()
md_azure = MarkItDown(docintel_enabled=True)

# Use standard converter for some files
standard_result = md_standard.convert("simple_document.pdf")

# Use Azure for complex files
azure_result = md_azure.convert("complex_scan.pdf")
```

## 📋 Supported Document Types

### PDF Documents
- **Text-based PDFs** - Enhanced text extraction
- **Scanned PDFs** - OCR with high accuracy
- **Mixed PDFs** - Combination of text and images

### Image Files
- **JPEG/JPG**, **PNG**, **BMP**, **TIFF**
- **High-resolution scans** - Up to 10,000 x 10,000 pixels
- **Multi-page TIFFs** - Each page processed separately

### Specific Document Types
- **Invoices** - Field extraction and structure recognition
- **Receipts** - Itemized data extraction
- **Business cards** - Contact information extraction
- **Forms** - Field value extraction

## 🎯 Advanced Features

### Layout Analysis

Azure Document Intelligence provides superior layout analysis:

```python
# Complex document with tables, headers, footers
result = md.convert("complex_report.pdf")

# Output preserves:
# - Table structure
# - Header/footer hierarchy
# - Column layouts
# - Text positioning
print(result.text_content)
```

### Handwriting Recognition

```python
# Document with handwritten annotations
result = md.convert("annotated_document.pdf")

# Handwritten text is included in output
print(result.text_content)
```

### Multi-language Support

```python
# Documents in multiple languages
result = md.convert("multilingual_document.pdf")

# Text is preserved with original language
# Language detection is automatic
print(result.text_content)
```

### Table Extraction

```python
# Document with complex tables
result = md.convert("financial_statement.pdf")

# Tables are converted to Markdown format:
# | Header 1 | Header 2 | Header 3 |
# |----------|----------|----------|
# | Data 1   | Data 2   | Data 3   |
print(result.text_content)
```

## ⚙️ Configuration Options

### Model Selection

```python
# Use specific analysis models (advanced usage)
md = MarkItDown(
    docintel_endpoint="https://your-resource.cognitiveservices.azure.com/",
    docintel_key="your-key",
    docintel_model="prebuilt-read"  # Options: "prebuilt-read", "prebuilt-layout", "prebuilt-document"
)
```

**Available Models:**
- `prebuilt-read` - General text extraction (default)
- `prebuilt-layout` - Layout analysis with tables
- `prebuilt-document` - General document model
- `prebuilt-invoice` - Invoice-specific extraction
- `prebuilt-receipt` - Receipt-specific extraction

### Custom Parameters

```python
# Configure advanced options
md = MarkItDown(
    docintel_endpoint="https://your-resource.cognitiveservices.azure.com/",
    docintel_key="your-key",
    docintel_language="en",  # Specify language (ISO 639-1 code)
    docintel_pages="1-3,5"   # Specify page ranges
)
```

## 🔍 Usage Examples

### Basic Document Processing

```python
from markitdown import MarkItDown

# Initialize with Azure Document Intelligence
md = MarkItDown(docintel_enabled=True)

# Convert scanned document
result = md.convert("scanned_contract.pdf")

print("Title:", result.title)
print("Content preview:", result.text_content[:500])
print("Metadata:", result.metadata)
```

### Batch Processing with Azure

```python
import glob
from markitdown import MarkItDown

md = MarkItDown(docintel_enabled=True)

# Process all PDFs in directory
for pdf_file in glob.glob("scanned_documents/*.pdf"):
    try:
        result = md.convert(pdf_file)

        # Save to corresponding .md file
        output_path = pdf_file.replace(".pdf", "_azure.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.text_content)

        print(f"✅ Processed with Azure: {pdf_file}")

    except Exception as e:
        print(f"❌ Failed: {pdf_file} - {e}")
```

### Comparison: Standard vs Azure Processing

```python
from markitdown import MarkItDown

# Create two instances
md_standard = MarkItDown()
md_azure = MarkItDown(docintel_enabled=True)

# Process the same document
document_path = "challenging_scan.pdf"

# Standard processing
result_standard = md_standard.convert(document_path)

# Azure processing
result_azure = md_azure.convert(document_path)

# Compare results
print("=== Standard Processing ===")
print(f"Length: {len(result_standard.text_content)} characters")
print(f"Preview:\n{result_standard.text_content[:300]}")

print("\n=== Azure Processing ===")
print(f"Length: {len(result_azure.text_content)} characters")
print(f"Preview:\n{result_azure.text_content[:300]}")
```

### Error Handling and Fallback

```python
from markitdown import MarkItDown
from markitdown._exceptions import MarkItDownException

def convert_with_fallback(file_path: str):
    """Convert with Azure Document Intelligence and fallback to standard."""

    # Try Azure first
    try:
        md_azure = MarkItDown(docintel_enabled=True)
        result = md_azure.convert(file_path)
        print(f"✅ Azure processing successful: {file_path}")
        return result

    except Exception as azure_error:
        print(f"⚠️ Azure processing failed: {azure_error}")

        # Fallback to standard processing
        try:
            md_standard = MarkItDown()
            result = md_standard.convert(file_path)
            print(f"✅ Standard processing successful: {file_path}")
            return result

        except Exception as standard_error:
            print(f"❌ Both methods failed: {standard_error}")
            raise

# Usage
result = convert_with_fallback("document.pdf")
```

## 📊 Performance Considerations

### Processing Speed

```python
import time
from markitdown import MarkItDown

md_azure = MarkItDown(docintel_enabled=True)

# Measure processing time
start_time = time.time()
result = md_azure.convert("large_document.pdf")
processing_time = time.time() - start_time

print(f"Processing time: {processing_time:.2f} seconds")
print(f"Document length: {len(result.text_content)} characters")
print(f"Processing speed: {len(result.text_content)/processing_time:.0f} chars/sec")
```

### Cost Optimization

```python
# Use Azure selectively based on document characteristics
import os
from markitdown import MarkItDown

def should_use_azure(file_path: str) -> bool:
    """Determine if Azure Document Intelligence should be used."""

    # File size threshold (5MB)
    file_size = os.path.getsize(file_path)
    if file_size > 5 * 1024 * 1024:
        return False  # Too large for cost efficiency

    # File extension
    if file_path.endswith(('.txt', '.md', '.html')):
        return False  # Text-based files don't need OCR

    # Use for images and PDFs
    return file_path.endswith(('.pdf', '.jpg', '.jpeg', '.png', '.tiff'))

def smart_convert(file_path: str):
    """Convert using optimal method."""

    if should_use_azure(file_path):
        md = MarkItDown(docintel_enabled=True)
        print(f"🤖 Using Azure Document Intelligence: {file_path}")
    else:
        md = MarkItDown()
        print(f"📄 Using standard processing: {file_path}")

    return md.convert(file_path)

# Usage
result = smart_convert("document.pdf")
```

### Batch Processing with Rate Limits

```python
import time
from markitdown import MarkItDown

def batch_convert_with_rate_limit(file_paths: list, requests_per_second: int = 5):
    """Convert files with Azure Document Intelligence, respecting rate limits."""

    md = MarkItDown(docintel_enabled=True)
    delay = 1.0 / requests_per_second

    results = []

    for i, file_path in enumerate(file_paths):
        try:
            result = md.convert(file_path)
            results.append({"file": file_path, "result": result, "error": None})
            print(f"✅ Processed {i+1}/{len(file_paths)}: {file_path}")

        except Exception as e:
            results.append({"file": file_path, "result": None, "error": str(e)})
            print(f"❌ Failed {i+1}/{len(file_paths)}: {file_path} - {e}")

        # Rate limiting
        if i < len(file_paths) - 1:  # Don't sleep after last file
            time.sleep(delay)

    return results

# Usage
import glob
pdf_files = glob.glob("documents/*.pdf")[:10]  # Limit to 10 files
results = batch_convert_with_rate_limit(pdf_files, requests_per_second=3)
```

## 🚨 Troubleshooting

### Common Issues

#### Authentication Errors

```python
# Test Azure credentials
from markitdown import MarkItDown

try:
    md = MarkItDown(
        docintel_endpoint="https://your-resource.cognitiveservices.azure.com/",
        docintel_key="your-key"
    )

    # Test with a simple document
    result = md.convert("test.pdf")
    print("✅ Azure Document Intelligence is working!")

except Exception as e:
    print(f"❌ Azure setup failed: {e}")
    print("Check your endpoint URL and API key")
```

#### Network Issues

```python
# Test connectivity
import requests

endpoint = "https://your-resource.cognitiveservices.azure.com/"
try:
    response = requests.get(endpoint, timeout=10)
    print(f"✅ Endpoint reachable: {response.status_code}")
except requests.RequestException as e:
    print(f"❌ Network issue: {e}")
```

#### Quota Exceeded

```python
# Handle quota limits gracefully
from markitdown import MarkItDown
from markitdown._exceptions import MarkItDownException

def convert_with_quota_handling(file_path: str, max_retries: int = 3):
    """Convert with retry logic for quota limits."""

    md = MarkItDown(docintel_enabled=True)

    for attempt in range(max_retries):
        try:
            return md.convert(file_path)

        except MarkItDownException as e:
            if "quota" in str(e).lower() and attempt < max_retries - 1:
                wait_time = (attempt + 1) * 30  # 30s, 60s, 90s
                print(f"⚠️ Quota limit reached, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise

# Usage
try:
    result = convert_with_quota_handling("document.pdf")
except Exception as e:
    print(f"❌ Conversion failed: {e}")
```

### Debug Information

```python
import logging
from markitdown import MarkItDown

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

md = MarkItDown(docintel_enabled=True)

# The logs will show:
# - Azure endpoint configuration
# - API request details
# - Processing status
# - Error information
result = md.convert("document.pdf")
```

## 📈 Best Practices

### 1. Use Azure Selectively

```python
# Define criteria for when to use Azure Document Intelligence
def should_use_azure(file_path: str, file_size: int = None) -> bool:
    """Determine if Azure Document Intelligence provides value."""

    if file_size is None:
        file_size = os.path.getsize(file_path)

    # Use for image-based content
    if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff', '.bmp')):
        return True

    # Use for PDFs that are likely scanned
    if file_path.lower().endswith('.pdf') and file_size > 100 * 1024:  # > 100KB
        return True

    return False
```

### 2. Implement Caching

```python
import hashlib
import os
from pathlib import Path

class CachedMarkItDown:
    def __init__(self, cache_dir: str = "markitdown_cache"):
        self.md = MarkItDown(docintel_enabled=True)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def convert(self, file_path: str):
        """Convert with caching."""

        # Create cache key
        file_stat = os.stat(file_path)
        cache_key = f"{file_path}_{file_stat.st_size}_{file_stat.st_mtime}"
        cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_hash}.md"

        # Check cache
        if cache_file.exists():
            print(f"📋 Using cached result: {file_path}")
            with open(cache_file, 'r', encoding='utf-8') as f:
                content = f.read()

            return type('Result', (), {'text_content': content})()

        # Convert and cache
        print(f"🤖 Processing with Azure: {file_path}")
        result = self.md.convert(file_path)

        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(result.text_content)

        return result

# Usage
cached_md = CachedMarkItDown()
result = cached_md.convert("document.pdf")
```

### 3. Monitor Usage and Costs

```python
import time
from collections import defaultdict

class AzureUsageTracker:
    def __init__(self):
        self.usage = defaultdict(list)
        self.md = MarkItDown(docintel_enabled=True)

    def convert(self, file_path: str):
        """Convert while tracking usage."""

        start_time = time.time()
        file_size = os.path.getsize(file_path)

        try:
            result = self.md.convert(file_path)
            processing_time = time.time() - start_time

            # Track usage
            self.usage['files'].append({
                'path': file_path,
                'size': file_size,
                'time': processing_time,
                'success': True,
                'timestamp': time.time()
            })

            return result

        except Exception as e:
            processing_time = time.time() - start_time

            # Track failed usage
            self.usage['files'].append({
                'path': file_path,
                'size': file_size,
                'time': processing_time,
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            })

            raise

    def get_usage_summary(self):
        """Get usage statistics."""
        files = self.usage['files']

        if not files:
            return "No usage data available"

        successful = [f for f in files if f['success']]
        failed = [f for f in files if not f['success']]

        total_size = sum(f['size'] for f in successful)
        total_time = sum(f['time'] for f in successful)

        return {
            'total_files': len(files),
            'successful': len(successful),
            'failed': len(failed),
            'total_size_mb': total_size / (1024 * 1024),
            'total_time_seconds': total_time,
            'average_time_per_file': total_time / len(successful) if successful else 0,
            'estimated_api_calls': len(successful)
        }

# Usage
tracker = AzureUsageTracker()
result = tracker.convert("document.pdf")
print(tracker.get_usage_summary())
```

---

Azure Document Intelligence significantly enhances MarkItDown's capabilities for processing complex, scanned, or image-based documents. The integration is designed to be seamless while providing the flexibility to optimize for cost, performance, and quality requirements.