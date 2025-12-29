# Bedrock Agents vs AgentCore - Arquitectura y Recursos

## ⚠️ IMPORTANTE: Son DOS Servicios DIFERENTES

| Servicio | Descripción | Console URL |
|----------|-------------|-------------|
| **Amazon Bedrock Agents** | Agentes conversacionales administrados (más antiguo) | `console.aws.amazon.com/bedrock/` |
| **Amazon Bedrock AgentCore** | Infraestructura para agentes (nuevo, re:Invent 2025) | `console.aws.amazon.com/bedrock-agentcore/` |

---

## TUS RECURSOS ACTUALES

### 1. Bedrock Agents (lo que tienes activo)

| Recurso | ID/ARN | Endpoint |
|---------|--------|----------|
| **Agent ID** | `MCP33AOQV8` | - |
| **Agent ARN** | `arn:aws:bedrock:us-east-1:124355682808:agent/MCP33AOQV8` | - |
| **Alias Producción** | `IYFPFU7ZC4` (Bible_App_Grace_Chat_Mem_Detailv1) | - |
| **Alias Test** | `TSTALIASID` (AgentTestAlias) | - |
| **Modelo** | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | - |
| **API Endpoint** | - | `bedrock-agent-runtime.us-east-1.amazonaws.com` |

**Cliente boto3**: `bedrock-agent-runtime`

```python
client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
client.invoke_agent(agentId='MCP33AOQV8', agentAliasId='IYFPFU7ZC4', ...)
```

### 2. AgentCore (configurado pero separado)

| Recurso | ID/ARN | Endpoint |
|---------|--------|----------|
| **Runtime ID** | `bible_companion-GrIcKjGWbo` | - |
| **Runtime ARN** | `arn:aws:bedrock-agentcore:us-east-1:124355682808:runtime/bible_companion-GrIcKjGWbo` | - |
| **Memory ID** | `memory_bqdqb-jtj3lc48bl` | - |
| **API Endpoint** | - | `bedrock-agentcore.us-east-1.amazonaws.com` |

**Cliente boto3**: `bedrock-agentcore`

```python
client = boto3.client('bedrock-agentcore', region_name='us-east-1')
client.invoke_agent_runtime(agentRuntimeArn='arn:aws:bedrock-agentcore:...', ...)
```

---

## TABLA COMPARATIVA: Bedrock Agents vs AgentCore

| Característica | Bedrock Agents | AgentCore |
|----------------|----------------|-----------|
| **Lanzamiento** | 2023 | re:Invent 2025 (Preview) |
| **Tipo** | Agentes conversacionales administrados | Infraestructura para agentes |
| **Memoria** | `SESSION_SUMMARY` (resúmenes) | Memory con estrategias (User Preferences, Summarization) |
| **Runtime** | Administrado por AWS | Container-based, tú defines el código |
| **Framework** | Solo Bedrock | Agnóstico (Strands, LangGraph, CrewAI, etc.) |
| **Console** | `/bedrock/` | `/bedrock-agentcore/` |
| **Cliente boto3** | `bedrock-agent-runtime` | `bedrock-agentcore` |
| **Necesita Lambda** | Solo para Action Groups | No, tiene su propio runtime |

---

