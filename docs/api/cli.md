# Command Line Interface Reference

The MarkItDown command-line interface provides a powerful and flexible way to convert documents from your terminal or scripts.

## 🚀 Installation and Setup

### Verify Installation

```bash
markitdown --version
```

### Available Commands

```bash
# Show help
markitdown --help

# List available plugins
markitdown --list-plugins
```

## 📋 Command Syntax

### Basic Syntax

```bash
markitdown [OPTIONS] SOURCE [SOURCE...] [-o OUTPUT]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `SOURCE` | Input file path(s), URL, or stdin. Multiple files can be specified. |
| `-o OUTPUT`, `--output OUTPUT` | Output file path. If not specified, output goes to stdout. |

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--use-plugins` | Enable third-party plugins |
| `--list-plugins` | List available plugins |
| `--doc-intel` | `-d` | Enable Azure Document Intelligence |
| `--endpoint ENDPOINT` | `-e` | Azure Document Intelligence endpoint |
| `--key KEY` | `-k` | Azure Document Intelligence API key |
| `--quiet` | Suppress warnings and verbose output |
| `--verbose` | Enable verbose output |
| `--version` | Show version information |
| `--help` | Show help message |

## 🎯 Usage Examples

### Basic Conversion

```bash
# Convert single file to stdout
markitdown document.pdf

# Convert single file to specific output
markitdown document.pdf -o output.md

# Convert multiple files (outputs to stdout for each)
markitdown file1.pdf file2.docx file3.pptx
```

### Input Methods

```bash
# From file path
markitdown /path/to/document.pdf

# From URL (web content)
markitdown https://example.com/article.html

# From stdin
cat document.pdf | markitdown

# Here document
markitdown << EOF
# Direct Markdown Input
This content is passed through directly.
EOF
```

### Advanced Features

```bash
# Enable plugins
markitdown document.docx --use-plugins

# Use Azure Document Intelligence
markitdown scan.pdf -d -e "https://your-resource.cognitiveservices.azure.com/" -k "your-api-key"

# Quiet mode (suppress warnings)
markitdown document.pdf --quiet -o output.md

# Verbose mode
markitdown document.pdf --verbose
```

### Batch Processing

```bash
# Process all PDFs in directory
markitdown documents/*.pdf

# Process multiple formats
markitdown docs/*.pdf docs/*.docx docs/*.pptx

# Using find for recursive processing
find documents/ -name "*.pdf" -exec markitdown {} -o {}.md \;
```

## 🔧 Configuration

### Environment Variables

```bash
# Azure Document Intelligence
export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://your-resource.cognitiveservices.azure.com/"
export AZURE_DOCUMENT_INTELLIGENCE_KEY="your-api-key"

# Plugin path (if applicable)
export MARKITDOWN_PLUGIN_PATH="/path/to/custom/plugins"

# LLM configuration (for image descriptions)
# Gemini (recommended for images)
export GEMINI_API_KEY="your-gemini-api-key"

# OpenAI
export OPENAI_API_KEY="your-openai-api-key"
export MARKITDOWN_LLM_MODEL="gpt-4o"
```

### Configuration Files

MarkItDown does not use configuration files. All configuration is done via command-line options and environment variables.

## 📊 Output Options

### Standard Output

```bash
# Output to stdout
markitdown document.pdf

# Pipe to other commands
markitdown document.pdf | grep "Important Section"
markitdown document.pdf | head -50
```

### File Output

```bash
# Single output file
markitdown document.pdf -o converted.md

# Multiple files (scripted approach)
for file in *.pdf; do
    markitdown "$file" -o "${file%.pdf}.md"
done
```

### Output Formatting

The CLI outputs raw Markdown content. For additional formatting:

```bash
# Add header
echo "# Document Conversion Results" > output.md
markitdown document.pdf >> output.md

# Add metadata
echo "Converted on: $(date)" >> output.md
markitdown document.pdf >> output.md
```

## 🌐 URL and Web Content

### Web Pages

```bash
# Convert HTML page
markitdown https://example.com/article.html

# Convert Wikipedia article
markitdown https://en.wikipedia.org/wiki/Artificial_intelligence

# Convert with output file
markitdown https://example.com -o webpage.md
```

### YouTube Videos

