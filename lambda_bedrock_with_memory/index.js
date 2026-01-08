/**
 * Lambda: Bedrock Agent con AgentCore Memory
 *
 * Flujo:
 * 1. Recibe mensaje de SNS
 * 2. Lee memoria del usuario desde AgentCore
 * 3. Llama a Bedrock Agent con contexto de memoria
 * 4. Guarda la interacción en AgentCore Memory
 * 5. Envía respuesta al backend
 */

const {
  BedrockAgentRuntimeClient,
  InvokeAgentCommand,
} = require("@aws-sdk/client-bedrock-agent-runtime");
const {
  BedrockAgentCoreClient,
  ListEventsCommand,
  CreateEventCommand,
} = require("@aws-sdk/client-bedrock-agentcore");
const axios = require("axios");

// Clientes AWS
const bedrockClient = new BedrockAgentRuntimeClient({
  region: process.env.AWS_REGION || "us-east-1",
});

const agentcoreClient = new BedrockAgentCoreClient({
  region: process.env.AWS_REGION || "us-east-1",
});

// Configuración
const MEMORY_ID = process.env.AGENTCORE_MEMORY_ID || "memory_bqdqb-jtj3lc48bl";
const AGENT_ID = process.env.BEDROCK_AGENT_ID;
const ALIAS_ID = process.env.BEDROCK_AGENT_ALIAS_ID;
const SEMANTIC_STRATEGY_ID =
  process.env.SEMANTIC_STRATEGY_ID || "semantic_grace_v1-I25PeS4v8Y";

/**
 * Buscar memorias relevantes usando búsqueda semántica
 */
async function getSemanticMemory(userId, userMessage, limit = 5) {
  try {
    const command = new RetrieveMemoryRecordsCommand({
      memoryId: MEMORY_ID,
      namespace: `/strategies/${SEMANTIC_STRATEGY_ID}/actors/${userId}`,
      searchCriteria: {
        searchQuery: userMessage,
        topK: limit,
      },
    });

    const response = await agentcoreClient.send(command);
    const records = response.memoryRecordSummaries || [];

    if (records.length === 0) {
      return { hasSemanticMemory: false, context: "" };
    }

    const relevantMemories = records
      .filter((r) => r.content?.text)
      .map((r) => r.content.text.substring(0, 300))
      .slice(0, 3);

    if (relevantMemories.length === 0) {
      return { hasSemanticMemory: false, context: "" };
    }

    return {
      hasSemanticMemory: true,
      context: `\n\n[Conversaciones relevantes anteriores]\n${relevantMemories.join(
        "\n---\n"
      )}\n[Fin de contexto relevante]\n\n`,
    };
  } catch (error) {
    console.log("Semantic search error:", error.message);
    return { hasSemanticMemory: false, context: "" };
  }
}

/**
 * Obtener memoria SOLO de la conversación actual (sessionId) desde AgentCore
 */
async function getUserMemory(userId, sessionId) {
  try {
    // Obtener eventos de ESA sesión únicamente
    const eventsCommand = new ListEventsCommand({
      memoryId: MEMORY_ID,
      actorId: userId,
      sessionId: sessionId,
      maxResults: 30, // puedes ajustar este número si quieres más/menos contexto
    });

    const eventsResponse = await agentcoreClient.send(eventsCommand);
    const events = eventsResponse.events || [];

    if (events.length === 0) {
      return { hasMemory: false, context: "" };
    }

    // Extraer texto de los eventos de esta sesión
    let memoryContext = [];

    for (const event of events) {
      if (event.payload && event.payload[0]?.conversational) {
        const conv = event.payload[0].conversational;
        const role = conv.role || "USER";
        const text = conv.content?.text || "";
        if (text) {
          memoryContext.push(`${role}: ${text.substring(0, 200)}`);
        }
      }
    }

    if (memoryContext.length === 0) {
      return { hasMemory: false, context: "" };
    }

    return {
      hasMemory: true,
      context: `\n\n[Conversación actual]\n${memoryContext.join(
        "\n"
      )}\n[Fin de contexto]\n\n`,
    };
  } catch (error) {
    console.log("No memory found or error:", error.message);
    return { hasMemory: false, context: "" };
  }
}

/**
 * Guardar interacción en AgentCore Memory
 */
