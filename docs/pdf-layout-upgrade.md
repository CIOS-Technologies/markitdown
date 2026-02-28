# PyMuPDF Layout upgrade – research summary

## Current situation

- **MarkItDown** uses **pymupdf4llm** for PDF→Markdown. pymupdf4llm is built on **PyMuPDF** (pymupdf).
- **pymupdf4llm** (0.3.4) depends on **pymupdf>=1.27.1**. So you already get PyMuPDF 1.27.x.
- Without the Layout extension, `to_markdown()` uses a non-layout path: reading order (especially multi-column) and header/footer handling are weaker, and `header`/`footer` parameters are not supported (they cause `TypeError` on current installs).

## PyMuPDF Layout

- **Package:** [pymupdf-layout](https://pypi.org/project/pymupdf-layout/) on PyPI.
- **Version:** 1.27.1 (production/stable).
- **Role:** Optional extension. When **imported before** pymupdf4llm (`import pymupdf.layout` then `import pymupdf4llm`), it switches `to_markdown()` to a layout-aware path that:
  - Improves reading order (e.g. multi-column, blocks).
  - Supports **header=False** and **footer=False** (so repeated page headers/footers can be excluded).
  - Better handling of tables, footnotes, and semantic structure.

## Compatibility

- **pymupdf-layout** requires **PyMuPDF == 1.27.1**.
- **pymupdf4llm** requires **pymupdf>=1.27.1**.
- Using **pymupdf==1.27.1** satisfies both. No version conflict.

## Dependencies of pymupdf-layout

| Package       | Note                |
|---------------|---------------------|
| PyMuPDF       | == 1.27.1           |
| pyyaml        |                     |
| numpy         |                     |
| onnxruntime   |                     |
| networkx      |                     |

MarkItDown already uses `onnxruntime` (with a version cap on Windows). The rest are common and should not conflict.

## License

- **pymupdf-layout** is dual-licensed: **Polyform Noncommercial** or **Artifex Commercial**.  
- For commercial use you need the Artifex commercial license.  
- For noncommercial use, Polyform Noncommercial is sufficient.  
- See [PyPI](https://pypi.org/project/pymupdf-layout/) and [Artifex](https://www.artifex.com/) for details.

## Can we do the upgrade?

**Yes.** The upgrade is:

1. **Install** the Layout extension when you want better PDF extraction:
   ```bash
   pip install pymupdf-layout
   ```
   With MarkItDown’s optional extra (if you add it):
   ```bash
   pip install 'markitdown[pdf,pdf-layout]'
   ```

2. **No code change required** for activation. The PDF converter already does:
   ```python
   import pymupdf.layout  # optional, before pymupdf4llm
   ```
   If the import succeeds, pymupdf4llm automatically uses the layout path.

3. **Optional:** After Layout is installed, you can pass **header=False, footer=False** in `convert(...)` to strip repeated headers/footers (once the parameter filter allows them through for your pymupdf4llm build).

## Recommendation

- **Noncommercial / internal use:** Add optional dependency **pymupdf-layout** (e.g. under a `pdf-layout` extra) and document that installing it improves PDF extraction. Users who need better order and header/footer control run `pip install 'markitdown[pdf,pdf-layout]'` (or equivalent).
- **Commercial use:** Confirm Artifex licensing for your product before depending on pymupdf-layout.

## References

- [PyMuPDF Layout on PyPI](https://pypi.org/project/pymupdf-layout/)
- [PyMuPDF Layout docs](https://pymupdf.readthedocs.io/en/latest/pymupdf-layout/index.html)
- [PyMuPDF4LLM with Layout](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/) (import order and header/footer)
