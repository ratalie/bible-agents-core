/**
 * API de Personalidades para el Backend
 * 
 * Este módulo provee endpoints para:
 * - Obtener companions predefinidos (FREE users)
 * - Configurar personalidad custom (PREMIUM users)
 * - Calcular Life Stage
 * - Manejar Spiritual Survey
 */

const { BedrockAgentCoreClient, CreateEventCommand, ListSessionsCommand, ListEventsCommand } = require("@aws-sdk/client-bedrock-agentcore");

const MEMORY_ID = process.env.AGENTCORE_MEMORY_ID || 'memory_bqdqb-jtj3lc48bl';

const agentcoreClient = new BedrockAgentCoreClient({
    region: process.env.AWS_REGION || 'us-east-1'
});

// ============================================================================
// COMPANIONS PREDEFINIDOS (FREE USERS)
// ============================================================================

const PREDEFINED_COMPANIONS = {
    caleb: {
        id: "caleb",
        name: "Caleb",
        description: "Joven guerrero de fe, energético y motivador",
        avatar: "/avatars/caleb.png",
        previewVoice: "/voices/caleb-preview.mp3",
        traits: {
            gender: "male",
            accent: "american",
            ageVibe: "young_adult",
            speechSpeed: "energetic",
            emotionalTone: "passionate",
            personalityColor: "Red"
        },
        tagline: "¡Vamos a conquistar este día juntos!"
    },
    ruth: {
        id: "ruth",
        name: "Ruth",
        description: "Compañera leal, cálida y empática",
        avatar: "/avatars/ruth.png",
        previewVoice: "/voices/ruth-preview.mp3",
        traits: {
            gender: "female",
            accent: "british_rp",
            ageVibe: "mature_adult",
            speechSpeed: "normal",
            emotionalTone: "warm_friendly",
            personalityColor: "Yellow"
        },
        tagline: "Estoy aquí para caminar contigo"
    },
    solomon: {
        id: "solomon",
        name: "Solomon",
        description: "Sabio consejero, reflexivo y profundo",
        avatar: "/avatars/solomon.png",
        previewVoice: "/voices/solomon-preview.mp3",
        traits: {
            gender: "male",
            accent: "british_rp",
            ageVibe: "senior",
            speechSpeed: "slow",
            emotionalTone: "calm_soothing",
            personalityColor: "Blue"
        },
        tagline: "La sabiduría comienza con una pregunta"
    },
    miriam: {
        id: "miriam",
        name: "Miriam",
        description: "Abuela espiritual, amorosa y reconfortante",
        avatar: "/avatars/miriam.png",
        previewVoice: "/voices/miriam-preview.mp3",
        traits: {
            gender: "female",
            accent: "southern_us",
            ageVibe: "senior",
            speechSpeed: "slow",
            emotionalTone: "gentle_grandmotherly",
            personalityColor: "Green"
        },
        tagline: "Ven, siéntate conmigo un momento"
    }
};

// ============================================================================
// OPCIONES PREMIUM
// ============================================================================

const PERSONALITY_OPTIONS = {
    gender: [
        { value: "male", label: "Masculino", icon: "👨" },
        { value: "female", label: "Femenino", icon: "👩" }
    ],
    accent: [
        { value: "american", label: "Americano", flag: "🇺🇸" },
        { value: "british_rp", label: "Británico", flag: "🇬🇧" },
        { value: "australian", label: "Australiano", flag: "🇦🇺" },
        { value: "african_american_aave", label: "Afroamericano", flag: "🇺🇸" },
        { value: "southern_us", label: "Sureño (US)", flag: "🇺🇸" },
        { value: "canadian", label: "Canadiense", flag: "🇨🇦" },
        { value: "indian_english", label: "Indio", flag: "🇮🇳" },
        { value: "latin_american", label: "Latinoamericano", flag: "🌎" }
    ],
    ageVibe: [
        { value: "young_adult", label: "Joven (20s)", description: "Energético, relatable" },
        { value: "mature_adult", label: "Adulto (30-50)", description: "Experimentado, balanceado" },
        { value: "senior", label: "Mayor (60+)", description: "Sabio, reconfortante" }
    ],
    speechSpeed: [
        { value: "slow", label: "Pausado", description: "Para reflexión profunda" },
        { value: "normal", label: "Normal", description: "Conversacional" },
        { value: "energetic", label: "Energético", description: "Motivador, dinámico" }
    ],
    emotionalTone: [
        { value: "calm_soothing", label: "Calmado", emoji: "🧘", description: "Paz y serenidad" },
        { value: "warm_friendly", label: "Cálido", emoji: "🤗", description: "Amigable y cercano" },
        { value: "passionate_energetic", label: "Apasionado", emoji: "🔥", description: "Inspirador y motivador" },
        { value: "gentle_grandmotherly", label: "Tierno", emoji: "💝", description: "Amoroso y reconfortante" }
    ],
    personalityColor: [
        { value: "Red", label: "Rojo", hex: "#E53935", trait: "Directo, orientado a acción" },
        { value: "Yellow", label: "Amarillo", hex: "#FDD835", trait: "Optimista, social" },
        { value: "Green", label: "Verde", hex: "#43A047", trait: "Paciente, armonioso" },
        { value: "Blue", label: "Azul", hex: "#1E88E5", trait: "Analítico, reflexivo" }
    ]
};


