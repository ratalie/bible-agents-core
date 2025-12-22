# 📖 Bible Companion - AgentCore Runtime Deployment Guide

## 🏗️ Architecture Overview

### Components:
- **AgentCore Runtime**: Serverless agent hosting
- **AgentCore Memory**: Managed conversation memory
- **MySQL Database**: User preferences storage
- **S3 Bucket**: Code deployment storage

### Data Flow:
```
App → AgentCore Runtime → MySQL (user data) + AgentCore Memory (conversations)
```

## 🚀 Step-by-Step Deployment

### 1. Prerequisites Setup

#### AWS Credentials:
```bash
aws configure set aws_access_key_id YOUR_ACCESS_KEY
aws configure set aws_secret_access_key YOUR_SECRET_KEY
aws configure set default.region us-east-1
```

#### S3 Bucket:
```bash
aws s3 mb s3://bible-companion-deployment-2025
```

### 2. AgentCore Memory Setup

#### Create Memory Resource:
1. Go to: https://us-east-1.console.aws.amazon.com/bedrock-agentcore/
2. Navigate to **Memory** section
3. **Create Memory**:
   - Name: `bible-companion-memory`
   - Event expiration: `90 days`
   - Strategies: `User Preferences` + `Summarization`

#### Memory Configuration:
- **Memory ID**: `memory_bqdqb-jtj3lc48bl` ✅ (Already created)
- **Status**: Active
- **Strategies**: 2 (User preferences + Summarization)
- **Retention**: 90 days

### 3. Code Deployment

#### Upload to S3:
```bash
# Create deployment package
python -c "import zipfile; z=zipfile.ZipFile('bible-companion.zip','w'); z.write('agentcore_runtime.py'); z.write('session_tools.py'); z.write('requirements_agentcore.txt'); z.close()"

# Upload files
aws s3 cp agentcore_runtime.py s3://bible-companion-deployment-2025/
aws s3 cp bible-companion.zip s3://bible-companion-deployment-2025/
```

#### Files in S3:
- ✅ `agentcore_runtime.py` (12.9 KB) - Main handler
- ✅ `bible-companion.zip` (15.3 KB) - Complete package
- ✅ `session_tools.py` (863 B) - Session management
- ✅ `requirements_agentcore.txt` (163 B) - Dependencies

### 4. AgentCore Runtime Configuration

#### Create Runtime Agent:
1. Go to: https://us-east-1.console.aws.amazon.com/bedrock-agentcore/
2. **Create Runtime Agent**:
   - **Name**: `bible_companion`
   - **Runtime**: `python3.11`
   - **Handler**: `agentcore_runtime.bible_companion`

#### Source Configuration:
- **Source Type**: S3
- **S3 Path**: `s3://bible-companion-deployment-2025/agentcore_runtime.py`

#### Protocol & Security:
- **Protocol**: `HTTP`
- **Inbound Auth**: `Use IAM permissions`
- **Security**: `Public` (needs MySQL access)

#### Environment Variables:
```
MYSQL_HOST=gpbible-prod-mysql.c4zg06smsewh.us-east-1.rds.amazonaws.com
MYSQL_USER=admin
MYSQL_PASSWORD=87uW3y4oU59f
MYSQL_DATABASE=gpbible
MYSQL_PORT=3306
MEMORY_ID=memory_bqdqb-jtj3lc48bl
```

### 5. Runtime Information

#### Deployed Agent Details:
- **Runtime ID**: `bible_companion-GrIcKjGWbo`
- **Runtime ARN**: `arn:aws:bedrock-agentcore:us-east-1:124355682808:runtime/bible_companion-GrIcKjGWbo`
- **Status**: Ready ✅
- **Endpoint**: DEFAULT (Ready)

## 🔍 Data Mapping & Integration Review

### 1. Environment Variables Review

#### **⚠️ Security Check Required**:
```
MYSQL_HOST=gpbible-prod-mysql.c4zg06smsewh.us-east-1.rds.amazonaws.com
MYSQL_USER=admin
MYSQL_PASSWORD=87uW3y4oU59f  ← SENSITIVE - Review if should be in AWS Secrets Manager
MYSQL_DATABASE=gpbible
MYSQL_PORT=3306
MEMORY_ID=memory_bqdqb-jtj3lc48bl
```

**Recommendation**: Move `MYSQL_PASSWORD` to AWS Secrets Manager for production.

### 2. App → Runtime User Mapping

