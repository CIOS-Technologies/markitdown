# LLM Integration Guide

MarkItDown supports integration with Large Language Models (LLMs) to enhance document processing, particularly for image descriptions, content analysis, and intelligent document summarization.

## 🌟 Overview

LLM integration in MarkItDown enables:
- **Image Description**: Generate detailed descriptions of images and diagrams
- **Content Enhancement**: Improve document structure and readability
- **Intelligent Summarization**: Create concise summaries of long documents
- **Content Analysis**: Extract key information and insights
- **Multimodal Processing**: Handle text, images, and structured data together

## 🚀 Supported LLM Providers

### Google Gemini (Recommended for Images)
- **Gemini 2.5 Flash** - Fast, cost-effective vision model with advanced prompts
- **Context-aware descriptions** - Understands document context around images
- **Smart filtering** - Automatically skips UI elements, focuses on content visualizations
- **PDF image extraction** - Extracts and processes images directly from PDFs

### OpenAI Models
- **GPT-4o** - Multimodal model with vision capabilities
- **GPT-4 Turbo** - High-performance text generation
- **GPT-3.5 Turbo** - Cost-effective text processing

### Azure OpenAI
- **Azure-hosted GPT models** - Enterprise security and compliance
- **Custom deployments** - Private model instances

### Other Compatible Models
- **Any OpenAI-compatible API** - Custom model endpoints
- **Local models** - Self-hosted solutions with OpenAI-compatible APIs

## ⚙️ Setup and Configuration

### 1. Google Gemini Setup (Recommended for Image Descriptions)

Gemini provides excellent image description capabilities with context-aware prompts optimized for business documents and visualizations.

```python
from markitdown import MarkItDown

# Method 1: Using API key parameter
md = MarkItDown(
    gemini_api_key="your-gemini-api-key",
    llm_model="gemini-2.5-flash"
)

# Method 2: Using environment variable
import os
os.environ['GEMINI_API_KEY'] = "your-gemini-api-key"
md = MarkItDown(llm_model="gemini-2.5-flash")

# Convert documents with image descriptions
result = md.convert("document.pdf")  # Extracts images from PDF automatically
result = md.convert("presentation.pptx")  # Uses slide context for descriptions
result = md.convert("image.png")  # Direct image description
```

**Key Features:**
- **Automatic image extraction** from PDFs - no links required
- **Context-aware descriptions** - uses surrounding text for better accuracy
- **Smart filtering** - skips UI elements, focuses on charts/diagrams
- **Advanced prompts** - optimized for business visualizations