## ARQUITECTURA ACTUAL (Bedrock Agents)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              TU APLICACIÓN                                       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ invoke_agent()
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    AMAZON BEDROCK AGENTS                                         │
│                    Endpoint: bedrock-agent-runtime.us-east-1.amazonaws.com       │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │  Agent: Bible_App_GraceAI_Chat_Person_Mem_Pers                             │ │
│  │  ID: MCP33AOQV8                                                            │ │
│  │  ARN: arn:aws:bedrock:us-east-1:124355682808:agent/MCP33AOQV8              │ │
│  │                                                                            │ │
│  │  ┌──────────────────────┐    ┌──────────────────────────────────────────┐ │ │
│  │  │  Alias: IYFPFU7ZC4   │    │  Memoria (SESSION_SUMMARY)               │ │ │
│  │  │  (Producción v1)     │    │  • 30 días retención                     │ │ │
│  │  ├──────────────────────┤    │  • 20 sesiones máx por usuario           │ │ │
│  │  │  Alias: TSTALIASID   │    │  • Variables: $memory_content$, etc.     │ │ │
│  │  │  (Test/DRAFT)        │    └──────────────────────────────────────────┘ │ │
│  │  └──────────────────────┘                                                  │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                           │
│                                      ▼                                           │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │  Modelo: us.anthropic.claude-haiku-4-5-20251001-v1:0                       │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## ARQUITECTURA AGENTCORE (Separada)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              TU APLICACIÓN                                       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ invoke_agent_runtime()
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    AMAZON BEDROCK AGENTCORE                                      │
│                    Endpoint: bedrock-agentcore.us-east-1.amazonaws.com           │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │  Runtime: bible_companion-GrIcKjGWbo                                       │ │
│  │  ARN: arn:aws:bedrock-agentcore:us-east-1:124355682808:runtime/...         │ │
│  │  Handler: agentcore_runtime.bible_companion                                │ │
│  │  Source: s3://bible-companion-deployment-2025/agentcore_runtime.py         │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                           │
│                                      ▼                                           │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │  Memory: memory_bqdqb-jtj3lc48bl                                           │ │
│  │  Estrategias: User Preferences + Summarization                             │ │
│  │  Retención: 90 días                                                        │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                           │
│                                      ▼                                           │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │  MySQL: gpbible-prod-mysql.c4zg06smsewh.us-east-1.rds.amazonaws.com        │ │
│  │  (User preferences, Bible versions, Denominations)                         │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Conceptos Clave (Bedrock Agents)

### 1. sessionId vs memoryId

| Concepto | Propósito | Ejemplo | Persistencia |
|----------|-----------|---------|--------------|
| `sessionId` | Identifica UNA conversación | `"conv-2024-12-29-abc123"` | Temporal (mientras dura el chat) |
| `memoryId` | Identifica UN USUARIO | `"user-maria-123"` | Permanente (30 días por defecto) |

```
Usuario María tiene:
├── memoryId: "user-maria-123" (siempre el mismo)
│   ├── sessionId: "conv-001" (lunes)
│   ├── sessionId: "conv-002" (martes)  
│   └── sessionId: "conv-003" (hoy)
```

### 2. Aliases del Agente

Tu agente tiene 2 aliases:

| Alias | ID | Versión | Uso |
|-------|-----|---------|-----|
| `AgentTestAlias` | `TSTALIASID` | DRAFT | Pruebas/desarrollo |
| `Bible_App_Grace_Chat_Mem_Detailv1` | `IYFPFU7ZC4` | v1 | **Producción** |

**Recomendación**: Usa `IYFPFU7ZC4` en producción para estabilidad.

---

## Flujo de la Memoria

```
PRIMERA SESIÓN DEL USUARIO
──────────────────────────
1. App invoca agente con memoryId="user-123", sessionId="session-A"
2. Bedrock busca memoria para memoryId="user-123" → No encuentra nada
3. Agente responde sin contexto previo
4. Usuario hace varias preguntas en la sesión
5. Al terminar sesión, Bedrock genera resumen automático y lo guarda

SEGUNDA SESIÓN (días después)
─────────────────────────────
1. App invoca agente con memoryId="user-123", sessionId="session-B" (nuevo)
2. Bedrock busca memoria para memoryId="user-123" → ENCUENTRA resumen de session-A
3. Inyecta resumen en $memory_content$ del prompt
4. Agente responde CON contexto de conversaciones anteriores
5. Al terminar, guarda nuevo resumen
```

---

## Código de Integración

### Invocar el Agente (con memoria)

