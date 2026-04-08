"""
Deterministic handoff to workspace_agent when user intent is clearly Workspace-related.

The coordinator LLM sometimes skips transfer_to_agent; this injects the same tool call.
"""

from __future__ import annotations

import re
import uuid
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse

from app.utils.logger import logger

_COORDINATOR_NAME = "coordinator_agent"
_WORKSPACE_AGENT = "workspace_agent"
_TRANSFER_TOOL = "transfer_to_agent"

# Calendar / mail / Drive–style intents (extend as you add MCP tools).
_WORKSPACE_PATTERNS = re.compile(
    r"(?i)"
    r"\bcalendar\b|"
    r"\b(events?|meetings?|appointments?|agenda)\b|"
    r"what'?s\s+on|what\s+is\s+on|"
    r"\b(schedule|scheduled|scheduling)\b|"
    r"\b(reminders?)\b|"
    r"\b(am\s+i\s+free|my\s+availability|book\s+a|reschedule|cancel)\b|"
    r"\b(gmail|e-?mail|email|inbox|mailbox)\b|"
    r"\b(drive|google\s+drive|my\s+drive)\b|"
    r"\b(doc|docs|document|sheet|sheets|spreadsheet|slides?|folder)\b|"
    r"\b(attachment|attach)\b"
)

_AFFIRMATIONS = frozenset(
    {
        "yes",
        "yeah",
        "yep",
        "sure",
        "please",
        "ok",
        "okay",
        "y",
        "go ahead",
        "do it",
        "thanks",
        "thank you",
    }
)


def _user_text_from_contents(contents: list) -> str:
    parts_out: list[str] = []
    for block in reversed(contents or []):
        if getattr(block, "role", None) != "user":
            continue
        for p in getattr(block, "parts", None) or []:
            t = getattr(p, "text", None)
            if t:
                parts_out.append(t)
        break
    return " ".join(parts_out).strip()


def _prior_assistant_snippet(contents: list, max_len: int = 800) -> str:
    """Text of the assistant turn immediately before the latest user turn."""
    seq = contents or []
    i = len(seq) - 1
    while i >= 0:
        if getattr(seq[i], "role", None) == "user":
            j = i - 1
            while j >= 0:
                role = getattr(seq[j], "role", None)
                if role in ("model", "assistant"):
                    texts: list[str] = []
                    for p in getattr(seq[j], "parts", None) or []:
                        t = getattr(p, "text", None)
                        if t:
                            texts.append(t)
                    return " ".join(texts)[:max_len].lower()
                j -= 1
            return ""
        i -= 1
    return ""


def _assistant_hinted_workspace(snippet: str) -> bool:
    if not snippet:
        return False
    keys = (
        "calendar",
        "event",
        "schedule",
        "list your",
        "meetings",
        "appointment",
        "agenda",
        "email",
        "gmail",
        "inbox",
        "drive",
        "file",
        "folder",
        "doc",
        "sheet",
    )
    return any(k in snippet for k in keys)


def _should_route_to_workspace(user_text: str, contents: list) -> bool:
    if not user_text:
        return False
    if _WORKSPACE_PATTERNS.search(user_text):
        return True
    low = user_text.strip().lower()
    if low in _AFFIRMATIONS or (
        len(low) <= 24 and low.rstrip(".!") in _AFFIRMATIONS
    ):
        return _assistant_hinted_workspace(_prior_assistant_snippet(contents))
    return False


def _synthetic_transfer_response() -> LlmResponse:
    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[
                types.Part(
                    function_call=types.FunctionCall(
                        id=str(uuid.uuid4()),
                        name=_TRANSFER_TOOL,
                        args={"agent_name": _WORKSPACE_AGENT},
                    )
                )
            ],
        ),
        partial=False,
    )


def coordinator_before_model(
    *,
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> Optional[LlmResponse]:
    # ADK passes Context as CallbackContext; agent identity is on ReadonlyContext.agent_name.
    if callback_context.agent_name != _COORDINATOR_NAME:
        return None

    user_text = _user_text_from_contents(llm_request.contents)
    if not _should_route_to_workspace(user_text, llm_request.contents):
        return None

    logger.info(
        "[routing] coordinator → %s (matched user text: %r)",
        _WORKSPACE_AGENT,
        user_text[:120],
    )
    return _synthetic_transfer_response()