// ============================================================================
// SPIRITUAL SURVEY (cada 90 días)
// ============================================================================

const SPIRITUAL_SURVEY_QUESTIONS = [
    {
        id: 1,
        question: "¿Con qué frecuencia lees la Biblia?",
        options: [
            { value: 1, label: "Raramente o nunca" },
            { value: 2, label: "Algunas veces al mes" },
            { value: 3, label: "Semanalmente" },
            { value: 4, label: "Varios días a la semana" },
            { value: 5, label: "Diariamente" }
        ]
    },
    {
        id: 2,
        question: "¿Cómo describirías tu vida de oración?",
        options: [
            { value: 1, label: "No oro regularmente" },
            { value: 2, label: "Oro en momentos de necesidad" },
            { value: 3, label: "Oro regularmente pero brevemente" },
            { value: 4, label: "Tengo tiempos dedicados de oración" },
            { value: 5, label: "La oración es constante en mi día" }
        ]
    },
    {
        id: 3,
        question: "¿Participas en una comunidad de fe?",
        options: [
            { value: 1, label: "No actualmente" },
            { value: 2, label: "Ocasionalmente" },
            { value: 3, label: "Asisto regularmente" },
            { value: 4, label: "Participo activamente" },
            { value: 5, label: "Sirvo y lidero en mi comunidad" }
        ]
    },
    {
        id: 4,
        question: "¿Cómo manejas los momentos difíciles?",
        options: [
            { value: 1, label: "Me cuesta encontrar paz" },
            { value: 2, label: "A veces recurro a mi fe" },
            { value: 3, label: "Busco a Dios pero con dudas" },
            { value: 4, label: "Confío en Dios aunque no entienda" },
            { value: 5, label: "Encuentro paz profunda en Dios" }
        ]
    },
    {
        id: 5,
        question: "¿Compartes tu fe con otros?",
        options: [
            { value: 1, label: "Me incomoda hablar de fe" },
            { value: 2, label: "Solo si me preguntan" },
            { value: 3, label: "Ocasionalmente comparto" },
            { value: 4, label: "Busco oportunidades naturales" },
            { value: 5, label: "Es parte natural de mi vida" }
        ]
    },
    {
        id: 6,
        question: "¿Cómo aplicas la Biblia a tu vida diaria?",
        options: [
            { value: 1, label: "No sé cómo aplicarla" },
            { value: 2, label: "A veces pienso en versículos" },
            { value: 3, label: "Intento aplicar lo que leo" },
            { value: 4, label: "Guía muchas de mis decisiones" },
            { value: 5, label: "Es el fundamento de mi vida" }
        ]
    },
    {
        id: 7,
        question: "¿Cómo es tu relación personal con Jesús?",
        options: [
            { value: 1, label: "Estoy explorando quién es" },
            { value: 2, label: "Creo pero me siento distante" },
            { value: 3, label: "Tengo una relación en desarrollo" },
            { value: 4, label: "Es mi amigo y Salvador" },
            { value: 5, label: "Es el centro de mi existencia" }
        ]
    },
    {
        id: 8,
        question: "¿Practicas el perdón?",
        options: [
            { value: 1, label: "Me cuesta mucho perdonar" },
            { value: 2, label: "Perdono eventualmente" },
            { value: 3, label: "Intento perdonar pronto" },
            { value: 4, label: "El perdón es importante para mí" },
            { value: 5, label: "Perdono como Cristo me perdonó" }
        ]
    },
    {
        id: 9,
        question: "¿Cómo manejas tus finanzas en relación a tu fe?",
        options: [
            { value: 1, label: "No conecto fe y finanzas" },
            { value: 2, label: "Doy ocasionalmente" },
            { value: 3, label: "Diezmo o doy regularmente" },
            { value: 4, label: "Soy generoso más allá del diezmo" },
            { value: 5, label: "Todo lo que tengo es de Dios" }
        ]
    },
    {
        id: 10,
        question: "¿Buscas crecer espiritualmente?",
        options: [
            { value: 1, label: "No activamente" },
            { value: 2, label: "Cuando tengo tiempo" },
            { value: 3, label: "Es una meta para mí" },
            { value: 4, label: "Busco activamente crecer" },
            { value: 5, label: "Es mi prioridad principal" }
        ]
    },
    {
        id: 11,
        question: "¿Cómo respondes cuando pecas o fallas?",
        options: [
            { value: 1, label: "Me siento condenado" },
            { value: 2, label: "Trato de olvidarlo" },
            { value: 3, label: "Pido perdón a Dios" },
            { value: 4, label: "Me arrepiento y busco cambiar" },
            { value: 5, label: "Experimento gracia y transformación" }
        ]
    },
    {
        id: 12,
        question: "¿Sirves a otros?",
        options: [
            { value: 1, label: "Raramente" },
            { value: 2, label: "Cuando es conveniente" },
            { value: 3, label: "Busco oportunidades" },
            { value: 4, label: "Sirvo regularmente" },
            { value: 5, label: "Mi vida es servicio" }
        ]
    },
    {
        id: 13,
        question: "¿Experimentas gozo en tu fe?",
        options: [
            { value: 1, label: "La fe se siente como obligación" },
            { value: 2, label: "A veces siento gozo" },
            { value: 3, label: "Generalmente disfruto mi fe" },
            { value: 4, label: "Mi fe me da gozo profundo" },
            { value: 5, label: "Reboso de gozo en Cristo" }
        ]
    },
    {
        id: 14,
        question: "¿Cómo ves tu futuro espiritual?",
        options: [
            { value: 1, label: "Incierto" },
            { value: 2, label: "Espero mejorar" },
            { value: 3, label: "Confío en el proceso" },
            { value: 4, label: "Emocionado por crecer" },
            { value: 5, label: "Seguro en las manos de Dios" }
        ]
    }
];

