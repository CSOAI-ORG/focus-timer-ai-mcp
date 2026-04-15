#!/usr/bin/env python3
"""MEOK AI Labs — focus-timer-ai-mcp MCP Server. Pomodoro-style focus timers with productivity tracking."""

import json
from datetime import datetime, timedelta, timezone
from typing import Any
import uuid
import sys, os

sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
from auth_middleware import check_access
from mcp.server.fastmcp import FastMCP
from collections import defaultdict

FREE_DAILY_LIMIT = 15
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now); return None

_store = {
    "sessions": [],
    "settings": {
        "work_duration": 25,
        "short_break": 5,
        "long_break": 15,
        "sessions_before_long": 4,
    },
}

mcp = FastMCP("focus-timer-ai", instructions="Pomodoro-style focus timers with productivity tracking.")


def create_session_id():
    return str(uuid.uuid4())[:8]


@mcp.tool()
def start_focus(minutes: int = 0, task: str = "Untitled session", api_key: str = "") -> str:
    """Start a new focus timer session"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    session_id = create_session_id()
    if not minutes:
        minutes = _store["settings"]["work_duration"]

    session = {
        "id": session_id,
        "type": "focus",
        "task": task,
        "duration_planned": minutes,
        "duration_actual": 0,
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "paused_at": None,
        "completed_at": None,
    }
    _store["sessions"].append(session)

    return json.dumps(
        {
            "session_id": session_id,
            "focus_started": True,
            "duration_minutes": minutes,
            "task": task,
            "tip": "Close notifications, put phone away, and eliminate distractions.",
        },
        indent=2,
    )


@mcp.tool()
def pause_focus(session_id: str, api_key: str = "") -> str:
    """Pause the current focus session"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    for s in _store["sessions"]:
        if s.get("id") == session_id and s["status"] == "running":
            s["status"] = "paused"
            s["paused_at"] = datetime.now().isoformat()
            return json.dumps({"paused": True, "session_id": session_id}, indent=2)
    return json.dumps({"error": "Session not found or not running"}, indent=2)


@mcp.tool()
def resume_focus(session_id: str, api_key: str = "") -> str:
    """Resume a paused focus session"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    for s in _store["sessions"]:
        if s.get("id") == session_id and s["status"] == "paused":
            s["status"] = "running"
            s["paused_at"] = None
            return json.dumps({"resumed": True, "session_id": session_id}, indent=2)
    return json.dumps({"error": "Session not found or not paused"}, indent=2)


@mcp.tool()
def end_focus(session_id: str, completed: bool = False, api_key: str = "") -> str:
    """End a focus session early"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    for s in _store["sessions"]:
        if s.get("id") == session_id:
            s["status"] = "completed"
            s["completed_at"] = datetime.now().isoformat()
            if completed:
                s["duration_actual"] = s["duration_planned"]
            return json.dumps(
                {
                    "ended": True,
                    "session_id": session_id,
                    "completed": completed,
                    "stats": {
                        "planned": s["duration_planned"],
                        "actual": s["duration_actual"],
                    },
                },
                indent=2,
            )
    return json.dumps({"error": "Session not found"}, indent=2)


@mcp.tool()
def get_sessions(date: str = "", limit: int = 10, api_key: str = "") -> str:
    """Get all focus sessions with stats"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    sessions = _store["sessions"][-limit:]
    if date:
        sessions = [
            s for s in sessions if s.get("started_at", "").startswith(date)
        ]
    return json.dumps({"sessions": sessions}, indent=2)


@mcp.tool()
def get_analytics(period: str = "week", api_key: str = "") -> str:
    """Get productivity analytics"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    now = datetime.now()

    if period == "today":
        start = now.replace(hour=0, minute=0, second=0)
    elif period == "week":
        start = now - timedelta(days=7)
    else:
        start = now - timedelta(days=30)

    relevant = [
        s
        for s in _store["sessions"]
        if s.get("started_at") and datetime.fromisoformat(s["started_at"]) >= start
    ]

    total_focus = sum(
        s.get("duration_actual", 0) for s in relevant if s.get("type") == "focus"
    )
    completed = sum(1 for s in relevant if s.get("status") == "completed")

    return json.dumps(
        {
            "period": period,
            "total_sessions": len(relevant),
            "completed_sessions": completed,
            "total_focus_minutes": total_focus,
            "average_session_length": total_focus / max(completed, 1),
        },
        indent=2,
    )


@mcp.tool()
def update_settings(work_duration: int = 0, short_break: int = 0, long_break: int = 0, api_key: str = "") -> str:
    """Update timer settings"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    settings = _store["settings"]
    if work_duration:
        settings["work_duration"] = work_duration
    if short_break:
        settings["short_break"] = short_break
    if long_break:
        settings["long_break"] = long_break
    return json.dumps({"settings_updated": True, "settings": settings}, indent=2)


@mcp.tool()
def start_break(break_type: str = "short", custom_minutes: int = 0, api_key: str = "") -> str:
    """Start a break timer"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    minutes = custom_minutes or (
        _store["settings"]["short_break"]
        if break_type == "short"
        else _store["settings"]["long_break"]
    )

    session_id = create_session_id()
    session = {
        "id": session_id,
        "type": "break",
        "break_type": break_type,
        "duration_planned": minutes,
        "status": "running",
        "started_at": datetime.now().isoformat(),
    }
    _store["sessions"].append(session)

    return json.dumps(
        {
            "break_started": True,
            "session_id": session_id,
            "break_type": break_type,
            "duration_minutes": minutes,
            "tip": "Stretch, hydrate, rest your eyes, take a short walk.",
        },
        indent=2,
    )


if __name__ == "__main__":
    mcp.run()
