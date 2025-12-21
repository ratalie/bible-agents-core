#!/usr/bin/env python3
"""
Deploy Bible Companion to AgentCore Runtime
"""

import boto3
from bedrock_agentcore.runtime import deploy_agent
from pathlib import Path

def deploy():
    """Deploy Bible Companion to AgentCore Runtime."""
    
    # Agent configuration
    config = {
        "name": "bible-companion",
        "description": "Personalized Bible companion with memory",
        "runtime": "python3.11",
        "handler": "agentcore_runtime.bible_companion",
        "memory_enabled": True,
        "session_isolation": True,
        "max_session_duration": 3600,  # 1 hour
        "environment": {
            "LOG_LEVEL": "INFO"
        }
    }
    
    # Deploy
    result = deploy_agent(
        agent_path=Path(__file__).parent,
        config=config
    )
    
    print(f"✅ Deployed Bible Companion to AgentCore Runtime")
    print(f"📍 Agent ID: {result['agent_id']}")
    print(f"🔗 Endpoint: {result['endpoint']}")
    
    return result

if __name__ == "__main__":
    deploy()