# Bible Agents for Bedrock AgentCore

Agentes de IA para guía espiritual usando **Bedrock Agents** con **AgentCore Memory**.

## Lambdas Disponibles

### 1. Bible Companion Personality (`lambda_personality_agent/`)
Lambda completo con personalidades dinámicas y memoria semántica.

- **Lambda**: `bible-companion-personality`
- **Features**:
  - ✅ 4 Companions predefinidos (Caleb, Ruth, Solomon, Miriam)
  - ✅ Personalidades customizables (premium)
  - ✅ Life Stage basado en edad
  - ✅ Spiritual Depth basado en survey
  - ✅ AgentCore Memory con búsqueda semántica

### 2. Bible Companion Memory (`lambda_bedrock_with_memory/`)
Lambda con memoria pero sin personalidades.

- **Lambda**: `gpbible-bedrock-processor-memory-test`
- **Features**:
  - ✅ AgentCore Memory
  - ✅ Búsqueda semántica
  - ❌ Sin personalidades

### 3. Verse of the Day (`agents/verse-of-the-day/`)
Agente simple para versículos diarios.

## AgentCore Memory

### Configuración Actual

| Resource | Value |
|----------|-------|
| Memory ID | `memory_bqdqb-jtj3lc48bl` |
| Retención | 90 días |
| Cuenta AWS | `124355682808` |

### Estrategias Configuradas

| Estrategia | ID | Tipo | Función |
|------------|-----|------|---------|
| **Summarization** | `summary_grace_v1-GQT3I7Ct8f` | SUMMARIZATION | Resúmenes XML de conversaciones |
| **User Preferences** | `preference_grace_v1-ePMoWwE9Yh` | USER_PREFERENCE | Extrae preferencias del usuario |
| **Semantic Search** | `semantic_grace_v1-I25PeS4v8Y` | SEMANTIC | Embeddings para búsqueda inteligente |

### Flujo de Memoria

```
Usuario envía mensaje
    │
    ├─► getUserMemory() - Lee últimas 3 sesiones
    │
    └─► getSemanticMemory() - Busca conversaciones relevantes
    │
    ▼
Prompt enriquecido con contexto → Bedrock Agent → Respuesta
    │
    ▼
saveToMemory() - Guarda USER + ASSISTANT en AgentCore
    │
    ▼
AgentCore ejecuta estrategias automáticamente:
  • Genera resumen de la conversación
  • Extrae preferencias del usuario
  • Crea embeddings para búsqueda futura
```

## Bedrock Agent

| Resource | Value |
|----------|-------|
| Agent ID | `OPFJ6RWI2P` |
| Agent Alias | `YWLZEUSKI8` |
| Modelo | Claude Haiku 4.5 |

## Deployment

### Lambda Personality (recomendado)
```powershell
cd lambda_personality_agent
npm install
.\deploy.ps1
```

### Lambda Memory Only
```powershell
cd lambda_bedrock_with_memory
npm install
Compress-Archive -Path index.js, package.json, node_modules -DestinationPath lambda_memory.zip -Force
aws lambda update-function-code --function-name gpbible-bedrock-processor-memory-test --zip-file fileb://lambda_memory.zip --region us-east-1 --profile gpbible
```

## IAM Permissions

El rol del Lambda necesita estos permisos para AgentCore:

```json
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
                "bedrock-agentcore:ListActors",
                "bedrock-agentcore:RetrieveMemoryRecords",
                "bedrock-agentcore:ListMemoryRecords"
            ],
            "Resource": "*"
        }
    ]
}
```

## AWS Profiles

| Profile | Account | Uso |
|---------|---------|-----|
| `gpbible` | `124355682808` | Producción (AgentCore, Lambdas) |
| `darshana-nataliegil` | `814092323470` | Darshana |

## Testing

### Test Personalidades
```bash
cd lambda_personality_agent
python test_personalities.py
```

### Test Directo
```bash
aws lambda invoke --function-name bible-companion-personality --payload fileb://test_invoke.json --profile gpbible --region us-east-1 response.json
```

### Ver Logs
```bash
aws logs tail "/aws/lambda/bible-companion-personality" --since 5m --region us-east-1 --profile gpbible
```

## Documentación Adicional

- `lambda_personality_agent/README.md` - Detalles del sistema de personalidades
- `lambda_bedrock_with_memory/README.md` - Lambda de solo memoria
- `AGENTCORE_MEMORY_ARCHITECTURE.md` - Arquitectura completa de memoria
- `AGENTCORE_DEPLOYMENT_GUIDE.md` - Guía de deployment