#### **Current Implementation**:
The app needs to send `user_id` in one of these ways:

**Option A - Session Attributes** (Recommended):
```python
response = client.invoke_agent_runtime(
    agentRuntimeArn='arn:aws:bedrock-agentcore:us-east-1:124355682808:runtime/bible_companion-GrIcKjGWbo',
    runtimeSessionId='session-123',
    payload=json.dumps({
        "prompt": "I'm struggling with anxiety",
        "sessionAttributes": {
            "userId": "user-abc-123"  # ← App sends this
        }
    })
)
```

**Option B - In Message**:
```python
payload = json.dumps({
    "prompt": "USER_ID:user-abc-123|I'm struggling with anxiety"
})
```

#### **⚠️ Integration Review Required**:
- How does the app currently identify users?
- What user ID format does the app use?
- How will the app pass the user_id to AgentCore Runtime?

### 3. Runtime → MySQL Mapping

#### **Database Schema Used**:
```sql
-- Main user data
SELECT u.firstName, u.birthDate, u.avatarIa, a.name as avatarName
FROM users u 
LEFT JOIN ai_avatars a ON u.avatarIa = a.id
WHERE u.id = %s  -- ← user_id from app

-- Bible version preference
SELECT bibleVersionId FROM user_preferences WHERE userId = %s

-- Denomination preference  
SELECT denominationId FROM user_preferences WHERE userId = %s

-- Bible version name lookup
SELECT abbreviation FROM bible_versions WHERE id = %s

-- Denomination name lookup
SELECT name FROM denominations WHERE id = %s
```

#### **⚠️ Database Mapping Review Required**:
1. **User ID Field**: Code uses `u.id` - confirm this matches app's user identifier
2. **User Preferences Table**: Uses `userId` field - verify this exists and matches
3. **Foreign Key Relationships**: Verify `bibleVersionId` and `denominationId` relationships
4. **Data Availability**: Confirm all users have entries in `user_preferences` table

### 4. Runtime → Memory Mapping

#### **AgentCore Memory Structure**:
```python
# Memory events stored as:
{
    "memoryId": "memory_bqdqb-jtj3lc48bl",
    "actorId": user_id,  # ← Same user_id from app
    "sessionId": session_id,
    "payload": [
        {
            "conversational": {
                "content": {"text": "user message"},
                "role": "USER"
            }
        }
    ]
}

# Long-term memories organized by namespace:
"/customer-support/{user_id}/preferences"
"/customer-support/{user_id}/{session_id}/summary"
```

#### **⚠️ Memory Integration Review Required**:
1. **Actor ID**: Uses same `user_id` from app - confirm this provides proper isolation
2. **Session Management**: How does app generate/manage `session_id`?
3. **Memory Strategies**: Current strategies extract user preferences and summaries - verify this meets requirements

## 🧪 Testing & Validation

### Test Invocation:
```python
import boto3
import json

client = boto3.client('bedrock-agentcore', region_name='us-east-1')

response = client.invoke_agent_runtime(
    agentRuntimeArn='arn:aws:bedrock-agentcore:us-east-1:124355682808:runtime/bible_companion-GrIcKjGWbo',
    runtimeSessionId='test-session-123',
    payload=json.dumps({
        "prompt": "USER_ID:test-user-123|I'm struggling with anxiety about work",
    })
)
```

### Expected Behavior:
1. ✅ Agent extracts `user_id` from message
2. ✅ Queries MySQL for user preferences (name, bible version, denomination)
3. ✅ Retrieves conversation context from AgentCore Memory
4. ✅ Generates personalized spiritual guidance
5. ✅ Saves interaction to AgentCore Memory for future context

### Validation Checklist:
- [ ] User data retrieved correctly from MySQL
- [ ] Memory events created in AgentCore Memory
- [ ] Long-term memories extracted by strategies
- [ ] Responses personalized with user preferences
- [ ] Session continuity maintained across interactions

## 🔧 Production Considerations

### Security:
- [ ] Move MySQL password to AWS Secrets Manager
- [ ] Implement proper IAM roles for AgentCore Runtime
- [ ] Review VPC configuration for MySQL access

### Monitoring:
- [ ] Enable CloudWatch logging for Runtime
- [ ] Set up observability dashboard for Memory
- [ ] Monitor MySQL connection pool usage

### Scaling:
- [ ] Test with concurrent users
- [ ] Monitor memory usage and retention policies
- [ ] Plan for session management at scale