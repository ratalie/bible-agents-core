# Bible Agents for Bedrock AgentCore

Two Claude Sonnet 4.5 agents for spiritual guidance using **AgentCore Runtime** with managed memory.

## Agents

### 1. Bible Companion
Personalized conversational agent with AgentCore Memory. Automatically loads user preferences from MySQL and maintains conversation context.

- **Runtime**: `agentcore_runtime.py`
- **Handler**: `agentcore_runtime.bible_companion`
- **Memory**: AgentCore Memory (managed)
- **Database**: MySQL for user preferences

### 2. Verse of the Day
Simple agent that returns daily Bible verses with reflections. No personalization.

- **Prompt**: `agents/verse-of-the-day/prompt.txt`
- **OpenAPI**: `agents/verse-of-the-day/openapi.json`
- **Lambda**: `agents/verse-of-the-day/lambda/index.py`

## Deployment

### AgentCore Runtime (Bible Companion)
See complete guide: `AGENTCORE_DEPLOYMENT_GUIDE.md`

**Quick Setup**:
1. Go to: https://us-east-1.console.aws.amazon.com/bedrock-agentcore/
2. Create Runtime Agent with `agentcore_runtime.py`
3. Connect to Memory: `memory_bqdqb-jtj3lc48bl`
4. Configure MySQL environment variables

### Traditional Bedrock Agent (Verse of the Day)
```bash
cd infrastructure
sam build
sam deploy --guided
```

## Data Architecture

### AgentCore Memory (Bible Companion)
- **Short-term**: Raw conversation events
- **Long-term**: User preferences and session summaries
- **Isolation**: By user_id
- **Retention**: 90 days

### MySQL Schema (User Data)
```sql
-- User basic info
users: id (PK) | firstName | birthDate | avatarIa

-- User preferences
user_preferences: userId (FK) | bibleVersionId | denominationId

-- Bible versions
bible_versions: id (PK) | abbreviation | name

-- Denominations  
denominations: id (PK) | name
```

### DynamoDB Schema (Verse of the Day only)
```
Daily Verses: date (PK) | references[] | theme
```

## Integration

### App → AgentCore Runtime
```python
response = client.invoke_agent_runtime(
    agentRuntimeArn='arn:aws:bedrock-agentcore:us-east-1:124355682808:runtime/bible_companion-GrIcKjGWbo',
    runtimeSessionId='session-123',
    payload=json.dumps({
        "prompt": "I'm struggling with anxiety",
        "sessionAttributes": {
            "userId": "user-abc-123"  # Required for personalization
        }
    })
)
```

### Memory Flow
1. User sends message with `userId`
2. Agent loads preferences from MySQL
3. Agent retrieves conversation context from AgentCore Memory
4. Agent generates personalized response
5. Agent saves interaction to AgentCore Memory
6. Memory strategies extract long-term insights automatically
