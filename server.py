#!/usr/bin/env python3
"""
MCP Image Tools Server

An MCP server that provides image processing tools:
- fetch_toy_image: Download toy-related images from the web
- resize_image: Resize images to specified dimensions
- remove_background_as_png: Remove image background keeping main object
"""

import asyncio
import logging
import os
import random
import signal
import sys
from typing import Optional
import requests
from PIL import Image

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("image-tools-server")

# Create server instance
mcp = FastMCP("image-tools-server")

@mcp.tool()
async def fetch_toy_image(keyword: str, count: int = 3, output_dir: str = "./images", max_search_results: int = 20) -> str:
    """Download toy-related images from the web using DuckDuckGo image search."""
    
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
                max_results=max_search_results  # Get more results for randomness
            )
            
            # Collect all results first
            all_results = list(ddgs_images_gen)
            
            # Randomly shuffle and select from available results
            if all_results:
                random.shuffle(all_results)
                selected_results = all_results[:min(count * 3, len(all_results))]  # Select up to 3x count for backup
            else:
                selected_results = []
            
            for i, result in enumerate(selected_results):
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
            return "No images were successfully downloaded."
        
        result_text = f"Successfully downloaded {downloaded_count} toy images for '{keyword}':\n" + "\n".join(results)
        return result_text
        
    except ImportError:
        return "Error: duckduckgo-search library not available. Please install it with: pip install duckduckgo-search"
    except Exception as e:
        return f"Error fetching images: {str(e)}"

@mcp.tool()
async def resize_image(image_path: str, width: int, height: int, output_path: Optional[str] = None, maintain_aspect: bool = False) -> str:
    """Resize an image to specified dimensions."""
    
    if not os.path.exists(image_path):
        return f"Error: Image file not found: {image_path}"
    
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
            
            return result_text
            
    except Exception as e:
        return f"Error resizing image: {str(e)}"

if __name__ == "__main__":
    mcp.run()