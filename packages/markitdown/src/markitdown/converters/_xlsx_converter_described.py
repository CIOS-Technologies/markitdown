"""XLSX converter that describes images when an LLM is configured.

This subclasses the upstream converter and does not modify it. With no LLM,
_image_to_html returns None and the sheet is rendered without images, which
is the upstream result. One counter covers every sheet in the workbook.
"""

from typing import Any, BinaryIO, Optional

from .._base_converter import DocumentConverterResult
from .._stream_info import StreamInfo
from ._xlsx_converter import XlsxConverter
from ._office_image_session import convert_with_descriptions, render_described_image


class XlsxConverterDescribed(XlsxConverter):
    """XlsxConverter plus the shared image-description pipeline."""

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        # super().convert forwards kwargs into _image_to_html once per image.
        # The same session object is used for every sheet.
        return convert_with_descriptions(
            super().convert,
            file_stream,
            stream_info,
            prefix="xlsx_img",
            **kwargs,
        )

    def _image_to_html(
        self,
        image_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> Optional[str]:
        # None means this image is omitted, matching upstream XLSX.
        return render_described_image(image_stream, stream_info, **kwargs)
