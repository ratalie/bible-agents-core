# Lambda: Bedrock Agent con AgentCore Memory

## Introducción

Este Lambda de AWS integra **Bedrock Agent** con **AgentCore Memory** para proporcionar conversaciones contextuales y persistentes. El Lambda actúa como un procesador intermedio que:

- **Mantiene memoria conversacional** por sesión usando AgentCore Memory
- **Enriquece las solicitudes** al Bedrock Agent con contexto de conversaciones previas
- **Persiste todas las interacciones** para mantener continuidad en futuras conversaciones
- **Procesa mensajes asíncronos** recibidos vía SNS (Simple Notification Service)

### Características Principales

- ✅ Memoria aislada por conversación (cada `conversationId` tiene su propia sesión)
- ✅ Recuperación de hasta 30 eventos (mensajes) de la conversación actual
- ✅ Integración con Bedrock Agent Runtime para respuestas inteligentes
- ✅ Webhook al backend para notificar respuestas
- ✅ Manejo robusto de errores con notificaciones al backend

---

## Definiciones

### Componentes Clave

#### **Evento (Event)**

Un evento representa un mensaje individual guardado en AgentCore Memory. Cada interacción genera dos eventos:

- **Evento USER**: Mensaje enviado por el usuario
- **Evento ASSISTANT**: Respuesta generada por el asistente

**Ejemplo**: Una conversación con 3 intercambios genera 6 eventos (3 del usuario + 3 del asistente).

#### **Sesión (Session)**

Una sesión agrupa todos los eventos de una conversación específica. Se identifica por `sessionId = "session-{conversationId}"`. Cada conversación tiene su propia sesión aislada.

#### **Actor (Actor)**

Representa al usuario en AgentCore Memory. Se identifica por `actorId = userId`. Todos los eventos de un usuario están asociados a su `actorId`.

#### **Memory ID**

Identificador único de la instancia de memoria en AgentCore. Configurado mediante la variable de entorno `AGENTCORE_MEMORY_ID`.

### Variables de Entorno

| Variable                 | Descripción                            | Requerido | Default                   |
| ------------------------ | -------------------------------------- | --------- | ------------------------- |
| `AGENTCORE_MEMORY_ID`    | ID de la memoria en AgentCore          | ✅        | `memory_bqdqb-jtj3lc48bl` |
| `BEDROCK_AGENT_ID`       | ID del Bedrock Agent                   | ✅        | -                         |
| `BEDROCK_AGENT_ALIAS_ID` | Alias del Bedrock Agent                | ✅        | -                         |
| `AWS_REGION`             | Región de AWS                          | ❌        | `us-east-1`               |
| `BACKEND_WEBHOOK_URL`    | URL del webhook para enviar respuestas | ✅        | -                         |
| `WEBHOOK_SECRET`         | Secret para autenticación del webhook  | ❌        | -                         |

### Límites y Configuración

- **Eventos recuperados**: 30 eventos por conversación (línea 47)
- **Truncamiento de mensajes**: 200 caracteres por mensaje en el contexto (línea 66)
- **Límite de respuesta guardada**: 5000 caracteres (línea 123)
- **Timeout del webhook**: 10 segundos (línea 174)

---

## Arquitectura

### Flujo de Procesamiento

