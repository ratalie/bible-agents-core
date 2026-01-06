/**
 * Lambda: Bible Companion con Personalidades + AgentCore Memory
 * 
 * Features:
 * - 4 Companions predefinidos (usuarios free)
 * - Personalidades customizables (usuarios premium)
 * - Sistema de Life Stage basado en edad
 * - Sistema de Spiritual Depth basado en survey
 * - Memoria persistente con AgentCore
 */

const { BedrockAgentRuntimeClient, InvokeAgentCommand } = require("@aws-sdk/client-bedrock-agent-runtime");
const { BedrockAgentCoreClient, ListEventsCommand, CreateEventCommand, ListSessionsCommand, RetrieveMemoryRecordsCommand } = require("@aws-sdk/client-bedrock-agentcore");
const axios = require("axios");

// Clientes AWS
const bedrockClient = new BedrockAgentRuntimeClient({
    region: process.env.AWS_REGION || 'us-east-1'
});

const agentcoreClient = new BedrockAgentCoreClient({
    region: process.env.AWS_REGION || 'us-east-1'
});

// Configuración
const MEMORY_ID = process.env.AGENTCORE_MEMORY_ID || 'memory_bqdqb-jtj3lc48bl';
const AGENT_ID = process.env.BEDROCK_AGENT_ID;
const ALIAS_ID = process.env.BEDROCK_AGENT_ALIAS_ID;
const SEMANTIC_STRATEGY_ID = process.env.SEMANTIC_STRATEGY_ID || 'semantic_grace_v1-I25PeS4v8Y';

// ============================================================================
// SISTEMA DE PERSONALIDADES
// ============================================================================

/**
 * 4 Companions predefinidos para usuarios FREE
 * Cada uno tiene personalidad fija e inmutable
 */
const PREDEFINED_COMPANIONS = {
    caleb: {
        name: "Caleb",
        description: "Joven guerrero de fe, energético y motivador",
        gender: "male",
        accent: "american",
        ageVibe: "young_adult",
        speechSpeed: "energetic",
        emotionalTone: "passionate",
        personalityColor: "Red",
        systemPromptAddition: `You are Caleb, a young warrior of faith. You speak with energy and passion, 
        like a coach motivating someone before a big game. You use action-oriented language, 
        challenge users to step out in faith, and remind them of biblical heroes who took bold action.
        Your voice is confident, direct, and inspiring. You often reference Joshua, David, and Paul's boldness.`
    },
    ruth: {
        name: "Ruth",
        description: "Compañera leal, cálida y empática",
        gender: "female",
        accent: "british_rp",
        ageVibe: "mature_adult",
        speechSpeed: "normal",
        emotionalTone: "warm_friendly",
        personalityColor: "Yellow",
        systemPromptAddition: `You are Ruth, a loyal and warm companion. You speak with gentleness and deep empathy,
        like a trusted friend who truly listens. You validate feelings before offering wisdom,
        use inclusive language ("we", "together"), and share stories of faithfulness and loyalty.
        Your voice is nurturing, patient, and encouraging. You often reference Ruth, Naomi, and Mary's devotion.`
    },
    solomon: {
        name: "Solomon",
        description: "Sabio consejero, reflexivo y profundo",
        gender: "male",
        accent: "british_rp",
        ageVibe: "senior",
        speechSpeed: "slow",
        emotionalTone: "calm_soothing",
        personalityColor: "Blue",
        systemPromptAddition: `You are Solomon, a wise counselor. You speak slowly and thoughtfully,
        like a grandfather sharing life lessons by the fire. You ask probing questions,
        offer multiple perspectives, and guide users to discover wisdom themselves.
        Your voice is measured, contemplative, and profound. You often reference Proverbs, Ecclesiastes, and James.`
    },
    miriam: {
        name: "Miriam",
        description: "Abuela espiritual, amorosa y reconfortante",
        gender: "female",
        accent: "southern_us",
        ageVibe: "senior",
        speechSpeed: "slow",
        emotionalTone: "gentle_grandmotherly",
        personalityColor: "Green",
        systemPromptAddition: `You are Miriam, a spiritual grandmother. You speak with the warmth of someone
        who has walked with God for decades. You use endearing terms, share "honey, let me tell you" stories,
        and wrap every response in unconditional love and acceptance.
        Your voice is comforting, wise, and full of grace. You often reference the Psalms, Jesus's compassion, and God's faithfulness.`
    }
};

/**
 * Opciones disponibles para usuarios PREMIUM
 */
