# AgentCore Runtime Deployment (Correct commands)

Write-Host "🚀 Deploying to AgentCore Runtime..." -ForegroundColor Green

# 1. Check if AgentCore CLI is available
try {
    aws bedrock-agentcore --version
} catch {
    Write-Host "❌ AgentCore CLI not available yet. Using manual deployment." -ForegroundColor Yellow
    Write-Host "📋 Manual steps for AgentCore Runtime:" -ForegroundColor Cyan
    Write-Host "1. Go to AWS Bedrock Console" -ForegroundColor White
    Write-Host "2. Navigate to AgentCore Runtime (Preview)" -ForegroundColor White
    Write-Host "3. Create new runtime agent" -ForegroundColor White
    Write-Host "4. Upload agentcore_runtime.py" -ForegroundColor White
    Write-Host "5. Configure memory and environment variables" -ForegroundColor White
    exit 0
}

# 2. Create AgentCore Runtime deployment
$AGENT_NAME = "bible-companion-$(Get-Date -Format 'yyyyMMddHHmmss')"

Write-Host "📦 Creating AgentCore Runtime agent: $AGENT_NAME" -ForegroundColor Cyan

# AgentCore specific deployment (when CLI becomes available)
aws bedrock-agentcore create-runtime-agent `
    --agent-name "$AGENT_NAME" `
    --runtime "python3.11" `
    --handler "agentcore_runtime.bible_companion" `
    --memory-enabled true `
    --environment-variables '{
        "MYSQL_HOST": "gpbible-prod-mysql.c4zg06smsewh.us-east-1.rds.amazonaws.com",
        "MYSQL_USER": "admin", 
        "MYSQL_PASSWORD": "87uW3y4oU59f",
        "MYSQL_DATABASE": "gpbible"
    }'

Write-Host "✅ AgentCore Runtime deployment initiated" -ForegroundColor Green