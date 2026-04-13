import time
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("focus-timer")

FOCUS_SESSIONS = []
ACTIVE_FOCUS = None
DISTRACTIONS = []

@mcp.tool()
def start_focus(goal: str, duration_minutes: int = 30) -> dict:
    """Start a focus session."""
    global ACTIVE_FOCUS
    ACTIVE_FOCUS = {"goal": goal, "start": time.time(), "duration": duration_minutes * 60}
    return {"status": "focusing", "goal": goal, "duration_minutes": duration_minutes}

@mcp.tool()
def log_distraction(note: str = "") -> dict:
    """Log a distraction."""
    DISTRACTIONS.append({"time": time.time(), "note": note})
    return {"distraction_count": len(DISTRACTIONS)}

@mcp.tool()
def end_focus() -> dict:
    """End focus and calculate score."""
    global ACTIVE_FOCUS
    if ACTIVE_FOCUS is None:
        return {"error": "No active focus session"}
    elapsed = time.time() - ACTIVE_FOCUS["start"]
    planned = ACTIVE_FOCUS["duration"]
    session_distractions = [d for d in DISTRACTIONS if d["time"] >= ACTIVE_FOCUS["start"]]
    distraction_penalty = min(len(session_distractions) * 10, 100)
    completion_score = min((elapsed / planned) * 100, 100)
    score = max(0, round(completion_score - distraction_penalty, 1))
    session = {
        "goal": ACTIVE_FOCUS["goal"],
        "elapsed_seconds": round(elapsed, 1),
        "planned_seconds": planned,
        "distractions": len(session_distractions),
        "score": score,
    }
    FOCUS_SESSIONS.append(session)
    ACTIVE_FOCUS = None
    return {"session": session, "lifetime_sessions": len(FOCUS_SESSIONS)}

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