/**
 * Calcula el Spiritual Stage basado en respuestas del survey
 */
function calculateSpiritualStage(answers) {
    // answers es un array de valores 1-5 para cada pregunta
    const totalScore = answers.reduce((sum, val) => sum + val, 0);
    const maxScore = answers.length * 5;
    const percentage = Math.round((totalScore / maxScore) * 100);
    
    // Mapear a tier 1-10
    let tier;
    if (percentage <= 10) tier = 1;
    else if (percentage <= 20) tier = 2;
    else if (percentage <= 30) tier = 3;
    else if (percentage <= 40) tier = 4;
    else if (percentage <= 50) tier = 5;
    else if (percentage <= 60) tier = 6;
    else if (percentage <= 70) tier = 7;
    else if (percentage <= 80) tier = 8;
    else if (percentage <= 90) tier = 9;
    else tier = 10;
    
    const stageNames = {
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
    
    return {
        spiritual_stage_name: stageNames[tier],
        spiritual_score_percent: percentage,
        spiritual_tier: tier,
        last_survey_at: new Date().toISOString()
    };
}

/**
 * Calcula Life Stage basado en edad
 */
function calculateLifeStage(birthDate) {
    const today = new Date();
    const birth = new Date(birthDate);
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
        age--;
    }
    
    if (age >= 18 && age <= 29) return { stage: "Explorer", age };
    if (age >= 30 && age <= 45) return { stage: "Builder", age };
    if (age >= 46 && age <= 69) return { stage: "Guide", age };
    if (age >= 70) return { stage: "Legacy", age };
    return { stage: "Explorer", age };
}

