"""
Google Workspace MCP Server — Multi-User Edition
Modularized Structure
"""

import os
import logging
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("workspace-mcp")

# ---------------------------------------------------------------------------
# MCP Setup
# ---------------------------------------------------------------------------
mcp = FastMCP("Google Workspace")

# Import and register tool packages
from auth import tools as auth_tools
from tools import calendar, gmail, drive

auth_tools.register(mcp)
calendar.register(mcp)
gmail.register(mcp)
drive.register(mcp)

# ---------------------------------------------------------------------------
# HTTP App Factory
# ---------------------------------------------------------------------------
def create_app():
    """
    Create a Starlette ASGI app that serves both:
    - /mcp  → MCP protocol (Streamable HTTP)
    - /auth → OAuth flow endpoints
    """
    from contextlib import asynccontextmanager
    from starlette.applications import Starlette
    from starlette.routing import Route
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

    from auth.routes import get_auth_routes

    session_manager = StreamableHTTPSessionManager(
        app=mcp._mcp_server,
        json_response=True,
    )

    @asynccontextmanager
    async def lifespan(app):
        async with session_manager.run():
            logger.info("MCP session manager started")
            yield
        logger.info("MCP session manager stopped")

    async def health(request):
        return JSONResponse({"status": "ok", "service": "google-workspace-mcp"})

    routes = [Route("/health", health)] + get_auth_routes()

    starlette_app = Starlette(routes=routes, lifespan=lifespan)

    # Wrap to route /mcp to the session manager directly
    async def combined_app(scope, receive, send):
        path = scope.get("path", "")
        if path == "/mcp":
            await session_manager.handle_request(scope, receive, send)
        else:
            await starlette_app(scope, receive, send)

    return combined_app

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    transport = os.environ.get("MCP_TRANSPORT", "streamable-http").lower()
    port = int(os.environ.get("PORT", "8080"))

    if transport in ("streamable-http", "streamable_http"):
        logger.info(f"Starting Google Workspace MCP server (Streamable HTTP) on port {port}")
        app = create_app()
        uvicorn.run(app, host="0.0.0.0", port=port)
    elif transport == "sse":
        logger.info(f"Starting Google Workspace MCP server (SSE) on port {port}")
        mcp.run(transport="sse", host="0.0.0.0", port=port)
    else:
        logger.info("Starting Google Workspace MCP server (stdio)")
        mcp.run(transport="stdio")