```
┌─────────────┐
│   SNS Topic │
└──────┬──────┘
       │ Event: { conversationId, messageId, userId, text }
       ▼
┌─────────────────────────────────────────────────────────┐
│              Lambda Handler                              │
│                                                          │
│  1. Parse SNS Message                                    │
│  2. Construir sessionId = "session-{conversationId}"     │
│                                                          │
│  ┌──────────────────────────────────────────────┐       │
│  │  getUserMemory(userId, sessionId)            │       │
│  │  └─> AgentCore: ListEventsCommand           │       │
│  │      └─> Recupera últimos 30 eventos        │       │
│  │      └─> Formatea contexto conversacional  │       │
│  └──────────────────────────────────────────────┘       │
│                          │                               │
│                          ▼                               │
│  ┌──────────────────────────────────────────────┐       │
│  │  Enriquecer prompt con contexto             │       │
│  │  enrichedText = memory.context + text        │       │
│  └──────────────────────────────────────────────┘       │
│                          │                               │
│                          ▼                               │
│  ┌──────────────────────────────────────────────┐       │
│  │  InvokeAgentCommand                          │       │
│  │  └─> Bedrock Agent Runtime                   │       │
│  │      └─> Procesa stream de respuesta        │       │
│  └──────────────────────────────────────────────┘       │
│                          │                               │
│                          ▼                               │
│  ┌──────────────────────────────────────────────┐       │
│  │  saveToMemory(userId, sessionId, ...)       │       │
│  │  └─> AgentCore: CreateEventCommand (USER)    │       │
│  │  └─> AgentCore: CreateEventCommand (ASSIST) │       │
│  └──────────────────────────────────────────────┘       │
│                          │                               │
│                          ▼                               │
│  ┌──────────────────────────────────────────────┐       │
│  │  sendToBackend(responseData)                 │       │
│  │  └─> POST a BACKEND_WEBHOOK_URL              │       │
│  └──────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

### Componentes del Sistema

```
┌─────────────────┐
│   Backend App   │
│  (Tu aplicación)│
└────────┬────────┘
         │ Publica mensaje
         ▼
┌─────────────────┐
│   SNS Topic     │
└────────┬────────┘
         │ Trigger
         ▼
┌─────────────────────────────────────┐
│  Lambda: bedrock-processor          │
│  ┌───────────────────────────────┐  │
│  │ AgentCore Memory Client      │  │
│  │ - ListEvents                 │  │
│  │ - CreateEvent                │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ Bedrock Agent Runtime Client  │  │
│  │ - InvokeAgent                 │  │
│  └───────────────────────────────┘  │
└────────┬────────────────────────────┘
         │
         ├──► AgentCore Memory
         │    (Almacena eventos)
         │
         ├──► Bedrock Agent
         │    (Genera respuestas)
         │
         └──► Backend Webhook
              (Notifica respuesta)
```

### Formato del Contexto de Memoria

Cuando se recupera memoria, el contexto se formatea así:

```
[Conversación actual]
USER: Hola, ¿qué es la Biblia?
ASSISTANT: La Biblia es una colección de textos sagrados...
USER: ¿Cuántos libros tiene?
ASSISTANT: La Biblia tiene 66 libros en total...
[Fin de contexto]

Usuario dice: ¿Y cuál es el más corto?
```

### Estructura de Datos

#### Mensaje SNS (Entrada)

```json
{
  "Records": [
    {
      "Sns": {
        "Message": "{\"conversationId\":\"conv-123\",\"messageId\":\"msg-456\",\"userId\":\"user-789\",\"text\":\"Hola\"}"
      }
    }
  ]
}
```

#### Respuesta al Backend (Salida)

```json
{
  "eventType": "bedrock_response",
  "conversationId": "conv-123",
  "messageId": "ai-msg-456",
  "responseText": "¡Hola! ¿En qué puedo ayudarte?",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "processingTimeMs": 1250,
  "hasMemoryContext": true,
  "tokensUsed": {
    "input": 150,
    "output": 25
  }
}
```

## <<<<<<< HEAD

## Ejemplo de Consumo en JavaScript

### Publicar Mensaje a SNS

```javascript
const { SNSClient, PublishCommand } = require("@aws-sdk/client-sns");

const snsClient = new SNSClient({ region: "us-east-1" });
const TOPIC_ARN = "arn:aws:sns:us-east-1:123456789012:bible-messages";

async function sendMessageToLambda(conversationId, messageId, userId, text) {
  const message = {
    conversationId,
    messageId,
    userId,
    text,
  };

  const command = new PublishCommand({
    TopicArn: TOPIC_ARN,
    Message: JSON.stringify(message),
    MessageAttributes: {
      conversationId: {
        DataType: "String",
        StringValue: conversationId,
      },
      userId: {
        DataType: "String",
        StringValue: userId,
      },
    },
  });

  try {
    const response = await snsClient.send(command);
    console.log("Message published:", response.MessageId);
    return response.MessageId;
  } catch (error) {
    console.error("Error publishing message:", error);
    throw error;
  }
}

// Uso
await sendMessageToLambda(
  "conv-123",
  "msg-456",
  "user-789",
  "¿Qué es la Biblia?"
);
```

### Recibir Respuesta del Webhook

```javascript
const express = require("express");
const app = express();

