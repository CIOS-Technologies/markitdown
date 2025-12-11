
import asyncio
import json
import os
import sys
import logging
import base64
import io
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
    from markitdown.converters._gemini_caption import gemini_caption_async
    from markitdown._stream_info import StreamInfo
    from markitdown.converters._llm_providers import create_gemini_client
except ImportError:
    # If running as script, add parent directory to path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from markitdown.converters._gemini_caption import gemini_caption_async
    from markitdown._stream_info import StreamInfo
    from markitdown.converters._llm_providers import create_gemini_client

async def process_images_async(
    image_data: List[Dict[str, Any]],
    api_key: str,
    model: str,
    max_workers: int,
    prompt: Optional[str] = None
) -> Dict[str, str]:
    """
    Process images asynchronously in a clean environment.
    """
    # Create client
    client = create_gemini_client(api_key)
    if not client:
        logger.error("Failed to create Gemini client")
        return {}
    
    semaphore = asyncio.Semaphore(max_workers)
    results = {}
    
    async def process_single(item):
        async with semaphore:
            img_path = item['path']
            try:
                # Read image
                with open(img_path, 'rb') as f:
                    img_bytes = f.read()
                
                stream = io.BytesIO(img_bytes)
                stream_info = StreamInfo(
                    filename=os.path.basename(img_path),
                    extension=os.path.splitext(img_path)[1],
                    mimetype='image/png'
                )
                
                context_before = item.get('context_before')
                context_after = item.get('context_after')
                
                logger.info(f"Processing: {os.path.basename(img_path)}")
                
                description = await gemini_caption_async(
                    stream,
                    stream_info,
                    client=client,
                    model=model,
                    prompt=prompt,
                    context_before=context_before,
                    context_after=context_after,
                    use_advanced_prompt=True
                )
                
                if description:
                    return os.path.basename(img_path), description
            except Exception as e:
                logger.error(f"Error processing {img_path}: {e}")
            return None

    tasks = [process_single(item) for item in image_data]
    processed = await asyncio.gather(*tasks)
    
    for p in processed:
        if p:
            results[p[0]] = p[1]
            
    return results

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
        
        logger.info(f"Worker starting with {len(images)} images, {max_workers} workers")
        
        # Run async processing
        results = asyncio.run(process_images_async(
            images, api_key, model, max_workers, prompt
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