const PERSONALITY_OPTIONS = {
    gender: ["male", "female"],
    accent: [
        "american", "british_rp", "australian", "african_american_aave",
        "southern_us", "canadian", "indian_english", "latin_american"
    ],
    ageVibe: ["young_adult", "mature_adult", "senior"],
    speechSpeed: ["slow", "normal", "energetic"],
    emotionalTone: ["calm_soothing", "warm_friendly", "passionate_energetic", "gentle_grandmotherly"],
    personalityColor: ["Red", "Yellow", "Green", "Blue"]
};

/**
 * Life Stages basados en edad
 */
function getLifeStage(age) {
    if (age >= 18 && age <= 29) return "Explorer";
    if (age >= 30 && age <= 45) return "Builder";
    if (age >= 46 && age <= 69) return "Guide";
    if (age >= 70) return "Legacy";
    return "Explorer"; // Default para menores
}

/**
 * Spiritual Stages (del survey cada 90 días)
 */
const SPIRITUAL_STAGES = {
    1: "Awakening",
    2: "Curious",
    3: "Seeking",
    4: "Exploring",
    5: "Engaging",
    6: "Growing",
    7: "Deepening",
    8: "Maturing",
    9: "Flourishing",
    10: "Abiding"
};


/**
 * Genera el system prompt basado en la personalidad del usuario
 * Default language: English
 */
function buildPersonalityPrompt(userProfile) {
    const {
        isPremium = false,
        selectedCompanion = null,
        customPersonality = null,
        age = 30,
        spiritualData = null,
        language = 'en' // Default English
    } = userProfile;

    // Calcular Life Stage
    const lifeStage = getLifeStage(age);
    
    // Obtener Spiritual Stage (default si no hay survey reciente)
    const spiritualStage = spiritualData?.spiritual_stage_name || "Awakening";
    const spiritualScore = spiritualData?.spiritual_score_percent || 10;
    const spiritualTier = spiritualData?.spiritual_tier || 1;
    
    let companionConfig;
    let companionName;
    
    if (isPremium && customPersonality) {
        // Usuario premium con personalidad custom
        companionName = customPersonality.name || "Companion";
        companionConfig = customPersonality;
    } else if (selectedCompanion && PREDEFINED_COMPANIONS[selectedCompanion.toLowerCase()]) {
        // Usuario free con companion predefinido
        companionConfig = PREDEFINED_COMPANIONS[selectedCompanion.toLowerCase()];
        companionName = companionConfig.name;
    } else {
        // Default: Ruth
        companionConfig = PREDEFINED_COMPANIONS.ruth;
        companionName = "Ruth";
    }
    
    // Construir prompt base (English by default)
    let systemPrompt = `
# COMPANION IDENTITY
You are {{companion_name}}, a Bible companion with the following characteristics:
- Personality Color: {{personality_color}}
- Communication Style: ${getStyleDescription(companionConfig)}

# LANGUAGE
Respond in English by default. If the user writes in another language, respond in that language.

# USER CONTEXT
- Life Stage: {{life_stage}} (${getLifeStageDescription(lifeStage)})
- Spiritual Journey: {{spiritual_stage_name}} (${spiritualScore}% - Tier {{spiritual_tier}})

# VOICE & TONE GUIDELINES
${companionConfig.systemPromptAddition || getDefaultVoiceGuidelines(companionConfig)}

# INTERACTION RULES
1. Always address the user with warmth appropriate to your personality
2. Reference their life stage when giving advice (${lifeStage} faces specific challenges)
3. Meet them at their spiritual level (${spiritualStage} - ${getSpiritualGuidance(spiritualTier)})
4. Use scripture naturally, not forced
5. Remember previous conversations and build on them
6. Be conversational, not preachy

# RESPONSE FORMAT
- Keep responses concise but meaningful (2-4 paragraphs max)
- End with a question or gentle prompt when appropriate
- Use your unique voice consistently
`;

    // Reemplazar variables
    systemPrompt = systemPrompt
        .replace(/\{\{companion_name\}\}/g, companionName)
        .replace(/\{\{personality_color\}\}/g, companionConfig.personalityColor || "Blue")
        .replace(/\{\{life_stage\}\}/g, lifeStage)
        .replace(/\{\{spiritual_stage_name\}\}/g, spiritualStage)
        .replace(/\{\{spiritual_score_percent\}\}/g, spiritualScore)
        .replace(/\{\{spiritual_tier\}\}/g, spiritualTier);
    
    return {
        systemPrompt,
        companionName,
        lifeStage,
        spiritualStage,
        spiritualTier
    };
}

