#!/bin/bash
# Automated deployment for Bible Companion AgentCore Runtime

set -e

echo "🚀 Starting Bible Companion deployment..."

# 1. Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Install: https://aws.amazon.com/cli/"
    exit 1
fi

# 2. Check credentials
echo "🔐 Checking AWS credentials..."
aws sts get-caller-identity || {
    echo "❌ AWS credentials not configured. Run: aws configure"
    exit 1
}

# 3. Create deployment package
echo "📦 Creating deployment package..."
zip -r bible-companion.zip \
    agentcore_runtime.py \
    session_tools.py \
    requirements_agentcore.txt \
    user_memory_isolation.py

# 4. Deploy using Bedrock Agent API
echo "🚀 Deploying to AgentCore Runtime..."

AGENT_NAME="bible-companion-$(date +%s)"
REGION="us-east-1"

# Create agent
aws bedrock-agent create-agent \
    --agent-name "$AGENT_NAME" \
    --description "Personalized Bible companion with memory" \
    --foundation-model "anthropic.claude-3-5-sonnet-20241022-v2:0" \
    --instruction "You are a Bible Companion agent. Load user context from database automatically." \
    --region "$REGION" > agent-response.json

AGENT_ID=$(jq -r '.agent.agentId' agent-response.json)
echo "✅ Agent created: $AGENT_ID"

# Create action group with Lambda
aws bedrock-agent create-agent-action-group \
    --agent-id "$AGENT_ID" \
    --agent-version "DRAFT" \
    --action-group-name "bible-companion-actions" \
    --description "Bible companion actions with memory" \
    --action-group-executor '{
        "customControl": "RETURN_CONTROL"
    }' \
    --region "$REGION"

# Enable memory
aws bedrock-agent associate-agent-memory \
    --agent-id "$AGENT_ID" \
    --memory-configuration '{
        "enabledMemoryTypes": ["SESSION_SUMMARY"],
        "storageDays": 365
    }' \
    --region "$REGION"

# Prepare agent
aws bedrock-agent prepare-agent \
    --agent-id "$AGENT_ID" \
    --region "$REGION"

echo "✅ Deployment complete!"
echo "📍 Agent ID: $AGENT_ID"
echo "🔗 Test with: aws bedrock-agent-runtime invoke-agent --agent-id $AGENT_ID"

# Save config
cat > deployment-info.json << EOF
{
    "agentId": "$AGENT_ID",
    "agentName": "$AGENT_NAME",
    "region": "$REGION",
    "deployedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo "💾 Deployment info saved to deployment-info.json"