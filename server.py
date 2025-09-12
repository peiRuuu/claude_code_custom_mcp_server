#!/usr/bin/env python3
"""
MCP Image Tools Server

An MCP server that provides image processing tools:
- fetch_toy_image: Download toy-related images from the web
- resize_image: Resize images to specified dimensions
- remove_background_as_png: Remove image background keeping main object
"""

import asyncio
import base64
import io
import logging
import os
import signal
import sys
import tempfile
from typing import Any, Sequence
from urllib.parse import quote_plus
import requests
from PIL import Image
import rembg

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    ServerCapabilities,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("image-tools-server")

# Create server instance
server = Server("image-tools-server")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="fetch_toy_image",
            description="Download toy-related images from the web using DuckDuckGo image search",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Search keyword (will be prefixed with 'toy' for better toy-related results)"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of images to download (1-10)",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 3
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Directory to save images (defaults to ./images)",
                        "default": "./images"
                    }
                },
                "required": ["keyword"]
            }
        ),
        Tool(
            name="resize_image",
            description="Resize an image to specified dimensions",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Path to the image file to resize"
                    },
                    "width": {
                        "type": "integer",
                        "description": "Target width in pixels",
                        "minimum": 1
                    },
                    "height": {
                        "type": "integer",
                        "description": "Target height in pixels",
                        "minimum": 1
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Output path for resized image (optional, defaults to input_path with _resized suffix)"
                    },
                    "maintain_aspect": {
                        "type": "boolean",
                        "description": "Whether to maintain aspect ratio (will fit within specified dimensions)",
                        "default": False
                    }
                },
                "required": ["image_path", "width", "height"]
            }
        ),
        Tool(
            name="remove_background_as_png",
            description="Remove background from image keeping only the main object, save as PNG",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Path to the input image file"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Output path for PNG with removed background (optional, defaults to input_path with _nobg.png suffix)"
                    },
                    "model": {
                        "type": "string",
                        "description": "Background removal model to use",
                        "enum": ["u2net", "u2netp", "silueta", "isnet-general-use"],
                        "default": "u2net"
                    }
                },
                "required": ["image_path"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    """Handle tool calls."""
    if arguments is None:
        arguments = {}
    
    try:
        if name == "fetch_toy_image":
            return await fetch_toy_image(arguments)
        elif name == "resize_image":
            return await resize_image(arguments)
        elif name == "remove_background_as_png":
            return await remove_background_as_png(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def fetch_toy_image(arguments: dict[str, Any]) -> list[TextContent]:
    """Fetch toy-related images using DuckDuckGo image search."""
    keyword = arguments.get("keyword", "")
    count = arguments.get("count", 3)
    output_dir = arguments.get("output_dir", "./images")
    
    # Ensure keyword includes "toy" for better results
    search_term = f"toy {keyword}" if not keyword.lower().startswith("toy") else keyword
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Using DuckDuckGo image search (simulated - in real implementation you'd use duckduckgo-search library)
        # For this example, we'll use a placeholder approach
        from duckduckgo_search import DDGS
        
        results = []
        downloaded_count = 0
        
        with DDGS() as ddgs:
            ddgs_images_gen = ddgs.images(
                keywords=search_term,
                region="wt-wt",
                safesearch="moderate",
                size="medium",
                max_results=count * 2  # Get more results to account for failed downloads
            )
            
            for i, result in enumerate(ddgs_images_gen):
                if downloaded_count >= count:
                    break
                
                try:
                    image_url = result.get("image")
                    if not image_url:
                        continue
                    
                    # Download image
                    response = requests.get(image_url, timeout=10, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    response.raise_for_status()
                    
                    # Determine file extension
                    content_type = response.headers.get('content-type', '')
                    if 'jpeg' in content_type or 'jpg' in content_type:
                        ext = 'jpg'
                    elif 'png' in content_type:
                        ext = 'png'
                    elif 'gif' in content_type:
                        ext = 'gif'
                    else:
                        ext = 'jpg'  # Default
                    
                    # Save image
                    filename = f"{keyword.replace(' ', '_')}_{downloaded_count + 1}.{ext}"
                    filepath = os.path.join(output_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    results.append(f"Downloaded: {filepath}")
                    downloaded_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to download image {i}: {str(e)}")
                    continue
        
        if downloaded_count == 0:
            return [TextContent(type="text", text="No images were successfully downloaded.")]
        
        result_text = f"Successfully downloaded {downloaded_count} toy images for '{keyword}':\n" + "\n".join(results)
        return [TextContent(type="text", text=result_text)]
        
    except ImportError:
        return [TextContent(type="text", text="Error: duckduckgo-search library not available. Please install it with: pip install duckduckgo-search")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error fetching images: {str(e)}")]

async def resize_image(arguments: dict[str, Any]) -> list[TextContent]:
    """Resize an image to specified dimensions."""
    image_path = arguments.get("image_path")
    width = arguments.get("width")
    height = arguments.get("height")
    output_path = arguments.get("output_path")
    maintain_aspect = arguments.get("maintain_aspect", False)
    
    if not os.path.exists(image_path):
        return [TextContent(type="text", text=f"Error: Image file not found: {image_path}")]
    
    try:
        # Open image
        with Image.open(image_path) as img:
            original_size = img.size
            
            if maintain_aspect:
                # Calculate aspect ratio preserving resize
                img.thumbnail((width, height), Image.Resampling.LANCZOS)
                resized_img = img
            else:
                # Direct resize
                resized_img = img.resize((width, height), Image.Resampling.LANCZOS)
            
            # Determine output path
            if not output_path:
                name, ext = os.path.splitext(image_path)
                output_path = f"{name}_resized{ext}"
            
            # Save resized image
            resized_img.save(output_path, quality=95)
            
            result_text = f"Image resized successfully!\n"
            result_text += f"Original size: {original_size[0]}x{original_size[1]}\n"
            result_text += f"New size: {resized_img.size[0]}x{resized_img.size[1]}\n"
            result_text += f"Saved to: {output_path}"
            
            return [TextContent(type="text", text=result_text)]
            
    except Exception as e:
        return [TextContent(type="text", text=f"Error resizing image: {str(e)}")]

async def remove_background_as_png(arguments: dict[str, Any]) -> list[TextContent]:
    """Remove background from image and save as PNG."""
    image_path = arguments.get("image_path")
    output_path = arguments.get("output_path")
    model_name = arguments.get("model", "u2net")
    
    if not os.path.exists(image_path):
        return [TextContent(type="text", text=f"Error: Image file not found: {image_path}")]
    
    try:
        # Determine output path
        if not output_path:
            name, _ = os.path.splitext(image_path)
            output_path = f"{name}_nobg.png"
        
        # Load image
        with open(image_path, 'rb') as f:
            input_data = f.read()
        
        # Remove background using new_session
        session = rembg.new_session(model_name)
        output_data = rembg.remove(input_data, session=session)
        
        # Save as PNG
        with open(output_path, 'wb') as f:
            f.write(output_data)
        
        result_text = f"Background removed successfully!\n"
        result_text += f"Model used: {model_name}\n"
        result_text += f"Input: {image_path}\n"
        result_text += f"Output: {output_path}"
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error removing background: {str(e)}")]

async def main():
    """Run the server using stdin/stdout streams."""
    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()
    shutdown_event = asyncio.Event()
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        loop.call_soon_threadsafe(shutdown_event.set)
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            # Create server run task
            server_task = asyncio.create_task(
                server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="image-tools-server",
                        server_version="0.1.0",
                        capabilities=ServerCapabilities(
                            tools={}
                        )
                    )
                )
            )
            
            # Wait for either server completion or shutdown signal
            done, pending = await asyncio.wait(
                [server_task, asyncio.create_task(shutdown_event.wait())],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel any remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            logger.info("Server shutdown complete")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())