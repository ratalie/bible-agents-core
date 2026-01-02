# Deploy Lambda para AgentCore Memory Action Group
# Ejecutar desde PowerShell

$LAMBDA_NAME = "bible-agentcore-memory"
$ROLE_NAME = "bible-agentcore-memory-role"
$REGION = "us-east-1"
$ACCOUNT_ID = "124355682808"
$AGENT_ID = "MCP33AOQV8"
$MEMORY_ID = "memory_bqdqb-jtj3lc48bl"

Write-Host "=== Desplegando Lambda para AgentCore Memory ===" -ForegroundColor Cyan

# 1. Crear rol IAM si no existe
Write-Host "`n1. Creando rol IAM..." -ForegroundColor Yellow

$trustPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": ["lambda.amazonaws.com", "bedrock.amazonaws.com"]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@

$trustPolicy | Out-File -FilePath trust-policy.json -Encoding UTF8

aws iam create-role `
    --role-name $ROLE_NAME `
    --assume-role-policy-document file://trust-policy.json `
    2>$null

# 2. Adjuntar políticas al rol
Write-Host "2. Adjuntando políticas..." -ForegroundColor Yellow

aws iam attach-role-policy `
    --role-name $ROLE_NAME `
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Política para AgentCore
$agentcorePolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:*"
      ],
      "Resource": "*"
    }
  ]
}
"@

$agentcorePolicy | Out-File -FilePath agentcore-policy.json -Encoding UTF8

aws iam put-role-policy `
    --role-name $ROLE_NAME `
    --policy-name AgentCoreAccess `
    --policy-document file://agentcore-policy.json

Write-Host "   Esperando propagación del rol (15s)..." -ForegroundColor Gray
Start-Sleep -Seconds 15

# 3. Crear ZIP del Lambda
Write-Host "3. Creando paquete ZIP..." -ForegroundColor Yellow

Compress-Archive -Path lambda_function.py -DestinationPath lambda.zip -Force

# 4. Crear o actualizar Lambda
Write-Host "4. Desplegando Lambda..." -ForegroundColor Yellow

$lambdaExists = aws lambda get-function --function-name $LAMBDA_NAME 2>$null

if ($lambdaExists) {
    Write-Host "   Actualizando Lambda existente..." -ForegroundColor Gray
    aws lambda update-function-code `
        --function-name $LAMBDA_NAME `
        --zip-file fileb://lambda.zip
} else {
    Write-Host "   Creando nuevo Lambda..." -ForegroundColor Gray
    aws lambda create-function `
        --function-name $LAMBDA_NAME `
        --runtime python3.11 `
        --role "arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}" `
        --handler lambda_function.lambda_handler `
        --zip-file fileb://lambda.zip `
        --timeout 30 `
        --memory-size 256 `
        --environment "Variables={MEMORY_ID=$MEMORY_ID}"
}

# 5. Agregar permiso para Bedrock Agent
Write-Host "5. Configurando permisos para Bedrock Agent..." -ForegroundColor Yellow

aws lambda add-permission `
    --function-name $LAMBDA_NAME `
    --statement-id bedrock-agent-invoke `
    --action lambda:InvokeFunction `
    --principal bedrock.amazonaws.com `
    --source-arn "arn:aws:bedrock:${REGION}:${ACCOUNT_ID}:agent/${AGENT_ID}" `
    2>$null

# 6. Obtener ARN del Lambda
$LAMBDA_ARN = aws lambda get-function --function-name $LAMBDA_NAME --query 'Configuration.FunctionArn' --output text

Write-Host "`n=== Despliegue Completado ===" -ForegroundColor Green
Write-Host "Lambda ARN: $LAMBDA_ARN" -ForegroundColor Cyan

Write-Host "`n=== Siguiente Paso ===" -ForegroundColor Yellow
Write-Host "Ahora necesitas agregar el Action Group al agente en la consola de Bedrock:"
Write-Host "1. Ve a: https://console.aws.amazon.com/bedrock/home?region=us-east-1#/agents/$AGENT_ID"
Write-Host "2. Click en 'Edit in Agent Builder'"
Write-Host "3. En 'Action groups', click 'Add'"
Write-Host "4. Configura:"
Write-Host "   - Name: AgentCoreMemory"
Write-Host "   - Action group type: Define with API schemas"
Write-Host "   - Action group invocation: Lambda function"
Write-Host "   - Lambda function: $LAMBDA_NAME"
Write-Host "   - API Schema: Upload openapi.json"
Write-Host "5. Save and Prepare agent"

# Limpiar archivos temporales
Remove-Item trust-policy.json, agentcore-policy.json -ErrorAction SilentlyContinue
