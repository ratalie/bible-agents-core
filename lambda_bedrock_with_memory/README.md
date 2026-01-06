# Bible Companion - Memory Lambda

Lambda para Bedrock Agent con AgentCore Memory integrado. Versión sin personalidades, solo memoria persistente.

## Features

- ✅ **AgentCore Memory** con 3 estrategias automáticas
- ✅ **Memoria reciente** - Últimas conversaciones del usuario
- ✅ **Búsqueda semántica** - Encuentra conversaciones relevantes al tema actual
- ✅ **Guardado automático** - Cada interacción se guarda en memoria

## Diferencia con lambda_personality_agent

| Feature | Este Lambda | lambda_personality_agent |
|---------|-------------|--------------------------|
| Memoria AgentCore | ✅ | ✅ |
| Búsqueda semántica | ✅ | ✅ |
| Personalidades | ❌ | ✅ 4 companions + custom |
| Life Stage | ❌ | ✅ |
| Spiritual Depth | ❌ | ✅ |

**Usa este Lambda** si solo necesitas memoria sin el sistema de personalidades.

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                  │
│  (envía mensaje SNS)                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Lambda: gpbible-bedrock-processor-memory-test       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. Recibe mensaje de SNS                                 │   │
│  │ 2. Lee memoria reciente (últimas 3 sesiones)             │   │
│  │ 3. Busca memorias relevantes (Semantic Search)           │   │
│  │ 4. Enriquece prompt con contexto                         │   │
│  │ 5. Llama a Bedrock Agent                                 │   │
│  │ 6. Guarda interacción en memoria                         │   │
│  │ 7. Envía respuesta al backend                            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────────────┐
│     Bedrock Agent        │    │      AgentCore Memory            │
│  OPFJ6RWI2P              │    │  memory_bqdqb-jtj3lc48bl         │
│                          │    │                                  │
│  Claude Haiku 4.5        │    │  Strategies:                     │
│                          │    │  • summary_grace_v1 (resúmenes)  │
│                          │    │  • preference_grace_v1 (prefs)   │
│                          │    │  • semantic_grace_v1 (búsqueda)  │
└──────────────────────────┘    └──────────────────────────────────┘
```

## AgentCore Memory Strategies

| Estrategia | ID | Función |
|------------|-----|---------|
| **Summarization** | `summary_grace_v1-GQT3I7Ct8f` | Genera resúmenes XML de conversaciones |
| **User Preferences** | `preference_grace_v1-ePMoWwE9Yh` | Extrae preferencias del usuario |
| **Semantic Search** | `semantic_grace_v1-I25PeS4v8Y` | Embeddings para búsqueda inteligente |

## Flujo de Memoria

```
Usuario: "Necesito paz en mi vida"
    │
    ├─► Memoria reciente (últimas 3 sesiones)
    │   └─► Conversaciones recientes
    │
    └─► Búsqueda semántica
        └─► Encuentra conversaciones pasadas sobre "paz", "versículos", etc.
    │
    ▼
Prompt enriquecido → Bedrock Agent → Respuesta contextualizada
```

## Deployment

```powershell
cd lambda_bedrock_with_memory
npm install
.\deploy.ps1
```

O manualmente:

```powershell
# Crear zip
Compress-Archive -Path index.js, package.json, node_modules -DestinationPath lambda_memory.zip -Force

# Actualizar Lambda
aws lambda update-function-code `
    --function-name gpbible-bedrock-processor-memory-test `
    --zip-file fileb://lambda_memory.zip `
    --region us-east-1 `
    --profile gpbible
```

## Mensaje SNS Esperado

```json
{
  "conversationId": "conv-123",
  "messageId": "msg-456",
  "userId": "user-789",
  "text": "User's message here"
}
```

## Respuesta al Backend

```json
{
  "eventType": "bedrock_response",
  "conversationId": "conv-123",
  "messageId": "ai-msg-456",
  "responseText": "Respuesta del agente...",
  "hasMemoryContext": true,
  "hasSemanticContext": true,
  "processingTimeMs": 2500,
  "tokensUsed": {
    "input": 500,
    "output": 200
  }
}
```

## Current Deployment

| Resource | Value |
|----------|-------|
| Lambda | `gpbible-bedrock-processor-memory-test` |
| Bedrock Agent ID | `OPFJ6RWI2P` |
| Bedrock Agent Alias | `YWLZEUSKI8` |
| AgentCore Memory ID | `memory_bqdqb-jtj3lc48bl` |
| Semantic Strategy ID | `semantic_grace_v1-I25PeS4v8Y` |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AGENTCORE_MEMORY_ID` | ID de la memoria AgentCore | `memory_bqdqb-jtj3lc48bl` |
| `BEDROCK_AGENT_ID` | ID del agente Bedrock | Required |
| `BEDROCK_AGENT_ALIAS_ID` | Alias del agente | Required |
| `SEMANTIC_STRATEGY_ID` | ID de la estrategia semántica | `semantic_grace_v1-I25PeS4v8Y` |
| `BACKEND_WEBHOOK_URL` | URL del webhook del backend | Required |
| `WEBHOOK_SECRET` | Secret para autenticar webhook | Optional |

## IAM Permissions

El rol del Lambda necesita:

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

## Testing

```python
import boto3
import json

lambda_client = boto3.client('lambda', region_name='us-east-1')

payload = {
    "Records": [{
        "Sns": {
            "Message": json.dumps({
                "conversationId": "test-123",
                "messageId": "msg-123",
                "userId": "test-user",
                "text": "Necesito guía espiritual"
            })
        }
    }]
}

response = lambda_client.invoke(
    FunctionName='gpbible-bedrock-processor-memory-test',
    Payload=json.dumps(payload)
)

print(response['Payload'].read().decode())
```

## Logs

```bash
aws logs tail "/aws/lambda/gpbible-bedrock-processor-memory-test" --since 5m --region us-east-1 --profile gpbible
```
