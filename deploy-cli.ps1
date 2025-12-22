# Automated deployment for Bible Companion AgentCore Runtime (Windows)

Write-Host "🚀 Starting Bible Companion deployment..." -ForegroundColor Green

# 1. Check AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "❌ AWS CLI not found. Install from: https://aws.amazon.com/cli/" -ForegroundColor Red
    exit 1
}

# 2. Check credentials
Write-Host "🔐 Checking AWS credentials..." -ForegroundColor Yellow
try {
    aws sts get-caller-identity | Out-Null
} catch {
    Write-Host "❌ AWS credentials not configured. Run: aws configure" -ForegroundColor Red
    exit 1
}

# 3. Set variables
$AGENT_NAME = "bible-companion-$(Get-Date -Format 'yyyyMMddHHmmss')"
$REGION = "us-east-1"

Write-Host "📦 Agent name: $AGENT_NAME" -ForegroundColor Cyan

# 4. Create agent
Write-Host "🚀 Creating agent..." -ForegroundColor Yellow

$createAgentCmd = @"
aws bedrock-agent create-agent `
    --agent-name "$AGENT_NAME" `
    --description "Personalized Bible companion with memory" `
    --foundation-model "anthropic.claude-3-5-sonnet-20241022-v2:0" `
    --instruction "You are a Bible Companion agent. Load user context from database automatically." `
    --region "$REGION"
"@

$agentResponse = Invoke-Expression $createAgentCmd | ConvertFrom-Json
$AGENT_ID = $agentResponse.agent.agentId

Write-Host "✅ Agent created: $AGENT_ID" -ForegroundColor Green

# 5. Enable memory
Write-Host "🧠 Enabling memory..." -ForegroundColor Yellow

aws bedrock-agent associate-agent-memory `
    --agent-id "$AGENT_ID" `
    --memory-configuration '{\"enabledMemoryTypes\":[\"SESSION_SUMMARY\"],\"storageDays\":365}' `
    --region "$REGION"

# 6. Prepare agent
Write-Host "⚙️ Preparing agent..." -ForegroundColor Yellow

aws bedrock-agent prepare-agent `
    --agent-id "$AGENT_ID" `
    --region "$REGION"

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "📍 Agent ID: $AGENT_ID" -ForegroundColor Cyan
Write-Host "🔗 Region: $REGION" -ForegroundColor Cyan

# 7. Save deployment info
$deploymentInfo = @{
    agentId = $AGENT_ID
    agentName = $AGENT_NAME
    region = $REGION
    deployedAt = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
} | ConvertTo-Json

$deploymentInfo | Out-File -FilePath "deployment-info.json" -Encoding UTF8

Write-Host "💾 Deployment info saved to deployment-info.json" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Go to AWS Bedrock Console" -ForegroundColor White
Write-Host "2. Find agent: $AGENT_ID" -ForegroundColor White
Write-Host "3. Add action groups and configure Lambda" -ForegroundColor White