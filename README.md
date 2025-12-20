# Bible Agents for Bedrock Agent Core

Two Claude Sonnet 4.5 agents for spiritual guidance.

## Agents

### 1. Bible Companion
Personalized conversational agent with memory. Uses user preferences (name, denomination, bible version) and saves conversation summaries.

- **Prompt**: `agents/bible-companion/prompt.txt`
- **OpenAPI**: `agents/bible-companion/openapi.json`
- **Lambda**: `agents/bible-companion/lambda/index.py`

### 2. Verse of the Day
Simple agent that returns daily Bible verses with reflections. No personalization.

- **Prompt**: `agents/verse-of-the-day/prompt.txt`
- **OpenAPI**: `agents/verse-of-the-day/openapi.json`
- **Lambda**: `agents/verse-of-the-day/lambda/index.py`

## Infrastructure

SAM template in `infrastructure/template.yaml` creates:
- DynamoDB tables for user preferences, conversation memory, and daily verses
- Lambda functions for agent actions
- Permissions for Bedrock to invoke Lambdas

## Deploy

```bash
cd infrastructure
sam build
sam deploy --guided
```

## Setup in Bedrock Console

1. Create Agent with Claude Sonnet 4.5
2. Copy prompt from `prompt.txt` to Instructions
3. Create Action Group with OpenAPI schema
4. Attach Lambda function
5. Enable memory (for bible-companion)

## DynamoDB Schema

### User Preferences
```
userId (PK) | firstName | bibleVersion | denomination | birthday | avatarName
```

### Conversation Memory
```
userId (PK) | timestamp (SK) | keyPoints | spiritualThemes | versesShared | userSentiment
```

### Daily Verses
```
date (PK) | references[] | theme
```

## Memory Flow

1. User starts conversation
2. Agent calls `checkFirstTimeToday` → determines greeting type
3. Agent calls `getUserPreferences` → gets personalization
4. Agent calls `getConversationMemory` → gets context from past sessions
5. Conversation happens...
6. When session ends (or `@@SUMMARIZE_SESSION@@`), agent calls `saveSessionSummary`
