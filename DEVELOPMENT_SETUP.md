# Development Setup for MarkItDown

## ✅ Current Setup

Your environment is configured with an **editable install** of markitdown. This means:
- **Any changes you make to the source code** in `packages/markitdown/src/markitdown/` will be **immediately reflected**
- No need to reinstall when modifying code
- The package is linked to your source code, not copied

## 🔍 Verify Editable Install

```bash
cd /home/denter/user/work/markitdown
source .venv/bin/activate

# Check where the package is loaded from
python -c "import markitdown; print(markitdown.__file__)"
# Should show: .../packages/markitdown/src/markitdown/__init__.py
```

## 🛠️ How to Modify and Test Code

### 1. Modify Source Code

Edit any file in `packages/markitdown/src/markitdown/`:
```bash
# Example: Edit a converter
vim packages/markitdown/src/markitdown/converters/_pdf.py
```

### 2. Test Your Changes Immediately

```bash
# Test using CLI
markitdown test.pdf

# Test using Python API
python -c "from markitdown import MarkItDown; md = MarkItDown(); result = md.convert('test.pdf'); print(result.text_content[:100])"
```

**Changes are live immediately - no reinstall needed!**

## 🧪 Running Tests

### Using Hatch (Recommended)
```bash
cd packages/markitdown
source ../../.venv/bin/activate
hatch test                    # Run all tests
hatch test tests/test_module_misc.py  # Run specific test file
hatch test -k "test_pdf"      # Run tests matching pattern
```

### Using Python Directly
```bash
cd packages/markitdown
source ../../.venv/bin/activate
python -m pytest tests/       # If pytest is installed
python -m unittest discover tests/  # Using unittest
```

## 📝 Workflow Example

1. **Modify code:**
   ```bash
   # Edit a file
   vim packages/markitdown/src/markitdown/_markitdown.py
   ```

2. **Test your changes:**
   ```bash
   source .venv/bin/activate
   markitdown test.pdf
   ```

3. **Run tests:**
   ```bash
   cd packages/markitdown
   hatch test
   ```

## 🎯 Quick Test Commands

```bash
# Activate environment
source .venv/bin/activate

# Convert test PDF
markitdown test.pdf

# Convert with output file
markitdown test.pdf -o output.md

# Run Python API test
python << EOF
from markitdown import MarkItDown
md = MarkItDown()
result = md.convert("test.pdf")
print(f"Converted {len(result.text_content)} characters")
EOF
```

## 📦 Project Structure

```
markitdown/
├── .venv/                    # Your virtual environment
├── packages/
│   └── markitdown/
│       ├── src/
│       │   └── markitdown/   # ← EDIT CODE HERE
│       ├── tests/            # Test files
│       └── pyproject.toml
└── test.pdf                   # Test file
```

## ⚠️ Important Notes

- **Editable install**: Changes to source code are immediately available
- **No reinstall needed**: Just modify and test!
- **Environment**: Always activate `.venv` before working
- **Testing**: Use `hatch test` from `packages/markitdown/` directory

