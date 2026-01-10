# Deploy Lambda con AgentCore Memory
# Actualiza el Lambda existente gpbible-bedrock-processor-dev

$LAMBDA_NAME = "gpbible-bedrock-processor-dev"
$REGION = "us-east-1"
$MEMORY_ID = "memory_bqdqb-jtj3lc48bl"

Write-Host "=== Actualizando Lambda con AgentCore Memory ===" -ForegroundColor Cyan

# 1. Instalar dependencias
Write-Host "`n1. Instalando dependencias..." -ForegroundColor Yellow
npm install

# 2. Crear ZIP
Write-Host "`n2. Creando paquete..." -ForegroundColor Yellow
if (Test-Path lambda.zip) { Remove-Item lambda.zip }
Compress-Archive -Path index.js, package.json, node_modules -DestinationPath lambda.zip -Force

# 3. Actualizar código del Lambda
Write-Host "`n3. Actualizando Lambda..." -ForegroundColor Yellow
aws lambda update-function-code `
    --function-name $LAMBDA_NAME `
    --zip-file fileb://lambda.zip

# 4. Agregar variable de entorno para Memory ID
Write-Host "`n4. Configurando variables de entorno..." -ForegroundColor Yellow

# Obtener variables actuales
$currentEnv = aws lambda get-function-configuration --function-name $LAMBDA_NAME --query 'Environment.Variables' --output json | ConvertFrom-Json

# Agregar AGENTCORE_MEMORY_ID
$envVars = @{}
$currentEnv.PSObject.Properties | ForEach-Object { $envVars[$_.Name] = $_.Value }
$envVars["AGENTCORE_MEMORY_ID"] = $MEMORY_ID

$envJson = $envVars | ConvertTo-Json -Compress
aws lambda update-function-configuration `
    --function-name $LAMBDA_NAME `
    --environment "Variables=$envJson"

# 5. Agregar permisos para AgentCore
Write-Host "`n5. Verificando permisos IAM..." -ForegroundColor Yellow

$roleName = aws lambda get-function-configuration --function-name $LAMBDA_NAME --query 'Role' --output text
$roleName = $roleName.Split('/')[-1]

Write-Host "   Role: $roleName" -ForegroundColor Gray

# Agregar política para AgentCore
$agentcorePolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:CreateEvent",
        "bedrock-agentcore:ListEvents",
        "bedrock-agentcore:ListSessions",
        "bedrock-agentcore:GetEvent",
        "bedrock-agentcore:DeleteEvent",
        "bedrock-agentcore:ListActors"
      ],
      "Resource": "*"
    }
  ]
}
"@

$agentcorePolicy | Out-File -FilePath agentcore-policy.json -Encoding UTF8

aws iam put-role-policy `
    --role-name $roleName `
    --policy-name AgentCoreMemoryAccess `
    --policy-document file://agentcore-policy.json

Remove-Item agentcore-policy.json

Write-Host "`n=== Despliegue Completado ===" -ForegroundColor Green
Write-Host "Lambda: $LAMBDA_NAME" -ForegroundColor Cyan
Write-Host "Memory ID: $MEMORY_ID" -ForegroundColor Cyan
Write-Host "`nEl Lambda ahora:" -ForegroundColor Yellow
Write-Host "  1. Lee memoria del usuario antes de llamar al agente"
Write-Host "  2. Enriquece el prompt con contexto de conversaciones anteriores"
Write-Host "  3. Guarda cada interacción en AgentCore Memory"
