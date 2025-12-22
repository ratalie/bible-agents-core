# AgentCore Runtime Deployment (Using available CLI)

Write-Host "🚀 AgentCore Runtime Deployment" -ForegroundColor Green

# Since AgentCore Runtime deployment is different, we need to:
# 1. Package the agent code
# 2. Use the AgentCore console or SDK

Write-Host "📦 Packaging agent files..." -ForegroundColor Yellow

# Create deployment package
$files = @(
    "agentcore_runtime.py",
    "session_tools.py", 
    "requirements_agentcore.txt",
    "user_memory_isolation.py"
)

Write-Host "📁 Files to deploy:" -ForegroundColor Cyan
foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file (missing)" -ForegroundColor Red
    }
}

# For now, AgentCore Runtime requires manual deployment through console
Write-Host "`n📋 Manual AgentCore Runtime Deployment Steps:" -ForegroundColor Yellow
Write-Host "1. Go to AWS Bedrock Console" -ForegroundColor White
Write-Host "2. Navigate to 'AgentCore Runtime' (Preview)" -ForegroundColor White
Write-Host "3. Click 'Create Runtime Agent'" -ForegroundColor White
Write-Host "4. Upload the files listed above" -ForegroundColor White
Write-Host "5. Set handler: agentcore_runtime.bible_companion" -ForegroundColor White
Write-Host "6. Configure environment variables:" -ForegroundColor White
Write-Host "   MYSQL_HOST=gpbible-prod-mysql.c4zg06smsewh.us-east-1.rds.amazonaws.com" -ForegroundColor Gray
Write-Host "   MYSQL_USER=admin" -ForegroundColor Gray
Write-Host "   MYSQL_PASSWORD=87uW3y4oU59f" -ForegroundColor Gray
Write-Host "   MYSQL_DATABASE=gpbible" -ForegroundColor Gray
Write-Host "7. Enable Memory with user isolation" -ForegroundColor White
Write-Host "8. Deploy and test" -ForegroundColor White

Write-Host "`n🔗 Console URL: https://console.aws.amazon.com/bedrock/" -ForegroundColor Cyan

# Test if we can invoke existing agents
Write-Host "`n🧪 Testing AgentCore CLI..." -ForegroundColor Yellow
try {
    aws bedrock-agentcore list-sessions --limit 1
    Write-Host "✅ AgentCore CLI working" -ForegroundColor Green
} catch {
    Write-Host "❌ AgentCore CLI access issue" -ForegroundColor Red
}