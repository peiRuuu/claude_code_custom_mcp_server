# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an MCP (Model Context Protocol) Image Tools Server that provides image processing capabilities to Claude Code. The server is implemented using the FastMCP framework and runs in a Docker container for consistent deployment.

## Architecture

**Core Components:**
- `server.py` - Main MCP server implementation using FastMCP framework
- `Dockerfile` - Container configuration with Python 3.11 and image processing dependencies
- `.mcp.json` - MCP server configuration for Claude Code integration
- Requirements managed via `requirements.txt` with dependencies for PIL, rembg, requests, and duckduckgo-search

**MCP Tools Available:**
- `fetch_toy_image` - Downloads toy-related images via DuckDuckGo search
- `resize_image` - Resizes images with optional aspect ratio preservation
- `remove_background_as_png` - AI-powered background removal using rembg models
- `crop_image` - Crops images into shapes (circle, square, rectangle)

**Directory Structure:**
- `./images/` - Working directory for downloaded and processed images
- `./input/` - Docker volume mount for input files
- `./output/` - Docker volume mount for output files

## Development Commands

### Docker Operations
```bash
# Build the Docker image (required after code changes)
docker build -t mcp-toy-image-tools-server .

# Check if Docker is running
docker --version

# Run the container interactively for testing
docker run --rm -i \
  -v $(pwd)/images:/app/images \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  mcp-toy-image-tools-server
```

### MCP Server Management
```bash
# Test server functionality directly
echo '{"method": "tools/list", "params": {}}' | python server.py

# Run server locally (requires dependencies installed)
python server.py
```

### Claude Code Integration
After making changes to the server code:
1. Rebuild Docker image: `docker build -t mcp-toy-image-tools-server .`
2. Use `/mcp` command in Claude Code
3. Reconnect to `image-tools-server-docker` server

## Implementation Details

**FastMCP Framework**: The server uses `@mcp.tool()` decorators to register async functions as MCP tools. Each tool function returns a string result that gets wrapped in TextContent by the framework.

**Image Processing Pipeline**: 
- Uses PIL (Pillow) for basic image operations
- Integrates rembg for AI-powered background removal
- DuckDuckGo search integration for image fetching
- All image outputs default to `./images/` directory

**Container Architecture**: Runs as non-root user `mcp-user` with volume mounts for file I/O. The container includes OpenGL and imaging libraries for processing support.

**Error Handling**: Each tool validates input files exist and provides descriptive error messages. Network operations include timeout and retry logic.

## Configuration Notes

The `.mcp.json` file configures the server for Claude Code with Docker execution. The `cwd` path should point to the project directory. The server is identified as `image-tools-server-docker` in Claude Code.

Volume mounts are essential for file persistence:
- `/app/images` for general image storage
- `/app/input` and `/app/output` for organized file handling

## Adding New Tools

To add new image processing tools:
1. Define async function with `@mcp.tool()` decorator
2. Include proper parameter typing and docstring
3. Follow existing error handling patterns
4. Default output to `./images/` directory unless specified
5. Rebuild Docker image and reconnect MCP server

## Dependencies Management

Core dependencies in `requirements.txt`:
- `mcp>=1.0.0` - MCP SDK
- `Pillow>=10.0.0` - Image processing
- `requests>=2.31.0` - HTTP client
- `duckduckgo-search>=6.1.0` - Image search
- `rembg` - Background removal models

System dependencies are handled in Dockerfile for containerized deployment.