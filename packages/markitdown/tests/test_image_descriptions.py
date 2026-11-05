"""Shared image-description pipeline.

Synthetic markdown and a fake OpenAI-style client. No network and no Gemini.
"""

import re
from pathlib import Path
from unittest.mock import MagicMock

from markitdown import MarkItDown
from markitdown.converters._image_description_worker import (
    stream_info_for_item,
    use_advanced_prompt_for,
)
from markitdown.converters._image_descriptions import (
    build_subprocess_payload,
    describe_images_in_markdown,
    extract_image_context,
    replace_images_with_descriptions,
)

_HEADING = "**[AI-Generated Image Description]**"
PDF_WITH_IMAGE = Path(__file__).parent / "test_files" / "test_image.pdf"


def _openai_client(caption: str) -> MagicMock:
    """A client detect_provider treats as OpenAI. The caption is fixed."""
    client = MagicMock()
    client.chat.completions.create.return_value.choices[0].message.content = caption
    return client


def _pipe_cells(line: str) -> list[str]:
    parts = line.strip().split("|")
    return [part.strip() for part in parts[1:-1]]


def test_plain_paragraph_puts_the_block_then_the_original_link() -> None:
    markdown = "Intro\n\n![Chart](images/chart1.png)\n\nOutro"

    result = replace_images_with_descriptions(
        markdown, {"chart1.png": "A bar chart."}
    )

    assert result.index(_HEADING) < result.index("A bar chart.")
    assert result.index("A bar chart.") < result.index("![Chart](images/chart1.png)")
    assert result.startswith("Intro\n")
    assert result.endswith("\n\nOutro")
    # The link text is unchanged, and it is the link that follows the block.
    assert (
        f"{_HEADING}\n\nA bar chart.\n\n![Chart](images/chart1.png)"
    ) in result


def test_image_inside_a_table_cell_stays_in_the_cell() -> None:
    markdown = (
        "| Item | Picture |\n"
        "| --- | --- |\n"
        "| Widget | ![shot](photos/widget.png) |\n"
        "\n"
        "After the table."
    )

    result = replace_images_with_descriptions(
        markdown, {"widget.png": "A small widget."}
    )

    lines = result.splitlines()
    table_lines = [line for line in lines if line.startswith("|")]
    assert table_lines == [
        "| Item | Picture |",
        "| --- | --- |",
        "| Widget | ![shot](photos/widget.png) |",
    ]
    assert all(len(_pipe_cells(line)) == 2 for line in table_lines)
    assert all(_HEADING not in line for line in table_lines)
    last_table = max(index for index, line in enumerate(lines) if line.startswith("|"))
    heading = lines.index(_HEADING)
    assert heading > last_table
    assert lines[heading + 2] == "A small widget."
    assert lines[-1] == "After the table."


def test_two_images_in_one_table_are_described_after_it_in_order() -> None:
    markdown = (
        "| Item | Picture |\n"
        "| --- | --- |\n"
        "| First | ![one](shots/img1.png) |\n"
        "| Second | ![two](shots/img10.png) |\n"
    )

    result = replace_images_with_descriptions(
        markdown, {"img1.png": "ONE", "img10.png": "TEN"}
    )

    lines = result.splitlines()
    table_lines = [line for line in lines if line.startswith("|")]
    assert "| First | ![one](shots/img1.png) |" in table_lines
    assert "| Second | ![two](shots/img10.png) |" in table_lines
    assert all(_HEADING not in line and "ONE" not in line and "TEN" not in line for line in table_lines)
    last_table = max(index for index, line in enumerate(lines) if line.startswith("|"))
    one_at = lines.index("ONE")
    ten_at = lines.index("TEN")
    assert last_table < one_at < ten_at


def test_substring_filenames_are_not_swapped() -> None:
    markdown = "![a](img10.png)\n\n![b](img1.png)"

    result = replace_images_with_descriptions(
        markdown, {"img1.png": "SHORT", "img10.png": "LONG"}
    )

    long_at = result.index("LONG")
    short_at = result.index("SHORT")
    link_long = result.index("![a](img10.png)")
    link_short = result.index("![b](img1.png)")
    assert long_at < link_long < short_at < link_short
    # The short name must not also be attached to the longer file.
    between = result[long_at:link_long]
    assert "SHORT" not in between


def test_context_uses_the_last_path_segment_exactly() -> None:
    # chart.png is a suffix of mychart.png. It is not that image.
    assert extract_image_context(
        "BEFORE ![a](mychart.png) AFTER", "chart.png"
    ) == (None, None)
    # img1.png is not img10.png.
    assert extract_image_context(
        "ONLY ![a](dir/img10.png) TAIL", "img1.png"
    ) == (None, None)

    before, after = extract_image_context(
        "LEFT ![a](dir/img10.png) MID ![b](dir/img1.png) RIGHT",
        "img1.png",
    )
    assert before is not None and before.endswith("MID")
    assert after == "RIGHT"


def test_threaded_jpg_is_sent_as_jpeg(tmp_path: Path) -> None:
    image = tmp_path / "photo.jpg"
    image.write_bytes(b"\xff\xd8\xff\xd9")
    client = _openai_client("A photo")

    described = describe_images_in_markdown(
        "See ![pic](photo.jpg) here",
        [image],
        llm_client=client,
        llm_model="test-model",
    )

    client.chat.completions.create.assert_called_once()
    messages = client.chat.completions.create.call_args.kwargs["messages"]
    url = messages[0]["content"][1]["image_url"]["url"]
    assert url.startswith("data:image/jpeg;base64,")
    assert f"{_HEADING}\n\nA photo\n\n![pic](photo.jpg)" in described


def test_subprocess_payload_carries_mimetype_and_advanced_flag(tmp_path: Path) -> None:
    image = tmp_path / "photo.jpg"
    image.write_bytes(b"\xff\xd8\xff\xd9")

    payload = build_subprocess_payload(
        [image],
        "![pic](photo.jpg)",
        api_key="not-a-real-key",
        llm_model="gemini-2.5-flash",
        max_workers=2,
        llm_prompt="Be brief",
        use_advanced_prompt=False,
    )

    item = payload["images"][0]
    assert item["mimetype"] == "image/jpeg"
    assert item["extension"] == ".jpg"
    assert payload["config"]["use_advanced_prompt"] is False
    # The worker must read those fields. Forcing image/png or True fails here.
    info = stream_info_for_item(item)
    assert info.mimetype == "image/jpeg"
    assert info.extension == ".jpg"
    assert use_advanced_prompt_for(item, payload["config"]) is False


def test_pdf_keeps_the_description_block_format() -> None:
    """A real PDF image, described by a fake client, keeps the old block shape.

    pymupdf4llm writes each image under a fresh temp directory, so the
    paths from two conversions are not the same string. The check is the
    block that follows this conversion's own links: heading, caption, then
    the original link.
    """
    assert PDF_WITH_IMAGE.is_file()
    caption = "Synthetic description of the figure."
    client = _openai_client(caption)

    described = MarkItDown(llm_client=client, llm_model="test-model").convert(
        str(PDF_WITH_IMAGE)
    ).markdown

    client.chat.completions.create.assert_called()
    links = re.findall(r"!\[[^\]]*\]\([^)]+\)", described)
    assert links
    for link in links:
        # Heading, then the caption, then the original link. A swapped
        # order or a dropped link fails this.
        assert f"{_HEADING}\n\n{caption}\n\n{link}" in described
