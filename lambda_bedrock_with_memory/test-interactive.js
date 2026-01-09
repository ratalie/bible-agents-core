#!/usr/bin/env node

/**
 * Test interactivo para el Lambda con AgentCore Memory
 * Permite tener una conversación desde la terminal
 *
 * Uso: node test-interactive.js
 */

const { LambdaClient, InvokeCommand } = require("@aws-sdk/client-lambda");
const readline = require("readline");

// Configuración
const LAMBDA_NAME = process.env.LAMBDA_NAME || "gpbible-bedrock-processor-dev";
const REGION = process.env.AWS_REGION || "us-east-1";
const USER_ID = process.env.TEST_USER_ID || `test-user-${Date.now()}`;
const CONVERSATION_ID =
  process.env.TEST_CONVERSATION_ID || `test-conv-${Date.now()}`;

// Cliente Lambda
const lambdaClient = new LambdaClient({ region: REGION });

// Configurar readline para entrada interactiva
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  prompt: "\n💬 Tú: ",
});

let messageCounter = 1;

/**
 * Invoca el Lambda con un mensaje
 */
async function sendMessage(text) {
  const messageId = `msg-${Date.now()}-${messageCounter++}`;

  const payload = {
    Records: [
      {
        Sns: {
          Message: JSON.stringify({
            conversationId: CONVERSATION_ID,
            messageId: messageId,
            userId: USER_ID,
            text: text,
          }),
        },
      },
    ],
  };

  try {
    console.log("⏳ Procesando...");

    const command = new InvokeCommand({
      FunctionName: LAMBDA_NAME,
      InvocationType: "RequestResponse",
      Payload: JSON.stringify(payload),
    });

    const startTime = Date.now();
    const response = await lambdaClient.send(command);
    const processingTime = Date.now() - startTime;

    console.log(response);

    // Decodificar respuesta
    const result = JSON.parse(new TextDecoder().decode(response.Payload));

    if (response.FunctionError) {
      console.error("\n❌ Error en el Lambda:");
      console.error(result.errorMessage || result);
      if (result.stackTrace) {
        console.error("\nStack trace:");
        result.stackTrace.forEach((line) => console.error(line));
      }
      return null;
    }

    // Si el Lambda procesó correctamente, la respuesta puede estar en el resultado
    // o necesitamos verificar los logs
    console.log(`\n✅ Procesado en ${processingTime}ms`);

    // El Lambda no retorna la respuesta directamente (la envía al webhook)
    // Pero podemos verificar que se ejecutó correctamente
    if (result.statusCode === 200 || !result.errorMessage) {
      console.log("\n🤖 Respuesta del agente:");
      console.log("   (La respuesta se envió al webhook configurado)");
      console.log("   (Revisa los logs para ver la respuesta completa)");
      return true;
    }

    return result;
  } catch (error) {
    console.error("\n❌ Error invocando Lambda:", error.message);
    if (error.stack) {
      console.error("\nStack:", error.stack);
    }
    return null;
  }
}

/**
 * Función principal
 */
function startConversation() {
  console.log("=".repeat(60));
  console.log("🤖 Test Interactivo - Lambda con AgentCore Memory");
  console.log("=".repeat(60));
  console.log(`\n📋 Configuración:`);
  console.log(`   Lambda: ${LAMBDA_NAME}`);
  console.log(`   Usuario: ${USER_ID}`);
  console.log(`   Conversación: ${CONVERSATION_ID}`);
  console.log(`\n💡 Comandos:`);
  console.log(`   - Escribe tu mensaje y presiona Enter`);
  console.log(`   - Escribe "exit" o "quit" para salir`);
  console.log(`   - Escribe "clear" para limpiar la pantalla`);
  console.log(`   - Escribe "info" para ver la configuración`);
  console.log("=".repeat(60));

  rl.prompt();

  rl.on("line", async (input) => {
    const text = input.trim();

    // Comandos especiales
    if (!text) {
      rl.prompt();
      return;
    }

    if (text.toLowerCase() === "exit" || text.toLowerCase() === "quit") {
      console.log("\n👋 ¡Hasta luego!");
      rl.close();
      process.exit(0);
    }

    if (text.toLowerCase() === "clear") {
      console.clear();
      console.log("=".repeat(60));
      console.log("🤖 Test Interactivo - Lambda con AgentCore Memory");
      console.log("=".repeat(60));
      rl.prompt();
      return;
    }

    if (text.toLowerCase() === "info") {
      console.log("\n📋 Configuración actual:");
      console.log(`   Lambda: ${LAMBDA_NAME}`);
      console.log(`   Región: ${REGION}`);
      console.log(`   Usuario: ${USER_ID}`);
      console.log(`   Conversación: ${CONVERSATION_ID}`);
      console.log(`   Mensajes enviados: ${messageCounter - 1}`);
      rl.prompt();
      return;
    }

    // Enviar mensaje al Lambda
    await sendMessage(text);

    // Continuar la conversación
    rl.prompt();
  });

  rl.on("close", () => {
    console.log("\n👋 ¡Hasta luego!");
    process.exit(0);
  });
}

// Manejar Ctrl+C
process.on("SIGINT", () => {
  console.log("\n\n👋 ¡Hasta luego!");
  rl.close();
  process.exit(0);
});

// Iniciar conversación
startConversation();
