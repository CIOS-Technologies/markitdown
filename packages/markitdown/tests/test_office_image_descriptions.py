"""DOCX and XLSX image descriptions, plus PPTX grouped-picture context.

Synthetic documents and the OCR fixtures. A fake OpenAI-style client.
No network and no Gemini.
"""

import base64
import io
import re
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pptx import Presentation
from pptx.util import Inches

from markitdown import MarkItDown
from markitdown._stream_info import StreamInfo
from markitdown.converters import _image_descriptions
from markitdown.converters._docx_converter import DocxConverter
from markitdown.converters._docx_converter_described import DocxConverterDescribed
from markitdown.converters._office_image_session import (
    SESSION_KEY,
    ImageDescriptionSession,
)
from markitdown.converters._pptx_converter import _slide_text_around_picture
from markitdown.converters._xlsx_converter import XlsxConverter
from markitdown.converters._xlsx_converter_described import XlsxConverterDescribed

_CAPTION = "Synthetic office image description."
_HEADING = "**[AI-Generated Image Description]**"
_FIXTURES = (
    Path(__file__).resolve().parents[2]
    / "markitdown-ocr"
    / "tests"
    / "ocr_test_data"
)
_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def _client() -> MagicMock:
    """A client detect_provider treats as OpenAI. The caption is fixed."""
    client = MagicMock()
    client.chat.completions.create.return_value.choices[0].message.content = _CAPTION
    return client


def _docx(body: str, *, extension: str = "png", content_type: str = "image/png", blob: bytes = _PNG) -> bytes:
    """A tiny docx whose only embedded image is blob."""
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr(
            "[Content_Types].xml",
            f"""<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="{extension}" ContentType="{content_type}"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>""",
        )
        archive.writestr(
            "_rels/.rels",
            """<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdDocument" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>""",
        )
        archive.writestr(
            "word/_rels/document.xml.rels",
            f"""<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rIdImage" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image.{extension}"/>
</Relationships>""",
        )
        archive.writestr(
            "word/document.xml",
            f"""<w:document
  xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
  xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
  xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
  <w:body>{body}</w:body>
</w:document>""",
        )
        archive.writestr(f"word/media/image.{extension}", blob)
    return stream.getvalue()


def _image_drawing() -> str:
    return """<w:r><w:drawing><wp:inline>
  <wp:extent cx="9525" cy="9525"/>
  <wp:docPr id="1" name="Image 1"/>
  <a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
    <pic:pic>
      <pic:nvPicPr><pic:cNvPr id="1" name="Image 1"/><pic:cNvPicPr/></pic:nvPicPr>
      <pic:blipFill><a:blip r:embed="rIdImage"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
      <pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="9525" cy="9525"/></a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
      </pic:spPr>
    </pic:pic>
  </a:graphicData></a:graphic>
</wp:inline></w:drawing></w:r>"""


def _paragraph(text: str) -> str:
    return f'<w:p><w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>'


def _table_docx() -> bytes:
    """One image inside the first cell of a two-column table."""
    body = (
        _paragraph("Before the table")
        + "<w:tbl><w:tr>"
        + "<w:tc><w:p>"
        + _image_drawing()
        + "</w:p></w:tc>"
        + '<w:tc><w:p><w:r><w:t xml:space="preserve">Beside</w:t></w:r></w:p></w:tc>'
        + "</w:tr></w:tbl>"
        + _paragraph("After the table")
    )
    return _docx(body)


def _emf_docx() -> bytes:
    return _docx(
        _paragraph("Before emf") + "<w:p>" + _image_drawing() + "</w:p>" + _paragraph("After emf"),
        extension="emf",
        content_type="image/x-emf",
        blob=b"\x01\x00\x00\x00not-a-vision-image",
    )


def _convert(converter, data: bytes, extension: str, **kwargs):
    return converter.convert(
        io.BytesIO(data), StreamInfo(extension=extension), **kwargs
    ).markdown


def _pipe_cells(line: str) -> list[str]:
    parts = line.strip().split("|")
    return [part.strip() for part in parts[1:-1]]


