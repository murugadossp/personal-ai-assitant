"""
MCPManager — loads MCP server definitions from mcp_settings.json
and creates the appropriate MCPToolset for any registered server.
"""

import os
import json

from google.adk.tools.mcp_tool import (
    MCPToolset,
    StdioConnectionParams,
    SseConnectionParams,
    StreamableHTTPConnectionParams,
)
from mcp.client.stdio import StdioServerParameters


class MCPManager:
    """Manages MCP server connections from mcp_settings.json."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        settings_path = os.path.join(
            os.path.dirname(__file__), "../..", "mcp_settings.json"
        )
        with open(settings_path, "r") as f:
            self._settings = json.load(f)

    @property
    def servers(self) -> dict:
        """Returns all configured MCP server definitions."""
        return self._settings.get("mcpServers", {})

    def list_servers(self) -> list[str]:
        """Returns the names of all configured MCP servers."""
        return list(self.servers.keys())

    def get_toolset(self, server_name: str) -> MCPToolset:
        """
        Creates and returns an MCPToolset for the given server name.
        Supported transports: stdio, sse, streamable_http.
        """
        if server_name not in self.servers:
            available = ", ".join(self.servers.keys()) or "(none)"
            raise ValueError(
                f"MCP server '{server_name}' not found in mcp_settings.json. "
                f"Available: {available}"
            )

        srv = self.servers[server_name]
        transport = srv.get("transport", "stdio")

        if transport == "stdio":
            connection = StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=srv["command"],
                    args=srv.get("args", []),
                    env=srv.get("env"),
                )
            )
        elif transport == "sse":
            connection = SseConnectionParams(
                url=srv["url"],
                headers=srv.get("headers", {}),
            )
        elif transport == "streamable_http":
            connection = StreamableHTTPConnectionParams(
                url=srv["url"],
            )
        else:
            raise ValueError(
                f"Unsupported MCP transport '{transport}' for server '{server_name}'"
            )

        return MCPToolset(connection_params=connection)


# Module-level convenience — backwards-compatible
mcp_manager = MCPManager()

def get_mcp_toolset(server_name: str) -> MCPToolset:
    """Convenience wrapper so existing imports still work."""
    return mcp_manager.get_toolset(server_name)
