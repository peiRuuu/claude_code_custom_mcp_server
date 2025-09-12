# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an MCP (Model Context Protocol) Image Tools Server that provides image processing capabilities to Claude Code. The server is implemented using the FastMCP framework and runs in a Docker container for consistent deployment across environments.

## Architecture

**Core Implementation:**
- `server.py` - Single-file MCP server using FastMCP framework with `@mcp.tool()` decorators
- `Dockerfile` - Python 3.11 container with image processing dependencies (PIL, rembg, OpenGL libraries)
- `.mcp.json` - Client configuration for Claude Code integration with Docker execution

**Available MCP Tools:**
- `fetch_toy_image` - Downloads images via DuckDuckGo search with automatic "toy" prefix for better results
- `resize_image` - Resizes images with optional aspect ratio preservation using Lanczos resampling
- `remove_background_as_png` - AI-powered background removal using rembg models (u2net default)

**Key Dependencies:**
- `mcp>=1.0.0` - MCP SDK for tool registration and communication
- `Pillow>=10.0.0` - Core image processing operations
- `rembg>=2.0.50` + `onnxruntime>=1.15.0` - AI background removal
- `duckduckgo-search>=6.1.0` - Web image search functionality

## Development Commands

### Docker Operations (Primary Development Method)
```bash
# Build image after code changes
docker build -t mcp-toy-image-tools-server .

# Verify Docker is running
docker --version

# Test server functionality
docker run --rm -i \
  -v $(pwd)/images:/app/images \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  mcp-toy-image-tools-server

# Direct tool testing
echo '{"method": "tools/list", "params": {}}' | docker run --rm -i mcp-toy-image-tools-server python server.py
```

### MCP Integration Workflow
1. After code changes: `docker build -t mcp-toy-image-tools-server .`
2. In Claude Code: Use `/mcp` command
3. Reconnect to `image-tools-server-docker` server

### Local Development (Alternative)
```bash
# Install dependencies (requires virtual environment on managed systems)
pip install -r requirements.txt

# Run server directly
python server.py

# Test tool listing
echo '{"method": "tools/list", "params": {}}' | python server.py
```

## Implementation Details

**FastMCP Pattern**: Each MCP tool is an async function decorated with `@mcp.tool()`. The function signature defines the tool's parameters, and the docstring becomes the tool description. Return values are automatically wrapped as TextContent.

**Image Processing Flow**:
- Input validation (file existence checks)
- PIL-based operations with error handling
- Default output to `./images/` directory
- Comprehensive error messages for debugging

**Search Integration**: DuckDuckGo search automatically prefixes keywords with "toy" for better image relevance. Results are shuffled and filtered with retry logic for failed downloads.

**Background Removal**: Uses rembg library with configurable models. Creates new session per operation for memory efficiency. Always outputs PNG format for transparency support.

## Container Architecture

The Docker container runs as non-root user `mcp-user` with these volume mounts:
- `/app/images` - Primary working directory for image operations
- `/app/input` - Input files (optional organization)
- `/app/output` - Processed output files (optional organization)

System dependencies include OpenGL libraries for image processing and GLib for threading support.

## Configuration Notes

The `.mcp.json` configuration uses Docker execution with the `image-tools-server-docker` identifier. The `cwd` path must point to the project directory containing the Docker context.

Volume mounts are essential for persistence since the container is ephemeral (`--rm` flag).

## Adding New Tools

To extend functionality:
1. Add async function with `@mcp.tool()` decorator
2. Include proper type hints and descriptive docstring
3. Validate inputs and provide clear error messages
4. Default outputs to `./images/` unless user specifies path
5. Rebuild Docker image and reconnect MCP server

Example pattern:
```python
@mcp.tool()
async def new_tool(input_param: str, optional_param: int = 10) -> str:
    """Brief description of what the tool does."""
    # Validation
    # Processing
    # Return descriptive result
```