app.use(express.json());

// Endpoint para recibir respuestas del Lambda
app.post("/webhook/bedrock-response", (req, res) => {
  const secret = req.headers["x-webhook-secret"];

  // Validar secret (opcional)
  if (process.env.WEBHOOK_SECRET && secret !== process.env.WEBHOOK_SECRET) {
    return res.status(401).json({ error: "Unauthorized" });
  }

  const {
    eventType,
    conversationId,
    messageId,
    responseText,
    hasMemoryContext,
  } = req.body;

  if (eventType === "bedrock_response") {
    console.log(`✅ Respuesta recibida para conversación ${conversationId}`);
    console.log(`   Mensaje ID: ${messageId}`);
    console.log(`   Tiene contexto: ${hasMemoryContext}`);
    console.log(`   Respuesta: ${responseText}`);

    // Aquí puedes procesar la respuesta:
    // - Guardarla en tu base de datos
    // - Enviarla al cliente via WebSocket
    // - Actualizar la UI
    // etc.

    res.json({ success: true });
  } else if (eventType === "processing_error") {
    console.error(`❌ Error procesando mensaje ${messageId}:`, req.body.error);
    res.json({ success: true }); // Acknowledge el error
  } else {
    res.status(400).json({ error: "Unknown event type" });
  }
});

app.listen(3000, () => {
  console.log("Webhook server listening on port 3000");
});
```

### Ejemplo Completo: Cliente de Chat

```javascript
const { SNSClient, PublishCommand } = require("@aws-sdk/client-sns");
const axios = require("axios");

class BibleChatClient {
  constructor(snsTopicArn, webhookUrl, userId) {
    this.snsClient = new SNSClient({ region: "us-east-1" });
    this.topicArn = snsTopicArn;
    this.webhookUrl = webhookUrl;
    this.userId = userId;
    this.conversationId = `conv-${Date.now()}`;
  }

  async sendMessage(text) {
    const messageId = `msg-${Date.now()}`;

    // Publicar mensaje a SNS
    const command = new PublishCommand({
      TopicArn: this.topicArn,
      Message: JSON.stringify({
        conversationId: this.conversationId,
        messageId,
        userId: this.userId,
        text,
      }),
    });

    await this.snsClient.send(command);
    console.log(`📤 Mensaje enviado: ${text}`);

    return messageId;
  }

  // Este método se llamaría desde tu webhook handler
  async handleResponse(responseData) {
    if (responseData.eventType === "bedrock_response") {
      console.log(`📥 Respuesta recibida: ${responseData.responseText}`);
      return responseData.responseText;
    }
  }
}

// Uso
const client = new BibleChatClient(
  "arn:aws:sns:us-east-1:123456789012:bible-messages",
  "https://tu-backend.com/webhook",
  "user-123"
);

// Enviar mensaje
await client.sendMessage("¿Qué es la Biblia?");

// La respuesta llegará al webhook configurado en BACKEND_WEBHOOK_URL
```

### Ejemplo con Async/Await y Promesas

```javascript
// Función helper para esperar respuesta
function waitForResponse(conversationId, messageId, timeout = 30000) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();

    // En un caso real, esto se conectaría a tu sistema de eventos
    // (WebSocket, polling, etc.)
    const checkInterval = setInterval(() => {
      // Simulación: en producción, esto consultaría tu base de datos
      // o escucharía eventos en tiempo real
      if (Date.now() - startTime > timeout) {
        clearInterval(checkInterval);
        reject(new Error("Timeout waiting for response"));
      }
    }, 100);
  });
}

