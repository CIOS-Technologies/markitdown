# MCP Server Documentation

MarkItDown provides a Model Context Protocol (MCP) server that enables seamless integration with LLM applications like Claude Desktop, allowing direct document conversion capabilities within AI workflows.

## 🌟 Overview

The MarkItDown MCP server exposes document conversion functionality through the Model Context Protocol, enabling:

- **Direct LLM Integration**: Convert documents without leaving your AI assistant
- **Seamless Workflows**: Process documents as part of natural language conversations
- **Real-time Conversion**: Convert files on-demand during AI interactions
- **Multiple Format Support**: All MarkItDown converters available through MCP
- **Secure Processing**: Local processing with optional cloud enhancements

## 🚀 Installation and Setup

### Prerequisites

- **Node.js 16+** - Required for MCP server runtime
- **Claude Desktop** - Or other MCP-compatible LLM application
- **MarkItDown** - Core package with desired converters

### Install MCP Server

```bash
# Install from PyPI
pip install markitdown-mcp

# Or install from source
cd markitdown/packages/markitdown-mcp
pip install -e .
```

### Verify Installation

```bash
# Check MCP server installation
python -m markitdown_mcp --help

# Test server functionality
python -m markitdown_mcp --test
```

## ⚙️ Configuration

### Claude Desktop Setup

1. **Locate Claude Desktop configuration file**:

   **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   **Linux**: `~/.config/claude/claude_desktop_config.json`

2. **Add MarkItDown MCP server**:

```json
{
  "mcpServers": {
    "markitdown": {
      "command": "python",
      "args": [
        "-m",
        "markitdown_mcp.server"
      ],
      "env": {
        "MARKITDOWN_PLUGINS": "enabled",
        "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT": "https://your-resource.cognitiveservices.azure.com/",
        "AZURE_DOCUMENT_INTELLIGENCE_KEY": "your-api-key"
      }
    }
  }
}
```

### Advanced Configuration

```json
{
  "mcpServers": {
    "markitdown": {
      "command": "python",
      "args": [
        "-m", "markitdown_mcp.server",
        "--log-level", "debug",
        "--max-file-size", "50MB"
      ],
      "env": {
        "MARKITDOWN_ENABLE_PLUGINS": "true",
        "MARKITDOWN_AZURE_ENABLED": "true",
        "MARKITDOWN_LLM_MODEL": "gpt-4o",
        "OPENAI_API_KEY": "your-openai-key",
        "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT": "https://your-resource.cognitiveservices.azure.com/",
        "AZURE_DOCUMENT_INTELLIGENCE_KEY": "your-api-key"
      }
    }
  }
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MARKITDOWN_ENABLE_PLUGINS` | Enable third-party plugins | `false` |
| `MARKITDOWN_AZURE_ENABLED` | Enable Azure Document Intelligence | `false` |
| `MARKITDOWN_LLM_MODEL` | LLM model for image descriptions | `none` |
| `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` | Azure Document Intelligence endpoint | `none` |
| `AZURE_DOCUMENT_INTELLIGENCE_KEY` | Azure Document Intelligence API key | `none` |
| `OPENAI_API_KEY` | OpenAI API key for LLM integration | `none` |
| `MARKITDOWN_LOG_LEVEL` | Logging level (debug, info, warning, error) | `info` |
| `MARKITDOWN_MAX_FILE_SIZE` | Maximum file size to process | `100MB` |

## 🔧 MCP Tools and Capabilities

### Available Tools

#### 1. `convert_document`

Convert a document to Markdown format.

**Parameters:**
- `file_path` (string, required): Path to the document file
- `options` (object, optional): Conversion options
  - `enable_plugins` (boolean): Enable plugin converters
  - `azure_enabled` (boolean): Use Azure Document Intelligence
  - `llm_model` (string): LLM model for image descriptions

**Example Usage:**
```
Please convert the PDF file "contract.pdf" to Markdown format and summarize the key terms.
```

#### 2. `convert_from_url`

Convert a document from a URL.

**Parameters:**
- `url` (string, required): URL to the document
- `options` (object, optional): Conversion options

**Example Usage:**
```
Convert the Wikipedia article about artificial intelligence to Markdown format.
```

#### 3. `list_supported_formats`

List all supported document formats and converters.

**Example Usage:**
```
What file formats does MarkItDown support?
```

#### 4. `get_converter_info`

Get detailed information about specific converters.

**Parameters:**
- `format` (string, optional): Specific format to query

**Example Usage:**
```
Tell me about the PDF conversion capabilities.
```

## 📚 Usage Examples

### Basic Document Conversion

**User:**
```
Can you convert the PDF document "research_paper.pdf" to Markdown and extract the main findings?
```

**Claude Response:**
```
I'll convert the research paper to Markdown format and analyze the key findings for you.

[Converts research_paper.pdf using markitdown.convert_document]

# Research Paper Analysis

## Main Findings

Based on the converted document, here are the key findings:

1. **Primary Discovery**: The research demonstrates a 40% improvement in processing efficiency
2. **Methodology**: Used a novel machine learning approach with 10,000 samples
3. **Statistical Significance**: Results show p < 0.001, indicating strong statistical significance
4. **Practical Applications**: Findings have immediate implications for real-world deployment

## Full Document Content

[Inserts converted Markdown content here]

The paper provides compelling evidence for the new approach and suggests several directions for future research...
```

