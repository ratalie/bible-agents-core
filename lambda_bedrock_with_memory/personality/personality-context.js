/**
 * Personality Context Builder
 *
 * Genera contexto de personalidad basado en:
 * - Personality Color (DISC: Red, Yellow, Green, Blue)
 * - Spiritual Depth (10 niveles basados en porcentaje 0-100)
 * - Life Stage (basado en edad: Explorer, Builder, Guide, Legacy)
 *
 * Este contexto se inyecta como prefijo al inputText del Bedrock Agent
 * para ajustar tono y estilo sin modificar el prompt del sistema.
 */

const PERSONALITY_COLORS = {
  red: {
    name: "Red",
    disc: "Dominant (D)",
    toneAdjustment:
      "Respond with directness and action-orientation. Be concise and results-focused. Use confident, motivational language. Challenge the user to take action.",
    communicationStyle:
      "Get to the point quickly. Focus on outcomes and next steps. Use strong, decisive language.",
    scriptureApproach:
      "Present scripture as actionable principles. Emphasize verses about courage, leadership, and overcoming challenges.",
  },
  yellow: {
    name: "Yellow",
    disc: "Influential (I)",
    toneAdjustment:
      "Respond with enthusiasm and warmth. Be engaging and personable. Use encouraging, optimistic language. Celebrate and inspire.",
    communicationStyle:
      "Be conversational and energetic. Use stories and examples. Show excitement and positivity.",
    scriptureApproach:
      "Present scripture with stories and context. Emphasize verses about joy, community, and God's love.",
  },
  green: {
    name: "Green",
    disc: "Steady (S)",
    toneAdjustment:
      "Respond with patience and gentleness. Be calm and reassuring. Use supportive, empathetic language. Take time to explain.",
    communicationStyle:
      "Be patient and understanding. Listen carefully. Provide steady support. Avoid rushing.",
    scriptureApproach:
      "Present scripture with care and context. Emphasize verses about peace, patience, and God's faithfulness.",
  },
  blue: {
    name: "Blue",
    disc: "Conscientious (C)",
    toneAdjustment:
      "Respond with thoughtfulness and precision. Be thorough and analytical. Use methodical, detailed language. Show depth of understanding.",
    communicationStyle:
      "Be thorough and precise. Provide detailed explanations. Use logical structure. Ask clarifying questions.",
    scriptureApproach:
      "Present scripture with context and analysis. Emphasize verses about wisdom, understanding, and God's plan.",
  },
};

const LIFE_STAGES = {
  explorer: {
    ages: [18, 29],
    name: "Explorer",
    description: "Young adults exploring faith and life",
    guidance:
      "Address their search for identity and purpose. Be relatable and authentic. Focus on questions about career, relationships, and calling.",
    depth:
      "Use accessible language. Connect scripture to their daily life experiences.",
  },
  builder: {
    ages: [30, 45],
    name: "Builder",
    description: "Adults building careers and families",
    guidance:
      "Address practical life challenges. Focus on balance, priorities, and building strong foundations. Be practical and actionable.",
    depth:
      "Provide practical biblical application. Connect to work, family, and life management.",
  },
  guide: {
    ages: [46, 69],
    name: "Guide",
    description: "Mature adults mentoring others",
    guidance:
      "Respect their wisdom and experience. Focus on legacy, impact, and deeper spiritual maturity. Be thoughtful and reflective.",
    depth:
      "Engage at deeper theological level. Reference complex concepts and mature faith practices.",
  },
  legacy: {
    ages: [70, 120],
    name: "Legacy",
    description: "Seniors leaving a lasting impact",
    guidance:
      "Honor their life experience. Focus on reflection, wisdom sharing, and eternal perspective. Be respectful and gentle.",
    depth:
      "Engage with profound spiritual concepts. Focus on eternal perspective and wisdom.",
  },
};

const SPIRITUAL_DEPTH_LEVELS = {
  1: {
    stageName: "Awakening",
    description: "Brand-new or re-starting seeker",
    approach:
      "Use simple, clear language. Focus on God's love and grace. Avoid theological complexity. Be patient and encouraging.",
    depth: "Use foundational verses. Explain context simply.",
  },
  2: {
    stageName: "Exploring",
    description: "Curious, inconsistent practice",
    approach:
      "Encourage curiosity. Help build basic habits. Be supportive. Don't overwhelm.",
    depth: "Introduce key stories and themes. Connect verses to daily life.",
  },
  3: {
    stageName: "Engaging",
    description: "Building basic habits",
    approach:
      "Help establish regular practices. Be encouraging about growth. Provide clear guidance.",
    depth: "Use clear, practical verses. Show how faith applies daily.",
  },
  4: {
    stageName: "Growing",
    description: "Regular practice emerging",
    approach:
      "Support their growing consistency. Celebrate progress. Provide deeper insights.",
    depth: "Use more context. Connect verses to spiritual growth.",
  },
  5: {
    stageName: "Rooting",
    description: "Faith becoming a real anchor",
    approach:
      "Acknowledge their deepening faith. Provide mature guidance. Encourage service.",
    depth: "Use verses with theological depth. Discuss spiritual disciplines.",
  },
  6: {
    stageName: "Flourishing",
    description: "Daily rhythm, joy increasing",
    approach:
      "Engage with their daily rhythm. Provide advanced insights. Encourage mentoring.",
    depth: "Use complex passages. Discuss deeper meanings.",
  },
  7: {
    stageName: "Anchoring",
    description: "Deep strength, mentoring others",
    approach:
      "Respect their spiritual maturity. Provide profound insights. Focus on service.",
    depth: "Reference advanced theology. Explore deeper spiritual concepts.",
  },
  8: {
    stageName: "Transforming",
    description: "Life is being reshaped",
    approach:
      "Engage at deep level. Trust their maturity. Focus on transformation.",
    depth: "Use complex theological concepts. Discuss life transformation.",
  },
  9: {
    stageName: "Radiating",
    description: "Walking in authority & intimacy",
    approach:
      "Engage at expert level. Reference advanced concepts. Focus on authority.",
    depth: "Use profound theological passages. Discuss spiritual authority.",
  },
  10: {
    stageName: "Abiding",
    description: "Fully surrendered, Christlike reflex",
    approach:
      "Engage at deepest level. Reference complex concepts. Trust full maturity.",
    depth: "Reference complex theology. Explore deepest spiritual meanings.",
  },
};

