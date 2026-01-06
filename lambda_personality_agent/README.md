# Bible Companion - Personality Agent

Sistema de personalidades dinámicas para el Bible Companion AI con memoria persistente y búsqueda semántica.

## Features

- ✅ **4 Companions predefinidos** (Caleb, Ruth, Solomon, Miriam)
- ✅ **Personalidades customizables** (usuarios premium)
- ✅ **Life Stage** basado en edad del usuario
- ✅ **Spiritual Depth** basado en survey
- ✅ **AgentCore Memory** con 3 estrategias:
  - **Summarization** - Resúmenes automáticos de conversaciones
  - **User Preferences** - Extracción de preferencias del usuario
  - **Semantic Search** - Búsqueda inteligente de conversaciones relevantes

## Cómo Funciona

1. **Idioma por defecto: Inglés** - El agente responde en inglés por defecto
2. **Personalidad se inyecta via `userProfile`** - En cada mensaje SNS envías el perfil del usuario
3. **Cambio de preferencias** - Cuando el usuario cambia su companion o configuración, simplemente envías el nuevo `userProfile` en el siguiente mensaje

### Flujo de Inyección de Personalidad

```
Usuario selecciona "Caleb" en la app
        ↓
Backend guarda preferencia en DB
        ↓
Usuario envía mensaje
        ↓
Backend lee preferencias de DB
        ↓
Backend envía SNS con userProfile: { selectedCompanion: "caleb", ... }
        ↓
Lambda construye prompt con personalidad de Caleb
        ↓
Respuesta con voz/estilo de Caleb
```

### Cuándo Re-inyectar Personalidad

- **Cada mensaje**: Siempre envía `userProfile` (el Lambda lo necesita)
- **Cambio de companion**: Usuario cambia de Ruth a Caleb → siguiente mensaje usa Caleb
- **Cambio de preferencias premium**: Usuario ajusta accent/tone → siguiente mensaje refleja cambios
- **Survey completado**: Actualiza `spiritualData` → siguiente mensaje adapta profundidad

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                  │
│  (envía mensaje SNS con userProfile)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SNS Topic                                     │
│         bible-companion-personality-topic                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Lambda: bible-companion-personality                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. Recibe mensaje con userProfile                        │   │
│  │ 2. Construye personalidad (companion + life stage +      │   │
│  │    spiritual depth)                                      │   │
│  │ 3. Lee memoria reciente (AgentCore - últimas sesiones)   │   │
│  │ 4. Busca memorias relevantes (Semantic Search)           │   │
│  │ 5. Enriquece prompt con personalidad + contexto          │   │
│  │ 6. Llama a Bedrock Agent                                 │   │
│  │ 7. Guarda interacción en memoria                         │   │
│  │ 8. Envía respuesta al backend                            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────────────┐
│     Bedrock Agent        │    │      AgentCore Memory            │
│  bible-companion-pers    │    │  memory_bqdqb-jtj3lc48bl         │
│                          │    │                                  │
│  Claude Haiku 4.5        │    │  Strategies:                     │
│                          │    │  • summary_grace_v1 (resúmenes)  │
│                          │    │  • preference_grace_v1 (prefs)   │
│                          │    │  • semantic_grace_v1 (búsqueda)  │
└──────────────────────────┘    └──────────────────────────────────┘
```

## AgentCore Memory

### Estrategias Configuradas

| Estrategia | ID | Función |
|------------|-----|---------|
| **Summarization** | `summary_grace_v1-GQT3I7Ct8f` | Genera resúmenes XML de cada conversación |
| **User Preferences** | `preference_grace_v1-ePMoWwE9Yh` | Extrae preferencias del usuario (idioma, temas, etc.) |
| **Semantic Search** | `semantic_grace_v1-I25PeS4v8Y` | Crea embeddings para búsqueda inteligente |

### Flujo de Memoria

```
Usuario: "Necesito paz en mi vida"
    │
    ├─► Memoria reciente (últimas 3 sesiones, 10 eventos c/u)
    │   └─► "Ayer hablamos de trabajo..."
    │
    └─► Búsqueda semántica
        └─► Encuentra conversación de hace 2 semanas sobre "versículos de paz"
    │
    ▼
