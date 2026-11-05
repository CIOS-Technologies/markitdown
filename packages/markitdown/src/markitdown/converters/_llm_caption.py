from typing import BinaryIO, Optional, Union
import base64
import mimetypes
from .._stream_info import StreamInfo
from ._gemini_caption import CaptionOutcome, classify_model_text, compose_image_prompt


def openai_caption_outcome(
    file_stream: BinaryIO,
    stream_info: StreamInfo,
    *,
    client,
    model,
    prompt=None,
    context_before: Optional[str] = None,
    context_after: Optional[str] = None,
    use_advanced_prompt: bool = True,
) -> CaptionOutcome:
    """OpenAI vision call. API errors still raise. A SKIP: answer is a skip.

    The default prompt is the same policy the Gemini path uses. A prompt
    passed by the caller is sent as given, with surrounding text appended.
    """
    filename = stream_info.filename or "unknown"
    prompt = compose_image_prompt(
        prompt, context_before, context_after, use_advanced_prompt
    )

    # Get the content type
    content_type = stream_info.mimetype
    if not content_type:
        content_type, _ = mimetypes.guess_type("_dummy" + (stream_info.extension or ""))
    if not content_type:
        content_type = "application/octet-stream"

    # Convert to base64
    cur_pos = file_stream.tell()
    try:
        base64_image = base64.b64encode(file_stream.read()).decode("utf-8")
    except Exception as e:
        return CaptionOutcome("failed", reason=str(e))
    finally:
        file_stream.seek(cur_pos)

    # Prepare the data-uri
    data_uri = f"data:{content_type};base64,{base64_image}"

    # Prepare the OpenAI API request
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": data_uri,
                    },
                },
            ],
        }
    ]

    # Call the OpenAI API. Errors propagate so callers can tell a failure
    # from a skip. A "SKIP:" body is classified, not used as the caption.
    response = client.chat.completions.create(model=model, messages=messages)
    content = response.choices[0].message.content
    return classify_model_text(content, filename)


def llm_caption(
    file_stream: BinaryIO,
    stream_info: StreamInfo,
    *,
    client,
    model,
    prompt=None,
    context_before: Optional[str] = None,
    context_after: Optional[str] = None,
    use_advanced_prompt: bool = True,
) -> Union[None, str]:
    """Description text, or None when the image was skipped or the call failed."""
    outcome = openai_caption_outcome(
        file_stream,
        stream_info,
        client=client,
        model=model,
        prompt=prompt,
        context_before=context_before,
        context_after=context_after,
        use_advanced_prompt=use_advanced_prompt,
    )
    if outcome.status == "described":
        return outcome.description
    return None
