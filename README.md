<div align="center">

# Focus Timer Ai MCP

**MCP server for focus timer ai mcp operations**

[![PyPI](https://img.shields.io/pypi/v/meok-focus-timer-ai-mcp)](https://pypi.org/project/meok-focus-timer-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Focus Timer Ai MCP provides AI-powered tools via the Model Context Protocol (MCP).

## Tools

| Tool | Description |
|------|-------------|
| `start_focus` | Start a new focus timer session |
| `pause_focus` | Pause the current focus session |
| `resume_focus` | Resume a paused focus session |
| `end_focus` | End a focus session early |
| `get_sessions` | Get all focus sessions with stats |
| `get_analytics` | Get productivity analytics |
| `update_settings` | Update timer settings |
| `start_break` | Start a break timer |

## Installation

```bash
pip install meok-focus-timer-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "focus-timer-ai": {
      "command": "python",
      "args": ["-m", "meok_focus_timer_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 8 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
