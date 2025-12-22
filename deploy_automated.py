#!/usr/bin/env python3
"""
Automated AgentCore Runtime deployment using boto3
"""

import boto3
import json
import zipfile
import base64
from pathlib import Path

def deploy_agentcore_runtime():
    """Deploy Bible Companion to AgentCore Runtime via SDK."""
    
    # Initialize AgentCore client
    agentcore = boto3.client('bedrock-agentcore', region_name='us-east-1')
    
    print("Starting AgentCore Runtime deployment...")
    
    # 1. Create deployment package
    print("Creating deployment package...")
    
    files_to_zip = [
        'agentcore_runtime.py',
        'session_tools.py', 
        'requirements_agentcore.txt',
        'user_memory_isolation.py'
    ]
    
    with zipfile.ZipFile('bible-companion.zip', 'w') as zipf:
        for file in files_to_zip:
            if Path(file).exists():
                zipf.write(file)
                print(f"  Added {file}")
            else:
                print(f"  Missing {file}")
    
    # 2. Read deployment package
    with open('bible-companion.zip', 'rb') as f:
        deployment_package = base64.b64encode(f.read()).decode('utf-8')
    
    # 3. Create AgentCore Runtime agent
    agent_config = {
        'agentName': f'bible-companion-{int(__import__("time").time())}',
        'description': 'Bible Companion with AgentCore Memory',
        'runtime': 'python3.11',
        'handler': 'agentcore_runtime.bible_companion',
        'code': deployment_package,
        'environment': {
            'MYSQL_HOST': 'gpbible-prod-mysql.c4zg06smsewh.us-east-1.rds.amazonaws.com',
            'MYSQL_USER': 'admin',
            'MYSQL_PASSWORD': '87uW3y4oU59f',
            'MYSQL_DATABASE': 'gpbible'
        },
        'memoryConfiguration': {
            'enabledMemoryTypes': ['SESSION_SUMMARY'],
            'storageDays': 365
        }
    }
    
    try:
        print("Creating AgentCore Runtime agent...")
        
        # Try AgentCore specific API
        response = agentcore.create_runtime_agent(**agent_config)
        agent_id = response['agentId']
        print(f"Agent created: {agent_id}")
        
        # Save deployment info
        deployment_info = {
            'agentId': agent_id,
            'agentName': agent_config['agentName'],
            'region': 'us-east-1',
            'deployedAt': __import__('datetime').datetime.utcnow().isoformat(),
            'type': 'agentcore-runtime',
            'endpoint': f'https://bedrock-agentcore.us-east-1.amazonaws.com/agents/{agent_id}'
        }
        
        with open('deployment-info.json', 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        print(f"""
Deployment Complete!
Agent ID: {agent_id}
Endpoint: {deployment_info['endpoint']}
Console: https://us-east-1.console.aws.amazon.com/bedrock-agentcore/
Info saved to: deployment-info.json
        """)
        
        return deployment_info
        
    except Exception as e:
        print(f"AgentCore API failed: {e}")
        
        # Fallback: Show manual steps with correct URL
        print(f"""
Manual Deployment Required:
1. Go to: https://us-east-1.console.aws.amazon.com/bedrock-agentcore/
2. Create Runtime Agent
3. Upload bible-companion.zip (created above)
4. Configure environment variables:
   MYSQL_HOST=gpbible-prod-mysql.c4zg06smsewh.us-east-1.rds.amazonaws.com
   MYSQL_USER=admin
   MYSQL_PASSWORD=87uW3y4oU59f
   MYSQL_DATABASE=gpbible
5. Enable memory with user isolation
        """)
        
        return None

if __name__ == "__main__":
    deploy_agentcore_runtime()