### Web Content Processing

**User:**
```
Please analyze the Wikipedia article about renewable energy and create a summary of the main types of renewable energy sources.
```

**Claude Response:**
```
I'll fetch the Wikipedia article about renewable energy and analyze it for you.

[Converts Wikipedia URL using markitdown.convert_from_url]

# Renewable Energy Sources Analysis

Based on the Wikipedia article, here are the main types of renewable energy:

## Solar Energy
- **Photovoltaic Systems**: Direct conversion of sunlight to electricity
- **Solar Thermal**: Uses heat from the sun for power generation
- **Advantages**: Abundant, decreasing costs, minimal environmental impact

## Wind Energy
- **Onshore Wind**: Land-based wind turbines
- **Offshore Wind**: Ocean-based wind farms with higher capacity factors
- **Advantages**: Mature technology, cost-competitive with fossil fuels

## Hydroelectric Power
- **Large-scale Dams**: Traditional hydroelectric plants
- **Run-of-river**: Less environmental impact, smaller scale
- **Pumped Storage**: Energy storage capabilities

## Other Sources
- **Geothermal**: Heat from the Earth's core
- **Biomass**: Organic materials for energy production
- **Ocean Energy**: Tidal and wave energy systems

Each source has unique advantages and challenges in terms of scalability, cost, and environmental impact...
```

### Advanced Analysis with Azure Integration

**User:**
```
This scanned document contains handwritten notes and complex tables. Can you convert it and extract all the numerical data?
```

**Claude Response:**
```
I'll convert the scanned document using enhanced OCR capabilities to handle the handwritten content and complex tables.

[Uses markitdown.convert_document with Azure Document Intelligence enabled]

# Scanned Document Analysis

## Conversion Results
I've successfully converted your scanned document using advanced OCR and layout analysis. Here's what I found:

## Extracted Numerical Data

### Financial Summary Table
| Quarter | Revenue | Expenses | Profit |
|---------|---------|----------|--------|
| Q1 2024 | $125,000 | $87,500 | $37,500 |
| Q2 2024 | $142,000 | $91,000 | $51,000 |
| Q3 2024 | $158,000 | $95,000 | $63,000 |
| Q4 2024 | $175,000 | $98,000 | $77,000 |

### Handwritten Notes Analysis
The document contains handwritten annotations including:
- "Focus on Q4 growth strategy"
- "Consider expanding into new markets"
- "Review competitor pricing models"

## Complete Document Content

[Inserts full converted content with preserved formatting]

The document shows strong quarterly growth with a 40% increase in revenue from Q1 to Q4...
```

### Batch Processing Workflow

**User:**
```
I have several meeting transcripts in audio format. Can you convert them all and create a consolidated summary of action items?
```

**Claude Response:**
```
I'll convert your audio files and extract action items from each meeting.

[Processes multiple audio files using markitdown.convert_document]

# Meeting Transcripts Summary

## Individual Meeting Analysis

### Meeting 1: Project Kickoff (March 15)
**Action Items:**
- [ ] Define project scope and objectives
- [ ] Assemble development team
- [ ] Set up development environment
- [ ] Create initial project timeline

### Meeting 2: Design Review (March 22)
**Action Items:**
- [ ] Finalize UI/UX designs
- [ ] Review technical architecture
- [ ] Plan testing strategy
- [ ] Prepare for stakeholder presentation

### Meeting 3: Progress Update (March 29)
**Action Items:**
- [ ] Address performance optimization issues
- [ ] Update project timeline based on current progress
- [ ] Schedule user testing sessions
- [ ] Prepare status report for management

## Consolidated Action Items

### High Priority (This Week)
- [ ] Finalize UI/UX designs
- [ ] Address performance optimization issues
- [ ] Define project scope and objectives

### Medium Priority (Next Week)
- [ ] Assemble development team
- [ ] Create initial project timeline
- [ ] Review technical architecture

### Low Priority (Following Weeks)
- [ ] Set up development environment
- [ ] Plan testing strategy
- [ ] Schedule user testing sessions

## Next Steps
I recommend prioritizing the design finalization and performance optimization as they appear to be blocking other activities...
```

## 🛠️ Advanced Configuration

### Custom Server Configuration

Create a custom server configuration file:

```python
# custom_server_config.py
import os
from markitdown_mcp.server import create_server

# Custom configuration
config = {
    "log_level": "debug",
    "max_file_size": "100MB",
    "enable_plugins": True,
    "azure_enabled": True,
    "default_llm_model": "gpt-4o",
    "cache_enabled": True,
    "cache_dir": os.path.expanduser("~/.markitdown_cache")
}

# Create and run server
server = create_server(config)
server.run()
```

Update Claude Desktop configuration:

```json
{
  "mcpServers": {
    "markitdown": {
      "command": "python",
      "args": [
        "/path/to/custom_server_config.py"
      ]
    }
  }
}
```

