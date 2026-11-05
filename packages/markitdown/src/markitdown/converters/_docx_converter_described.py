"""DOCX converter that describes images when an LLM is configured.

This subclasses the upstream converter and does not modify it. With no LLM,
_image_to_html returns None and mammoth keeps the native data-URI image.
"""

from typing import Any, BinaryIO, Optional

from .._base_converter import DocumentConverterResult
from .._stream_info import StreamInfo
from ._docx_converter import DocxConverter
from ._office_image_session import convert_with_descriptions, render_described_image


class DocxConverterDescribed(DocxConverter):
    """DocxConverter plus the shared image-description pipeline."""

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        # super().convert forwards kwargs into _image_to_html. The session
        # rides in that dict for this call only.
        return convert_with_descriptions(
            super().convert,
            file_stream,
            stream_info,
            prefix="docx_img",
            **kwargs,
        )

    def _image_to_html(
        self,
        image_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> Optional[str]:
        # None keeps mammoth's data URI. A supported image becomes a temp
        # file name the shared pipeline can find after conversion.
        return render_described_image(image_stream, stream_info, **kwargs)
