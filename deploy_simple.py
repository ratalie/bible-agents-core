#!/usr/bin/env python3
"""
Simple deployment for Bible Companion AgentCore Runtime
"""

import boto3
import json
from pathlib import Path

def deploy_bible_companion():
    """Deploy Bible Companion to AgentCore Runtime."""
    
    # 1. Install dependencies
    print("📦 Installing dependencies...")
    import subprocess
    subprocess.run(["pip", "install", "-r", "requirements_agentcore.txt"], check=True)
    
    # 2. Create deployment package
    print("📁 Creating deployment package...")
    
    # 3. Deploy using AWS CLI (simpler than SDK)
    deployment_config = {
        "agent_name": "bible-companion",
        "runtime": "python3.11", 
        "handler": "agentcore_runtime.bible_companion",
        "memory_enabled": True,
        "environment": {
            "MYSQL_HOST": "gpbible-prod-mysql.c4zg06smsewh.us-east-1.rds.amazonaws.com",
            "MYSQL_USER": "admin",
            "MYSQL_PASSWORD": "87uW3y4oU59f",
            "MYSQL_DATABASE": "gpbible"
        }
    }
    
    print("🚀 Deploying to AgentCore Runtime...")
    print(f"Config: {json.dumps(deployment_config, indent=2)}")
    
    # For now, show manual steps since AgentCore Runtime is new
    print("\n📋 Manual deployment steps:")
    print("1. Go to AWS Bedrock Console")
    print("2. Navigate to AgentCore Runtime")
    print("3. Create new agent with config above")
    print("4. Upload agentcore_runtime.py as main handler")
    print("5. Set environment variables")
    print("6. Enable memory with user isolation")
    
    return {"status": "ready_for_manual_deployment"}

if __name__ == "__main__":
    result = deploy_bible_companion()
    print(f"✅ {result['status']}")