function getStyleDescription(config) {
    const styles = [];
    if (config.gender) styles.push(`Voice: ${config.gender}`);
    if (config.accent) styles.push(`Accent: ${config.accent.replace(/_/g, ' ')}`);
    if (config.ageVibe) styles.push(`Age vibe: ${config.ageVibe.replace(/_/g, ' ')}`);
    if (config.speechSpeed) styles.push(`Pace: ${config.speechSpeed}`);
    if (config.emotionalTone) styles.push(`Tone: ${config.emotionalTone.replace(/_/g, ' ')}`);
    return styles.join(', ');
}

function getLifeStageDescription(stage) {
    const descriptions = {
        Explorer: "discovering identity, career, relationships - needs guidance without judgment",
        Builder: "establishing family, career, purpose - needs practical wisdom and encouragement",
        Guide: "mentoring others, facing transitions - needs affirmation and deeper meaning",
        Legacy: "reflecting on life, sharing wisdom - needs companionship and eternal perspective"
    };
    return descriptions[stage] || descriptions.Explorer;
}

function getSpiritualGuidance(tier) {
    if (tier <= 2) return "use simple language, focus on God's love, avoid heavy theology";
    if (tier <= 4) return "introduce basic concepts, encourage questions, build foundation";
    if (tier <= 6) return "explore deeper truths, challenge growth, connect dots";
    if (tier <= 8) return "discuss mature topics, encourage leadership, address doubts honestly";
    return "engage as spiritual peer, explore mysteries, support their ministry";
}

function getDefaultVoiceGuidelines(config) {
    const tone = config.emotionalTone || "warm_friendly";
    const guidelines = {
        calm_soothing: "Speak slowly and peacefully. Use phrases like 'Take a breath with me' and 'Let's sit with this together.'",
        warm_friendly: "Be approachable and encouraging. Use phrases like 'I hear you' and 'That makes so much sense.'",
        passionate_energetic: "Be enthusiastic and motivating. Use phrases like 'This is exciting!' and 'You've got this!'",
        gentle_grandmotherly: "Be nurturing and wise. Use phrases like 'Oh honey' and 'Let me share something with you.'"
    };
    return guidelines[tone] || guidelines.warm_friendly;
}


// ============================================================================
// FUNCIONES DE MEMORIA (heredadas del agente original)
// ============================================================================

/**
 * Buscar memorias relevantes usando búsqueda semántica
 * Encuentra conversaciones pasadas relacionadas con el mensaje actual
 */
async function getSemanticMemory(userId, userMessage, limit = 5) {
    try {
        const command = new RetrieveMemoryRecordsCommand({
            memoryId: MEMORY_ID,
            namespace: `/strategies/${SEMANTIC_STRATEGY_ID}/actors/${userId}`,
            searchCriteria: {
                searchQuery: userMessage,
                topK: limit
            }
        });
        
        const response = await agentcoreClient.send(command);
        const records = response.memoryRecordSummaries || [];
        
        if (records.length === 0) {
            return { hasSemanticMemory: false, context: "" };
        }
        
        // Formatear memorias relevantes
        const relevantMemories = records
            .filter(r => r.content?.text)
            .map(r => r.content.text.substring(0, 300))
            .slice(0, 3);
        
        if (relevantMemories.length === 0) {
            return { hasSemanticMemory: false, context: "" };
        }
        
        return {
            hasSemanticMemory: true,
            context: `\n\n[Relevant past conversations]\n${relevantMemories.join('\n---\n')}\n[End of relevant context]\n\n`
        };
        
    } catch (error) {
        console.log('Semantic search error (may be empty):', error.message);
        return { hasSemanticMemory: false, context: "" };
    }
}

/**
 * Obtener memoria reciente del usuario desde AgentCore
 */
