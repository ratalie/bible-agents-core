/**
 * Script para probar el Lambda con AgentCore Memory
 * Ejecutar: node test_lambda_memory.js
 */

const { LambdaClient, InvokeCommand } = require("@aws-sdk/client-lambda");
const { BedrockAgentCoreClient, ListSessionsCommand, ListEventsCommand } = require("@aws-sdk/client-bedrock-agentcore");
const { CloudWatchLogsClient, DescribeLogStreamsCommand, GetLogEventsCommand } = require("@aws-sdk/client-cloudwatch-logs");

// Configuración
const LAMBDA_NAME = "gpbible-bedrock-processor-memory-test";
const REGION = "us-east-1";
const MEMORY_ID = "memory_bqdqb-jtj3lc48bl";

// Clientes AWS
const lambdaClient = new LambdaClient({ region: REGION });
const agentcoreClient = new BedrockAgentCoreClient({ region: REGION });
const logsClient = new CloudWatchLogsClient({ region: REGION });

/**
 * Invoca el Lambda con un mensaje de prueba
 */
async function invokeLambda(userId, conversationId, messageId, text) {
    const payload = {
        Records: [{
            Sns: {
                Message: JSON.stringify({
                    conversationId,
                    messageId,
                    userId,
                    text
                })
            }
        }]
    };

    console.log(`\n📤 Enviando: ${text.substring(0, 50)}...`);

    try {
        const command = new InvokeCommand({
            FunctionName: LAMBDA_NAME,
            InvocationType: "RequestResponse",
            Payload: JSON.stringify(payload)
        });

        const response = await lambdaClient.send(command);
        const result = JSON.parse(new TextDecoder().decode(response.Payload));

        if (response.FunctionError) {
            console.log("⚠️  Lambda ejecutado con error (esperado si webhook no está configurado)");
        } else {
            console.log("✅ Lambda ejecutado exitosamente");
        }

        return result;
    } catch (error) {
        console.error("❌ Error invocando Lambda:", error.message);
        throw error;
    }
}

/**
 * Verifica la memoria guardada para un usuario
 */
async function checkMemory(userId) {
    console.log(`\n🔍 Verificando memoria para: ${userId}`);

    try {
        // Listar sesiones
        const sessionsCommand = new ListSessionsCommand({
            memoryId: MEMORY_ID,
            actorId: userId
        });

        const sessionsResponse = await agentcoreClient.send(sessionsCommand);
        const sessionList = sessionsResponse.sessionSummaries || [];

        console.log(`   Sesiones encontradas: ${sessionList.length}`);

        for (const session of sessionList) {
            const sessionId = session.sessionId;
            console.log(`\n   📁 Sesión: ${sessionId}`);

            // Listar eventos de la sesión
            const eventsCommand = new ListEventsCommand({
                memoryId: MEMORY_ID,
                actorId: userId,
                sessionId: sessionId,
                maxResults: 10
            });

            const eventsResponse = await agentcoreClient.send(eventsCommand);
            const events = eventsResponse.events || [];

            for (const event of events) {
                const payload = event.payload || [];
                if (payload.length > 0 && payload[0].conversational) {
                    const conv = payload[0].conversational;
                    const role = conv.role || "UNKNOWN";
                    const text = (conv.content?.text || "").substring(0, 100);
                    console.log(`      ${role}: ${text}...`);
                }
            }
        }

        return sessionList.length;
    } catch (error) {
        console.log(`   Error: ${error.message}`);
        return 0;
    }
}

/**
 * Obtiene los logs más recientes del Lambda
 */
async function getRecentLogs(limit = 10) {
    const logGroup = `/aws/lambda/${LAMBDA_NAME}`;

    try {
        // Obtener el stream más reciente
        const streamsCommand = new DescribeLogStreamsCommand({
            logGroupName: logGroup,
            orderBy: "LastEventTime",
            descending: true,
            limit: 1
        });

        const streamsResponse = await logsClient.send(streamsCommand);

        if (!streamsResponse.logStreams || streamsResponse.logStreams.length === 0) {
            console.log("No hay logs disponibles");
            return;
        }

        const streamName = streamsResponse.logStreams[0].logStreamName;

        // Obtener eventos del stream
        const eventsCommand = new GetLogEventsCommand({
            logGroupName: logGroup,
            logStreamName: streamName,
            limit: limit
        });

        const eventsResponse = await logsClient.send(eventsCommand);

        console.log(`\n📋 Últimos logs (${streamName}):`);
        console.log("-".repeat(60));

        for (const event of eventsResponse.events || []) {
            let msg = event.message.trim();
            const keywords = ["INFO", "ERROR", "Memory", "memory", "Fetching", "saved", "Found"];
            
            if (keywords.some(kw => msg.includes(kw))) {
                // Limpiar mensaje
                if (msg.includes("\t")) {
                    const parts = msg.split("\t");
                    if (parts.length >= 3) {
                        msg = parts[2];
                    }
                }
                console.log(msg.substring(0, 200));
            }
        }
    } catch (error) {
        console.log(`Error obteniendo logs: ${error.message}`);
    }
}

/**
 * Espera un tiempo determinado
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Ejecuta una prueba completa
 */
async function runTest() {
    console.log("=".repeat(60));
    console.log("🧪 PRUEBA DE LAMBDA CON AGENTCORE MEMORY");
    console.log("=".repeat(60));

    // Usar un userId único para la prueba
    const testUser = `test-user-${Date.now()}`;

    // 1. Primera conversación (sin memoria previa)
    console.log("\n" + "=".repeat(60));
    console.log("1️⃣  PRIMERA CONVERSACIÓN (sin memoria previa)");
    console.log("=".repeat(60));

    await invokeLambda(
        testUser,
        "conv-001",
        "msg-001",
        "Hola, estoy pasando por un momento difícil y necesito guía espiritual"
    );

    await sleep(2000);

    // 2. Verificar que se guardó la memoria
    console.log("\n" + "=".repeat(60));
    console.log("2️⃣  VERIFICANDO MEMORIA GUARDADA");
    console.log("=".repeat(60));

    const sessions = await checkMemory(testUser);

    if (sessions === 0) {
        console.log("❌ No se guardó la memoria");
        return;
    }

    // 3. Segunda conversación (debería leer memoria)
    console.log("\n" + "=".repeat(60));
    console.log("3️⃣  SEGUNDA CONVERSACIÓN (con memoria)");
    console.log("=".repeat(60));

    await invokeLambda(
        testUser,
        "conv-002",
        "msg-002",
        "¿Qué versículo me recomiendas para encontrar paz?"
    );

    await sleep(2000);

    // 4. Ver logs
    console.log("\n" + "=".repeat(60));
    console.log("4️⃣  LOGS DEL LAMBDA");
    console.log("=".repeat(60));

    await getRecentLogs(15);

    // 5. Verificar memoria final
    console.log("\n" + "=".repeat(60));
    console.log("5️⃣  MEMORIA FINAL");
    console.log("=".repeat(60));

    await checkMemory(testUser);

    console.log("\n" + "=".repeat(60));
    console.log("✅ PRUEBA COMPLETADA");
    console.log("=".repeat(60));
    console.log(`\nUsuario de prueba: ${testUser}`);
    console.log("Revisa los logs para ver '✅ Found previous conversations' en la segunda llamada");
}

// Ejecutar
runTest().catch(error => {
    console.error("Error en la prueba:", error);
    process.exit(1);
});

