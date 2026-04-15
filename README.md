# Focus Timer Ai

> By [MEOK AI Labs](https://meok.ai) — Pomodoro-style focus timers with productivity tracking.

MEOK AI Labs — focus-timer-ai-mcp MCP Server. Pomodoro-style focus timers with productivity tracking.

## Installation

```bash
pip install focus-timer-ai-mcp
```

## Usage

```bash
# Run standalone
python server.py

# Or via MCP
mcp install focus-timer-ai-mcp
```

## Tools

### `start_focus`
Start a new focus timer session

**Parameters:**
- `minutes` (int)
- `task` (str)

### `pause_focus`
Pause the current focus session

**Parameters:**
- `session_id` (str)

### `resume_focus`
Resume a paused focus session

**Parameters:**
- `session_id` (str)

### `end_focus`
End a focus session early

**Parameters:**
- `session_id` (str)
- `completed` (bool)

### `get_sessions`
Get all focus sessions with stats

**Parameters:**
- `date` (str)
- `limit` (int)

### `get_analytics`
Get productivity analytics

**Parameters:**
- `period` (str)

### `update_settings`
Update timer settings

**Parameters:**
- `work_duration` (int)
- `short_break` (int)
- `long_break` (int)

### `start_break`
Start a break timer

**Parameters:**
- `break_type` (str)
- `custom_minutes` (int)


## Authentication

Free tier: 15 calls/day. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## Links

- **Website**: [meok.ai](https://meok.ai)
- **GitHub**: [CSOAI-ORG/focus-timer-ai-mcp](https://github.com/CSOAI-ORG/focus-timer-ai-mcp)
- **PyPI**: [pypi.org/project/focus-timer-ai-mcp](https://pypi.org/project/focus-timer-ai-mcp/)

## License

MIT — MEOK AI Labs