async function saveToMemory(userId, sessionId, userMessage, assistantResponse) {
  try {
    // Timestamp como Date object (no string)
    const now = new Date();

    // Guardar mensaje del usuario
    await agentcoreClient.send(
      new CreateEventCommand({
        memoryId: MEMORY_ID,
        actorId: userId,
        sessionId: sessionId,
        eventTimestamp: now,
        payload: [
          {
            conversational: {
              content: { text: userMessage },
              role: "USER",
            },
          },
        ],
      })
    );

    // Guardar respuesta del asistente (con pequeño delay para orden)
    await agentcoreClient.send(
      new CreateEventCommand({
        memoryId: MEMORY_ID,
        actorId: userId,
        sessionId: sessionId,
        eventTimestamp: new Date(now.getTime() + 1000), // +1 segundo
        payload: [
          {
            conversational: {
              content: { text: assistantResponse.substring(0, 5000) }, // Limitar tamaño
              role: "ASSISTANT",
            },
          },
        ],
      })
    );

    console.log(`✅ Memory saved for user ${userId}`);
    return true;
  } catch (error) {
    console.error("Error saving to memory:", error.message);
    return false;
  }
}

/**
 * Procesar stream de Bedrock
 */
async function processStream(stream) {
  let fullResponse = "";
  try {
    for await (const chunk of stream) {
      if (chunk.chunk) {
        const decodedChunk = new TextDecoder().decode(chunk.chunk.bytes);
        fullResponse += decodedChunk;
      }
    }
    return fullResponse;
  } catch (error) {
    console.error("Error processing stream:", error);
    throw error;
  }
}

/**
 * Enviar respuesta al backend
 */
async function sendToBackend(data) {
  const webhookUrl = process.env.BACKEND_WEBHOOK_URL;
  const webhookSecret = process.env.WEBHOOK_SECRET;

  if (!webhookUrl) {
    throw new Error("BACKEND_WEBHOOK_URL not configured");
  }

  await axios.post(webhookUrl, data, {
    headers: {
      "Content-Type": "application/json",
      "x-webhook-secret": webhookSecret || "",
    },
    timeout: 10000,
  });
}

/**
 * Handler principal
 */
exports.handler = async (event) => {
  console.log("Received SNS event:", JSON.stringify(event, null, 2));

  for (const record of event.Records) {
    const startTime = Date.now();

    try {
      const message = JSON.parse(record.Sns.Message);
      const { conversationId, messageId, userId, text } = message;

      console.log(`Processing message ${messageId} for user ${userId}`);

      // Construir sessionId UNA sola vez para esta conversación
      const sessionId = `session-${conversationId}`;

      // Validar configuración
      if (!AGENT_ID || !ALIAS_ID) {
        throw new Error("Bedrock Agent configuration missing");
      }

      // 1. Obtener memoria del usuario SOLO de esta conversación
      console.log("📚 Fetching user memory...");
      const memory = await getUserMemory(userId, sessionId);

      if (memory.hasMemory) {
        console.log("✅ Found previous messages in this conversation");
      } else {
        console.log("ℹ️ No previous memory for this conversation");
      }

      // 2. Construir prompt con contexto de memoria
      const enrichedText = memory.hasMemory
        ? `${memory.context}Usuario dice: ${text}`
        : text;

      // 3. Llamar a Bedrock Agent
      console.log("🤖 Invoking Bedrock Agent...");
      const command = new InvokeAgentCommand({
        agentId: AGENT_ID,
        agentAliasId: ALIAS_ID,
        sessionId: sessionId,
        inputText: enrichedText,
      });

      const response = await bedrockClient.send(command);

      if (!response.completion) {
        throw new Error("No completion received from Bedrock");
      }

      // 4. Procesar respuesta
      const responseText = await processStream(response.completion);
      const processingTime = Date.now() - startTime;

      console.log(`Response received in ${processingTime}ms`);

      // 5. Guardar en AgentCore Memory
      console.log("💾 Saving to AgentCore Memory...");
      await saveToMemory(userId, sessionId, text, responseText);

      // 6. Enviar respuesta al backend
      await sendToBackend({
        eventType: "bedrock_response",
        conversationId,
        messageId: `ai-${messageId}`,
        responseText,
        timestamp: new Date().toISOString(),
        processingTimeMs: processingTime,
        hasMemoryContext: memory.hasMemory,
        tokensUsed: {
          input: Math.floor(enrichedText.length / 4),
          output: Math.floor(responseText.length / 4),
        },
      });

      console.log(`✅ Response sent for message ${messageId}`);
    } catch (error) {
      console.error("❌ Error processing message:", error);

      try {
        const message = JSON.parse(record.Sns.Message);
        await sendToBackend({
          eventType: "processing_error",
          conversationId: message.conversationId,
          messageId: message.messageId,
          error: error.message,
          source: "lambda-bedrock-memory",
          timestamp: new Date().toISOString(),
        });
      } catch (notifyError) {
        console.error("Failed to notify backend:", notifyError);
      }

      throw error;
    }
  }

  console.log("✅ All messages processed");
};
