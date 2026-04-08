import os
import sys

# Ensure the root project directory is in the Python path for 'app' imports to work
# regardless of how the adk web CLI resolves the working directory.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from google.adk.agents import Agent

from app.agents.coordinator.routing import coordinator_before_model
from app.agents.coordinator.workspace_agent import get_workspace_agent
from app.config import resolve_agent_model
from app.utils.temporal_context import global_clock_instruction


def get_coordinator_agent():
    """
    Coordinator: small talk + routing. All Google Workspace work goes to workspace_agent.
    """
    workspace_agent = get_workspace_agent()

    return Agent(
        name="coordinator_agent",
        model=resolve_agent_model("coordinator"),
        global_instruction=global_clock_instruction,
        before_model_callback=coordinator_before_model,
        description=(
            "Routes requests. Handles only general chit-chat; has no Google Workspace tools."
        ),
        instruction=(
            "You are the coordinator. You have NO Google Workspace tools and cannot read "
            "Calendar, Gmail, or Drive yourself.\n\n"
            "Hand off **immediately** with transfer_to_agent and agent_name=\"workspace_agent\" "
            "(only the tool call in that turn, no extra text) when the user wants anything "
            "involving: calendar, events, meetings, schedule, email/Gmail, Drive, Docs, "
            "Sheets, files, folders, or attachments—or confirms (e.g. \"yes\") after you "
            "offered Workspace help.\n\n"
            "Do not list events, emails, or files; do not ask permission to open Workspace "
            "when they already asked—workspace_agent has the MCP tools.\n\n"
            "Do not ask for user ID yourself; workspace_agent handles account identifiers.\n\n"
            "Pure greetings or non-Workspace questions: answer briefly yourself."
        ),
        sub_agents=[workspace_agent],
    )


root_agent = get_coordinator_agent()