async function getUserMemory(userId, limit = 5) {
    try {
        const sessionsCommand = new ListSessionsCommand({
            memoryId: MEMORY_ID,
            actorId: userId,
            maxResults: limit
        });
        
        const sessionsResponse = await agentcoreClient.send(sessionsCommand);
        const sessions = sessionsResponse.sessionSummaries || [];
        
        if (sessions.length === 0) {
            return { hasMemory: false, context: "" };
        }
        
        let memoryContext = [];
        
        for (const session of sessions.slice(0, 3)) {
            const eventsCommand = new ListEventsCommand({
                memoryId: MEMORY_ID,
                actorId: userId,
                sessionId: session.sessionId,
                maxResults: 10
            });
            
            const eventsResponse = await agentcoreClient.send(eventsCommand);
            const events = eventsResponse.events || [];
            
            for (const event of events) {
                if (event.payload && event.payload[0]?.conversational) {
                    const conv = event.payload[0].conversational;
                    const role = conv.role || 'USER';
                    const text = conv.content?.text || '';
                    if (text) {
                        memoryContext.push(`${role}: ${text.substring(0, 200)}`);
                    }
                }
            }
        }
        
        if (memoryContext.length === 0) {
            return { hasMemory: false, context: "" };
        }
        
        return {
            hasMemory: true,
            context: `\n\n[Previous conversations]\n${memoryContext.slice(0, 10).join('\n')}\n[End of context]\n\n`
        };
        
    } catch (error) {
        console.log('No memory found or error:', error.message);
        return { hasMemory: false, context: "" };
    }
}

/**
 * Obtener perfil del usuario (personalidad, edad, spiritual data)
 */
async function getUserProfile(userId) {
    try {
        // Buscar en memoria el perfil del usuario
        const sessionsCommand = new ListSessionsCommand({
            memoryId: MEMORY_ID,
            actorId: `profile-${userId}`,
            maxResults: 1
        });
        
        const response = await agentcoreClient.send(sessionsCommand);
        const sessions = response.sessionSummaries || [];
        
        if (sessions.length > 0) {
            const eventsCommand = new ListEventsCommand({
                memoryId: MEMORY_ID,
                actorId: `profile-${userId}`,
                sessionId: sessions[0].sessionId,
                maxResults: 1
            });
            
            const eventsResponse = await agentcoreClient.send(eventsCommand);
            const events = eventsResponse.events || [];
            
            if (events.length > 0 && events[0].payload?.[0]?.blob) {
                const profileData = JSON.parse(events[0].payload[0].blob.content);
                return profileData;
            }
        }
        
        // Perfil por defecto
        return {
            isPremium: false,
            selectedCompanion: "ruth",
            age: 30,
            spiritualData: {
                spiritual_stage_name: "Awakening",
                spiritual_score_percent: 10,
                spiritual_tier: 1,
                last_survey_at: null
            }
        };
        
    } catch (error) {
        console.log('Error getting profile:', error.message);
        return {
            isPremium: false,
            selectedCompanion: "ruth",
            age: 30,
            spiritualData: null
        };
    }
}

/**
 * Guardar interacción en AgentCore Memory
 */
async function saveToMemory(userId, sessionId, userMessage, assistantResponse, companionName) {
    try {
        const now = new Date();
        
        // Guardar mensaje del usuario
        await agentcoreClient.send(new CreateEventCommand({
            memoryId: MEMORY_ID,
            actorId: userId,
            sessionId: sessionId,
            eventTimestamp: now,
            payload: [{
                conversational: {
                    content: { text: userMessage },
                    role: "USER"
                }
            }]
        }));
        
        // Guardar respuesta del asistente con metadata del companion
        await agentcoreClient.send(new CreateEventCommand({
            memoryId: MEMORY_ID,
            actorId: userId,
            sessionId: sessionId,
            eventTimestamp: new Date(now.getTime() + 1000),
            payload: [{
                conversational: {
                    content: { text: `[${companionName}]: ${assistantResponse.substring(0, 5000)}` },
                    role: "ASSISTANT"
                }
            }]
        }));
        
        console.log(`✅ Memory saved for user ${userId} with companion ${companionName}`);
        return true;
        
    } catch (error) {
        console.error('Error saving to memory:', error.message);
        return false;
    }
}

/**
 * Procesar stream de Bedrock
 */
async function processStream(stream) {
    let fullResponse = '';
    try {
        for await (const chunk of stream) {
            if (chunk.chunk) {
                const decodedChunk = new TextDecoder().decode(chunk.chunk.bytes);
                fullResponse += decodedChunk;
            }
        }
        return fullResponse;
    } catch (error) {
        console.error('Error processing stream:', error);
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
        throw new Error('BACKEND_WEBHOOK_URL not configured');
    }
    
    await axios.post(webhookUrl, data, {
        headers: {
            'Content-Type': 'application/json',
            'x-webhook-secret': webhookSecret || '',
        },
        timeout: 10000,
    });
}


// ============================================================================
// HANDLER PRINCIPAL
// ============================================================================