```python
import boto3

client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

def chat_with_agent(user_id: str, session_id: str, message: str):
    """
    Invoca el agente con memoria persistente por usuario.
    
    Args:
        user_id: ID único del usuario (se usa como memoryId)
        session_id: ID de la sesión actual de chat
        message: Mensaje del usuario
    """
    response = client.invoke_agent(
        agentId='MCP33AOQV8',
        agentAliasId='IYFPFU7ZC4',  # Alias de producción
        sessionId=session_id,
        memoryId=user_id,  # ← CLAVE: Esto activa la memoria
        inputText=message
    )
    
    # Leer respuesta del stream
    full_response = ""
    for event in response['completion']:
        if 'chunk' in event:
            full_response += event['chunk']['bytes'].decode('utf-8')
    
    return full_response
```

### Consultar Memoria de un Usuario

```python
def get_user_memory(user_id: str):
    """Obtiene todos los resúmenes de sesión de un usuario."""
    
    response = client.get_agent_memory(
        agentId='MCP33AOQV8',
        agentAliasId='IYFPFU7ZC4',
        memoryId=user_id,
        memoryType='SESSION_SUMMARY',
        maxItems=20
    )
    
    memories = []
    for content in response.get('memoryContents', []):
        if 'sessionSummary' in content:
            summary = content['sessionSummary']
            memories.append({
                'sessionId': summary.get('sessionId'),
                'startTime': summary.get('sessionStartTime'),
                'summary': summary.get('summaryText')
            })
    
    return memories
```

### Eliminar Memoria de un Usuario

```python
def delete_user_memory(user_id: str):
    """Elimina toda la memoria de un usuario (GDPR, etc.)."""
    
    client.delete_agent_memory(
        agentId='MCP33AOQV8',
        agentAliasId='IYFPFU7ZC4',
        memoryId=user_id
    )
```

---

## Configuración Actual del Agente

```json
{
  "memoryConfiguration": {
    "enabledMemoryTypes": ["SESSION_SUMMARY"],
    "storageDays": 30,
    "sessionSummaryConfiguration": {
      "maxRecentSessions": 20
    }
  }
}
```

### Modificar Configuración (si necesitas)

```bash
aws bedrock-agent update-agent \
  --agent-id MCP33AOQV8 \
  --agent-name "Bible_App_GraceAI_Chat_Person_Mem_Pers" \
  --memory-configuration '{
    "enabledMemoryTypes": ["SESSION_SUMMARY"],
    "storageDays": 365,
    "sessionSummaryConfiguration": {
      "maxRecentSessions": 50
    }
  }'
```

---

## Prompt de Resumen de Memoria

El agente usa este prompt (MEMORY_SUMMARIZATION) para generar resúmenes:

```
Genera un resumen XML con:
- <topic name='user goals'>: Objetivos y preguntas del usuario
- <topic name='assistant actions'>: Acciones tomadas por el asistente
```

El resumen se guarda automáticamente y se inyecta en `$memory_content$` en futuras sesiones.

---

## ¿Necesito Lambda?

**NO para la memoria básica.** La memoria de AgentCore es nativa.

**SÍ necesitas Lambda si quieres:**
- Action Groups (herramientas personalizadas)
- Guardar datos adicionales en DynamoDB
- Integrar con APIs externas
- Lógica de negocio personalizada

---

## Resumen de Recursos

### Bedrock Agents (Activo)

| Recurso | Valor |
|---------|-------|
| Agent ID | `MCP33AOQV8` |
| Agent ARN | `arn:aws:bedrock:us-east-1:124355682808:agent/MCP33AOQV8` |
| Alias Producción | `IYFPFU7ZC4` |
| Alias Test | `TSTALIASID` |
| Endpoint | `bedrock-agent-runtime.us-east-1.amazonaws.com` |
| Cliente boto3 | `bedrock-agent-runtime` |
| Memoria | SESSION_SUMMARY (30 días, 20 sesiones) |
| ¿Necesita Lambda? | NO (memoria nativa) |

