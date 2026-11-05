# Upstream v0.1.9 merge + image descriptions for DOCX/XLSX — plan

Lane: **desktop** · Branch: `cursor/upstream-v0.1.9-merge` (from `main` @ `682b3af`) · Upstream: `microsoft/markitdown` `main` @ `7482c09` (v0.1.9)

---

## Part 1 — what we are doing and why

### Goal

1. Bring our fork up to date with the open-source project (we are 131 commits behind: v0.1.3 → v0.1.9) **without losing our own features**: AI image descriptions (Gemini/OpenAI), our PyMuPDF-based PDF converter, parallel/gevent-safe image processing.
2. Extend AI image descriptions to **Word (DOCX)** and **Excel (XLSX)** files. Today they only work for PDF, PowerPoint and standalone images.
3. Let ai_personality pick up the new version (it pins our fork at commit `682b3af` in `requirements.txt`).

### Decisions already taken (discussion 2026-11-05)

- **PDF: keep our converter.** Upstream's PDF work (table detection, list-numbering fix, memory fix) is built on a different engine (pdfminer/pdfplumber) and has no images, headings or descriptions. We do not adopt it. We *will* run upstream's PDF test files against our converter as a quality comparison, so we know with data whether upstream extracts some tables better.
- **Everything else: take upstream** (≈120 fixes across PPTX, DOCX, RSS, EPUB, CSV, ZIP, YouTube, Outlook; new Azure Content Understanding converter; MCP server on MCP SDK 2.x).
- **Not adopting `markitdown-ocr`** — it is LLM-vision "OCR" for OpenAI-compatible clients only; ai_personality has Google OCR. The package arrives in the repo with the merge but nothing installs it.

### What changes for ai_personality after the pin bump

- Many format fixes for free (e.g. ZIP now passes the LLM settings to the files inside it; PPTX/DOCX/CSV/RSS/EPUB crash fixes).
- Word and Excel files with images will start getting AI descriptions automatically whenever the Gemini key is set — same as PDFs today. **More Gemini calls and longer conversion for image-heavy DOCX books.**
- The description block looks the same as in PDFs (`**[AI-Generated Image Description]**` + text, original image link kept after it), so downstream text handling sees one format.
- Two dependency pins in ai_personality must move: `certifi` (upstream now requires ≥ 2026.10.19; we pin 2026.2.25) and `mammoth` (upstream requires ≥ 1.12.2; we pin 1.11.0).

### Out of scope (separate tasks if wanted)

- Image descriptions for EPUB (books!) — upstream has no image hook there; it would need its own design.
- Moving from `google-generativeai` (deprecated by Google) to `google-genai`.
- Removing PyMuPDF / pymupdf4llm (AGPL-3.0 or Artifex commercial; `pymupdf-layout` is Polyform Noncommercial and is **not installed** in ai_personality, so the `header=False/footer=False` options it sends are silently ignored today) — separate tickets **ENG-2** (fork PDF engine) and **PD-743** (ai_personality side, blocked by ENG-2). Does not block this work.

---

## Part 2 — technical plan

### Verified facts