```bash
# Get YouTube transcript
markitdown https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Save transcript to file
markitdown https://www.youtube.com/watch?v=video_id -o transcript.md
```

### Specialized URLs

```bash
# Bing search results
markitdown "https://www.bing.com/search?q=markitdown"

# RSS feeds
markitdown https://example.com/feed.xml
```

## 🔌 Plugin Usage

### Listing Plugins

```bash
# List all available plugins
markitdown --list-plugins
```

Output example:
```
Available plugins:
- json_converter: JSON to Markdown converter (v0.1.0)
- custom_format: Custom file format processor (v1.2.0)
```

### Enabling Plugins

```bash
# Enable all plugins
markitdown document.xyz --use-plugins

# Plugins are disabled by default for security
markitdown document.xyz  # Plugins not used
```

## ☁️ Azure Document Intelligence

### Setup

```bash
# Set environment variables
export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://your-resource.cognitiveservices.azure.com/"
export AZURE_DOCUMENT_INTELLIGENCE_KEY="your-api-key"
```

### Usage

```bash
# Enable with environment variables
markitdown scan.pdf -d

# Specify endpoint explicitly
markitdown scan.pdf -d -e "https://your-resource.cognitiveservices.azure.com/"

# With API key (not recommended for production)
markitdown scan.pdf -d -e "endpoint" -k "api-key"
```

### Best Results

Azure Document Intelligence works best with:
- Scanned documents
- Complex layouts
- Handwritten text
- Forms and invoices
- Multiple language documents

```bash
# Process scanned document with Azure
markitdown scanned_contract.pdf -d -o contract_with_ocr.md
```

## 📝 Scripting and Automation

### Basic Script

```bash
#!/bin/bash
# convert_docs.sh - Simple batch conversion script

OUTPUT_DIR="converted_docs"
mkdir -p "$OUTPUT_DIR"

for file in "$@"; do
    if [ -f "$file" ]; then
        output="${OUTPUT_DIR}/$(basename "${file%.*}").md"
        echo "Converting $file -> $output"
        markitdown "$file" -o "$output"
    else
        echo "File not found: $file"
    fi
done
```

Usage:
```bash
chmod +x convert_docs.sh
./convert_docs.sh document1.pdf document2.docx
```

### Advanced Script with Error Handling

```bash
#!/bin/bash
# convert_with_retry.sh - Robust conversion with retry logic

OUTPUT_DIR="converted_docs"
MAX_RETRIES=3
mkdir -p "$OUTPUT_DIR"

convert_with_retry() {
    local file="$1"
    local output="$2"
    local retries=0

    while [ $retries -lt $MAX_RETRIES ]; do
        if markitdown "$file" -o "$output" 2>/dev/null; then
            echo "✅ Success: $file"
            return 0
        else
            retries=$((retries + 1))
            echo "⚠️  Retry $retries/$MAX_RETRIES: $file"
            sleep 1
        fi
    done

    echo "❌ Failed after $MAX_RETRIES attempts: $file"
    return 1
}

for file in "$@"; do
    if [ -f "$file" ]; then
        output="${OUTPUT_DIR}/$(basename "${file%.*}").md"
        convert_with_retry "$file" "$output"
    else
        echo "❌ File not found: $file"
    fi
done
```

### Processing Pipeline

```bash
#!/bin/bash
# pipeline.sh - Document processing pipeline

INPUT_DIR="input_docs"
OUTPUT_DIR="processed_docs"
TEMP_DIR="temp"

mkdir -p "$OUTPUT_DIR" "$TEMP_DIR"

echo "📁 Processing documents from $INPUT_DIR"

# Step 1: Convert all documents
echo "🔄 Converting documents..."
find "$INPUT_DIR" -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.pptx" \) | while read file; do
    filename=$(basename "$file")
    temp_output="$TEMP_DIR/${filename%.*}.md"

    echo "  Converting $filename"
    if markitdown "$file" -o "$temp_output"; then
        echo "    ✅ Success"
    else
        echo "    ❌ Failed"
    fi
done

# Step 2: Combine results
echo "📚 Combining results..."
cat "$TEMP_DIR"/*.md > "$OUTPUT_DIR/combined_output.md"

# Step 3: Add metadata
{
    echo "# Document Processing Results"
    echo ""
    echo "**Generated on:** $(date)"
    echo "**Source directory:** $INPUT_DIR"
    echo "**Total files processed:** $(ls -1 "$TEMP_DIR"/*.md | wc -l)"
    echo ""
    echo "---"
    echo ""
} | cat - "$OUTPUT_DIR/combined_output.md" > "$OUTPUT_DIR/final_output.md"

# Cleanup
rm -rf "$TEMP_DIR"

echo "✅ Processing complete. Output in $OUTPUT_DIR/final_output.md"
```

