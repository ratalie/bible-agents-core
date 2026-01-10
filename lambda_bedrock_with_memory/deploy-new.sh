#!/bin/bash

# ============================================
# Script de Deployment para Nueva Lambda
# ============================================
# Crea una nueva función Lambda desde cero
# Lambda: gpbible-ai-agent-dev
# ============================================

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================
# CONFIGURACIÓN - AJUSTA ESTOS VALORES
# ============================================
LAMBDA_NAME="gpbible-ai-agent-dev"
REGION="us-east-1"
MEMORY_ID="memory_bqdqb-jtj3lc48bl"

# Obtener Account ID automáticamente
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)

if [ -z "$ACCOUNT_ID" ]; then
    echo -e "${RED}❌ Error: No se pudo obtener el Account ID. Verifica que AWS CLI esté configurado.${NC}"
    exit 1
fi

# Variables que el usuario debe configurar
echo -e "${CYAN}=== Configuración de Lambda ===${NC}"
echo -e "${YELLOW}Lambda Name: ${LAMBDA_NAME}${NC}"
echo -e "${YELLOW}Region: ${REGION}${NC}"
echo -e "${YELLOW}Account ID: ${ACCOUNT_ID}${NC}"
echo ""

# Solicitar valores requeridos
read -p "Bedrock Agent ID: " AGENT_ID
read -p "Bedrock Agent Alias ID: " ALIAS_ID
read -p "SNS Topic Name (o ARN completo): " SNS_TOPIC_INPUT
read -p "Backend Webhook URL (opcional, presiona Enter para omitir): " WEBHOOK_URL

# Determinar si es ARN o nombre
if [[ $SNS_TOPIC_INPUT == arn:* ]]; then
    SNS_TOPIC_ARN=$SNS_TOPIC_INPUT
else
    SNS_TOPIC_ARN="arn:aws:sns:${REGION}:${ACCOUNT_ID}:${SNS_TOPIC_INPUT}"
fi

# Validar valores requeridos
if [ -z "$AGENT_ID" ] || [ -z "$ALIAS_ID" ] || [ -z "$SNS_TOPIC_INPUT" ]; then
    echo -e "${RED}❌ Error: Agent ID, Alias ID y SNS Topic son requeridos${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}=== Resumen de Configuración ===${NC}"
echo "Lambda Name: $LAMBDA_NAME"
echo "Region: $REGION"
echo "Agent ID: $AGENT_ID"
echo "Alias ID: $ALIAS_ID"
echo "SNS Topic: $SNS_TOPIC_ARN"
echo "Webhook URL: ${WEBHOOK_URL:-(no configurado)}"
echo "Memory ID: $MEMORY_ID"
echo ""
read -p "¿Continuar con el deployment? (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo -e "${YELLOW}Deployment cancelado${NC}"
    exit 0
fi

# ============================================
# 1. CREAR ROL IAM
# ============================================
echo ""
echo -e "${CYAN}1. Creando rol IAM...${NC}"

ROLE_NAME="${LAMBDA_NAME}-role"

# Trust policy
cat > /tmp/lambda-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Verificar si el rol ya existe
if aws iam get-role --role-name $ROLE_NAME --region $REGION >/dev/null 2>&1; then
    echo -e "${YELLOW}   El rol $ROLE_NAME ya existe, omitiendo creación...${NC}"
else
    # Crear rol
    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
        --region $REGION >/dev/null
    
    echo -e "${GREEN}   ✓ Rol creado: $ROLE_NAME${NC}"
fi

# Política básica de Lambda (CloudWatch Logs)
echo -e "${CYAN}   Agregando política básica de Lambda...${NC}"
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
    --region $REGION 2>/dev/null || echo -e "${YELLOW}   (Política ya adjunta)${NC}"

# Política para Bedrock y AgentCore
echo -e "${CYAN}   Agregando permisos para Bedrock y AgentCore...${NC}"
cat > /tmp/bedrock-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:InvokeAgent",
        "bedrock-agent:InvokeAgent",
        "bedrock-agent-runtime:InvokeAgent"
      ],
      "Resource": "*"
    },
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
EOF

aws iam put-role-policy \
    --role-name $ROLE_NAME \
    --policy-name BedrockAgentCoreAccess \
    --policy-document file:///tmp/bedrock-policy.json \
    --region $REGION >/dev/null

echo -e "${GREEN}   ✓ Permisos configurados${NC}"

ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

# Esperar a que el rol esté listo
echo -e "${CYAN}   Esperando a que el rol esté disponible...${NC}"
sleep 5

# ============================================
# 2. PREPARAR CÓDIGO
# ============================================
echo ""
echo -e "${CYAN}2. Preparando código...${NC}"

# Asegurarse de estar en el directorio correcto
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Instalar dependencias
if [ ! -d "node_modules" ]; then
    echo -e "${CYAN}   Instalando dependencias npm...${NC}"
    npm install
else
    echo -e "${YELLOW}   node_modules existe, omitiendo npm install${NC}"
    echo -e "${CYAN}   (Si necesitas actualizar dependencias, ejecuta: npm install)${NC}"
fi

# Crear ZIP
echo -e "${CYAN}   Creando paquete ZIP...${NC}"
rm -f lambda.zip
zip -r lambda.zip index.js package.json node_modules/ personality/ >/dev/null 2>&1

if [ ! -f "lambda.zip" ]; then
    echo -e "${RED}❌ Error: No se pudo crear lambda.zip${NC}"
    exit 1
fi

ZIP_SIZE=$(du -h lambda.zip | cut -f1)
echo -e "${GREEN}   ✓ Paquete creado: lambda.zip (${ZIP_SIZE})${NC}"

