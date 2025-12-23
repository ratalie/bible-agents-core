from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

# Lazy loading - Agent se carga solo cuando se necesita
_agent = None

def get_agent():
    """Lazy load Strands Agent to avoid cold start timeout."""
    global _agent
    if _agent is None:
        from strands import Agent
        _agent = Agent()
    return _agent

@app.entrypoint
def invoke(payload):
    """Bible Companion AI agent function"""
    
    # Extract user message
    user_message = payload.get("prompt", "Hello! How can I help you today?")
    
    # Extract user_id if provided
    session_attributes = payload.get("sessionAttributes", {})
    user_id = session_attributes.get("userId", "default-user")
    
    # Lazy load agent and process
    agent = get_agent()
    result = agent(f"As a Bible Companion, respond to: {user_message}")
    
    return {"result": result.message}

if __name__ == "__main__":
    app.run()