### Custom Tool Extensions

```python
# custom_tools.py
from markitdown_mcp.server import MCPServer
from markitdown import MarkItDown

class CustomMarkItDownServer(MCPServer):
    def __init__(self):
        super().__init__()
        self.md = MarkItDown(enable_plugins=True)

    async def convert_batch(self, file_paths: list, options: dict = None):
        """Convert multiple documents in batch."""
        results = []

        for file_path in file_paths:
            try:
                result = self.md.convert(file_path)
                results.append({
                    "file": file_path,
                    "success": True,
                    "content": result.text_content,
                    "metadata": result.metadata
                })
            except Exception as e:
                results.append({
                    "file": file_path,
                    "success": False,
                    "error": str(e)
                })

        return results

    async def analyze_document_sentiment(self, file_path: str):
        """Analyze document sentiment using LLM."""
        # Custom sentiment analysis implementation
        pass
```

## 🔍 Troubleshooting

### Common Issues

#### Server Connection Issues

```bash
# Test MCP server directly
python -m markitdown_mcp.server --test

# Check server logs
python -m markitdown_mcp.server --log-level debug

# Verify configuration
python -c "
import json
import os
config_path = os.path.expanduser('~/Library/Application Support/Claude/claude_desktop_config.json')
with open(config_path) as f:
    config = json.load(f)
    print('MCP Servers:', config.get('mcpServers', {}))
"
```

#### Permission Issues

```bash
# Check file permissions
ls -la /path/to/document.pdf

# Test with a simple file
echo "# Test Document" > test.md
python -m markitdown_mcp.server --test-file test.md
```

#### Plugin Issues

```bash
# List available plugins
python -c "
from markitdown import MarkItDown
md = MarkItDown(enable_plugins=True)
print('Plugins loaded successfully')
"

# Test specific plugin
python -c "
from markitdown_sample_plugin.converter import JsonConverter
print('Sample plugin available')
"
```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```json
{
  "mcpServers": {
    "markitdown": {
      "command": "python",
      "args": [
        "-m", "markitdown_mcp.server",
        "--log-level", "debug"
      ],
      "env": {
        "MARKITDOWN_LOG_LEVEL": "debug"
      }
    }
  }
}
```

### Performance Optimization

```python
# Performance monitoring
import time
import psutil

class MonitoredMCPServer:
    def __init__(self):
        self.process_count = 0
        self.total_time = 0

    async def convert_with_monitoring(self, file_path: str):
        """Convert with performance monitoring."""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss

        try:
            result = await self.convert_document(file_path)

            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss

            # Log performance metrics
            processing_time = end_time - start_time
            memory_used = end_memory - start_memory

            self.process_count += 1
            self.total_time += processing_time

            return result

        except Exception as e:
            return {"error": str(e)}
```

## 📊 Best Practices

### 1. Security Considerations

```json
{
  "mcpServers": {
    "markitdown": {
      "command": "python",
      "args": ["-m", "markitdown_mcp.server"],
      "env": {
        "MARKITDOWN_ALLOWED_PATHS": "/Users/username/Documents,/Users/username/Downloads",
        "MARKITDOWN_MAX_FILE_SIZE": "50MB",
        "MARKITDOWN_SANDBOX_ENABLED": "true"
      }
    }
  }
}
```

### 2. Resource Management

```python
# Resource limits configuration
config = {
    "max_concurrent_conversions": 3,
    "max_file_size": "100MB",
    "cache_size_limit": "1GB",
    "cleanup_interval": 3600  # 1 hour
}
```

### 3. Error Handling

```python
async def safe_convert_document(self, file_path: str, options: dict = None):
    """Convert document with comprehensive error handling."""
    try:
        # Validate file path
        if not self._is_safe_path(file_path):
            return {"error": "File path not allowed"}

        # Check file size
        if not self._check_file_size(file_path):
            return {"error": "File too large"}

        # Convert document
        result = await self.convert_document(file_path, options)
        return result

    except Exception as e:
        return {
            "error": f"Conversion failed: {str(e)}",
            "file_path": file_path
        }
```

## 🚀 Usage in Different Applications

### Claude Desktop

The primary use case is with Claude Desktop for seamless document processing:

```
User: "Please convert this contract PDF and highlight any unusual clauses"
Claude: [Uses markitdown.convert_document] "I've converted the contract and found several clauses that may need attention..."
```

### Other MCP Clients

The server can be used with any MCP-compatible application:

```python
# Example Python MCP client
from mcp import Client

client = Client()
client.connect_to_server("markitdown")

# Convert document
result = client.call_tool("convert_document", {
    "file_path": "document.pdf",
    "options": {"azure_enabled": True}
})
```

### Integration in Workflows

```bash
# Command-line usage with MCP
echo '{"method": "tools/call", "params": {"name": "convert_document", "arguments": {"file_path": "test.pdf"}}}' | python -m markitdown_mcp.client
```

The MarkItDown MCP server provides a powerful bridge between document processing capabilities and AI interactions, enabling seamless workflows where documents can be converted and analyzed as part of natural language conversations.