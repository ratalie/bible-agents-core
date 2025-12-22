#!/usr/bin/env python3
"""
Test deployed Bible Companion agent
"""

import boto3
import json
import sys

def test_agent():
    """Test the deployed agent."""
    
    # Load deployment info
    try:
        with open('deployment-info.json', 'r') as f:
            deployment = json.load(f)
        
        agent_id = deployment['agentId']
        region = deployment['region']
        
        print(f"🧪 Testing agent: {agent_id}")
        
    except FileNotFoundError:
        print("❌ deployment-info.json not found. Deploy first.")
        return
    
    # Initialize Bedrock client
    client = boto3.client('bedrock-agent-runtime', region_name=region)
    
    # Test message
    test_message = "I'm struggling with anxiety about work"
    user_id = "test-user-123"
    session_id = "test-session-456"
    
    print(f"📤 Sending: {test_message}")
    
    try:
        response = client.invoke_agent(
            agentId=agent_id,
            agentAliasId='TSTALIASID',  # Test alias
            sessionId=session_id,
            inputText=test_message,
            sessionState={
                'sessionAttributes': {
                    'userId': user_id
                }
            }
        )
        
        # Process response
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    text = chunk['bytes'].decode('utf-8')
                    print(f"📥 Response: {text}")
        
        print("✅ Test successful!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("💡 Make sure agent is prepared and has proper permissions")

if __name__ == "__main__":
    test_agent()