| Fact | Source |
|---|---|
| Fork base = upstream `3d4fe3c`; upstream `main` is a descendant (131 commits) | `git merge-base`, trial merge 2026-11-05 |
| Trial merge conflicts: `README.md`, `pyproject.toml`, `_pdf_converter.py`, `_plain_text_converter.py`, `_pptx_converter.py`, `tests/test_module_misc.py`. `_markitdown.py`, `_image_converter.py` auto-merge. | trial merge in a throwaway clone |
| Upstream net change to `_image_converter.py` is empty (graceful-failure added in #1948, reverted by #2476) | `git diff 3d4fe3c upstream/main -- …` |
| Upstream PPTX moved picture handling into `PptxConverter._convert_picture_to_markdown(shape, **kwargs)`, calling `llm_caption` (OpenAI-only) without slide context | upstream `_pptx_converter.py:171` |
| Upstream DOCX/XLSX expose `_image_to_html(image_stream, stream_info, **kwargs)`; the image adapter is wired **only when a subclass overrides it** (`type(self)._image_to_html is not DocxConverter._image_to_html`) | upstream `_docx_converter.py:107`, `_xlsx_converter.py:146` |
| XLSX images are rendered after their sheet's table, not interleaved | upstream `_xlsx_converter.py`, `converter_utils/_xlsx_images.py` |
| Our PDF image pipeline is filename-keyed over markdown text: `_process_images_parallel` → (async Gemini / subprocess under gevent / threads) → `_replace_images_with_descriptions`, with `_extract_image_context` taking 800 chars before/after | `_pdf_converter.py:297–893` |
| Upstream `tests/test_pdf.py` is engine-specific in parts (`TestPdfMemoryOptimization` asserts pdfplumber page.close calls; `TestPdfFullOutputComparison` compares exact output) and content-level in others (table data present, pipe format) | upstream `tests/test_pdf.py` |
| ai_personality contract: `MarkItDown(gemini_api_key=…, llm_model="gemini-2.5-flash")`; `convert(path, max_image_workers=…, page_chunks=True, margins=0, header=False, footer=False)` for PDF; all other formats with no extra kwargs | ai_personality `utils/text_utils.py:497–531` |
| ai_personality installs markitdown core only (no extras) and pins `pymupdf4llm==0.3.4`, `pymupdf==1.27.1`, `mammoth==1.11.0`, `certifi==2026.2.25`, `magika==0.6.3`, `google-generativeai==0.8.5` directly | ai_personality `requirements.txt` |
| Test instrument: repo-root `.venv` (Python 3.12.3, pytest 9.0.2, editable install of `packages/markitdown`) | checked on desktop 2026-11-05 |

### Slice 0 — setup (Cowork)

1. Branch `cursor/upstream-v0.1.9-merge` from `main` ✔; remote `upstream` added and fetched ✔.
2. **Runner:** `run_live.sh` always `cd`s into `REPO_DIR` from `lane.env` (= ai_personality). Make it overridable: in `~/cursor_collab/lane.env` change to `REPO_DIR="${REPO_DIR:-$HOME/user/work/ai_personality}"`, launch with `REPO_DIR=$HOME/user/work/markitdown ./run_live.sh …`. Same edit synced to `~/cursor-sync/lane/` and the laptop. *Needs Denys's OK — shared infra.*
3. Task instruments note `~/cursor_collab/markitdown-upstream-merge/instruments.md`: tests run from repo root with `.venv/bin/python -m pytest packages/markitdown/tests/<file> -q`; no installs, no new venvs; LLM tests skip without `GEMINI_API_KEY`/`OPENAI_API_KEY`.
4. Two Cursor chats (discussion / work), recorded in `state.md`.
5. Baseline on `main`: full `packages/markitdown/tests` run once, results recorded.

### Slice 1 — merge and conflict resolution (Cursor, work chat, agent mode)

Cowork starts `git merge --no-commit --no-ff upstream/main` on the branch; Cursor resolves. Rules per file:

| File | Resolution |
|---|---|
| `_pdf_converter.py` | **Ours, entirely.** |
| `_pptx_converter.py` | **Upstream's file**, then one change inside `_convert_picture_to_markdown`: replace the `llm_caption(...)` call with our `caption_image(...)` passing `context_before/context_after` built from the slide's other text shapes (slide reachable as `shape.part.slide`; verify for group and placeholder pictures) and `use_advanced_prompt`. Port our current logic (`HEAD:_pptx_converter.py`), do not rewrite it. |
| `_plain_text_converter.py` | Upstream's version (same fix as ours, plus a `None` guard). |
| `pyproject.toml` | Core deps = upstream's (incl. `certifi>=2026.10.19`, `magika>=0.6.1,<2`; Windows onnxruntime pin dropped as upstream did). Extras = upstream's, except `pdf = ["pymupdf4llm"]` and `all` uses `pymupdf4llm` instead of pdfminer/pdfplumber; keep our `pdf-layout`, `google-generativeai`, `pillow`. |
| `tests/test_module_misc.py` | Upstream's version. Our Gemini tests move unchanged to a fork-owned file `tests/test_llm_gemini.py` (fewer conflicts on the next upstream sync). |
| `README.md` | Upstream body + our fork section on top. |
| `__about__.py` | `0.1.9+cios` (PEP 440 local label — shows it's our build of 0.1.9). |
| `_markitdown.py`, `_image_converter.py` (auto-merged) | Check our Gemini client creation and `llm_use_advanced_prompt` default survived. |

**Upstream PDF tests vs our converter.** Run upstream `tests/test_pdf.py` and the PDF entries in `_test_vectors.py`. Classify each failure:
- *engine-internal* (pdfplumber call counts, `_merge_partial_numbering_lines` unit tests, exact full-output snapshots) → remove from our tree with a one-line note in the fork section of README;
- *content-level* (a value, row or table missing from our output) → **do not fix in this slice**; list it in a comparison table (file, what upstream extracts, what we extract). This is the evidence for whether any upstream PDF idea is worth porting (e.g. the partial-numbering post-process is pure text and cheap to adopt).

Targeted tests (no other runs): `test_module_misc.py`, `test_llm_gemini.py`, `test_pdf.py`, PPTX test file(s), `test_module_vectors.py` (or upstream's equivalent after consolidation). Before running, Cowork refreshes the venv with the repo's own documented install `pip install -e 'packages/markitdown[all]'` (new declared deps such as `azure-ai-contentunderstanding`); Cursor installs nothing.

**Commit point:** Denys commits the merge commit (true merge, so the next upstream sync starts from `7482c09`).

### Slice 2 — image descriptions for DOCX and XLSX (Cursor, work chat)

**What each step sees**

| Step | Sees | Produces |
|---|---|---|
| mammoth image callback → `_image_to_html` (DOCX) | one image's bytes + content type; **no surrounding text** | an HTML fragment placed where the image is |
| `_XlsxImages.to_html` → `_image_to_html` (XLSX) | one image's bytes; sheet name | HTML after the sheet's table |
| our PDF pipeline (`_process_images_parallel` …) | list of image files + the **finished markdown** (for 800-char context) | `{filename: description}`, then inserted next to each `![…](filename)` |

**Options**

- **A — describe inside the hook.** `_image_to_html` calls `caption_image` and returns the description. Simple, but: one image at a time (no parallelism), no surrounding-text context, and the Gemini call runs inside the gevent worker in ai_personality — the exact situation our PDF code routes to a subprocess to avoid.
- **B — hook only marks, shared pipeline describes (recommended).** `_image_to_html` writes the image to a per-conversion temp dir under a unique name (`docx_img_0001.png`…) and returns `<img src="docx_img_0001.png" alt="…">`. After the base conversion, run the **same** pipeline the PDF converter uses on those files and the finished markdown. Gives parallelism, gevent-safe subprocess path, context before/after, identical output format to PDF.

**B in practice**

1. Move the image-description methods out of `PdfConverter` into a shared module (`converters/_image_descriptions.py`) — a pure move; `PdfConverter` calls the shared functions. Verified mechanically (AST comparison of moved bodies vs `git show HEAD:`).
2. Fork-owned subclasses in new files (`_docx_converter_described.py`, `_xlsx_converter_described.py`) overriding `_image_to_html` and wrapping `convert()` (temp dir → `super().convert()` → describe → replace → cleanup in `finally`). Registered in `_markitdown.py` in place of the upstream classes. Upstream files stay untouched → the next upstream sync has nothing to conflict on.
3. When no LLM client/model is configured, the subclasses behave exactly like upstream (hook returns `None`).
4. Image types the model cannot read (EMF/WMF and similar) are skipped and keep their native rendering.

Targeted tests: new tests for DOCX and XLSX with a fake LLM client (synthetic fixtures; upstream's `markitdown-ocr/tests/ocr_test_data/docx_*.docx`/`xlsx_*.xlsx` are usable fixtures), plus the PDF test file to prove the pipeline move changed nothing.

**Commit point:** Denys commits slice 2 as its own commit.

### Final cycle (once, after slice 2)

1. Full `packages/markitdown/tests` run vs the slice-0 baseline.
2. One live check with a real Gemini key: convert one PDF with images, one PPTX, one DOCX, one XLSX through `MarkItDown(gemini_api_key=…, llm_model="gemini-2.5-flash")` with ai_personality's exact PDF kwargs.
3. Push the branch, merge to fork `main` (Denys).

### Slice 3 — ai_personality pin bump (separate repo, separate task)

`requirements.in`/`requirements.txt`: markitdown → new fork commit; `certifi>=2026.10.19`; `mammoth>=1.12.2`; recompile. Then ai_personality's own `make test` and one book upload on the test stack. **Not on the desktop lane right now** — its ai_personality checkout is on `cursor/knowledge-connections` (another task). Run it on the laptop lane or once desktop is back on `deploy`.

### Decisions (Denys, 2026-11-05)

1. `REPO_DIR` overridable in the desktop runner — **approved, done** (`~/cursor_collab/lane.env`, backup `lane.env.bak-20261105`).
2. DOCX/XLSX descriptions **on by default** whenever the LLM is configured — **approved**.
3. Option B for slice 2 — **approved**.
4. Artifex/PyMuPDF will be **removed** later — fork PDF engine under **ENG-2**, ai_personality side under **PD-743** (clean-room reimplementation on MIT/Apache libraries). Consequences for this plan: keep our PDF converter for now, but nothing new may deepen the PyMuPDF dependency; the shared image-description module must not import PyMuPDF; the slice-1 PDF comparison table is the starting gap list for ENG-2.
5. **EPUB image descriptions: skipped** (Denys, 2026-11-05) — CIOS does not expect EPUB from clients. Step 3 covers DOCX + XLSX (+ PPTX grouped-picture context) only.
6. Jira: this work is **ENG-1** (project ENG "Engineering Tools & Forks", created 2026-11-05 for forks, internal tooling and side repos).

## Review log

### Round 1 — Cursor (discussion chat, ask mode), 2026-11-05

All 12 findings accepted (two blockers verified by Cowork against the code). They change the slice rules as follows; where a rule above conflicts, **this section wins**.

| # | Finding | Closed by |
|---|---|---|
| 1 | BLOCKER — plain text: ours falls back to detection when a *declared* charset fails to decode (`_plain_text_converter.py:69–76`); upstream only guards `best() is None`. "Take upstream" was wrong (Cowork's error). | **Keep both**: declared charset → on decode error fall back to detection → if detection returns `None`, `utf-8` with `errors="ignore"`. Upstream's `None` tests must pass. |
| 2 | BLOCKER — upstream `tests/test_image.py:137` patches `ImageConverter._get_llm_description`; our converter removed it. | Restore `_get_llm_description` as the seam in our `ImageConverter`, implemented via `caption_image` (keeps upstream's raise-on-failure semantics for OpenAI). Add `test_image.py` to the slice-1 run list. |
| 3 | PPTX: three upstream tests patch `_pptx_converter.llm_caption` (`test_pptx.py:719, 736, 837`), one asserts exact kwargs. | Keep the module-level name `llm_caption` in `_pptx_converter` as a thin wrapper that adds slide context and calls `caption_image`; update only the exact-kwargs assertion. |
| 4 | `tests/test_pdf.py:10–13` imports upstream-only helpers → collection error. | Split the import first; helper unit tests (partial numbering) move to a "not applicable to fork engine" list, then run and classify the rest. |
| 5 | Image pipeline hardcodes `image/png` (`_pdf_converter.py:573–577, 792–796`, `_image_description_worker.py:60–64`). | Thread the real mimetype/extension through all three paths (subprocess payload included). DOCX hook returns `None` for EMF/WMF/SVG so mammoth keeps its native rendering. |
| 6 | Replacer pastes a multi-line block into a DOCX table cell → broken table. | **Decision (Cowork):** image link stays in the cell; the description block goes right after the table. No content is lost and the table stays valid. |
| 7 | `_extract_image_context` matches filename as substring; replacer matches last path segment. | Context lookup uses the same last-segment match. One counter per conversion across all sheets. |
| 8 | Auto-merged `_markitdown.py` keeps our Gemini client + advanced-prompt default; CU only active with `cu_endpoint`. | No action. |
| 9 | ai_personality passes `max_image_workers` for **all** formats (`text_utils.py:517–519`), so after the merge PDFs inside ZIPs get described too. | Fact table corrected (see note below); accepted as intended. |
| 10 | `list(slide.shapes).index(shape)` misses grouped pictures; `shape.part.slide` works but is a worse seam. | Pass the `slide` from `get_shape_content` into `_convert_picture_to_markdown`. |
| 11 | markitdown-ocr at priority −1.0 would pre-empt our subclasses if plugins are enabled; ai_personality doesn't enable plugins. | Register only our subclasses (replace the two builtin registrations); don't register the upstream classes beside them. |
| 12 | A `GEMINI_API_KEY` in the environment makes plain `MarkItDown()` caption during ordinary tests. | Instruments: tests run with `env -u GEMINI_API_KEY -u OPENAI_API_KEY` (no keys are set on the desktop shell today; the prefix guards it). |

Also from the review:
- The pipeline move is a **function extraction**, not a pure move (methods call `self._…`). Verified by the PDF tests + new unit tests of the replacer/context functions, not by AST equality.
- Per-conversion temp dir and counter live in a local object inside `convert()`, cleared in `finally` — never on `self` (converter instances are reused).
- PPTX captions stay synchronous in-process (current production behaviour); moving PPTX onto the shared pipeline is not in this merge.

**Correction to "Verified facts":** ai_personality's call is `convert(path, max_image_workers=N)` for every format, plus the four layout kwargs for PDF only.

## Implementation log (ENG-1)

| Commit | Slice | Notes |
|---|---|---|
| `000726e` | 1 — merge upstream v0.1.9 | Conflicts resolved per Round 1; fork test divergences in `tests/conftest.py` (5+4 skips, 23 non-strict xfails); PDF comparison in `upstream-pdf-comparison.md`. |
| `8b1e349` | 2a — shared pipeline | `converters/_image_descriptions.py` (`describe_images_in_markdown`); real mimetypes on async/threaded/subprocess paths; exact last-segment context; table-safe replacement. |
| `32a896e` | 2b — DOCX/XLSX + PPTX groups | `DocxConverterDescribed` / `XlsxConverterDescribed` registered in place of the builtins; per-call session via kwargs; png/jpeg/gif/webp only; `keep_data_uris` restores data URIs; grouped PPTX pictures use the converter's walk order. |

Review: each slice reviewed by Cowork against the plan; 8 guard tests mutation-checked (all caught).

Live check (Gemini 2.5 Flash, `MarkItDown(gemini_api_key=…, llm_model="gemini-2.5-flash")`, `convert(…, max_image_workers=4)`), 2026-11-05:
- PDF `test_image.pdf`: 2 descriptions. PPTX `test.pptx`: description in alt text. DOCX with a real diagram: described. XLSX banners: 1 of 2 described.
- Subprocess worker path (production under gevent): JPEG described, real mimetype passed.
- Synthetic text-banner images are sometimes answered `SKIP:` by Gemini — this is the advanced prompt's "skip decorative/UI images" rule in `_gemini_caption.py`, not a pipeline fault (same DOCX with a real photo is described).
- Not verified here: the real gevent switch inside ai_personality (gevent is not in markitdown's venv) — covered by the ai_personality pin-bump step (upload on the test stack).

LOW end-list (not blocking):
1. `ImageDescriptionSession.add` base64-encodes every image even when `keep_data_uris` is off (memory only).
2. Ungrouped PPTX pictures still take context from `slide.shapes` collection order, grouped ones from the visual walk order — unify on walk order.
3. Pre-existing: the subprocess worker receives the API key via a temp JSON file under `/tmp`.