// Uso completo
async function chatFlow() {
  const client = new BibleChatClient(
    "arn:aws:sns:us-east-1:123456789012:bible-messages",
    "https://tu-backend.com/webhook",
    "user-123"
  );

  try {
    // Primer mensaje
    const msg1 = await client.sendMessage("Hola");
    console.log("Esperando respuesta...");
    // En producción, esperarías la respuesta del webhook

    // Segundo mensaje (con contexto de memoria)
    const msg2 = await client.sendMessage("¿Qué me dijiste antes?");
    // El Lambda recuperará el contexto de la conversación anterior
  } catch (error) {
    console.error("Error en el flujo de chat:", error);
  }
}
```

### Manejo de Errores

```javascript
// En tu webhook handler
app.post("/webhook/bedrock-response", async (req, res) => {
  try {
    const data = req.body;

    if (data.eventType === "processing_error") {
      // Manejar error del Lambda
      console.error("Error del Lambda:", {
        conversationId: data.conversationId,
        messageId: data.messageId,
        error: data.error,
        source: data.source,
      });

      // Notificar al usuario
      await notifyUser(
        data.conversationId,
        "Lo siento, hubo un error procesando tu mensaje."
      );

      return res.json({ success: true });
    }

    // Procesar respuesta exitosa
    await processResponse(data);
    res.json({ success: true });
  } catch (error) {
    console.error("Error en webhook:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});
```

---

## Despliegue

Ver el script `deploy.ps1` para instrucciones de despliegue automatizado.

### Despliegue Manual

```bash
cd lambda_bedrock_with_memory

# 1. Instalar dependencias
npm install

# 2. Crear paquete
zip -r lambda.zip index.js package.json node_modules/

# 3. Actualizar Lambda
aws lambda update-function-code \
    --function-name gpbible-bedrock-processor-dev \
    --zip-file fileb://lambda.zip \
    --region us-east-1
```

---

## Notas Adicionales

- **Aislamiento de memoria**: Cada `conversationId` tiene su propia sesión aislada. No se comparte contexto entre conversaciones diferentes.
- **Orden de eventos**: Los eventos se ordenan por timestamp. El asistente usa +1 segundo para asegurar orden correcto.
- **Truncamiento**: Los mensajes se truncarán a 200 caracteres en el contexto para optimizar tokens, pero se guardan completos en AgentCore.
- # **Streaming**: El Lambda procesa el stream completo de Bedrock antes de guardar y responder.

## Current Deployment

| Resource             | Value                                   |
| -------------------- | --------------------------------------- |
| Lambda               | `gpbible-bedrock-processor-memory-test` |
| Bedrock Agent ID     | `OPFJ6RWI2P`                            |
| Bedrock Agent Alias  | `YWLZEUSKI8`                            |
| AgentCore Memory ID  | `memory_bqdqb-jtj3lc48bl`               |
| Semantic Strategy ID | `semantic_grace_v1-I25PeS4v8Y`          |

## Environment Variables

| Variable                 | Description                    | Default                        |
| ------------------------ | ------------------------------ | ------------------------------ |
| `AGENTCORE_MEMORY_ID`    | ID de la memoria AgentCore     | `memory_bqdqb-jtj3lc48bl`      |
| `BEDROCK_AGENT_ID`       | ID del agente Bedrock          | Required                       |
| `BEDROCK_AGENT_ALIAS_ID` | Alias del agente               | Required                       |
| `SEMANTIC_STRATEGY_ID`   | ID de la estrategia semántica  | `semantic_grace_v1-I25PeS4v8Y` |
| `BACKEND_WEBHOOK_URL`    | URL del webhook del backend    | Required                       |
| `WEBHOOK_SECRET`         | Secret para autenticar webhook | Optional                       |

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

### Test Interactivo (Recomendado)

El script `test-interactive.js` permite tener una conversación interactiva con el Lambda desde la terminal:

```bash
cd lambda_bedrock_with_memory
node test-interactive.js
```

**Características:**

- Conversación interactiva en tiempo real
- Mantiene el contexto de la conversación (mismo `conversationId`)
- Comandos especiales: `exit`, `quit`, `clear`, `info`
- Configurable mediante variables de entorno

**Variables de entorno opcionales:**

```bash
LAMBDA_NAME=gpbible-bedrock-processor-dev \
TEST_USER_ID=mi-usuario \
TEST_CONVERSATION_ID=mi-conversacion \
node test-interactive.js
```

**Nota:** El Lambda envía las respuestas al webhook configurado. Para ver las respuestas completas, abre otra terminal y ejecuta:

```bash
aws logs tail /aws/lambda/gpbible-bedrock-processor-dev --follow --region us-east-1
```

### Test con Python

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

> > > > > > > e07059073ee9a86079964fee604686b5a2bd2418