def test_docx_image_between_paragraphs_is_described_with_context(monkeypatch) -> None:
    path = _FIXTURES / "docx_image_middle.docx"
    seen: list[dict] = []
    real = _image_descriptions.caption_image

    def spy(stream, info, **kwargs):
        # The OpenAI caption path ignores context. Record it here so a
        # missing before/after fails even though the client is OpenAI-style.
        seen.append(kwargs)
        return real(stream, info, **kwargs)

    monkeypatch.setattr(_image_descriptions, "caption_image", spy)
    client = _client()
    markdown = MarkItDown(llm_client=client, llm_model="test-model").convert(str(path)).markdown

    client.chat.completions.create.assert_called()
    block = f"{_HEADING}\n\n{_CAPTION}\n\n![](docx_img_0001.png)"
    assert block in markdown
    assert markdown.index("We will see an image below.") < markdown.index(block)
    assert markdown.index(block) < markdown.index("# Analysis")
    assert seen
    before = seen[0]["context_before"] or ""
    after = seen[0]["context_after"] or ""
    assert "We will see an image below." in before
    assert "This section comes after the image." in after
    assert "This section comes after the image." not in before


def test_docx_image_inside_a_table_cell_stays_in_the_cell() -> None:
    markdown = _convert(
        DocxConverterDescribed(),
        _table_docx(),
        ".docx",
        llm_client=_client(),
        llm_model="test-model",
    )

    lines = markdown.splitlines()
    table_lines = [line for line in lines if line.strip().startswith("|")]
    assert table_lines
    assert any("docx_img_0001.png" in line for line in table_lines)
    assert any("Beside" in line for line in table_lines)
    width = len(_pipe_cells(table_lines[0]))
    assert width >= 2
    assert all(len(_pipe_cells(line)) == width for line in table_lines)
    assert all(_HEADING not in line and _CAPTION not in line for line in table_lines)
    last_table = max(index for index, line in enumerate(lines) if line.strip().startswith("|"))
    assert lines.index(_HEADING) > last_table
    assert "Before the table" in markdown
    assert "After the table" in markdown


def test_xlsx_images_use_one_counter_across_sheets() -> None:
    data = (_FIXTURES / "xlsx_multiple_images.xlsx").read_bytes()
    markdown = _convert(
        XlsxConverterDescribed(),
        data,
        ".xlsx",
        llm_client=_client(),
        llm_model="test-model",
    )

    names = re.findall(r"xlsx_img_(\d+)\.png", markdown)
    assert len(names) >= 2
    assert len(names) == len(set(names))
    numbers = [int(name) for name in names]
    # One sequence for the workbook. A per-sheet reset would repeat 0001.
    assert numbers == list(range(1, len(numbers) + 1))
    sections_with_images = [
        part for part in markdown.split("\n## ") if "xlsx_img_" in part
    ]
    assert len(sections_with_images) >= 2
    assert markdown.count(_HEADING) == len(names)
    assert all(
        f"{_HEADING}\n\n{_CAPTION}\n\n![](xlsx_img_{int(name):04d}.png)" in markdown
        for name in names
    )


@pytest.mark.parametrize(
    ("builder", "extension", "upstream_type", "described_type"),
    [
        (
            lambda: (_FIXTURES / "docx_image_middle.docx").read_bytes(),
            ".docx",
            DocxConverter,
            DocxConverterDescribed,
        ),
        (lambda: _table_docx(), ".docx", DocxConverter, DocxConverterDescribed),
        (
            lambda: (_FIXTURES / "xlsx_multiple_images.xlsx").read_bytes(),
            ".xlsx",
            XlsxConverter,
            XlsxConverterDescribed,
        ),
    ],
)
def test_no_llm_matches_the_upstream_converter(builder, extension, upstream_type, described_type) -> None:
    data = builder()
    assert _convert(described_type(), data, extension) == _convert(upstream_type(), data, extension)


def test_unsupported_image_keeps_native_rendering() -> None:
    data = _emf_docx()
    client = _client()
    described = _convert(
        DocxConverterDescribed(),
        data,
        ".docx",
        llm_client=client,
        llm_model="test-model",
    )
    upstream = _convert(DocxConverter(), data, ".docx")

    assert described == upstream
    assert "docx_img_" not in described
    assert _HEADING not in described
    client.chat.completions.create.assert_not_called()


def test_keep_data_uris_swaps_the_temp_name_back_to_the_bytes() -> None:
    path = _FIXTURES / "docx_image_middle.docx"
    with zipfile.ZipFile(path) as archive:
        png = archive.read("word/media/image1.png")
    encoded = base64.b64encode(png).decode("ascii")

    markdown = _convert(
        DocxConverterDescribed(),
        path.read_bytes(),
        ".docx",
        llm_client=_client(),
        llm_model="test-model",
        keep_data_uris=True,
    )

    link = f"![](data:image/png;base64,{encoded})"
    assert f"{_HEADING}\n\n{_CAPTION}\n\n{link}" in markdown
    assert "docx_img_" not in markdown


