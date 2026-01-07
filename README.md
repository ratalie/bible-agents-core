# Bible Agents for Bedrock AgentCore

Agentes de IA para guía espiritual usando **Bedrock Agents** con **AgentCore Memory**.

## Inventario de Agentes - Cuenta AWS: 124355682808

### Agentes de Producción

| Agente | Agent ID | Status | Última Actualización |
|--------|----------|--------|---------------------|
| **bible-companion-personality** | `SADSVG3N5Q` | ✅ PREPARED | 2026-01-02 |
| **Bible_App_GraceAI_Chat_Person_v2** (Grace v2) | `NFL5LXYSUW` | ✅ PREPARED | 2026-01-02 |
| **Bible_App_GraceAI_Chat_Claude_Person** (Grace v1) | `OPFJ6RWI2P` | ✅ PREPARED | 2025-09-30 |
| **Bible_App_GraceAI_Chat_Person_Mem_Pers** | `MCP33AOQV8` | ✅ PREPARED | 2025-12-05 |
| **BrotherBen** | `PLGO7CNWUR` | ✅ PREPARED | 2026-01-02 |
| **Bible_App_DailyVerse_Reflection** | `LDJOFRZS0H` | ✅ PREPARED | 2025-11-17 |
| **Bible_App_DailyReflection** | `O4ECQHVBCG` | ✅ PREPARED | 2025-07-21 |
| **Bible_App_DailyVerse** | `AGUM300IVR` | ✅ PREPARED | 2025-07-11 |
| **Bible_App_GraceAI_Path** | `Y3QJS0ZVS7` | ✅ PREPARED | 2025-07-11 |

---

## Agentes Principales - Detalle de Versiones

### 1. Bible Companion Personality Agent
**Agent ID**: `SADSVG3N5Q` | **Modelo**: Claude Haiku 4.5

Sistema completo con personalidades dinámicas y memoria semántica.

#### Versiones
| Versión | Alias | Alias ID | Fecha Creación | Estado |
|---------|-------|----------|----------------|--------|
| **v1** | `production` | `FS3FHAOFWO` | 2026-01-02 | ✅ PREPARED |
| DRAFT | `AgentTestAlias` | `TSTALIASID` | 2026-01-02 | 🧪 TEST |

#### Features
- ✅ 4 Companions predefinidos (Caleb, Ruth, Solomon, Miriam)
- ✅ Personalidades customizables (premium)
- ✅ Life Stage basado en edad
- ✅ Spiritual Depth basado en survey
- ✅ AgentCore Memory con búsqueda semántica

#### Lambda Asociado
- **Función**: `bible-companion-personality`
- **Runtime**: Node.js 20.x
- **Última actualización**: 2026-01-05

---

### 2. Grace AI Chat v2 (Activo en producción)
**Agent ID**: `NFL5LXYSUW` | **Modelo**: Claude Haiku 4.5

Agente principal de chat con personalización v2.

#### Versiones
| Versión | Alias | Alias ID | Fecha Creación | Estado | Notas |
|---------|-------|----------|----------------|--------|-------|
| **v5** 🔥 | `Bible_App_GraceAI_Chat_Person_v2_v4` | `CKLXTRRBZA` | 2026-01-02 | ✅ ACTIVO | Versión actual producción |
| v4 | `Bible_App_GraceAI_Chat_Person_v2_v4` | `CKLXTRRBZA` | 2025-12-15 | ⚠️ REEMPLAZADA | |
| v3 | `Bible_App_GraceAI_Chat_Person_v2_v3` | `PGCL3UGSQ4` | 2025-12-15 | 📦 ARCHIVADA | |
| v2 | `Bible_App_GraceAI_Chat_Person_v2_v2` | `MDOO3WGM66` | 2025-11-25 | 📦 ARCHIVADA | |
| v1 | `Bible_App_GraceAI_Chat_Person_v2_v1` | `DTOKM7QHUW` | 2025-11-06 | 📦 ARCHIVADA | |
| DRAFT | `AgentTestAlias` | `TSTALIASID` | 2025-11-05 | 🧪 TEST | |

#### Lambda Asociado
- **Función**: `gpbible-bedrock-processor-dev`
- **Runtime**: Node.js 18.x
- **Última actualización**: 2026-01-07

---

### 3. Grace AI Chat v1 (Legacy)
**Agent ID**: `OPFJ6RWI2P` | **Modelo**: Claude Haiku 4.5

Primera versión del chat personalizado (legacy, en transición).

#### Versiones
| Versión | Alias | Alias ID | Fecha Creación | Estado |
|---------|-------|----------|----------------|--------|
| v3 | `Bible_App_GraceAI_Chat_Claude_Personv3` | `2NUF6QJQQB` | 2025-09-30 | ⚠️ LEGACY |
| v2 | `Bible_App_GraceAI_Chat_Claude_Personv2` | `GUQFFT9MNM` | 2025-09-23 | 📦 ARCHIVADA |
| v1 | `Bible_App_GraceAI_Chat_Claude_Personv1` | `YWLZEUSKI8` | 2025-07-11 | 📦 ARCHIVADA |
| DRAFT | `AgentTestAlias` | `TSTALIASID` | 2025-07-11 | 🧪 TEST |

---

## Lambdas Disponibles

### Lambda con Personalidades
**Función**: `bible-companion-personality`
- **Runtime**: Node.js 20.x
- **Última actualización**: 2026-01-05 23:39:54
- **Directorio**: `lambda_personality_agent/`
- **Features**:
  - ✅ AgentCore Memory con búsqueda semántica
  - ✅ Sistema de personalidades dinámicas
  - ✅ 4 companions predefinidos

### Lambda con Memoria (Sin Personalidades)
**Función**: `gpbible-bedrock-processor-memory-test`
- **Runtime**: Node.js 18.x
- **Última actualización**: 2026-01-05 23:42:20
- **Directorio**: `lambda_bedrock_with_memory/`
- **Features**:
  - ✅ AgentCore Memory
  - ✅ Búsqueda semántica
  - ❌ Sin personalidades

### Lambda Principal (Dev/Prod)
**Función**: `gpbible-bedrock-processor-dev`
- **Runtime**: Node.js 18.x
- **Última actualización**: 2026-01-07 15:53:23
- **Features**: Procesador principal para Grace AI v2

### Otras Lambdas
| Función | Runtime | Propósito |
|---------|---------|-----------|
| `bible-agentcore-memory` | Python 3.11 | Pruebas AgentCore |
| `gpbible-send-emails` | Node.js 20.x | Envío de emails |
| `gpbible-process-emails` | Node.js 22.x | Procesamiento emails |
| `gpbible-send-pushNotifications` | Node.js 20.x | Push notifications |

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
