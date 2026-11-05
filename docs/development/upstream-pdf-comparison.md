# Upstream PDF tests vs our converter

Slice 1 comparison (ENG-1) — input for ENG-2, the PDF engine replacement. The PDF converter was not changed to make these tests pass.

Our converter is the existing PyMuPDF / pymupdf4llm path. Upstream's tests were written for pdfminer / pdfplumber. `tests/test_pdf.py` collects. Two helper unit tests are skipped in `tests/conftest.py` because the helpers are not in our converter. They are not rows below.

Run: 11 failed, 5 errors, 17 passed, 4 skipped (`test_pdf.py`).

Classifications:

- **engine-internal** — pdfplumber call counts, upstream-only helpers, or an exact snapshot of upstream's engine.
- **content-loss** — text, a value, a row, or a table is missing from our output.
- **format-only** — the same content is present, with different Markdown layout.
- **text distortion** — the content is there, but words are split or merged (e.g. `repa` / `ir`, `UnitCost`, `EST -1008`). Not content-loss, but it hurts exact-match search and LLM reading. Tracked as acceptance cases for the replacement engine (ENG-2).

No failing test in this run is content-loss. Values upstream looks for are in our output. The gaps are layout, text distortion, or tests that call pdfplumber.

Cowork re-check (2026-11-05): an earlier version of this table said pymupdf4llm raised on `test.pdf` and a fallback produced the text. That is wrong. `pymupdf4llm.to_markdown` converts `test.pdf` without error with no options, with the fork's options (`write_images`, `page_chunks`, `margins=0`), and through a default `MarkItDown().convert`; no fallback warning is logged. The real gap on that file is that headings are not detected.

## test_pdf.py

