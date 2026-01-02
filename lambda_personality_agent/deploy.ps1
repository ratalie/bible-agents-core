# Deploy Bible Companion Personality Agent
# Ejecutar desde la carpeta lambda_personality_agent
#
# PASOS:
# 1. Primero ejecuta: .\clone-bedrock-agent.ps1 (crea el agente en Bedrock)
# 2. Luego ejecuta este script con los IDs generados

$FUNCTION_NAME = "bible-companion-personality"
$REGION = "us-east-1"
$MEMORY_ID = "memory_bqdqb-jtj3lc48bl"

# Cargar IDs del agente clonado (si existe el archivo)
if (Test-Path "personality-agent-deployment.json") {
    $agentInfo = Get-Content "personality-agent-deployment.json" | ConvertFrom-Json
    $AGENT_ID = $agentInfo.newAgentId
    $ALIAS_ID = $agentInfo.aliasId
    Write-Host "✅ Usando agente clonado: $AGENT_ID" -ForegroundColor Green
} else {
    Write-Host "⚠️ No se encontró personality-agent-deployment.json" -ForegroundColor Yellow
    Write-Host "   Ejecuta primero: .\clone-bedrock-agent.ps1" -ForegroundColor Yellow
    $AGENT_ID = "YOUR_AGENT_ID"
    $ALIAS_ID = "YOUR_ALIAS_ID"
}

# Obtener Role ARN del Lambda existente o crear uno
$existingLambda = aws lambda get-function --function-name "gpbible-bedrock-processor-dev" --region $REGION 2>$null | ConvertFrom-Json
if ($existingLambda) {
    $ROLE_ARN = $existingLambda.Configuration.Role
    Write-Host "✅ Usando role existente: $ROLE_ARN" -ForegroundColor Green
} else {
    $ROLE_ARN = "arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-bedrock-role"
    Write-Host "⚠️ Actualiza ROLE_ARN manualmente" -ForegroundColor Yellow
}

Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
npm install

Write-Host "🗜️ Creating deployment package..." -ForegroundColor Cyan
if (Test-Path "lambda_personality.zip") { Remove-Item "lambda_personality.zip" }
Compress-Archive -Path "index.js", "package.json", "node_modules" -DestinationPath "lambda_personality.zip"

Write-Host "🚀 Deploying to AWS Lambda..." -ForegroundColor Cyan

# Verificar si la función existe
$functionExists = aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>$null

if ($functionExists) {
    Write-Host "Updating existing function..." -ForegroundColor Yellow
    aws lambda update-function-code `
        --function-name $FUNCTION_NAME `
        --zip-file fileb://lambda_personality.zip `
        --region $REGION
} else {
    Write-Host "Creating new function..." -ForegroundColor Green
    aws lambda create-function `
        --function-name $FUNCTION_NAME `
        --runtime nodejs20.x `
        --handler index.handler `
        --role $ROLE_ARN `
        --zip-file fileb://lambda_personality.zip `
        --timeout 90 `
        --memory-size 512 `
        --region $REGION `
        --environment "Variables={AGENTCORE_MEMORY_ID=$MEMORY_ID,BEDROCK_AGENT_ID=$AGENT_ID,BEDROCK_AGENT_ALIAS_ID=$ALIAS_ID,BACKEND_WEBHOOK_URL=YOUR_WEBHOOK_URL}"
}

# Configurar SNS trigger (igual que el Lambda original)
Write-Host "`n📡 Configurando SNS trigger..." -ForegroundColor Yellow
$SNS_TOPIC_ARN = "arn:aws:sns:${REGION}:YOUR_ACCOUNT_ID:bible-companion-personality-topic"

# Crear topic SNS si no existe
aws sns create-topic --name "bible-companion-personality-topic" --region $REGION 2>$null

# Agregar permiso para SNS
aws lambda add-permission `
    --function-name $FUNCTION_NAME `
    --statement-id sns-trigger `
    --action lambda:InvokeFunction `
    --principal sns.amazonaws.com `
    --source-arn $SNS_TOPIC_ARN `
    --region $REGION 2>$null

Write-Host "`n=== Deployment Complete ===" -ForegroundColor Green
Write-Host "Lambda: $FUNCTION_NAME" -ForegroundColor Cyan
Write-Host "Agent ID: $AGENT_ID" -ForegroundColor Cyan
Write-Host "Alias ID: $ALIAS_ID" -ForegroundColor Cyan
Write-Host "Memory ID: $MEMORY_ID" -ForegroundColor Cyan
Write-Host "`n📋 Próximos pasos:" -ForegroundColor Yellow
Write-Host "  1. Actualiza BACKEND_WEBHOOK_URL en las variables de entorno"
Write-Host "  2. Suscribe el Lambda al topic SNS"
Write-Host "  3. Actualiza tu backend para enviar userProfile en el mensaje SNS"
