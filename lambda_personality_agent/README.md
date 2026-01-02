# Bible Companion - Personality Agent

Sistema de personalidades dinámicas para el Bible Companion AI.

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
│  │ 3. Lee memoria del usuario (AgentCore)                   │   │
│  │ 4. Enriquece prompt con personalidad + contexto          │   │
│  │ 5. Llama a Bedrock Agent                                 │   │
│  │ 6. Guarda interacción en memoria                         │   │
│  │ 7. Envía respuesta al backend                            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│           Bedrock Agent: bible-companion-personality             │
│  (Instrucciones con sistema de personalidad integrado)          │
└─────────────────────────────────────────────────────────────────┘
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
  "processingTimeMs": 2500
}
```

## Archivos

- `index.js` - Lambda principal con sistema de personalidades
- `personality-api.js` - API para el backend (companions, survey, etc.)
- `clone-bedrock-agent.ps1` - Script para clonar el agente de Bedrock
- `deploy.ps1` - Script de deployment del Lambda
- `package.json` - Dependencias Node.js
