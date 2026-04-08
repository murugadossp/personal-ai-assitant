"""
FastAPI entry: `/api/chat` + `/api/health`.

Set `ENABLE_ADK_WEB_UI=true` to mount the same ADK Web UI as `adk web` (Angular assets + `/run_sse`, etc.).
Uses absolute `app/agents` so Cloud Run cwd does not break agent loading.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from google.adk.apps.app import App
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.events.event import Event
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.utils.context_utils import Aclosing
from google.genai import types

from app.agents import get_coordinator_agent
from app.schemas import ChatRequest, ChatResponse
from app.utils.logger import logger
from app.utils.sqlite.db import append_message, ensure_conversation, init_db

adk_runner: Runner | None = None
_startup_error: str | None = None

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = str(_PROJECT_ROOT / "app" / "agents")


def _response_text_from_events(events: list[Event]) -> str:
    """Pick the best user-visible string from ADK events (mirrors CLI behavior)."""
    final_text = ""
    last_agent_text = ""
    for event in events:
        if not event.content or not event.content.parts:
            continue
        text = "".join(part.text or "" for part in event.content.parts)
        if not text or event.author == "user":
            continue
        last_agent_text = text
        if event.is_final_response():
            final_text = text
    return (final_text or last_agent_text or "").strip() or "(No text response from the model.)"


@asynccontextmanager
async def chat_runner_lifespan(app: FastAPI):
    global adk_runner, _startup_error
    _startup_error = None
    logger.info("Initializing SQLite database")
    init_db()

    logger.info("Loading coordinator agent and ADK Runner for /api/chat")
    try:
        root_agent = get_coordinator_agent()
        adk_app = App(name="coordinator", root_agent=root_agent)
        adk_runner = Runner(
            app=adk_app,
            session_service=InMemorySessionService(),
            artifact_service=InMemoryArtifactService(),
            memory_service=InMemoryMemoryService(),
            auto_create_session=True,
        )
    except Exception as e:
        _startup_error = f"{type(e).__name__}: {e}"
        logger.exception("Agent / Runner init failed: %s", e)
        adk_runner = None

    yield

    if adk_runner is not None:
        await adk_runner.close()
    logger.info("Shutdown complete")


def register_api_routes(application: FastAPI) -> None:
    @application.post("/api/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest):
        if adk_runner is None:
            raise HTTPException(
                status_code=503,
                detail={
                    "message": "Agent system not initialized.",
                    "startup_error": _startup_error,
                    "hints": [
                        "Set GOOGLE_API_KEY (AI Studio) or use Vertex with "
                        "GOOGLE_GENAI_USE_VERTEXAI=True plus project/ADC.",
                        "Ensure GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION if using Vertex.",
                        "Check MCP URL in mcp_settings.json is reachable from this service.",
                    ],
                },
            )

        ensure_conversation(request.session_id, request.user_id)
        append_message(request.session_id, "user", request.message)

        content = types.Content(
            role="user",
            parts=[types.Part(text=request.message)],
        )

        try:
            events: list[Event] = []
            async with Aclosing(
                adk_runner.run_async(
                    user_id=request.user_id,
                    session_id=request.session_id,
                    new_message=content,
                )
            ) as agen:
                async for event in agen:
                    events.append(event)

            reply = _response_text_from_events(events)
            append_message(request.session_id, "assistant", reply)
            return ChatResponse(response=reply)
        except Exception as e:
            logger.exception("Chat invocation failed")
            raise HTTPException(status_code=500, detail=str(e)) from e

    @application.get("/api/health")
    async def health_check():
        return {
            "status": "healthy" if adk_runner else "degraded",
            "agent_ready": adk_runner is not None,
            "startup_error": _startup_error,
            "adk_web_ui": os.environ.get("ENABLE_ADK_WEB_UI", "").lower()
            in ("1", "true", "yes"),
            "message": "FastAPI is running; agent_ready indicates /api/chat Runner.",
        }


def _build_app() -> FastAPI:
    enable_ui = os.environ.get("ENABLE_ADK_WEB_UI", "false").lower() in (
        "1",
        "true",
        "yes",
    )
    if enable_ui:
        from google.adk.cli.fast_api import get_fast_api_app

        # Same-origin browser UI: CORS optional. Pass None to skip extra origin checks.
        cors_raw = os.environ.get("ADK_CORS_ORIGINS", "").strip()
        allow = [x.strip() for x in cors_raw.split(",") if x.strip()] if cors_raw else None

        application = get_fast_api_app(
            agents_dir=AGENTS_DIR,
            web=True,
            allow_origins=allow,
            use_local_storage=True,
            auto_create_session=True,
            lifespan=chat_runner_lifespan,
        )
        logger.info("ADK Web UI enabled; agents_dir=%s", AGENTS_DIR)
    else:
        application = FastAPI(
            title="Google ADK Multi-Agent System",
            lifespan=chat_runner_lifespan,
        )
    register_api_routes(application)
    return application


app = _build_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
