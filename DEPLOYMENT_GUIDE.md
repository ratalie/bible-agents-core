# 🚀 Deployment Guide - Bible Companion AgentCore Runtime

## 📋 Manual Deployment Steps

### 1. AWS Console Setup
1. Go to **AWS Bedrock Console**
2. Navigate to **AgentCore Runtime** 
3. Click **Create Agent**

### 2. Agent Configuration
```json
{
  "agent_name": "bible-companion",
  "description": "Personalized Bible companion with memory",
  "runtime": "python3.11",
  "handler": "agentcore_runtime.bible_companion",
  "timeout": 300,
  "memory_size": 512
}
```

### 3. Environment Variables
```
MYSQL_HOST=gpbible-prod-mysql.c4zg06smsewh.us-east-1.rds.amazonaws.com
MYSQL_USER=admin
MYSQL_PASSWORD=87uW3y4oU59f
MYSQL_DATABASE=gpbible
MYSQL_PORT=3306
```

### 4. Memory Configuration
- ✅ Enable Memory
- ✅ User Isolation: True
- ✅ Short-term retention: 7 days
- ✅ Long-term retention: 365 days
- ✅ Auto-summarize: True

### 5. Upload Files
- `agentcore_runtime.py` (main handler)
- `session_tools.py` (session management)
- `requirements_agentcore.txt` (dependencies)

### 6. Test Deployment
```python
# Test call
response = bible_companion(
    input_text="I'm struggling with anxiety",
    user_id="test-user-123", 
    session_id="test-session-456"
)
```

### 7. Get Endpoint
After deployment, you'll get:
- **Agent ID**: `arn:aws:bedrock:us-east-1:account:agent/agent-id`
- **Endpoint**: `https://bedrock-agent-runtime.us-east-1.amazonaws.com`

## 🔧 Alternative: AWS CLI Deployment
```bash
# If AgentCore CLI is available
aws bedrock-agentcore deploy \
  --agent-path . \
  --config deployment-config.json
```