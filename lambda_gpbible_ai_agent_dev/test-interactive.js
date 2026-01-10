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
const LAMBDA_NAME = process.env.LAMBDA_NAME || "gpbible-ai-agent-dev";
const REGION = process.env.AWS_REGION || "us-east-1";
const USER_ID = process.env.TEST_USER_ID || `test-user-${Date.now()}`;
const CONVERSATION_ID =
  process.env.TEST_CONVERSATION_ID || `test-conv-${Date.now()}`;

// Configuración de personalidad (puede ser modificada con comandos)
let userProfile = {
  personalityColor: process.env.TEST_PERSONALITY_COLOR || "blue",
  spiritualDepthPercent: parseInt(process.env.TEST_SPIRITUAL_DEPTH || "10"),
  age: parseInt(process.env.TEST_AGE || "30"),
  language: process.env.TEST_LANGUAGE || "en",
};

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

  // Construir mensaje con userProfile si está configurado
  const message = {
    conversationId: CONVERSATION_ID,
    messageId: messageId,
    userId: USER_ID,
    text: text,
  };

  // Agregar userProfile si tiene valores válidos
  if (
    userProfile &&
    (userProfile.personalityColor ||
      userProfile.spiritualDepthPercent ||
      userProfile.age)
  ) {
    message.userProfile = userProfile;
  }

  const payload = {
    Records: [
      {
        Sns: {
          Message: JSON.stringify(message),
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
  console.log(`\n🎭 Personalidad:`);
  console.log(`   Color: ${userProfile.personalityColor.toUpperCase()}`);
  console.log(`   Spiritual Depth: ${userProfile.spiritualDepthPercent}%`);
  console.log(`   Age: ${userProfile.age} años`);
  console.log(`   Language: ${userProfile.language.toUpperCase()}`);
  console.log(`\n💡 Comandos:`);
  console.log(`   - Escribe tu mensaje y presiona Enter`);
  console.log(`   - "exit" o "quit" - Salir`);
  console.log(`   - "clear" - Limpiar pantalla`);
  console.log(`   - "info" - Ver configuración`);
  console.log(`   - "profile" - Ver perfil de personalidad`);
  console.log(
    `   - "set-personality <color> <depth> <age>" - Cambiar personalidad`
  );
  console.log(`     Ejemplo: set-personality red 45 35`);
  console.log(`     Colores: red, yellow, green, blue`);
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
      console.log(`\n🎭 Personalidad:`);
      console.log(`   Color: ${userProfile.personalityColor.toUpperCase()}`);
      console.log(`   Spiritual Depth: ${userProfile.spiritualDepthPercent}%`);
      console.log(`   Age: ${userProfile.age} años`);
      console.log(`   Language: ${userProfile.language.toUpperCase()}`);
      rl.prompt();
      return;
    }

    if (text.toLowerCase() === "profile") {
      console.log("\n🎭 Perfil de Personalidad Actual:");
      console.log(
        `   Personality Color: ${userProfile.personalityColor.toUpperCase()}`
      );
      console.log(
        `   Spiritual Depth: ${
          userProfile.spiritualDepthPercent
        }% (Level ${Math.ceil(userProfile.spiritualDepthPercent / 10)})`
      );
      console.log(`   Age: ${userProfile.age} años`);

      // Determinar Life Stage
      let lifeStage = "Explorer";
      if (userProfile.age >= 30 && userProfile.age <= 45) lifeStage = "Builder";
      else if (userProfile.age >= 46 && userProfile.age <= 69)
        lifeStage = "Guide";
      else if (userProfile.age >= 70) lifeStage = "Legacy";

      console.log(`   Life Stage: ${lifeStage}`);
      console.log(
        `   Language: ${userProfile.language.toUpperCase()} (${
          userProfile.language === "es" ? "Español" : "English"
        })`
      );
      console.log(`\n💡 Para cambiar:`);
      console.log(`   - Personalidad: set-personality <color> <depth> <age>`);
      console.log(`   - Idioma: set-language <en|es>`);
      console.log(`   Ejemplo: set-personality red 45 35`);
      console.log(`   Ejemplo: set-language es`);
      rl.prompt();
      return;
    }

    if (text.toLowerCase().startsWith("set-personality")) {
      const parts = text.split(" ");
      if (parts.length >= 4) {
        const color = parts[1].toLowerCase();
        const depth = parseInt(parts[2]);
        const age = parseInt(parts[3]);

        const validColors = ["red", "yellow", "green", "blue"];
        if (!validColors.includes(color)) {
          console.log(`\n❌ Color inválido. Usa: red, yellow, green, o blue`);
          rl.prompt();
          return;
        }

        if (isNaN(depth) || depth < 0 || depth > 100) {
          console.log(`\n❌ Spiritual Depth debe ser un número entre 0 y 100`);
          rl.prompt();
          return;
        }

        if (isNaN(age) || age < 18 || age > 120) {
          console.log(`\n❌ Age debe ser un número entre 18 y 120`);
          rl.prompt();
          return;
        }

        userProfile = {
          personalityColor: color,
          spiritualDepthPercent: depth,
          age: age,
          language: userProfile.language, // Mantener idioma actual
        };

        console.log(`\n✅ Personalidad actualizada:`);
        console.log(`   Color: ${color.toUpperCase()}`);
        console.log(`   Spiritual Depth: ${depth}%`);
        console.log(`   Age: ${age} años`);
        console.log(
          `   Language: ${userProfile.language.toUpperCase()} (mantenido)`
        );
      } else {
        console.log(
          `\n❌ Formato incorrecto. Usa: set-personality <color> <depth> <age>`
        );
        console.log(`   Ejemplo: set-personality red 45 35`);
      }
      rl.prompt();
      return;
    }

    if (text.toLowerCase().startsWith("set-language")) {
      const parts = text.split(" ");
      if (parts.length >= 2) {
        const language = parts[1].toLowerCase();
        const validLanguages = ["en", "es"];

        if (!validLanguages.includes(language)) {
          console.log(`\n❌ Idioma inválido. Usa: en o es`);
          rl.prompt();
          return;
        }

        userProfile.language = language;
        const languageName = language === "es" ? "Español" : "English";
        console.log(
          `\n✅ Idioma actualizado: ${language.toUpperCase()} (${languageName})`
        );
        console.log(`   El agente responderá siempre en ${languageName}`);
      } else {
        console.log(`\n❌ Formato incorrecto. Usa: set-language <en|es>`);
        console.log(`   Ejemplo: set-language es`);
      }
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