# ============================================
# 3. CREAR LAMBDA
# ============================================
echo ""
echo -e "${CYAN}3. Creando función Lambda...${NC}"

# Construir variables de entorno
# Nota: AWS_REGION es una variable reservada que Lambda establece automáticamente
ENV_VARS="AGENTCORE_MEMORY_ID=${MEMORY_ID},BEDROCK_AGENT_ID=${AGENT_ID},BEDROCK_AGENT_ALIAS_ID=${ALIAS_ID}"

if [ -n "$WEBHOOK_URL" ]; then
    ENV_VARS="${ENV_VARS},BACKEND_WEBHOOK_URL=${WEBHOOK_URL}"
fi

# Verificar si la Lambda ya existe
if aws lambda get-function --function-name $LAMBDA_NAME --region $REGION >/dev/null 2>&1; then
    echo -e "${YELLOW}   La Lambda $LAMBDA_NAME ya existe.${NC}"
    read -p "   ¿Actualizar código y configuración? (y/n): " UPDATE_CONFIRM
    
    if [ "$UPDATE_CONFIRM" = "y" ] || [ "$UPDATE_CONFIRM" = "Y" ]; then
        echo -e "${CYAN}   Actualizando código...${NC}"
        aws lambda update-function-code \
            --function-name $LAMBDA_NAME \
            --zip-file fileb://lambda.zip \
            --region $REGION >/dev/null
        
        echo -e "${CYAN}   Actualizando configuración...${NC}"
        aws lambda update-function-configuration \
            --function-name $LAMBDA_NAME \
            --timeout 300 \
            --memory-size 512 \
            --environment "Variables={${ENV_VARS}}" \
            --region $REGION >/dev/null
        
        echo -e "${GREEN}   ✓ Lambda actualizada${NC}"
    else
        echo -e "${YELLOW}   Omitiendo actualización${NC}"
    fi
else
    # Crear función Lambda
    aws lambda create-function \
        --function-name $LAMBDA_NAME \
        --runtime nodejs20.x \
        --role $ROLE_ARN \
        --handler index.handler \
        --zip-file fileb://lambda.zip \
        --timeout 300 \
        --memory-size 512 \
        --environment "Variables={${ENV_VARS}}" \
        --region $REGION >/dev/null
    
    echo -e "${GREEN}   ✓ Lambda creada: $LAMBDA_NAME${NC}"
fi

# Obtener ARN del Lambda
LAMBDA_ARN=$(aws lambda get-function \
    --function-name $LAMBDA_NAME \
    --region $REGION \
    --query 'Configuration.FunctionArn' \
    --output text)

echo -e "${GREEN}   Lambda ARN: $LAMBDA_ARN${NC}"

# ============================================
# 4. CONFIGURAR TRIGGER SNS
# ============================================
echo ""
echo -e "${CYAN}4. Configurando trigger SNS...${NC}"

# Verificar si ya existe una suscripción
EXISTING_SUB=$(aws sns list-subscriptions-by-topic \
    --topic-arn $SNS_TOPIC_ARN \
    --region $REGION \
    --query "Subscriptions[?Endpoint=='$LAMBDA_ARN'].SubscriptionArn" \
    --output text 2>/dev/null)

if [ -n "$EXISTING_SUB" ] && [ "$EXISTING_SUB" != "None" ]; then
    echo -e "${YELLOW}   Ya existe una suscripción SNS para este Lambda${NC}"
else
    # Dar permiso a SNS para invocar el Lambda
    STATEMENT_ID="sns-trigger-$(date +%s)"
    echo -e "${CYAN}   Agregando permiso para SNS...${NC}"
    
    aws lambda add-permission \
        --function-name $LAMBDA_NAME \
        --statement-id $STATEMENT_ID \
        --action lambda:InvokeFunction \
        --principal sns.amazonaws.com \
        --source-arn $SNS_TOPIC_ARN \
        --region $REGION >/dev/null 2>&1 || echo -e "${YELLOW}   (Permiso ya existe o error)${NC}"
    
    # Suscribir Lambda al SNS
    echo -e "${CYAN}   Suscribiendo Lambda al SNS Topic...${NC}"
    aws sns subscribe \
        --topic-arn $SNS_TOPIC_ARN \
        --protocol lambda \
        --notification-endpoint $LAMBDA_ARN \
        --region $REGION >/dev/null
    
    echo -e "${GREEN}   ✓ Trigger SNS configurado${NC}"
fi

# ============================================
# LIMPIEZA
# ============================================
rm -f /tmp/lambda-trust-policy.json
rm -f /tmp/bedrock-policy.json

# ============================================
# RESUMEN
# ============================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Deployment Completado${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${CYAN}Lambda:${NC} $LAMBDA_NAME"
echo -e "${CYAN}ARN:${NC} $LAMBDA_ARN"
echo -e "${CYAN}Region:${NC} $REGION"
echo -e "${CYAN}Trigger:${NC} $SNS_TOPIC_ARN"
echo ""
echo -e "${YELLOW}Variables de Entorno:${NC}"
echo "  - AGENTCORE_MEMORY_ID: $MEMORY_ID"
echo "  - BEDROCK_AGENT_ID: $AGENT_ID"
echo "  - BEDROCK_AGENT_ALIAS_ID: $ALIAS_ID"
echo "  - AWS_REGION: $REGION (reservada, establecida automáticamente por Lambda)"
if [ -n "$WEBHOOK_URL" ]; then
    echo "  - BACKEND_WEBHOOK_URL: $WEBHOOK_URL"
fi
echo ""
echo -e "${CYAN}Próximos pasos:${NC}"
echo "  1. Verifica la Lambda en la consola de AWS"
echo "  2. Prueba enviando un mensaje al SNS Topic"
echo "  3. Revisa los logs en CloudWatch"
echo ""