Prompt enriquecido con AMBOS contextos → Respuesta más relevante
```

### Permisos IAM Requeridos

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

## Companions Predefinidos (FREE Users)

| Companion | Color | Voz | Tono | Estilo |
|-----------|-------|-----|------|--------|
| **Caleb** | 🔴 Red | Male, American, Joven, Energético | Apasionado | Motivador, orientado a acción |
| **Ruth** | 🟡 Yellow | Female, British, Adulta, Normal | Cálido | Empático, validador |
| **Solomon** | 🔵 Blue | Male, British, Senior, Pausado | Calmado | Reflexivo, hace preguntas |
| **Miriam** | 🟢 Green | Female, Southern, Senior, Pausado | Tierno | Amoroso, reconfortante |

## Opciones Premium (Customizable)

### Gender
- Male / Female

### Accent
- American, British RP, Australian, African American (AAVE)
- Southern US, Canadian, Indian English, Latin American

### Age Vibe
- Young adult (20s), Mature adult (30-50), Senior (60+)

### Speech Speed
- Slow (contemplativo), Normal, Energetic (motivador)

### Emotional Tone
- Calm/soothing, Warm/friendly, Passionate/energetic, Gentle/grandmotherly

### Personality Color
- Red (directo), Yellow (optimista), Green (paciente), Blue (analítico)

## Life Stages (basado en edad)

| Stage | Edad | Enfoque |
|-------|------|---------|
| Explorer | 18-29 | Identidad, propósito, relaciones |
| Builder | 30-45 | Familia, carrera, propósito práctico |
| Guide | 46-69 | Mentoría, transiciones, significado |
| Legacy | 70+ | Reflexión, sabiduría, eternidad |

## Spiritual Stages (survey cada 90 días)

| Tier | Stage | Approach |
|------|-------|----------|
| 1-2 | Awakening/Curious | Lenguaje simple, amor de Dios |
| 3-4 | Seeking/Exploring | Conceptos básicos, preguntas |
| 5-6 | Engaging/Growing | Verdades profundas, conexiones |
| 7-8 | Deepening/Maturing | Temas maduros, liderazgo |
| 9-10 | Flourishing/Abiding | Peer espiritual, misterios |

## Deployment

### Opción Simple (Recomendada)
Usa el agente Bedrock existente y las personalidades se inyectan via prompt:

```powershell
cd lambda_personality_agent
npm install
.\deploy.ps1
```

El Lambda usa el agente original (`OPFJ6RWI2P`) y construye el prompt con la personalidad.

### Opción Avanzada (Agente Dedicado)
Si quieres un agente Bedrock separado con instrucciones de personalidad:

```powershell
.\clone-bedrock-agent.ps1   # Clona el agente
.\deploy.ps1                 # Despliega Lambda
```

Nota: Requiere configurar permisos IAM adicionales para el nuevo agente.

## Configuración del Backend

El backend debe enviar mensajes SNS con este formato:

```json
{
  "conversationId": "conv-123",
  "messageId": "msg-456",
  "userId": "user-789",
  "text": "User's message here",
  "userProfile": {
    "isPremium": false,
    "selectedCompanion": "ruth",
    "age": 35,
    "customPersonality": null,
    "spiritualData": {
      "spiritual_stage_name": "Growing",
      "spiritual_score_percent": 65,
      "spiritual_tier": 6,
      "last_survey_at": "2025-10-01T00:00:00Z"
    }
  }
}
```

### Campos de userProfile

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `isPremium` | boolean | No | Si es usuario premium (default: false) |
| `selectedCompanion` | string | No | "caleb", "ruth", "solomon", "miriam" (default: "ruth") |
| `age` | number | No | Edad del usuario para calcular Life Stage (default: 30) |
| `customPersonality` | object | No | Solo premium: personalidad customizada |
| `spiritualData` | object | No | Datos del survey espiritual |

### Ejemplo: Cambio de Companion

```javascript
// Usuario cambia de Ruth a Caleb en la app
// Backend actualiza DB y envía siguiente mensaje con:
{
  "userProfile": {
    "selectedCompanion": "caleb",  // Cambió de "ruth" a "caleb"
    // ... resto igual
  }
}
// Lambda automáticamente usa personalidad de Caleb
```

### Ejemplo: Usuario Premium con Custom Personality

```json
{
  "userProfile": {
    "isPremium": true,
    "customPersonality": {
      "name": "Grace",
      "gender": "female",
      "accent": "australian",
      "ageVibe": "mature_adult",
      "speechSpeed": "normal",
      "emotionalTone": "warm_friendly",
      "personalityColor": "Yellow"
    }
  }
}
```

## Respuesta al Backend

```json
{
  "eventType": "bedrock_response",
  "conversationId": "conv-123",
  "messageId": "ai-msg-456",
  "responseText": "Respuesta del companion...",
  "companion": {
    "name": "Ruth",
    "lifeStage": "Builder",
    "spiritualStage": "Growing",
    "spiritualTier": 6
  },
  "hasMemoryContext": true,
  "hasSemanticContext": true,
  "processingTimeMs": 2500
}
```

### Campos de Respuesta

| Campo | Descripción |
|-------|-------------|
| `hasMemoryContext` | Si se encontró memoria reciente del usuario |
| `hasSemanticContext` | Si se encontraron conversaciones relevantes via búsqueda semántica |

## Archivos

- `index.js` - Lambda principal con sistema de personalidades
- `personality-api.js` - API para el backend (companions, survey, etc.)
- `clone-bedrock-agent.ps1` - Script para clonar el agente de Bedrock
- `deploy.ps1` - Script de deployment del Lambda
- `package.json` - Dependencias Node.js


## Testing

### Test all 4 companions
```bash
python test_personalities.py
```

This sends test messages via SNS for each companion (Caleb, Ruth, Solomon, Miriam) with different age/spiritual profiles.

### Test single companion directly
```python
import boto3
import json

