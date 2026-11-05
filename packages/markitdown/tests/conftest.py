"""Fork divergences from upstream tests.

This is the one fork-owned list. Upstream test files stay as close to
upstream as possible, because every edit there is a conflict on the next sync.

Two mechanisms:

- Skips: the test cannot run on this fork, or it checks an engine we do not
  have. A skip is not a failure and will not turn into XPASS.
- Xfails: the test runs, and our PDF engine is known to disagree with
  upstream. strict is off, so an engine that starts passing shows XPASS.

The output gaps are classified in
docs/development/upstream-pdf-comparison.md. Replacing the engine is ENG-2.
"""

import pytest

# Short name -> why. Used only for test_pdf.py. Parametrized ids use the
# name before the first "[".
FORK_TEST_SKIPS = {
    "test_partial_numbering_pattern_regex": (
        "Not applicable to the fork PDF engine. "
        "Upstream's PARTIAL_NUMBERING_PATTERN helper is not in our converter."
    ),
    "test_merge_partial_numbering_with_empty_lines_between": (
        "Not applicable to the fork PDF engine. "
        "Upstream's _merge_partial_numbering_lines helper is not in our converter."
    ),
}

# pdfplumber is imported while the fixture is set up, or at the top of the
# test before the body pytest can mark xfail. xfail does not catch that.
# These are skipped instead. Keys are file-scoped node ids.
_PDFPLUMBER_SKIP_REASON = (
    "pdfplumber internals of upstream's engine; not applicable to fork engine"
)
FORK_TEST_SKIPS.update(
    {
        node_id: _PDFPLUMBER_SKIP_REASON
        for node_id in (
            "test_pdf.py::TestPdfMemoryOptimization::test_page_close_called_on_every_page",
            "test_pdf.py::TestPdfMemoryOptimization::test_plain_text_pdf_falls_back_to_pdfminer",
            "test_pdf.py::TestPdfMemoryOptimization::test_plain_text_pdf_still_closes_all_pages",
            "test_pdf.py::TestPdfMemoryOptimization::test_mixed_pdf_uses_form_extraction_per_page",
            "test_pdf.py::TestPdfMemoryOptimization::test_only_one_pdfplumber_open_call",
        )
    }
)

# Known output gaps. Same reason on every row. strict=False so a future
# engine that passes is reported as XPASS, not as a new failure.
_PDF_XFAIL_REASON = (
    "Fork PDF engine (pymupdf4llm) diverges from upstream; "
    "classified in docs/development/upstream-pdf-comparison.md; "
    "replacement engine tracked in ENG-2."
)
FORK_TEST_XFAILS = {
    node_id: _PDF_XFAIL_REASON
    for node_id in (
        "test_pdf.py::TestPdfTableExtraction::test_borderless_table_extraction",
        "test_pdf.py::TestPdfTableExtraction::test_borderless_table_correct_position",
        "test_pdf.py::TestPdfTableExtraction::test_multipage_invoice_extraction",
        "test_pdf.py::TestPdfFullOutputComparison::test_movie_theater_full_output",
        "test_pdf.py::TestPdfFullOutputComparison::test_sparse_borderless_table_full_output",
        "test_pdf.py::TestPdfFullOutputComparison::test_repair_multipage_full_output",
        "test_pdf.py::TestPdfFullOutputComparison::test_receipt_full_output",
        "test_pdf.py::TestPdfFullOutputComparison::test_academic_paper_full_output",
        "test_pdf.py::TestPdfFullOutputComparison::test_medical_scan_full_output",
        "test_pdf.py::TestPdfTableStructureConsistency::test_all_pdfs_table_rows_consistent[REPAIR-2022-INV-001_multipage.pdf-6]",
        "test_pdf.py::TestPdfMemoryOptimization::test_real_pdf_page_cleanup",
        "test_module_vectors.py::test_convert_local[test_vector11]",
        "test_module_vectors.py::test_convert_local[test_vector12]",
        "test_module_vectors.py::test_convert_stream_with_hints[test_vector11]",
        "test_module_vectors.py::test_convert_stream_with_hints[test_vector12]",
        "test_module_vectors.py::test_convert_stream_without_hints[test_vector11]",
        "test_module_vectors.py::test_convert_stream_without_hints[test_vector12]",
        "test_module_vectors.py::test_convert_http_uri[test_vector11]",
        "test_module_vectors.py::test_convert_http_uri[test_vector12]",
        "test_module_vectors.py::test_convert_file_uri[test_vector11]",
        "test_module_vectors.py::test_convert_file_uri[test_vector12]",
        "test_module_vectors.py::test_convert_data_uri[test_vector11]",
        "test_module_vectors.py::test_convert_data_uri[test_vector12]",
    )
}

# Edits to upstream test files that still run. Recorded here so the reason
# is not only a comment buried in the test.
FORK_TEST_EDITS = {
    "packages/markitdown/tests/test_pdf.py": (
        "Import of PARTIAL_NUMBERING_PATTERN and _merge_partial_numbering_lines "
        "is wrapped. Without that, the module cannot be collected. "
        "The two helper tests above are skipped. No other assertion was changed."
    ),
    "packages/markitdown/tests/test_pptx.py": (
        "test_caption_failure_precedes_hook_with_fresh_image_stream asserts the "
        "kwargs of llm_caption. The fork wrapper also receives slide, shape, "
        "and use_advanced_prompt. Only that assertion was updated."
    ),
    "packages/markitdown/tests/test_module_misc.py": (
        "Taken from upstream unchanged. Fork Gemini tests moved to "
        "tests/test_llm_gemini.py."
    ),
}


def _file_scoped_nodeid(nodeid: str) -> str:
    """Return 'test_pdf.py::Class::test[id]' from a pytest node id.

    The directory prefix is dropped so the map does not depend on where
    pytest was started. Only the two PDF modules are recognized.
    """
    normalized = nodeid.replace("\\", "/")
    for filename in ("test_pdf.py", "test_module_vectors.py"):
        token = filename + "::"
        start = normalized.find(token)
        if start != -1:
            return normalized[start:]
    return ""


def pytest_collection_modifyitems(config, items):
    """Skip tests that cannot run here, and xfail known PDF output gaps."""
    for item in items:
        scoped = _file_scoped_nodeid(item.nodeid)
        if not scoped:
            continue

        # Helper unit tests are registered by short name. Everything else in
        # the skip map is a full node id, so a same-named test in another
        # file is left alone.
        skip_reason = FORK_TEST_SKIPS.get(scoped)
        if skip_reason is None and scoped.startswith("test_pdf.py::"):
            short_name = item.name.split("[", 1)[0]
            skip_reason = FORK_TEST_SKIPS.get(short_name)
        if skip_reason:
            item.add_marker(pytest.mark.skip(reason=skip_reason))
            continue

        xfail_reason = FORK_TEST_XFAILS.get(scoped)
        if xfail_reason:
            # strict=False: a pass is XPASS, which is how we will notice
            # that ENG-2 has closed this gap.
            item.add_marker(pytest.mark.xfail(reason=xfail_reason, strict=False))
