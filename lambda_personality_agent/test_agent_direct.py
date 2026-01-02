"""Test directo del Bedrock Agent"""
import boto3
import json

client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

AGENT_ID = "SADSVG3N5Q"
ALIAS_ID = "FS3FHAOFWO"

try:
    response = client.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=ALIAS_ID,
        sessionId="test-session-123",
        inputText="Hola, ¿cómo estás?"
    )
    
    print("Response received!")
    
    # Process stream
    full_response = ""
    for event in response['completion']:
        if 'chunk' in event:
            chunk_data = event['chunk']['bytes'].decode('utf-8')
            full_response += chunk_data
            print(chunk_data, end='', flush=True)
    
    print("\n\nFull response:", full_response)
    
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
