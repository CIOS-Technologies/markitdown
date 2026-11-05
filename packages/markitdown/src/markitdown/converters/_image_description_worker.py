
import asyncio
import json
import os
import sys
import logging
import base64
import io
import mimetypes
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("image_worker")

# Import markitdown modules
# We need to ensure we can import from the package
try:
    from markitdown.converters._gemini_caption import CaptionOutcome, gemini_caption_async
    from markitdown._stream_info import StreamInfo
    from markitdown.converters._llm_providers import create_gemini_client
except ImportError:
    # If running as script, add parent directory to path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from markitdown.converters._gemini_caption import CaptionOutcome, gemini_caption_async
    from markitdown._stream_info import StreamInfo
    from markitdown.converters._llm_providers import create_gemini_client

def stream_info_for_item(item: Dict[str, Any]) -> "StreamInfo":
    """StreamInfo from the worker payload.

    The parent process sends mimetype and extension. We do not label the
    file image/png when those fields say otherwise. If a field is missing,
    guess from the file name.
    """
    img_path = item["path"]
    extension = item.get("extension") or os.path.splitext(img_path)[1] or None
    mimetype = item.get("mimetype")
    if not mimetype:
        guessed, _ = mimetypes.guess_type(os.path.basename(img_path))
        mimetype = guessed or "application/octet-stream"
    return StreamInfo(
        filename=os.path.basename(img_path),
        extension=extension,
        mimetype=mimetype,
    )


def use_advanced_prompt_for(item: Dict[str, Any], config: Dict[str, Any]) -> bool:
    """Read the advanced-prompt flag from the payload.

    A per-image value wins. Otherwise the config value is used. The old
    worker always passed True; that default remains only when the payload
    does not say.
    """
    if "use_advanced_prompt" in item:
        return bool(item["use_advanced_prompt"])
    if "use_advanced_prompt" in config:
        return bool(config["use_advanced_prompt"])
    return True


async def process_images_async(
    image_data: List[Dict[str, Any]],
    api_key: str,
    model: str,
    max_workers: int,
    prompt: Optional[str] = None,
    use_advanced_prompt: bool = True,
) -> Dict[str, Any]:
    """
    Process images asynchronously in a clean environment.

    The result separates descriptions, skips, and failures so the parent
    process can print one summary line.
    """
    # Create client
    client = create_gemini_client(api_key)
    if not client:
        logger.error("Failed to create Gemini client")
        return {
            "descriptions": {},
            "skipped": 0,
            "failed": len(image_data),
        }
    
    semaphore = asyncio.Semaphore(max_workers)
    descriptions = {}
    skipped = 0
    failed = 0

    async def process_single(item):
        async with semaphore:
            img_path = item['path']
            name = os.path.basename(img_path)
            try:
                # Read image
                with open(img_path, 'rb') as f:
                    img_bytes = f.read()

                stream = io.BytesIO(img_bytes)
                # Payload fields, not a fixed PNG type or a forced advanced prompt.
                stream_info = stream_info_for_item(item)

                context_before = item.get('context_before')
                context_after = item.get('context_after')

                logger.info(f"Processing: {name}")

                outcome = await gemini_caption_async(
                    stream,
                    stream_info,
                    client=client,
                    model=model,
                    prompt=prompt,
                    context_before=context_before,
                    context_after=context_after,
                    use_advanced_prompt=use_advanced_prompt_for(
                        item, {"use_advanced_prompt": use_advanced_prompt}
                    ),
                )
                return name, outcome
            except Exception as e:
                logger.error(f"Error processing {img_path}: {e}")
                return name, CaptionOutcome("failed", reason=str(e))

    tasks = [process_single(item) for item in image_data]
    processed = await asyncio.gather(*tasks)

    for name, outcome in processed:
        if outcome.status == "described" and outcome.description:
            descriptions[name] = outcome.description
        elif outcome.status == "skipped":
            # The skip line was already logged inside gemini_caption_async.
            skipped += 1
        else:
            failed += 1

    return {"descriptions": descriptions, "skipped": skipped, "failed": failed}

def main():
    """Main entry point for the worker process."""
    try:
        # Read input JSON from stdin or file
        if len(sys.argv) > 1:
            input_file = sys.argv[1]
            with open(input_file, 'r') as f:
                data = json.load(f)
        else:
            logger.error("No input file provided")
            sys.exit(1)
            
        images = data.get('images', [])
        config = data.get('config', {})
        
        api_key = config.get('api_key') or os.environ.get('GEMINI_API_KEY')
        model = config.get('model', 'gemini-2.5-flash')
        max_workers = config.get('max_workers', 20)
        prompt = config.get('prompt')
        # Absent flag keeps the previous default. A present flag is obeyed,
        # including False.
        advanced = config.get('use_advanced_prompt', True)
        
        logger.info(f"Worker starting with {len(images)} images, {max_workers} workers")
        
        # Run async processing
        results = asyncio.run(process_images_async(
            images, api_key, model, max_workers, prompt, advanced
        ))
        
        # Write results to stdout as JSON
        # We use a specific delimiter to separate log output from result JSON if needed
        # But cleanest is to write to a output file provided in args
        
        if len(sys.argv) > 2:
            output_file = sys.argv[2]
            with open(output_file, 'w') as f:
                json.dump(results, f)
            logger.info(f"Results written to {output_file}")
        else:
            print(json.dumps(results))
            
    except Exception as e:
        logger.error(f"Worker failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()



