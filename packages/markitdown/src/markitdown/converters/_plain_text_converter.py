from typing import BinaryIO, Any
from charset_normalizer import from_bytes
from .._base_converter import DocumentConverter, DocumentConverterResult
from .._stream_info import StreamInfo

ACCEPTED_MIME_TYPE_PREFIXES = [
    "text/",
    "application/json",
    "application/markdown",
]

ACCEPTED_FILE_EXTENSIONS = [
    ".txt",
    ".text",
    ".md",
    ".markdown",
    ".json",
    ".jsonl",
]


def _text_from_detection(file_bytes: bytes) -> str:
    """Decode bytes when a declared charset is missing or cannot be used.

    charset_normalizer returns None when no charset claims the bytes.
    str(None) is the word "None", which was never in the file.
    Drop undecodable bytes with utf-8 instead.
    """
    detected = from_bytes(file_bytes).best()
    if detected is not None:
        return str(detected)
    return file_bytes.decode("utf-8", errors="ignore")


class PlainTextConverter(DocumentConverter):
    """Anything with content type text/plain"""

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,  # Options to pass to the converter
    ) -> bool:
        mimetype = (stream_info.mimetype or "").lower()
        extension = (stream_info.extension or "").lower()

        # If we have a charset, we can safely assume it's text
        # With Magika in the earlier stages, this handles most cases
        if stream_info.charset is not None:
            return True

        # Otherwise, check the mimetype and extension
        if extension in ACCEPTED_FILE_EXTENSIONS:
            return True

        for prefix in ACCEPTED_MIME_TYPE_PREFIXES:
            if mimetype.startswith(prefix):
                return True

        return False

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,  # Options to pass to the converter
    ) -> DocumentConverterResult:
        # Read once. A failed declared charset must still see the same bytes.
        file_bytes = file_stream.read()

        if stream_info.charset:
            # A declared charset wins when it can decode the file.
            # If it cannot (wrong name, or ASCII bytes that are really UTF-8),
            # fall back to detection, then to utf-8 with errors ignored.
            try:
                text_content = file_bytes.decode(stream_info.charset)
            except (UnicodeDecodeError, LookupError):
                text_content = _text_from_detection(file_bytes)
        else:
            text_content = _text_from_detection(file_bytes)

        return DocumentConverterResult(markdown=text_content)