sns = boto3.client('sns', region_name='us-east-1')

message = {
    "conversationId": "test-123",
    "messageId": "msg-123",
    "userId": "user-123",
    "text": "I'm going through a difficult time at work",
    "userProfile": {
        "isPremium": False,
        "selectedCompanion": "caleb",  # or "ruth", "solomon", "miriam"
        "age": 28,
        "spiritualData": {
            "spiritual_stage_name": "Growing",
            "spiritual_score_percent": 55,
            "spiritual_tier": 5
        }
    }
}

sns.publish(
    TopicArn="arn:aws:sns:us-east-1:124355682808:bible-companion-personality-topic",
    Message=json.dumps(message)
)
```

### Check logs
```bash
aws logs tail "/aws/lambda/bible-companion-personality" --since 5m --region us-east-1
```

## Current Deployment

| Resource | Value |
|----------|-------|
| Lambda | `bible-companion-personality` |
| SNS Topic | `bible-companion-personality-topic` |
| Bedrock Agent ID | `OPFJ6RWI2P` |
| Bedrock Agent Alias | `YWLZEUSKI8` |
| AgentCore Memory ID | `memory_bqdqb-jtj3lc48bl` |
| Semantic Strategy ID | `semantic_grace_v1-I25PeS4v8Y` |
| Summary Strategy ID | `summary_grace_v1-GQT3I7Ct8f` |
| Preference Strategy ID | `preference_grace_v1-ePMoWwE9Yh` |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AGENTCORE_MEMORY_ID` | ID de la memoria AgentCore | `memory_bqdqb-jtj3lc48bl` |
| `BEDROCK_AGENT_ID` | ID del agente Bedrock | Required |
| `BEDROCK_AGENT_ALIAS_ID` | Alias del agente | Required |
| `SEMANTIC_STRATEGY_ID` | ID de la estrategia semántica | `semantic_grace_v1-I25PeS4v8Y` |
| `BACKEND_WEBHOOK_URL` | URL del webhook del backend | Required |
| `WEBHOOK_SECRET` | Secret para autenticar webhook | Optional |
