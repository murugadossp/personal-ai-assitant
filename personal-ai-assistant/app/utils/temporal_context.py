"""Server-side date/time for agent instructions (avoids model hallucinating 'today')."""

from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from google.adk.agents.readonly_context import ReadonlyContext


def authoritative_time_block() -> str:
    """
    Human- and tool-oriented snapshot of 'now' for calendar reasoning.
    Set ASSISTANT_TIMEZONE to an IANA zone (e.g. Asia/Kolkata, America/Los_Angeles).
    """
    raw = (os.environ.get("ASSISTANT_TIMEZONE") or "UTC").strip() or "UTC"
    try:
        tz = ZoneInfo(raw)
        tz_label = raw
    except Exception:
        tz = ZoneInfo("UTC")
        tz_label = f"UTC (invalid ASSISTANT_TIMEZONE={raw!r}, using UTC)"

    now = datetime.now(tz)
    utc = datetime.now(ZoneInfo("UTC"))
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    return (
        "**Authoritative current time** (use for 'today', 'tomorrow', 'this week'; "
        "do not invent dates from training data):\n"
        f"- Local ({tz_label}): {now.strftime('%Y-%m-%d %H:%M:%S %Z')} — {now.strftime('%A')}\n"
        f"- Today's local date: **{now.date().isoformat()}**\n"
        f"- Local day window (for tool timeMin/timeMax): "
        f"{day_start.isoformat()} .. {day_end.isoformat()}\n"
        f"- UTC now (reference): {utc.strftime('%Y-%m-%dT%H:%M:%S')}Z\n\n"
        "For 'what's on today', include events whose time range **overlaps** that "
        "local calendar day (including multi-day and all-day events). "
        "When filtering by title (e.g. 'BTS ALPHA'), still apply the same date window.\n"
    )


def global_clock_instruction(_ctx: ReadonlyContext) -> str:
    """
    Root-agent global instruction: prepended to every agent turn (coordinator + workspace).
    ADK merges this before per-agent instructions.
    """
    return (
        authoritative_time_block()
        + "\nFor questions like **what is today's date**, **what day is it**, or "
        "**current time**, answer **only** using the lines above—never invent a year "
        "or month from training data.\n"
    )
