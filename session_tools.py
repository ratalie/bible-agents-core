from bedrock_agentcore.tools import Tool
from agentcore_runtime import summarize_and_save_session

@Tool(name="end_session")
def end_session(user_id: str, session_id: str) -> dict:
    """Explicitly end session and create summary."""
    try:
        summarize_and_save_session(user_id, session_id)
        return {"success": True, "message": "Session summarized and saved"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@Tool(name="get_session_summary") 
def get_session_summary(user_id: str, limit: int = 5) -> list:
    """Get recent session summaries."""
    from agentcore_runtime import memory
    
    summaries = memory.get_long_term_memories(
        user_id=user_id,
        limit=limit
    )
    
    return [{"content": s.get("content"), "date": s.get("metadata", {}).get("timestamp")} 
            for s in summaries]