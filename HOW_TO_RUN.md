# How to Run MarkItDown

## ✅ Correct Ways to Call MarkItDown

### Method 1: Activate Virtual Environment First (Recommended)

```bash
cd /home/denter/user/work/markitdown
source .venv/bin/activate

# Now markitdown command is available
markitdown test.pdf -o output.md
```

### Method 2: Using Python Module

```bash
cd /home/denter/user/work/markitdown
source .venv/bin/activate

# Use as Python module
python -m markitdown test.pdf -o output.md
```

### Method 3: Direct Python Script

```bash
cd /home/denter/user/work/markitdown
source .venv/bin/activate

# Use Python API directly
python << 'EOF'
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("test.pdf")
print(result.text_content)
EOF
```

## 🔍 Troubleshooting

### Issue: "markitdown: command not found"

**Cause**: Virtual environment is not activated, or you're using a different virtual environment.

**Solution**:
1. Make sure you're in the markitdown directory
2. Activate the correct virtual environment:
   ```bash
   source .venv/bin/activate
   ```
3. Verify activation:
   ```bash
   which markitdown
   # Should show: /home/denter/user/work/markitdown/.venv/bin/markitdown
   ```

### Check Virtual Environment Status

```bash
# Check if venv is activated (should show .venv in prompt or PATH)
echo $VIRTUAL_ENV

# Check if markitdown is available
which markitdown

# Check if markitdown package is installed
pip show markitdown
```

## 📝 Quick Reference

```bash
# 1. Navigate to project
cd /home/denter/user/work/markitdown

# 2. Activate environment
source .venv/bin/activate

# 3. Run markitdown
markitdown test.pdf -o output.md

# Or use Python module
python -m markitdown test.pdf -o output.md
```

## 🔧 Alternative: Create a Convenience Script

You can create a wrapper script to avoid activating the venv each time:

```bash
#!/bin/bash
cd /home/denter/user/work/markitdown
source .venv/bin/activate
markitdown "$@"
```

Save as `run_markitdown.sh` and make it executable:
```bash
chmod +x run_markitdown.sh
./run_markitdown.sh test.pdf -o output.md
```