/**
 * Obtiene el Life Stage basado en la edad
 */
function getLifeStage(age) {
  if (age >= 18 && age <= 29) return LIFE_STAGES.explorer;
  if (age >= 30 && age <= 45) return LIFE_STAGES.builder;
  if (age >= 46 && age <= 69) return LIFE_STAGES.guide;
  if (age >= 70) return LIFE_STAGES.legacy;
  return LIFE_STAGES.explorer; // Default
}

/**
 * Mapea porcentaje de profundidad espiritual (0-100) a nivel (1-10)
 */
function getSpiritualLevel(percentage) {
  if (percentage <= 10 || !percentage) return 1;
  if (percentage <= 20) return 2;
  if (percentage <= 30) return 3;
  if (percentage <= 40) return 4;
  if (percentage <= 50) return 5;
  if (percentage <= 60) return 6;
  if (percentage <= 70) return 7;
  if (percentage <= 80) return 8;
  if (percentage <= 90) return 9;
  return 10;
}

/**
 * Valida y normaliza el userProfile
 */
function validateUserProfile(userProfile) {
  const validColors = ["red", "yellow", "green", "blue"];
  const validLanguages = ["en", "es"];
  const color = userProfile?.personalityColor?.toLowerCase();
  const language = userProfile?.language?.toLowerCase();

  return {
    personalityColor: validColors.includes(color) ? color : "blue",
    spiritualDepthPercent: Math.max(
      0,
      Math.min(100, userProfile?.spiritualDepthPercent || 10)
    ),
    age: Math.max(18, Math.min(120, userProfile?.age || 30)),
    language: validLanguages.includes(language) ? language : "en",
  };
}

/**
 * Construye el contexto de personalidad que se inyecta al inputText
 *
 * @param {Object} userProfile - Perfil del usuario
 * @param {string} userProfile.personalityColor - "red", "yellow", "green", o "blue"
 * @param {number} userProfile.spiritualDepthPercent - 0-100
 * @param {number} userProfile.age - Edad del usuario
 * @param {string} userProfile.language - "en" o "es"
 * @returns {string} Contexto de personalidad formateado
 */
function buildPersonalityContext(userProfile) {
  if (!userProfile) {
    return "";
  }

  // Validar y normalizar
  const validated = validateUserProfile(userProfile);

  // Obtener configuraciones
  const colorConfig = PERSONALITY_COLORS[validated.personalityColor];
  const lifeStage = getLifeStage(validated.age);
  const spiritualLevel = getSpiritualLevel(validated.spiritualDepthPercent);
  const spiritualConfig = SPIRITUAL_DEPTH_LEVELS[spiritualLevel];

  // Mapeo de códigos de idioma a nombres
  const languageNames = {
    en: "English",
    es: "Spanish (Español)",
  };

  const languageName = languageNames[validated.language] || "English";

  // Construir contexto con instrucción de idioma al inicio
  const context = `[PERSONALITY CONTEXT - Adjust your response tone and style based on this, but maintain all your core identity and response structure]

**CRITICAL LANGUAGE INSTRUCTION:**
You MUST respond in ${languageName} (${validated.language}).
- The user may write in any language, but you MUST always respond in ${languageName}.
- This is the user's preferred language setting.
- Do not switch languages mid-conversation.
- If the user writes in a different language, acknowledge it but continue responding in ${languageName}.

PERSONALITY COLOR: ${colorConfig.name} (${colorConfig.disc})
${colorConfig.toneAdjustment}
COMMUNICATION STYLE: ${colorConfig.communicationStyle}
SCRIPTURE APPROACH: ${colorConfig.scriptureApproach}

USER LIFE STAGE: ${lifeStage.name} (Ages ${lifeStage.ages[0]}-${lifeStage.ages[1]})
${lifeStage.description}
- Guidance: ${lifeStage.guidance}
- Depth Adjustment: ${lifeStage.depth}

SPIRITUAL DEPTH LEVEL: ${spiritualConfig.stageName} (Level ${spiritualLevel}, ${validated.spiritualDepthPercent}%)
${spiritualConfig.description}
- Approach: ${spiritualConfig.approach}
- Scripture Depth: ${spiritualConfig.depth}

[Now respond to the user's message below, maintaining your core identity but adjusting tone, style, and depth according to the above context. ALWAYS respond in ${languageName} (${validated.language})]`;

  return context;
}

module.exports = {
  buildPersonalityContext,
  getLifeStage,
  getSpiritualLevel,
  validateUserProfile,
  PERSONALITY_COLORS,
  LIFE_STAGES,
  SPIRITUAL_DEPTH_LEVELS,
};
