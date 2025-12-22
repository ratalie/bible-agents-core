from bedrock_agentcore.runtime import Runtime
from bedrock_agentcore.memory import MemoryConfig
from agentcore_runtime import bible_companion

# AgentCore Runtime configuration
runtime_config = {
    "agent_name": "bible-companion",
    "description": "Personalized Bible companion with memory",
    "version": "1.0.0",
    "timeout": 300,  # 5 minutes
    "memory_size": 512,  # MB
    "environment": {
        "BIBLE_API_KEY": "your-bible-api-key",
        "LOG_LEVEL": "INFO"
    }
}

# Memory configuration with user isolation
memory_config = MemoryConfig(
    short_term_retention_days=7,
    long_term_retention_days=365,
    auto_summarize=True,
    user_attributes_enabled=True,
    user_isolation=True  # Key: Each user gets isolated memory
)

# Deploy to AgentCore Runtime
runtime = Runtime(
    config=runtime_config,
    memory_config=memory_config
)

# Register the agent
runtime.register_agent(bible_companion)

# Optional: Add MCP tools
@runtime.mcp_tool("bible_search")
def bible_search(query: str, version: str = "NIV") -> dict:
    """Search Bible verses by topic or keyword."""
    # Integrate with Bible API
    return {"verses": [], "query": query}

@runtime.mcp_tool("daily_verse")
def daily_verse(date: str = None) -> dict:
    """Get daily Bible verse."""
    # Return daily verse
    return {"verse": "John 3:16", "text": "For God so loved the world..."}

if __name__ == "__main__":
    # Deploy to AgentCore Runtime
    runtime.deploy()
    print("Bible Companion deployed to AgentCore Runtime!")