### AgentCore (Separado)

| Recurso | Valor |
|---------|-------|
| Runtime ID | `bible_companion-GrIcKjGWbo` |
| Runtime ARN | `arn:aws:bedrock-agentcore:us-east-1:124355682808:runtime/bible_companion-GrIcKjGWbo` |
| Memory ID | `memory_bqdqb-jtj3lc48bl` |
| Endpoint | `bedrock-agentcore.us-east-1.amazonaws.com` |
| Cliente boto3 | `bedrock-agentcore` |
| Memoria | User Preferences + Summarization (90 días) |
| ¿Necesita Lambda? | NO (tiene su propio runtime) |

---

## ¿Cuál usar?

| Escenario | Recomendación |
|-----------|---------------|
| Agente conversacional simple | **Bedrock Agents** (MCP33AOQV8) |
| Necesitas memoria avanzada con estrategias | **AgentCore** (memory_bqdqb-jtj3lc48bl) |
| Quieres usar LangGraph, CrewAI, etc. | **AgentCore** |
| Quieres algo rápido y administrado | **Bedrock Agents** |

**Actualmente tu app usa Bedrock Agents.** AgentCore está configurado pero es un servicio separado.

---

## Lambda Clonado para Pruebas con AgentCore Memory

### ¿Qué se hizo?

Se creó un **clon** del Lambda de producción para probar la integración con AgentCore Memory sin afectar el sistema actual.

| Lambda | Propósito | Estado |
|--------|-----------|--------|
| `gpbible-bedrock-processor-dev` | **ORIGINAL** - Producción | ⚠️ NO TOCAR |
| `gpbible-bedrock-processor-memory-test` | **CLON** - Pruebas con memoria | ✅ Para pruebas |

### Detalles del Clon

| Propiedad | Valor |
|-----------|-------|
| **Nombre** | `gpbible-bedrock-processor-memory-test` |
| **ARN** | `arn:aws:lambda:us-east-1:124355682808:function:gpbible-bedrock-processor-memory-test` |
| **Creado** | 29 de diciembre 2025 |
| **Basado en** | `gpbible-bedrock-processor-dev` (21 nov 2025) |
| **Runtime** | nodejs18.x |
| **Memory ID** | `memory_bqdqb-jtj3lc48bl` |

### ¿Qué se agregó al clon?

1. **Lectura de memoria** - Antes de llamar al agente, lee conversaciones anteriores del usuario
2. **Enriquecimiento de prompt** - Agrega contexto de memoria al mensaje
3. **Guardado de interacciones** - Guarda cada mensaje (usuario + asistente) en AgentCore Memory
4. **Variable de entorno** - `AGENTCORE_MEMORY_ID=memory_bqdqb-jtj3lc48bl`
5. **Permisos IAM** - Política `AgentCoreMemoryAccess` para acceder a AgentCore

### Flujo del Lambda con Memoria

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FLUJO DEL LAMBDA                                    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  1. RECIBE MENSAJE (SNS)                                                         │
│     { conversationId, messageId, userId, text }                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  2. LEE MEMORIA DEL USUARIO                                                      │
│     AgentCore Memory → list_sessions(userId) → list_events(sessionId)           │
│     Obtiene últimas 3 sesiones, 10 eventos cada una                             │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  3. ENRIQUECE EL PROMPT                                                          │
│     Si hay memoria:                                                              │
│       "[Conversaciones anteriores del usuario]                                   │
│        USER: mensaje anterior...                                                 │
│        ASSISTANT: respuesta anterior...                                          │
│        [Fin de contexto previo]                                                  │
│        Usuario dice: {mensaje actual}"                                           │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  4. LLAMA A BEDROCK AGENT                                                        │
│     invoke_agent(agentId, aliasId, sessionId, enrichedText)                     │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  5. GUARDA EN AGENTCORE MEMORY                                                   │
│     create_event(userId, sessionId, userMessage, role=USER)                     │
│     create_event(userId, sessionId, assistantResponse, role=ASSISTANT)          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  6. ENVÍA RESPUESTA AL BACKEND                                                   │
│     POST webhook con: responseText, hasMemoryContext, processingTimeMs          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Código del Lambda (ubicación)