| Test | Fixture | Upstream expects | Our converter produces | Classification |
|---|---|---|---|---|
| `TestPdfTableExtraction::test_borderless_table_extraction` | `SPARSE-2024-INV-1234_borderless_table.pdf` | `Report ID: SPARSE-2024-INV-1234` and `Prepared By: Sarah Martinez` | `**Report ID:** SPARSE-2024-INV-1234` and `**Prepared By:** Sarah Martinez`. SKUs, `$4,287.50`, and both tables are present. Second-table headers are concatenated (`UnitCost`, `LastAudit`). | format-only + text distortion |
| `TestPdfTableExtraction::test_borderless_table_correct_position` | `SPARSE-2024-INV-1234_borderless_table.pdf` | The literal `Prepared By: Sarah Martinez` before `Product Code` | `**Prepared By:** Sarah Martinez` (the unbolded string is absent, so the order assert never runs). `Product Code` and `Variance Analysis:` are present. | format-only |
| `TestPdfTableExtraction::test_multipage_invoice_extraction` | `REPAIR-2022-INV-001_multipage.pdf` | A cell matching `\| Insured name \|` | `\|**Insured name**\|Gabriel Diaz\|**Year**\|2022\|`. Names, totals (`5,738`, `211,522`), and both vehicles are present. The note word "repair" is split across cells on page 1 (`repa` / `ir`). | format-only + text distortion |
| `TestPdfFullOutputComparison::test_movie_theater_full_output` | `movie-theater-booking-2024.pdf` | Exact file `expected_outputs/movie-theater-booking-2024.md`, starting `BOOKING ORDER` and a pipe row `\| Order / Rev: \| 2024-12-5678 \|` | `# BOOKING ORDER Print Date 12/15/2024 14:30:22` then plain lines `Order / Rev: 2024-12-5678`. No expected token is missing. The totals table is still pipes. | engine-internal |
| `TestPdfFullOutputComparison::test_sparse_borderless_table_full_output` | `SPARSE-2024-INV-1234_borderless_table.pdf` | Exact `expected_outputs/SPARSE-2024-INV-1234_borderless_table.md`: `INVENTORY RECONCILIATION REPORT` and `\| Product Code \| Location \| Expected \|` | `# **INVENTORY RECONCILIATION REPORT**` and `\|Product Code\|Location\|Expected\|Actual\|Variance\|Status\|`. Same SKUs and amounts. A page image link is appended. | engine-internal |
| `TestPdfFullOutputComparison::test_repair_multipage_full_output` | `REPAIR-2022-INV-001_multipage.pdf` | Exact `expected_outputs/REPAIR-2022-INV-001_multipage.md`: `ZAVA AUTO REPAIR` and `\| Insured name \| Gabriel Diaz \|` | `## **ZAVA AUTO REPAIR**` plus a leading page image, then `\|**Insured name**\|Gabriel Diaz\|`. Estimate id is `PreliminaryEstimate(ID:EST -1008)` (spaces removed). Amounts match. | engine-internal + text distortion |
| `TestPdfFullOutputComparison::test_receipt_full_output` | `RECEIPT-2024-TXN-98765_retail_purchase.pdf` | Exact `expected_outputs/RECEIPT-2024-TXN-98765_retail_purchase.md`, with a blank line around each `===================================` rule | Same receipt text (`Store #0342`, `SUBTOTAL $863.91`, `TXN98765202411231432`). Those blank lines are absent. No token is missing. | engine-internal |
| `TestPdfFullOutputComparison::test_academic_paper_full_output` | `test.pdf` | Exact `expected_outputs/test.md`: a `1` line, then `Introduction`, then the paragraph. Line-break hyphens kept (`con-` / `firming`). | `**1** **Introduction**` and the paragraph with emphasis (`_agents_`). Hyphens at line breaks are joined (`confirming`, `chatoptimized`). Headings are not detected — they come out as bold text, not `#`. | engine-internal + text distortion |
| `TestPdfFullOutputComparison::test_medical_scan_full_output` | `MEDRPT-2024-PAT-3847_medical_report_scan.pdf` | Empty string. Upstream extracts no text from this scan. | Three page-image links and no text: `![](...pdf-0-full.png)` through `pdf-2-full.png`. | engine-internal |
| `TestPdfTableStructureConsistency::test_all_pdfs_table_rows_consistent[REPAIR-2022-INV-001_multipage.pdf-6]` | `REPAIR-2022-INV-001_multipage.pdf` | 6 pipe tables (customer, labor totals, and supplies counted separately, on two pages) | 4 pipe tables. Supplies and tax rows sit inside the totals table (`Paint Supplies` 60, `GRAND TOTAL` `5,738` / `211,522`). The other three PDFs in this test match the expected counts and passed. | format-only |
| `TestPdfMemoryOptimization::test_page_close_called_on_every_page` | `pdf_cleanup_form.pdf` | pdfplumber `Page.close` once per page, after form extraction | Error at setup: `ModuleNotFoundError: No module named 'pdfplumber'`. pdfplumber is not a fork dependency. | engine-internal |
| `TestPdfMemoryOptimization::test_plain_text_pdf_falls_back_to_pdfminer` | `pdf_cleanup_plain.pdf` | One `pdfminer` extract, and the sentence `While there is contemporaneous exploration` three times | Same error: `No module named 'pdfplumber'`. | engine-internal |
| `TestPdfMemoryOptimization::test_plain_text_pdf_still_closes_all_pages` | `pdf_cleanup_plain.pdf` | Each plain page is closed before the pdfminer fallback | Same error: `No module named 'pdfplumber'`. | engine-internal |
| `TestPdfMemoryOptimization::test_mixed_pdf_uses_form_extraction_per_page` | `pdf_cleanup_mixed.pdf` | Per-page activity `[("form", 1), ("plain", 2), ("form", 3)]` | Same error: `No module named 'pdfplumber'`. | engine-internal |
| `TestPdfMemoryOptimization::test_only_one_pdfplumber_open_call` | `pdf_cleanup_form.pdf` | `pdfplumber.open` called once | Same error: `No module named 'pdfplumber'`. | engine-internal |
| `TestPdfMemoryOptimization::test_real_pdf_page_cleanup` | `REPAIR-2022-INV-001_multipage.pdf` | Patches `pdfplumber.page.Page.extract_words` and `Page.close` | Error in the test: `ModuleNotFoundError: No module named 'pdfplumber'` (`test_pdf.py` imports it directly). | engine-internal |

## PDF rows in test_module_vectors.py

These are not `test_pdf.py`. They failed on the same layout gap. Twelve tests, two fixtures. Each entry point failed the first missing `must_include` string.

| Tests | Fixture | Upstream expects | Our converter produces | Classification |
|---|---|---|---|---|
| `test_convert_local`, `test_convert_stream_with_hints`, `test_convert_stream_without_hints`, `test_convert_http_uri`, `test_convert_file_uri`, `test_convert_data_uri` — each `[test_vector11]` | `pdf_cleanup_form.pdf` | `\| Customer Information \|` (also `Gabriel Diaz`, `\| GRAND TOTAL`, `5,738`) | `\|**Customer Information**\|**Customer Information**\|**Vehicle Information**\|` and `\|**GRAND TOTAL**\|\|\|\|\|**5,738**\|`. `Gabriel Diaz` and `5,738` are present. | format-only |
| same six tests — `[test_vector12]` | `pdf_cleanup_mixed.pdf` | `\| Customer Information \|` plus `While there is contemporaneous exploration of multi-agent approaches` | Same bold customer table as the form fixture. The academic sentence is present. | format-only |

`pdf_cleanup_plain.pdf` and `test.pdf` vector rows passed.