## 🚨 Error Handling

### Exit Codes

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | Success | Conversion completed successfully |
| 1 | General Error | Invalid arguments, system error |
| 2 | File Not Found | Input file does not exist |
| 3 | Unsupported Format | File format not supported |
| 4 | Missing Dependency | Required library not installed |
| 5 | Conversion Failed | Document conversion failed |

### Error Handling in Scripts

```bash
#!/bin/bash
# robust_convert.sh - Conversion with comprehensive error handling

handle_error() {
    local exit_code=$?
    local file=$1

    case $exit_code in
        0)
            echo "✅ Success: $file"
            ;;
        2)
            echo "❌ File not found: $file"
            ;;
        3)
            echo "❌ Unsupported format: $file"
            echo "   Try installing: pip install 'markitdown[all]'"
            ;;
        4)
            echo "❌ Missing dependency for $file"
            echo "   Try installing: pip install 'markitdown[required-features]'"
            ;;
        5)
            echo "❌ Conversion failed: $file"
            echo "   File may be corrupted or password protected"
            ;;
        *)
            echo "❌ Unknown error ($exit_code): $file"
            ;;
    esac
}

for file in "$@"; do
    markitdown "$file" -o "${file%.*}.md"
    handle_error $? "$file"
done
```

## 🔍 Debugging

### Verbose Mode

```bash
# Enable verbose output for debugging
markitdown document.pdf --verbose
```

### Testing with Sample Files

```bash
# Test with different formats
echo "Testing PDF conversion..."
markitdown sample.pdf -o test_pdf.md

echo "Testing DOCX conversion..."
markitdown sample.docx -o test_docx.md

echo "Testing with plugins..."
markitdown sample.custom --use-plugins -o test_plugin.md
```

### Checking File Types

```bash
# Check if file is supported
if markitdown sample.unknown 2>&1 | grep -q "Unsupported"; then
    echo "File type not supported"
else
    echo "File type supported"
fi
```

## 📊 Performance Considerations

### Memory Usage

```bash
# For large files, consider processing one at a time
for file in large_documents/*.pdf; do
    echo "Processing $file..."
    markitdown "$file" -o "processed/$(basename "$file" .pdf).md"
done
```

### Parallel Processing

```bash
# Parallel processing with xargs
find documents/ -name "*.pdf" | xargs -P 4 -I {} bash -c 'markitdown "{}" -o "processed/$(basename "{}" .pdf).md"'
```

### Batch Script for Large Numbers

```bash
#!/bin/bash
# batch_convert.sh - Efficient batch conversion

INPUT_DIR="large_input"
OUTPUT_DIR="large_output"
BATCH_SIZE=10

mkdir -p "$OUTPUT_DIR"

count=0
batch=()

for file in "$INPUT_DIR"/*; do
    if [ -f "$file" ]; then
        batch+=("$file")
        count=$((count + 1))

        if [ $count -eq $BATCH_SIZE ]; then
            echo "Processing batch of $count files..."
            for f in "${batch[@]}"; do
                markitdown "$f" -o "$OUTPUT_DIR/$(basename "$f" .${f##*.}).md" &
            done
            wait  # Wait for all background jobs
            batch=()
            count=0
        fi
    fi
done

# Process remaining files
if [ ${#batch[@]} -gt 0 ]; then
    echo "Processing final batch of ${#batch[@]} files..."
    for f in "${batch[@]}"; do
        markitdown "$f" -o "$OUTPUT_DIR/$(basename "$f" .${f##*.}).md"
    done
fi

echo "Batch conversion complete."
```

This CLI reference provides comprehensive coverage of the MarkItDown command-line interface, enabling effective use of the tool for both simple conversions and complex automated workflows.