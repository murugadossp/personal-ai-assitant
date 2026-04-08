import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from google.adk.agents import Agent

from app.agents.coordinator.workspace_instructions import workspace_instruction
from app.config import resolve_agent_model
from app.utils.mcp import get_mcp_toolset


def get_workspace_agent():
    """
    Google Workspace sub-agent (Calendar, Gmail, Drive via MCP). Used only as a sub-agent
    of the coordinator — not a separate ADK app root (no root_agent in this module).
    """
    workspace_mcp = get_mcp_toolset("google-workspace")

    return Agent(
        name="workspace_agent",
        model=resolve_agent_model("workspace"),
        description=(
            "Google Workspace specialist: Calendar, Gmail, and Drive through MCP tools."
        ),
        instruction=workspace_instruction,
        tools=[workspace_mcp],
    )
