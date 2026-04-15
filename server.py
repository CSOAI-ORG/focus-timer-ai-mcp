#!/usr/bin/env python3
"""MEOK AI Labs — focus-timer-ai-mcp MCP Server. Pomodoro-style focus timers with productivity tracking."""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Any
import uuid

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent
import mcp.types as types
import sys, os
sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
from auth_middleware import check_access
from collections import defaultdict
import json

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

server = Server("focus-timer-ai")


def create_session_id():
    return str(uuid.uuid4())[:8]


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    return [
        Resource(
            uri="focus://sessions",
            name="Focus Sessions",
            description="List of all focus sessions",
            mimeType="application/json",
        ),
        Resource(
            uri="focus://settings",
            name="Timer Settings",
            description="Current timer configuration",
            mimeType="application/json",
        ),
    ]


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="start_focus",
            description="Start a new focus timer session",
            inputSchema={
                "type": "object",
                "properties": {
                    "minutes": {
                        "type": "number",
                        "description": "Duration in minutes (default: 25)",
                        "default": 25,
                    },
                    "task": {
                        "type": "string",
                        "description": "What are you focusing on?",
                    },
                },
            },
        ),
        Tool(
            name="pause_focus",
            description="Pause the current focus session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to pause",
                    }
                },
            },
        ),
        Tool(
            name="resume_focus",
            description="Resume a paused focus session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to resume",
                    }
                },
            },
        ),
        Tool(
            name="end_focus",
            description="End a focus session early",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to end",
                    },
                    "completed": {
                        "type": "boolean",
                        "description": "Was the full duration completed?",
                        "default": False,
                    },
                },
            },
        ),
        Tool(
            name="get_sessions",
            description="Get all focus sessions with stats",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Filter by date (YYYY-MM-DD)",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Number of sessions to return",
                        "default": 10,
                    },
                },
            },
        ),
        Tool(
            name="get_analytics",
            description="Get productivity analytics",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["today", "week", "month"],
                        "description": "Time period",
                        "default": "week",
                    }
                },
            },
        ),
        Tool(
            name="update_settings",
            description="Update timer settings",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_duration": {
                        "type": "number",
                        "description": "Work duration in minutes",
                    },
                    "short_break": {
                        "type": "number",
                        "description": "Short break in minutes",
                    },
                    "long_break": {
                        "type": "number",
                        "description": "Long break in minutes",
                    },
                },
            },
        ),
        Tool(
            name="start_break",
            description="Start a break timer",
            inputSchema={
                "type": "object",
                "properties": {
                    "break_type": {
                        "type": "string",
                        "enum": ["short", "long"],
                        "description": "Type of break",
                    },
                    "custom_minutes": {
                        "type": "number",
                        "description": "Custom duration in minutes",
                    },
                },
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Any | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    args = arguments or {}
    api_key = args.get("api_key", "")
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return [TextContent(type="text", text=json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"}))]
    if err := _rl(): return [TextContent(type="text", text=err)]

    if name == "start_focus":
        session_id = create_session_id()
        minutes = args.get("minutes", _store["settings"]["work_duration"])
        task = args.get("task", "Untitled session")

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

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "session_id": session_id,
                        "focus_started": True,
                        "duration_minutes": minutes,
                        "task": task,
                        "tip": "Close notifications, put phone away, and eliminate distractions.",
                    },
                    indent=2,
                ),
            )
        ]

    elif name == "pause_focus":
        session_id = args.get("session_id")
        for s in _store["sessions"]:
            if s.get("id") == session_id and s["status"] == "running":
                s["status"] = "paused"
                s["paused_at"] = datetime.now().isoformat()
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {"paused": True, "session_id": session_id}, indent=2
                        ),
                    )
                ]
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"error": "Session not found or not running"}, indent=2
                ),
            )
        ]

    elif name == "resume_focus":
        session_id = args.get("session_id")
        for s in _store["sessions"]:
            if s.get("id") == session_id and s["status"] == "paused":
                s["status"] = "running"
                s["paused_at"] = None
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {"resumed": True, "session_id": session_id}, indent=2
                        ),
                    )
                ]
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": "Session not found or not paused"}, indent=2),
            )
        ]

    elif name == "end_focus":
        session_id = args.get("session_id")
        completed = args.get("completed", False)
        for s in _store["sessions"]:
            if s.get("id") == session_id:
                s["status"] = "completed"
                s["completed_at"] = datetime.now().isoformat()
                if completed:
                    s["duration_actual"] = s["duration_planned"]
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
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
                        ),
                    )
                ]
        return [
            TextContent(
                type="text", text=json.dumps({"error": "Session not found"}, indent=2)
            )
        ]

    elif name == "get_sessions":
        sessions = _store["sessions"][-args.get("limit", 10) :]
        date_filter = args.get("date")
        if date_filter:
            sessions = [
                s for s in sessions if s.get("started_at", "").startswith(date_filter)
            ]
        return [
            TextContent(type="text", text=json.dumps({"sessions": sessions}, indent=2))
        ]

    elif name == "get_analytics":
        period = args.get("period", "week")
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

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "period": period,
                        "total_sessions": len(relevant),
                        "completed_sessions": completed,
                        "total_focus_minutes": total_focus,
                        "average_session_length": total_focus / max(completed, 1),
                    },
                    indent=2,
                ),
            )
        ]

    elif name == "update_settings":
        settings = _store["settings"]
        if "work_duration" in args:
            settings["work_duration"] = args["work_duration"]
        if "short_break" in args:
            settings["short_break"] = args["short_break"]
        if "long_break" in args:
            settings["long_break"] = args["long_break"]
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"settings_updated": True, "settings": settings}, indent=2
                ),
            )
        ]

    elif name == "start_break":
        break_type = args.get("break_type", "short")
        custom = args.get("custom_minutes")

        minutes = custom or (
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

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "break_started": True,
                        "session_id": session_id,
                        "break_type": break_type,
                        "duration_minutes": minutes,
                        "tip": "Stretch, hydrate, rest your eyes, take a short walk.",
                    },
                    indent=2,
                ),
            )
        ]

    return [
        TextContent(type="text", text=json.dumps({"error": "Unknown tool"}, indent=2))
    ]


async def main():
    async with stdio_server(server._read_stream, server._write_stream) as (
        read_stream,
        write_stream,
    ):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="focus-timer-ai",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())