**Get your Gemini API key:** [Google AI Studio](https://makersuite.google.com/app/apikey)

### 2. OpenAI API Setup

```python
from openai import OpenAI
from markitdown import MarkItDown

# Initialize OpenAI client
client = OpenAI(api_key="your-openai-api-key")

# Configure MarkItDown with LLM
md = MarkItDown(
    llm_client=client,
    llm_model="gpt-4o",
    llm_prompt="Describe this image in detail for document accessibility"
)
```

### 2. Azure OpenAI Setup

```python
from openai import AzureOpenAI
from markitdown import MarkItDown

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key="your-azure-api-key",
    api_version="2024-02-15-preview",
    azure_endpoint="https://your-resource.openai.azure.com/"
)

# Configure MarkItDown
md = MarkItDown(
    llm_client=client,
    llm_model="gpt-4o",  # or your deployment name
    llm_prompt="Analyze this content and provide a structured summary"
)
```

### 3. Environment Variable Configuration

```bash
# Set Gemini API key (recommended for images)
export GEMINI_API_KEY="your-gemini-api-key"

# Set OpenAI API key
export OPENAI_API_KEY="your-openai-api-key"

# Set Azure OpenAI credentials
export AZURE_OPENAI_API_KEY="your-azure-api-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
```

### 4. Custom LLM Client Setup

```python
import requests
from markitdown import MarkItDown

class CustomLLMClient:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key

    def chat_completions_create(self, **kwargs):
        """Mimic OpenAI client interface."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Convert OpenAI format to your API format
        payload = {
            "model": kwargs.get("model", "default"),
            "messages": kwargs.get("messages", []),
            "max_tokens": kwargs.get("max_tokens", 1000)
        }

        response = requests.post(self.api_url, json=payload, headers=headers)
        return response.json()

# Use custom client
custom_client = CustomLLMClient("https://your-api.com/v1/chat", "your-api-key")
md = MarkItDown(llm_client=custom_client, llm_model="your-model")
```

## 🎯 Core Features

### Image Description Generation

#### Using Gemini (Recommended)

```python
from markitdown import MarkItDown

# Gemini with automatic image extraction from PDFs
md = MarkItDown(
    gemini_api_key="your-gemini-api-key",
    llm_model="gemini-2.5-flash"
)

# Convert PDF - images are automatically extracted and processed
result = md.convert("document_with_charts.pdf")
print(result.text_content)

# Output includes AI-generated descriptions:
# **[AI-Generated Image Description]**
# Bar Chart. The chart displays quarterly revenue data...
```

#### Using OpenAI

```python
from openai import OpenAI
from markitdown import MarkItDown

client = OpenAI()
md = MarkItDown(
    llm_client=client,
    llm_model="gpt-4o",
    llm_prompt="Describe this image in detail, focusing on data visualizations and key insights"
)

# Convert PowerPoint with images
result = md.convert("presentation_with_charts.pptx")
print(result.text_content)

# Output includes:
# ![Chart showing quarterly revenue growth](data:image/jpeg;base64,...)
#
# *Image Description: The chart displays quarterly revenue data from Q1 2023 to Q4 2023.
# Revenue shows consistent growth with Q4 achieving the highest at $2.5M,
# representing a 25% increase from Q1.*
```

#### Key Differences

| Feature | Gemini | OpenAI |
|---------|--------|--------|
| **PDF Image Extraction** | ✅ Automatic | ❌ Link-based only |
| **Context Awareness** | ✅ Yes | ❌ Limited |
| **Smart Filtering** | ✅ Skips UI elements | ❌ No |
| **Cost** | Lower | Higher |
| **Speed** | Fast | Medium |

### Custom Prompts for Different Use Cases

```python
# Academic paper processing
md_academic = MarkItDown(
    llm_client=client,
    llm_model="gpt-4o",
    llm_prompt="""Analyze this academic figure and provide:
1. A clear description of what the figure shows
2. Key findings or data points
3. Methodology if applicable
4. Implications for the research"""
)

# Business document processing
md_business = MarkItDown(
    llm_client=client,
    llm_model="gpt-4o",
    llm_prompt="Analyze this business chart and extract actionable insights, trends, and recommendations for stakeholders."
)

# Technical documentation
md_tech = MarkItDown(
    llm_client=client,
    llm_model="gpt-4o",
    llm_prompt="Describe this technical diagram, explaining architecture, data flow, and component relationships."
)
```

### Content Enhancement and Summarization

```python
def enhance_document_with_llm(file_path: str, focus_area: str = "key_insights"):
    """Enhance document with LLM-generated insights."""

    prompts = {
        "key_insights": "Extract the 5 most important insights from this document and explain their significance.",
        "executive_summary": "Create a concise executive summary (200 words max) of this document.",
        "action_items": "Identify action items, decisions, and next steps from this document.",
        "risks_challenges": "Analyze this document for potential risks, challenges, and mitigation strategies."
    }

    md = MarkItDown(
        llm_client=client,
        llm_model="gpt-4o",
        llm_prompt=prompts.get(focus_area, prompts["key_insights"])
    )

    result = md.convert(file_path)
    return result

# Usage
summary = enhance_document_with_llm("business_report.pdf", "executive_summary")
print(summary.text_content)
```

## 🔧 Advanced Configuration

### Prompt Engineering

```python
# Structured prompts for consistent output
structured_prompt = """
Analyze this image and provide a structured description in the following format:

## Image Overview
[Brief description of what the image shows]

## Key Elements
- Element 1: [Description]
- Element 2: [Description]

## Data Insights
[If applicable, describe data, trends, or metrics]

## Accessibility Notes
[Information for visually impaired users]

## Technical Details
[Resolution, format, or other technical information]
"""

md = MarkItDown(
    llm_client=client,
    llm_model="gpt-4o",
    llm_prompt=structured_prompt
)
```

### Model Parameter Tuning

```python
class EnhancedMarkItDown:
    def __init__(self, client, model="gpt-4o"):
        self.client = client
        self.model = model
        self.base_md = MarkItDown()

    def convert_with_custom_params(self, file_path: str, **llm_params):
        """Convert with custom LLM parameters."""

        # Default parameters
        default_params = {
            "max_tokens": 1000,
            "temperature": 0.3,  # Lower temperature for more consistent output
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1
        }

        # Merge with custom parameters
        params = {**default_params, **llm_params}

        # Custom processing logic
        # (This would require extending the base MarkItDown class)
        return self._process_with_llm(file_path, params)

# Usage
enhanced_md = EnhancedMarkItDown(client)
result = enhanced_md.convert_with_custom_params(
    "chart.png",
    max_tokens=1500,
    temperature=0.2
)
```

### Batch Processing with LLM

```python
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class LLMBatchProcessor:
    def __init__(self, client, model="gpt-4o", max_workers=3, rate_limit=1.0):
        self.client = client
        self.model = model
        self.max_workers = max_workers
        self.rate_limit = rate_limit  # Seconds between requests

    def process_batch(self, file_paths: list, prompt: str = None):
        """Process multiple files with LLM enhancement."""

        if prompt is None:
            prompt = "Describe this image in detail for document accessibility."

        md = MarkItDown(
            llm_client=self.client,
            llm_model=self.model,
            llm_prompt=prompt
        )

        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self._convert_with_delay, md, file_path): file_path
                for file_path in file_paths
            }

            # Collect results
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results.append({
                        'file': file_path,
                        'result': result,
                        'success': True
                    })
                    print(f"✅ Processed: {file_path}")

                except Exception as e:
                    results.append({
                        'file': file_path,
                        'result': None,
                        'success': False,
                        'error': str(e)
                    })
                    print(f"❌ Failed: {file_path} - {e}")

        return results

    def _convert_with_delay(self, md, file_path: str):
        """Convert with rate limiting delay."""
        if hasattr(self, '_last_request_time'):
            elapsed = time.time() - self._last_request_time
            if elapsed < self.rate_limit:
                time.sleep(self.rate_limit - elapsed)

        result = md.convert(file_path)
        self._last_request_time = time.time()
        return result

# Usage
processor = LLMBatchProcessor(client, max_workers=2, rate_limit=2.0)
files = ["chart1.png", "chart2.png", "diagram.jpg"]
results = processor.process_batch(files)
```

## 📊 Use Cases and Examples

### 1. Academic Research Paper Processing

```python
def process_research_paper(pdf_path: str):
    """Process academic paper with enhanced figure descriptions."""

    # Specialized prompt for academic figures
    academic_prompt = """
    Analyze this academic figure and provide:

    ## Figure Type
    [Chart, graph, diagram, table, etc.]

    ## Key Findings
    [Main insights or discoveries shown]

    ## Methodology Context
    [How this data was collected or generated]

    ## Implications
    [What this means for the research field]

    ## Statistical Information
    [Sample sizes, confidence intervals, p-values, etc.]
    """

    md = MarkItDown(
        llm_client=client,
        llm_model="gpt-4o",
        llm_prompt=academic_prompt
    )

    result = md.convert(pdf_path)

    # Add additional processing
    enhanced_content = enhance_academic_content(result.text_content)

    return type('Result', (), {
        'text_content': enhanced_content,
        'title': result.title,
        'metadata': result.metadata
    })()

def enhance_academic_content(content: str) -> str:
    """Add academic structure to processed content."""

    sections = [
        "# Enhanced Research Paper Analysis",
        "",
        "## Abstract Summary",
        extract_abstract(content),
        "",
        "## Key Findings",
        extract_findings(content),
        "",
        content,  # Original processed content
        "",
        "## References and Citations",
        extract_references(content)
    ]

    return "\n".join(sections)
```

### 2. Business Document Analysis

```python
def analyze_business_document(file_path: str):
    """Analyze business document for insights and recommendations."""

    business_prompt = """
    Analyze this business content and provide:

    ## Executive Summary
    [Key business insights in 2-3 sentences]

    ## Financial Implications
    [Cost, revenue, or ROI considerations]

    ## Strategic Recommendations
    [Actionable recommendations for stakeholders]

    ## Risk Assessment
    [Potential risks and mitigation strategies]

    ## Timeline Considerations
    [Urgency, deadlines, or scheduling implications]
    """

    md = MarkItDown(
        llm_client=client,
        llm_model="gpt-4o",
        llm_prompt=business_prompt
    )

    result = md.convert(file_path)

    # Extract and enhance business insights
    insights = extract_business_insights(result.text_content)

    return {
        'original_content': result.text_content,
        'insights': insights,
        'recommendations': generate_recommendations(insights)
    }

def extract_business_insights(content: str) -> dict:
    """Extract structured business insights from content."""

    # This would use NLP techniques or additional LLM calls
    # to extract specific business metrics and insights

    return {
        'key_metrics': [],
        'trends': [],
        'risks': [],
        'opportunities': []
    }
```

### 3. Technical Documentation Enhancement

```python
def enhance_technical_documentation(file_path: str):
    """Enhance technical documentation with better explanations."""

    tech_prompt = """
    Analyze this technical diagram or documentation and provide:

    ## Component Overview
    [Description of all major components]

    ## Data Flow
    [How information flows through the system]

    ## Dependencies
    [Components or services that depend on each other]

    ## Performance Considerations
    [Scalability, bottlenecks, or optimization opportunities]

    ## Security Notes
    [Security implications or considerations]
    """

    md = MarkItDown(
        llm_client=client,
        llm_model="gpt-4o",
        llm_prompt=tech_prompt
    )

    result = md.convert(file_path)

    # Add technical structure
    enhanced = add_technical_structure(result.text_content)

    return enhanced

def add_technical_structure(content: str) -> str:
    """Add structured technical documentation elements."""

    structured_content = f"""# Technical Documentation

## Table of Contents
{generate_toc(content)}

---

{content}

## API References
{extract_api_info(content)}

## Troubleshooting
{generate_troubleshooting(content)}
"""

    return structured_content
```

## 🔍 Monitoring and Optimization

### Usage Tracking

```python
import time
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class LLMUsageMetrics:
    request_count: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    average_response_time: float = 0.0
    error_count: int = 0

class LLMUsageTracker:
    def __init__(self, cost_per_token: float = 0.00001):  # Approximate cost
        self.cost_per_token = cost_per_token
        self.metrics = LLMUsageMetrics()
        self.request_times: List[float] = []

    def track_request(self, tokens_used: int, response_time: float, success: bool = True):
        """Track LLM usage metrics."""

        self.metrics.request_count += 1
        self.metrics.total_tokens += tokens_used
        self.metrics.total_cost += tokens_used * self.cost_per_token
        self.request_times.append(response_time)

        if not success:
            self.metrics.error_count += 1

        # Update average response time
        self.metrics.average_response_time = sum(self.request_times) / len(self.request_times)

    def get_summary(self) -> Dict:
        """Get usage summary."""
        return {
            'requests': self.metrics.request_count,
            'total_tokens': self.metrics.total_tokens,
            'total_cost': self.metrics.total_cost,
            'avg_response_time': self.metrics.average_response_time,
            'error_rate': self.metrics.error_count / max(1, self.metrics.request_count)
        }

# Usage
tracker = LLMUsageTracker()

# Wrap MarkItDown to track usage
class TrackedMarkItDown:
    def __init__(self, client, model="gpt-4o", tracker=None):
        self.md = MarkItDown(llm_client=client, llm_model=model)
        self.tracker = tracker or LLMUsageTracker()

    def convert(self, file_path: str):
        """Convert with usage tracking."""
        start_time = time.time()

        try:
            result = self.md.convert(file_path)
            response_time = time.time() - start_time

            # Estimate tokens (rough approximation)
            estimated_tokens = len(result.text_content.split()) * 1.3

            self.tracker.track_request(estimated_tokens, response_time, success=True)
            return result

        except Exception as e:
            response_time = time.time() - start_time
            self.tracker.track_request(0, response_time, success=False)
            raise

# Usage
tracked_md = TrackedMarkItDown(client, tracker=tracker)
result = tracked_md.convert("document.pdf")
print(tracker.get_summary())
```

### Cost Optimization

```python
class CostOptimizedProcessor:
    def __init__(self, client, budget_limit: float = 10.0):
        self.client = client
        self.budget_limit = budget_limit
        self.current_spend = 0.0
        self.cost_per_token = 0.00001

    def can_process(self, estimated_tokens: int) -> bool:
        """Check if processing fits within budget."""
        estimated_cost = estimated_tokens * self.cost_per_token
        return (self.current_spend + estimated_cost) <= self.budget_limit

    def process_with_budget_check(self, file_path: str):
        """Process file with budget validation."""

        # Estimate file complexity (rough heuristic)
        file_size = os.path.getsize(file_path)
        estimated_tokens = file_size // 4  # Rough estimate

        if not self.can_process(estimated_tokens):
            raise ValueError(f"Processing would exceed budget limit of ${self.budget_limit}")

        # Use smaller model for cost savings if budget is tight
        if self.budget_limit - self.current_spend < 5.0:
            model = "gpt-3.5-turbo"
        else:
            model = "gpt-4o"

        md = MarkItDown(
            llm_client=self.client,
            llm_model=model,
            llm_prompt="Provide a concise description of this image."
        )

        result = md.convert(file_path)

        # Update spend
        actual_tokens = len(result.text_content.split()) * 1.3
        self.current_spend += actual_tokens * self.cost_per_token

        return result

    def get_remaining_budget(self) -> float:
        """Get remaining budget."""
        return self.budget_limit - self.current_spend

# Usage
budget_processor = CostOptimizedProcessor(client, budget_limit=5.0)
result = budget_processor.process_with_budget_check("chart.png")
print(f"Remaining budget: ${budget_processor.get_remaining_budget():.2f}")
```

## 🚨 Troubleshooting

### Common Issues

#### API Rate Limits

```python
import time
from tenacity import retry, stop_after_attempt, wait_exponential

class RobustLLMProcessor:
    def __init__(self, client, model="gpt-4o"):
        self.client = client
        self.model = model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def convert_with_retry(self, file_path: str):
        """Convert with exponential backoff retry."""

        md = MarkItDown(
            llm_client=self.client,
            llm_model=self.model,
            llm_prompt="Describe this image clearly and concisely."
        )

        return md.convert(file_path)

# Usage
robust_processor = RobustLLMProcessor(client)
try:
    result = robust_processor.convert_with_retry("image.png")
except Exception as e:
    print(f"Failed after retries: {e}")
```

#### Token Limits

```python
def process_large_content(file_path: str, max_tokens: int = 4000):
    """Process large content by splitting into chunks."""

    # First, get basic conversion without LLM
    md_basic = MarkItDown()
    basic_result = md_basic.convert(file_path)

    # If content is too long, create summary
    content_length = len(basic_result.text_content.split())

    if content_length > max_tokens:
        # Create summary prompt
        summary_prompt = f"""
        Summarize this content in under {max_tokens//4} words, focusing on key information:

        {basic_result.text_content[:max_tokens*2]}  # First part for context
        """

        # Use LLM for summarization
        md_summary = MarkItDown(
            llm_client=client,
            llm_model="gpt-4o",
            llm_prompt=summary_prompt
        )

        # Create a text file for the LLM to process
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(basic_result.text_content)
            temp_file = f.name

        try:
            summary_result = md_summary.convert(temp_file)
            return summary_result
        finally:
            import os
            os.unlink(temp_file)

    return basic_result
```

#### Authentication Issues

```python
def test_llm_connection(client):
    """Test LLM client connection."""
    try:
        # Simple test request
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello, test connection."}],
            max_tokens=10
        )
        print("✅ LLM connection successful")
        return True

    except Exception as e:
        print(f"❌ LLM connection failed: {e}")
        return False

# Usage
if test_llm_connection(client):
    md = MarkItDown(llm_client=client, llm_model="gpt-4o")
    result = md.convert("test.png")
else:
    print("Falling back to standard processing")
    md = MarkItDown()
    result = md.convert("test.png")
```

## 📈 Best Practices

### 1. Prompt Design

```python
# Effective prompts for different scenarios
PROMPTS = {
    "accessibility": "Describe this image for visually impaired users, focusing on essential information and context.",
    "data_analysis": "Analyze this chart or graph, highlighting key trends, patterns, and actionable insights.",
    "technical": "Explain this technical diagram, including component relationships and data flow.",
    "business": "Analyze this business content for strategic implications and recommendations.",
    "academic": "Describe this academic figure, including methodology, findings, and significance."
}

def get_prompt_for_context(context_type: str, custom_instruction: str = "") -> str:
    """Get appropriate prompt for specific context."""
    base_prompt = PROMPTS.get(context_type, "Describe this image clearly and concisely.")

    if custom_instruction:
        return f"{base_prompt}\n\nAdditional instruction: {custom_instruction}"

    return base_prompt
```

### 2. Error Handling

```python
def safe_llm_conversion(file_path: str, client, fallback_to_standard=True):
    """Convert with comprehensive error handling."""

    try:
        # Try LLM-enhanced conversion
        md = MarkItDown(llm_client=client, llm_model="gpt-4o")
        result = md.convert(file_path)
        return result, "llm_success"

    except Exception as llm_error:
        print(f"⚠️ LLM conversion failed: {llm_error}")

        if fallback_to_standard:
            try:
                # Fallback to standard conversion
                md_standard = MarkItDown()
                result = md_standard.convert(file_path)
                return result, "standard_fallback"

            except Exception as standard_error:
                raise Exception(f"Both LLM and standard conversion failed: {llm_error}, {standard_error}")
        else:
            raise llm_error
```

### 3. Performance Optimization

```python
# Cache LLM results for repeated images
import hashlib
import pickle
from pathlib import Path

class CachedLLMProcessor:
    def __init__(self, client, cache_dir: str = "llm_cache"):
        self.client = client
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_key(self, file_path: str, prompt: str) -> str:
        """Generate cache key for file and prompt combination."""
        content = f"{file_path}_{prompt}_{os.path.getmtime(file_path)}"
        return hashlib.md5(content.encode()).hexdigest()

    def convert_with_cache(self, file_path: str, prompt: str):
        """Convert with caching."""
        cache_key = self._get_cache_key(file_path, prompt)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        # Check cache
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                result = pickle.load(f)
            print(f"📋 Using cached result: {file_path}")
            return result

        # Process and cache
        md = MarkItDown(llm_client=self.client, llm_model="gpt-4o", llm_prompt=prompt)
        result = md.convert(file_path)

        with open(cache_file, 'wb') as f:
            pickle.dump(result, f)

        return result
```

## 🎯 PDF Image Extraction with Parallel Processing

MarkItDown automatically extracts images from PDF files when using Gemini integration, with **parallel processing** for fast conversion of PDFs with many images.

### Basic Usage

```python
from markitdown import MarkItDown

md = MarkItDown(
    gemini_api_key="your-gemini-api-key",
    llm_model="gemini-2.5-flash"
)

# Images are automatically extracted and processed in parallel
result = md.convert("document.pdf")

# Image descriptions are inserted where images appear
# Original image references are replaced with descriptions
```

### Parallel Processing Configuration

```python
# Default: 20 parallel workers (recommended for most cases)
result = md.convert("document.pdf", max_image_workers=20)

# Use fewer workers if you encounter rate limiting
result = md.convert("document.pdf", max_image_workers=10)

# Sequential processing (disable parallel - same as before)
result = md.convert("document.pdf", max_image_workers=1)
```

### Performance Benefits

**Before (Sequential Processing):**
- PDF with 20 images: ~20 seconds (1 second per image)
- PDF with 100 images: ~100 seconds

**After (Parallel Processing with 20 workers):**
- PDF with 20 images: ~1-2 seconds
- PDF with 100 images: ~5-10 seconds

**Speedup**: Up to 20x faster for PDFs with many images!

### How It Works

1. **PDF Conversion**: PDF is converted to Markdown using pymupdf4llm
2. **Image Extraction**: Images are extracted to a temporary directory
3. **Parallel Processing**: Images are processed simultaneously using a worker pool:
   - Default: 20 workers (configurable via `max_image_workers`)
   - Each worker processes one image at a time
   - Results are collected as they complete
4. **Context-Aware Descriptions**: Each image is sent to the LLM with:
   - Up to 800 characters of text before the image
   - Up to 800 characters of text after the image
   - This context helps generate more accurate descriptions
5. **Replacement**: Image references in markdown are replaced with AI-generated descriptions
6. **Cleanup**: Temporary files are automatically deleted after processing

### Adaptive Rate Limiting

The parallel processor includes built-in monitoring for rate limiting:

- **Error Detection**: Automatically detects rate limiting errors (429, quota exceeded, etc.)
- **Warning Logs**: Logs warnings when rate limiting is detected
- **Recommendations**: Suggests reducing worker count if rate limiting occurs
- **Graceful Degradation**: Individual image failures don't stop the entire batch

Example log output:
```
2024-01-15 10:30:45 - INFO - Found 240 images in PDF. Starting image description generation...
2024-01-15 10:30:45 - INFO - Parallel image processing enabled: 20 workers
2024-01-15 10:30:46 - INFO - Processing image 1/240: image-001.png
2024-01-15 10:30:46 - INFO - Processing image 2/240: image-002.png
...
2024-01-15 10:30:52 - INFO - Successfully generated description for image 1/240: image-001.png (245 chars)
...
2024-01-15 10:30:58 - INFO - Completed image processing: 240/240 images described successfully
```

### Best Practices

1. **Default Workers**: Start with the default 20 workers - it works well for most cases
2. **Rate Limiting**: If you see rate limiting errors, reduce `max_image_workers` to 10 or 5
3. **Large PDFs**: For PDFs with 100+ images, 20 workers provides excellent performance
4. **API Limits**: Check your API provider's rate limits and adjust workers accordingly
5. **Monitoring**: Watch the logs for warnings about rate limiting

### Example: Processing Large PDF

```python
from markitdown import MarkItDown
import time

md = MarkItDown(
    gemini_api_key="your-gemini-api-key",
    llm_model="gemini-2.5-flash"
)

# Process a large PDF with 200+ images
start_time = time.time()
result = md.convert("large_document.pdf", max_image_workers=20)
elapsed = time.time() - start_time

print(f"Processed {len(result.text_content)} characters in {elapsed:.2f} seconds")
# Output: Processed 450,234 characters in 12.34 seconds
```

### Technical Details

- **Thread Safety**: Uses `ThreadPoolExecutor` for I/O-bound API calls
- **Memory Efficient**: Images are read on-demand, not all loaded into memory
- **Error Handling**: Individual image failures are logged but don't stop processing
- **Backward Compatible**: Set `max_image_workers=1` for sequential processing (original behavior)

**Note:** Images are processed in-memory and temporary files are automatically deleted after processing.

### Standalone PDF Processing Script

A standalone script `process_pdf.py` is available in the repository root for convenient PDF processing:

```bash
# Basic usage
python process_pdf.py document.pdf

# With options
python process_pdf.py document.pdf --output result.md --workers 20

# With Gemini API key
python process_pdf.py document.pdf --gemini-key YOUR_API_KEY

# Or use environment variable
export GEMINI_API_KEY=your_key
python process_pdf.py document.pdf
```

**Features:**
- Parallel image processing (configurable workers)
- Progress logging with timestamps
- Automatic output file naming
- Error handling and statistics
- See `process_pdf.py --help` for all options

---

LLM integration significantly enhances MarkItDown's capabilities, particularly for processing images, complex documents, and generating intelligent summaries. By following these best practices, you can create efficient, cost-effective, and reliable document processing workflows.