def test_temp_dir_is_removed_after_success_and_when_the_client_raises(monkeypatch) -> None:
    created: list[str] = []
    real_mkdtemp = tempfile.mkdtemp

    def track(*args, **kwargs):
        path = real_mkdtemp(*args, **kwargs)
        created.append(path)
        return path

    monkeypatch.setattr(
        "markitdown.converters._office_image_session.tempfile.mkdtemp",
        track,
    )
    data = _table_docx()
    _convert(
        DocxConverterDescribed(),
        data,
        ".docx",
        llm_client=_client(),
        llm_model="test-model",
    )
    assert created
    assert all(not Path(path).exists() for path in created)

    created.clear()
    raising = _client()
    raising.chat.completions.create.side_effect = RuntimeError("boom")
    try:
        _convert(
            DocxConverterDescribed(),
            data,
            ".docx",
            llm_client=raising,
            llm_model="test-model",
        )
    except RuntimeError:
        pass
    assert created
    assert all(not Path(path).exists() for path in created)
    raising.chat.completions.create.assert_called()


def test_hook_returns_none_for_an_unsupported_type(tmp_path: Path) -> None:
    session = ImageDescriptionSession(tmp_path, "docx_img")
    result = DocxConverterDescribed()._image_to_html(
        io.BytesIO(b"<svg xmlns='http://www.w3.org/2000/svg'/>"),
        StreamInfo(mimetype="image/svg+xml", extension=".svg"),
        llm_client=_client(),
        llm_model="test-model",
        **{SESSION_KEY: session},
    )
    assert result is None
    assert session.paths == []


def _blank_slide():
    presentation = Presentation()
    return presentation.slides.add_slide(presentation.slide_layouts[6])


def test_grouped_picture_gets_text_from_its_position_in_the_walk() -> None:
    slide = _blank_slide()
    outside_before = slide.shapes.add_textbox(Inches(0), Inches(0), Inches(2), Inches(0.4))
    outside_before.text_frame.text = "OUTSIDE_BEFORE"
    group = slide.shapes.add_group_shape()
    # Added out of visual order on purpose. The walk sorts by top, then left.
    inner_after = group.shapes.add_textbox(Inches(0), Inches(4.2), Inches(2), Inches(0.4))
    inner_after.text_frame.text = "INNER_AFTER"
    picture = group.shapes.add_picture(
        io.BytesIO(_PNG), Inches(0), Inches(3), Inches(1), Inches(1)
    )
    inner_before = group.shapes.add_textbox(Inches(0), Inches(2), Inches(2), Inches(0.4))
    inner_before.text_frame.text = "INNER_BEFORE"
    outside_after = slide.shapes.add_textbox(Inches(0), Inches(6), Inches(2), Inches(0.4))
    outside_after.text_frame.text = "OUTSIDE_AFTER"

    before, after = _slide_text_around_picture(slide, picture)

    assert before is not None and after is not None
    assert "OUTSIDE_BEFORE" in before and "INNER_BEFORE" in before
    assert "INNER_AFTER" in after and "OUTSIDE_AFTER" in after
    assert "INNER_AFTER" not in before and "OUTSIDE_AFTER" not in before
    assert "INNER_BEFORE" not in after and "OUTSIDE_BEFORE" not in after


def test_ungrouped_picture_keeps_collection_order() -> None:
    slide = _blank_slide()
    # Visually this text sits below the picture. It was added first, so the
    # old index split puts it before the picture.
    first = slide.shapes.add_textbox(Inches(0), Inches(2), Inches(2), Inches(0.4))
    first.text_frame.text = "LIST_FIRST"
    picture = slide.shapes.add_picture(
        io.BytesIO(_PNG), Inches(0), Inches(0), Inches(1), Inches(1)
    )
    last = slide.shapes.add_textbox(Inches(0), Inches(0.5), Inches(2), Inches(0.4))
    last.text_frame.text = "LIST_LAST"

    before, after = _slide_text_around_picture(slide, picture)

    assert before is not None and "LIST_FIRST" in before
    assert after is not None and "LIST_LAST" in after
    assert "LIST_LAST" not in before
    assert "LIST_FIRST" not in after


def test_slide_context_is_capped_at_800_characters() -> None:
    slide = _blank_slide()
    box = slide.shapes.add_textbox(Inches(0), Inches(0), Inches(2), Inches(0.4))
    box.text_frame.text = "A" * 900
    picture = slide.shapes.add_picture(
        io.BytesIO(_PNG), Inches(0), Inches(1), Inches(1), Inches(1)
    )

    before, after = _slide_text_around_picture(slide, picture)

    assert before == "A" * 800
    assert after is None
