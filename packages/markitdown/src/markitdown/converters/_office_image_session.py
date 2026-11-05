"""Per-conversion image files for the DOCX and XLSX description hooks.

The converter instance is reused across calls, so the temp directory and the
filename counter live on this object. convert() creates one, puts it in
kwargs, and deletes the directory in finally. Nothing is stored on self.

Upstream forwards those kwargs into _image_to_html. The hook writes a file
and returns an <img> tag. After super().convert(), the shared pipeline
describes the files. When keep_data_uris is set, the temp name in the
markdown link is swapped back to a data URI so the bytes survive cleanup.
"""

import base64
import shutil
import tempfile
from pathlib import Path
from typing import Callable, Optional

from .._base_converter import DocumentConverterResult
from .._stream_info import StreamInfo
from ._image_descriptions import describe_images_in_markdown

# Key on the conversion kwargs. The HTML converter stores unknown options
# and does not print them, so the markdown stays free of this object.
SESSION_KEY = "markitdown_image_session"

# Types both vision paths can read.
# OpenAI's llm_caption sends stream_info.mimetype as a data URI and does not
# filter. The vision API accepts png, jpeg, gif, and webp.
# Gemini's gemini_caption opens the bytes with PIL and returns None on
# failure. This environment's Pillow opens those four (and also bmp).
# EMF, WMF, SVG, and anything else are left to the native renderer.
_MIME_EXTENSION = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/pjpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
}
_EXTENSION_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def llm_is_configured(options: dict) -> bool:
    """True when the caller asked for descriptions.

    Same pair the PDF converter checks: a client and a model name.
    """
    return options.get("llm_client") is not None and options.get("llm_model") is not None


def vision_type(stream_info: StreamInfo) -> Optional[tuple[str, str]]:
    """Return (mimetype, extension) for a file the vision path can read.

    The mimetype wins when it is set, because DOCX and XLSX take it from
    the package content type. A .jpeg file keeps that extension. A declared
    type we cannot read returns None so the hook keeps native rendering.
    """
    raw_mime = (stream_info.mimetype or "").split(";")[0].strip().lower()
    extension = (stream_info.extension or "").lower()
    if extension and not extension.startswith("."):
        extension = "." + extension

    if raw_mime:
        if raw_mime not in _MIME_EXTENSION:
            return None
        mimetype = "image/jpeg" if raw_mime in ("image/jpeg", "image/jpg", "image/pjpeg") else raw_mime
        if mimetype == "image/jpeg" and extension == ".jpeg":
            return mimetype, extension
        return mimetype, _MIME_EXTENSION[raw_mime]

    if extension in _EXTENSION_MIME:
        return _EXTENSION_MIME[extension], extension
    return None


class ImageDescriptionSession:
    """Files and data URIs for a single convert() call."""

    def __init__(self, directory: Path, prefix: str):
        # prefix is "docx_img" or "xlsx_img". The counter is one sequence
        # for the whole conversion, including every sheet.
        self.directory = directory
        self.prefix = prefix
        self.counter = 0
        self.paths: list[Path] = []
        # filename -> data URI, used only when keep_data_uris is set
        self.data_uris: dict[str, str] = {}

    def add(self, data: bytes, extension: str, mimetype: str) -> str:
        """Write one image and return its file name (not a path)."""
        self.counter += 1
        name = f"{self.prefix}_{self.counter:04d}{extension}"
        path = self.directory / name
        path.write_bytes(data)
        self.paths.append(path)
        encoded = base64.b64encode(data).decode("ascii")
        self.data_uris[name] = f"data:{mimetype};base64,{encoded}"
        return name


def render_described_image(
    image_stream,
    stream_info: StreamInfo,
    **kwargs,
) -> Optional[str]:
    """Hook body shared by the DOCX and XLSX subclasses.

    Returns None when there is no session, no LLM, or the type is not one
    the vision path reads. Upstream then keeps its own image output.
    The stream is borrowed: it is rewound and not closed.
    """
    session = kwargs.get(SESSION_KEY)
    if not isinstance(session, ImageDescriptionSession) or not llm_is_configured(kwargs):
        return None
    kind = vision_type(stream_info)
    if kind is None:
        return None

    mimetype, extension = kind
    position = image_stream.tell()
    try:
        data = image_stream.read()
    finally:
        image_stream.seek(position)

    name = session.add(data, extension, mimetype)
    # alt is empty. The description is inserted later, beside this link.
    return f'<img src="{name}" alt="">'


def restore_data_uris(markdown: str, session: ImageDescriptionSession) -> str:
    """Put the original bytes back into each image link.

    Only the markdown target is replaced (`](name)`). The description text
    is left alone. The temp file can then be deleted.
    """
    for name, uri in session.data_uris.items():
        markdown = markdown.replace(f"]({name})", f"]({uri})")
    return markdown


def convert_with_descriptions(
    base_convert: Callable,
    file_stream,
    stream_info: StreamInfo,
    *,
    prefix: str,
    **kwargs,
) -> DocumentConverterResult:
    """Run the upstream converter, then describe the images it marked.

    The session is local to this call. A copied kwargs dict carries it into
    the hook. The caller's own kwargs are not modified.
    """
    options = dict(kwargs)
    directory: Optional[str] = None
    session: Optional[ImageDescriptionSession] = None
    try:
        if llm_is_configured(options):
            directory = tempfile.mkdtemp(prefix=f"markitdown-{prefix}-")
            session = ImageDescriptionSession(Path(directory), prefix)
            options[SESSION_KEY] = session

        result = base_convert(file_stream, stream_info, **options)
        if session is None or not session.paths:
            return result

        filtered = {
            key: value
            for key, value in options.items()
            if key not in ("llm_client", "llm_model", SESSION_KEY)
        }
        markdown = describe_images_in_markdown(
            result.markdown,
            session.paths,
            llm_client=options.get("llm_client"),
            llm_model=options.get("llm_model"),
            **filtered,
        )
        # keep_data_uris: the link should still carry the image bytes.
        # The description block stays in front of that link.
        if options.get("keep_data_uris"):
            markdown = restore_data_uris(markdown, session)
        return DocumentConverterResult(markdown=markdown, title=result.title)
    finally:
        if directory is not None:
            shutil.rmtree(directory, ignore_errors=True)
