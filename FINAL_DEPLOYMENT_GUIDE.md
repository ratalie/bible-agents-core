# 🚀 DEPLOYMENT GUIDE - Bible Companion AgentCore Runtime

## ❌ Issue: Missing IAM Permissions
User `Natalie` needs `bedrock:CreateAgent` permission.

## ✅ SOLUTION: Manual Console Deployment

### 📋 Step-by-Step Instructions:

1. **Go to AWS Console**: https://console.aws.amazon.com/bedrock/

2. **Navigate to AgentCore Runtime** (or Agents if AgentCore not visible)

3. **Create New Agent**:
   - Name: `bible-companion`
   - Description: `Personalized Bible companion with memory`
   - Foundation Model: `Claude 3.5 Sonnet`

4. **Upload Code Files**:
   ```
   ✅ agentcore_runtime.py (main handler)
   ✅ session_tools.py (session management)  
   ✅ requirements_agentcore.txt (dependencies)
   ✅ user_memory_isolation.py (memory config)
   ```

5. **Configuration**:
   - Runtime: `python3.11`
   - Handler: `agentcore_runtime.bible_companion`
   - Timeout: `300 seconds`
   - Memory: `512 MB`

6. **Environment Variables**:
   ```
   MYSQL_HOST=gpbible-prod-mysql.c4zg06smsewh.us-east-1.rds.amazonaws.com
   MYSQL_USER=admin
   MYSQL_PASSWORD=87uW3y4oU59f
   MYSQL_DATABASE=gpbible
   MYSQL_PORT=3306
   ```

7. **Enable Memory**:
   - ✅ Session Memory: Enabled
   - ✅ User Isolation: True
   - ✅ Retention: 365 days
   - ✅ Auto-summarize: True

8. **Deploy & Test**:
   - Click "Deploy"
   - Test with sample message: "I'm struggling with anxiety"
   - Verify it pulls user data from MySQL
   - Check memory persistence

### 🔧 Alternative: Request IAM Permissions

Ask admin to add these permissions to user `Natalie`:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:CreateAgent",
                "bedrock:CreateAgentActionGroup", 
                "bedrock:PrepareAgent",
                "bedrock:InvokeAgent"
            ],
            "Resource": "*"
        }
    ]
}
```

### 📞 Support
If you need help with console deployment, let me know which step you're on!