exports.handler = async (event) => {
    console.log('Received event:', JSON.stringify(event, null, 2));
    
    for (const record of event.Records) {
        const startTime = Date.now();
        
        try {
            const message = JSON.parse(record.Sns.Message);
            const { 
                conversationId, 
                messageId, 
                userId, 
                text,
                // Nuevos campos para personalidad
                userProfile: incomingProfile = null
            } = message;
            
            console.log(`Processing message ${messageId} for user ${userId}`);
            
            if (!AGENT_ID || !ALIAS_ID) {
                throw new Error('Bedrock Agent configuration missing');
            }
            
            // 1. Obtener perfil del usuario (de la request o de memoria)
            console.log('👤 Loading user profile...');
            const userProfile = incomingProfile || await getUserProfile(userId);
            
            // 2. Construir personalidad
            console.log('🎭 Building personality prompt...');
            const personality = buildPersonalityPrompt(userProfile);
            console.log(`Companion: ${personality.companionName}, Life Stage: ${personality.lifeStage}, Spiritual: ${personality.spiritualStage}`);
            
            // 3. Obtener memoria del usuario (reciente + semántica)
            console.log('📚 Fetching user memory...');
            const [recentMemory, semanticMemory] = await Promise.all([
                getUserMemory(userId),
                getSemanticMemory(userId, text)
            ]);
            
            if (semanticMemory.hasSemanticMemory) {
                console.log('🔍 Found semantically relevant past conversations');
            }
            
            // 4. Construir prompt enriquecido
            const enrichedText = `
${personality.systemPrompt}

${recentMemory.hasMemory ? recentMemory.context : '[First conversation with this user]'}
${semanticMemory.hasSemanticMemory ? semanticMemory.context : ''}
User says: ${text}
`;
            
            // 5. Llamar a Bedrock Agent
            console.log('🤖 Invoking Bedrock Agent...');
            const command = new InvokeAgentCommand({
                agentId: AGENT_ID,
                agentAliasId: ALIAS_ID,
                sessionId: `session-${conversationId}`,
                inputText: enrichedText,
            });
            
            const response = await bedrockClient.send(command);
            
            if (!response.completion) {
                throw new Error('No completion received from Bedrock');
            }
            
            // 6. Procesar respuesta
            const responseText = await processStream(response.completion);
            const processingTime = Date.now() - startTime;
            
            console.log(`Response received in ${processingTime}ms`);
            
            // 7. Guardar en memoria
            console.log('💾 Saving to memory...');
            await saveToMemory(userId, `session-${conversationId}`, text, responseText, personality.companionName);
            
            // 8. Enviar respuesta al backend
            await sendToBackend({
                eventType: 'bedrock_response',
                conversationId,
                messageId: `ai-${messageId}`,
                responseText,
                timestamp: new Date().toISOString(),
                processingTimeMs: processingTime,
                // Metadata de personalidad
                companion: {
                    name: personality.companionName,
                    lifeStage: personality.lifeStage,
                    spiritualStage: personality.spiritualStage,
                    spiritualTier: personality.spiritualTier
                },
                hasMemoryContext: recentMemory.hasMemory,
                hasSemanticContext: semanticMemory.hasSemanticMemory,
                tokensUsed: {
                    input: Math.floor(enrichedText.length / 4),
                    output: Math.floor(responseText.length / 4),
                },
            });
            
            console.log(`✅ Response sent for message ${messageId}`);
            
        } catch (error) {
            console.error('❌ Error processing message:', error);
            
            try {
                const message = JSON.parse(record.Sns.Message);
                await sendToBackend({
                    eventType: 'processing_error',
                    conversationId: message.conversationId,
                    messageId: message.messageId,
                    error: error.message,
                    source: 'lambda-personality-agent',
                    timestamp: new Date().toISOString(),
                });
            } catch (notifyError) {
                console.error('Failed to notify backend:', notifyError);
            }
            
            throw error;
        }
    }
    
    console.log('✅ All messages processed');
};

// ============================================================================
// EXPORTS PARA TESTING Y API
// ============================================================================

module.exports.PREDEFINED_COMPANIONS = PREDEFINED_COMPANIONS;
module.exports.PERSONALITY_OPTIONS = PERSONALITY_OPTIONS;
module.exports.SPIRITUAL_STAGES = SPIRITUAL_STAGES;
module.exports.getLifeStage = getLifeStage;
module.exports.buildPersonalityPrompt = buildPersonalityPrompt;
module.exports.getSemanticMemory = getSemanticMemory;