```
lambda_bedrock_with_memory/
├── index.js          # Código con integración AgentCore Memory
├── package.json      # Dependencias
└── deploy.ps1        # Script de despliegue
```

### Cómo probar

**Opción 1: Script Python (recomendado)**
```bash
python test_lambda_memory.py
```

**Opción 2: AWS CLI**
```bash
# Invocar el Lambda de prueba directamente
aws lambda invoke \
  --function-name gpbible-bedrock-processor-memory-test \
  --payload '{"Records":[{"Sns":{"Message":"{\"conversationId\":\"test-123\",\"messageId\":\"msg-001\",\"userId\":\"user-test-001\",\"text\":\"Hola, necesito guía espiritual\"}"}}]}' \
  response.json

# Ver logs
aws logs tail /aws/lambda/gpbible-bedrock-processor-memory-test --follow
```

### Resultados de pruebas

Ver: [logs/test_results_2025-12-29.txt](https://github.com/ratalie/bible-agents-core/blob/main/logs/test_results_2025-12-29.txt)

| Funcionalidad | Estado |
|---------------|--------|
| Leer memoria (usuario nuevo) | ✅ |
| Guardar mensaje usuario | ✅ |
| Guardar respuesta asistente | ✅ |
| Leer memoria (usuario existente) | ✅ |
| Enriquecer prompt con contexto | ✅ |
| Invocar Bedrock Agent | ✅ |

### Para pasar a producción

Cuando las pruebas sean exitosas, actualiza el Lambda original:

```bash
# SOLO cuando estés seguro
aws lambda update-function-code \
  --function-name gpbible-bedrock-processor-dev \
  --zip-file fileb://lambda_bedrock_with_memory/lambda_memory.zip
```


---

## Arquitectura Final

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    TU APP                                            │
│                              (Mobile / Web)                                          │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ SNS Message
                                       │ {userId, conversationId, text}
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    LAMBDA: gpbible-bedrock-processor-memory-test                     │
│                    (Clon para pruebas con AgentCore Memory)                          │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │  1. RECIBE MENSAJE                                                             │ │
│  │     Extrae: userId, conversationId, text                                       │ │
│  └────────────────────────────────────────────────────────────────────────────────┘ │
│                                       │                                              │
│                                       ▼                                              │
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │  2. LEE MEMORIA (AgentCore)                                                    │ │
│  │     list_sessions(userId) → list_events(sessionId)                            │ │
│  │     Obtiene últimas 3 sesiones, 10 eventos cada una                           │ │
│  └────────────────────────────────────────────────────────────────────────────────┘ │
│                                       │                                              │
│                                       ▼                                              │
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │  3. ENRIQUECE PROMPT                                                           │ │
│  │     "[Conversaciones anteriores]                                               │ │
│  │      USER: mensaje previo...                                                   │ │
│  │      ASSISTANT: respuesta previa...                                            │ │
│  │      [Fin contexto]                                                            │ │
│  │      Usuario dice: {mensaje actual}"                                           │ │
│  └────────────────────────────────────────────────────────────────────────────────┘ │
│                                       │                                              │
│                                       ▼                                              │
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │  4. INVOCA BEDROCK AGENT                                                       │ │
│  │     Agent ID: OPFJ6RWI2P                                                       │ │
│  │     Alias: YWLZEUSKI8                                                          │ │
│  └────────────────────────────────────────────────────────────────────────────────┘ │
│                                       │                                              │
│                                       ▼                                              │
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │  5. GUARDA EN MEMORIA (AgentCore)                                              │ │
│  │     create_event(userId, sessionId, userMessage, role=USER)                   │ │
│  │     create_event(userId, sessionId, assistantResponse, role=ASSISTANT)        │ │
│  └────────────────────────────────────────────────────────────────────────────────┘ │
│                                       │                                              │
│                                       ▼                                              │
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │  6. ENVÍA RESPUESTA                                                            │ │
│  │     POST webhook → Backend                                                     │ │
│  └────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    │                                     │
                    ▼                                     ▼
┌───────────────────────────────────┐   ┌───────────────────────────────────────────┐
│      BEDROCK AGENT                │   │         AGENTCORE MEMORY                  │
│      ID: OPFJ6RWI2P               │   │         ID: memory_bqdqb-jtj3lc48bl       │
│      Alias: YWLZEUSKI8            │   │                                           │
│                                   │   │   ┌─────────────────────────────────────┐ │
│   Modelo: Claude Haiku 4.5        │   │   │  user-natalie-test                  │ │
│                                   │   │   │  ├── session-conv-001               │ │
│   Prompt: Bible Companion         │   │   │  │   ├── USER: "Hola..."            │ │
│   con variables de memoria        │   │   │  │   └── ASSISTANT: "Welcome..."    │ │
│   $memory_content$                │   │   │  └── session-conv-002               │ │
│   $memory_guideline$              │   │   │      ├── USER: "Qué versículo..."   │ │
│                                   │   │   │      └── ASSISTANT: "Te recomiendo."│ │
└───────────────────────────────────┘   │   └─────────────────────────────────────┘ │
                                        └───────────────────────────────────────────┘
```

---

## Archivos del Proyecto

| Archivo | Descripción | Link |
|---------|-------------|------|
| `AGENTCORE_MEMORY_ARCHITECTURE.md` | Esta documentación | [Ver](https://github.com/ratalie/bible-agents-core/blob/main/AGENTCORE_MEMORY_ARCHITECTURE.md) |
| `test_lambda_memory.py` | Script de prueba | [Ver](https://github.com/ratalie/bible-agents-core/blob/main/test_lambda_memory.py) |
| `logs/test_results_2025-12-29.txt` | Resultados de pruebas | [Ver](https://github.com/ratalie/bible-agents-core/blob/main/logs/test_results_2025-12-29.txt) |
| `lambda_bedrock_with_memory/index.js` | Código del Lambda con memoria | [Ver](https://github.com/ratalie/bible-agents-core/blob/main/lambda_bedrock_with_memory/index.js) |
| `lambda_bedrock_with_memory/package.json` | Dependencias | [Ver](https://github.com/ratalie/bible-agents-core/blob/main/lambda_bedrock_with_memory/package.json) |
| `lambda_bedrock_with_memory/deploy.ps1` | Script de despliegue | [Ver](https://github.com/ratalie/bible-agents-core/blob/main/lambda_bedrock_with_memory/deploy.ps1) |
| `agentcore-policy.json` | Política IAM para AgentCore | [Ver](https://github.com/ratalie/bible-agents-core/blob/main/agentcore-policy.json) |

```
bible/
├── AGENTCORE_MEMORY_ARCHITECTURE.md
├── test_lambda_memory.py
├── logs/
│   └── test_results_2025-12-29.txt
├── lambda_bedrock_with_memory/
│   ├── index.js
│   ├── package.json
│   └── deploy.ps1
└── agentcore-policy.json
```

---

## Comandos Útiles

```bash
# Ver memoria de un usuario
python -c "
import boto3
client = boto3.client('bedrock-agentcore', region_name='us-east-1')
sessions = client.list_sessions(memoryId='memory_bqdqb-jtj3lc48bl', actorId='USER_ID')
print(sessions)
"

# Ver logs del Lambda
aws logs tail /aws/lambda/gpbible-bedrock-processor-memory-test --follow

# Listar actores (usuarios) en memoria
aws bedrock-agentcore list-actors --memory-id memory_bqdqb-jtj3lc48bl
```
