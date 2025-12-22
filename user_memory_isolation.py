# User Memory Isolation for AgentCore

# 1. Memory is automatically isolated by user_id in AgentCore
# 2. Every memory operation includes user_id parameter
# 3. Users can only access their own memories

# Key functions that ensure user isolation:

def get_user_memory(user_id: str):
    """Get memories only for specific user."""
    return memory.get_context(user_id=user_id)

def save_user_memory(user_id: str, content: str):
    """Save memory only for specific user."""
    return memory.save_long_term_memory(user_id=user_id, content=content)

def search_user_memory(user_id: str, query: str):
    """Search memories only for specific user."""
    return memory.search_memories(user_id=user_id, query=query)

# AgentCore Memory automatically:
# - Partitions data by user_id
# - Prevents cross-user access
# - Maintains user session isolation