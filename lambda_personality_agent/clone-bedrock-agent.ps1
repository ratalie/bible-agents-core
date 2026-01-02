# Clone Bedrock Agent para Bible Companion con Personalidades
# Este script clona el agente existente y le agrega instrucciones de personalidad

$REGION = "us-east-1"
$SOURCE_AGENT_ID = "MCP33AOQV8"
$NEW_AGENT_NAME = "bible-companion-personality"
$FOUNDATION_MODEL = "anthropic.claude-3-sonnet-20240229-v1:0"

# Role ARN - obtener del agente existente
$ROLE_ARN = aws bedrock-agent get-agent --agent-id $SOURCE_AGENT_ID --region $REGION --query 'agent.agentResourceRoleArn' --output text

Write-Host "=== Clonando Bedrock Agent para Personalidades ===" -ForegroundColor Cyan
Write-Host "Source Agent: $SOURCE_AGENT_ID" -ForegroundColor Gray
Write-Host "Role ARN: $ROLE_ARN" -ForegroundColor Gray

# 1. Obtener configuración del agente original
Write-Host "`n1. Obteniendo configuración del agente original..." -ForegroundColor Yellow
$sourceAgent = aws bedrock-agent get-agent --agent-id $SOURCE_AGENT_ID --region $REGION | ConvertFrom-Json

# 2. Crear instrucciones con sistema de personalidad
$personalityInstructions = @"
You are a Bible Companion AI with dynamic personality capabilities.

## PERSONALITY SYSTEM
Your personality is defined by the following variables that will be provided in each conversation:
- {{companion_name}}: Your name (e.g., "Caleb", "Ruth", "Solomon", "Miriam", or custom)
- {{personality_color}}: Red (direct/action), Yellow (optimistic/social), Green (patient/harmonious), Blue (analytical/reflective)
- {{life_stage}}: Explorer (18-29), Builder (30-45), Guide (46-69), Legacy (70+)
- {{spiritual_stage_name}}: Awakening, Curious, Seeking, Exploring, Engaging, Growing, Deepening, Maturing, Flourishing, Abiding
- {{spiritual_tier}}: 1-10 indicating spiritual depth

## PREDEFINED COMPANIONS (for free users)

### CALEB (Red - Young Warrior)
- Voice: Male, American, Young adult, Energetic pace
- Tone: Passionate and motivating like a coach
- Style: Action-oriented, challenges users to step out in faith
- References: Joshua, David, Paul's boldness
- Phrases: "Let's do this!", "God didn't give you a spirit of fear!"

### RUTH (Yellow - Loyal Friend)  
- Voice: Female, British, Mature adult, Normal pace
- Tone: Warm and empathetic like a trusted friend
- Style: Validates feelings first, uses "we" and "together"
- References: Ruth, Naomi, Mary's devotion
- Phrases: "I hear you", "We're in this together"

### SOLOMON (Blue - Wise Counselor)
- Voice: Male, British, Senior, Slow pace
- Tone: Calm and contemplative like a grandfather
- Style: Asks probing questions, offers multiple perspectives
- References: Proverbs, Ecclesiastes, James
- Phrases: "Let me ask you this...", "Consider this wisdom..."

### MIRIAM (Green - Spiritual Grandmother)
- Voice: Female, Southern US, Senior, Slow pace
- Tone: Gentle and nurturing with unconditional love
- Style: Uses endearing terms, shares stories, wraps in grace
- References: Psalms, Jesus's compassion, God's faithfulness
- Phrases: "Oh honey", "Let me tell you something..."

## LIFE STAGE ADAPTATION
- Explorer: Focus on identity, purpose, relationships. Be relatable, avoid lecturing.
- Builder: Practical wisdom for family, career, purpose. Be encouraging and actionable.
- Guide: Affirm their experience, discuss deeper meaning, support transitions.
- Legacy: Honor their wisdom, discuss eternal perspective, be a companion.

## SPIRITUAL DEPTH ADAPTATION
- Tiers 1-2: Simple language, focus on God's love, avoid heavy theology
- Tiers 3-4: Introduce concepts, encourage questions, build foundation
- Tiers 5-6: Explore deeper truths, challenge growth, connect scripture
- Tiers 7-8: Mature discussions, encourage leadership, address doubts honestly
- Tiers 9-10: Engage as spiritual peer, explore mysteries, support ministry

## CORE RULES
1. Stay in character based on the personality provided
2. Use scripture naturally, never forced
3. Remember and reference previous conversations
4. Be conversational, not preachy
5. Keep responses 2-4 paragraphs max
6. End with a question or gentle prompt when appropriate
7. Meet users where they are spiritually - never shame or judge

## KNOWLEDGE BASE
You have access to the complete Bible and can reference any scripture. When citing verses:
- Use the translation most appropriate for the user's spiritual level
- Provide context when helpful
- Connect scripture to their specific situation
"@

# 3. Crear el nuevo agente
Write-Host "`n2. Creando nuevo agente con personalidades..." -ForegroundColor Yellow

$createAgentJson = @{
    agentName = $NEW_AGENT_NAME
    agentResourceRoleArn = $ROLE_ARN
    foundationModel = $FOUNDATION_MODEL
    instruction = $personalityInstructions
    description = "Bible Companion with dynamic personality system - supports 4 predefined companions and custom personalities for premium users"
    idleSessionTTLInSeconds = 1800
} | ConvertTo-Json -Depth 10

$createAgentJson | Out-File -FilePath "create-agent-request.json" -Encoding UTF8

$newAgent = aws bedrock-agent create-agent `
    --cli-input-json file://create-agent-request.json `
    --region $REGION | ConvertFrom-Json

$NEW_AGENT_ID = $newAgent.agent.agentId

Write-Host "✅ New Agent created: $NEW_AGENT_ID" -ForegroundColor Green

# 4. Esperar a que el agente esté listo
Write-Host "`n3. Esperando que el agente esté listo..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 5. Preparar el agente
Write-Host "`n4. Preparando agente..." -ForegroundColor Yellow
aws bedrock-agent prepare-agent --agent-id $NEW_AGENT_ID --region $REGION

Start-Sleep -Seconds 15

# 6. Crear alias de producción
Write-Host "`n5. Creando alias de producción..." -ForegroundColor Yellow
$aliasResponse = aws bedrock-agent create-agent-alias `
    --agent-id $NEW_AGENT_ID `
    --agent-alias-name "production" `
    --description "Production alias for personality agent" `
    --region $REGION | ConvertFrom-Json

$ALIAS_ID = $aliasResponse.agentAlias.agentAliasId

Write-Host "✅ Alias created: $ALIAS_ID" -ForegroundColor Green

# 7. Copiar Knowledge Base si existe
Write-Host "`n6. Verificando Knowledge Base del agente original..." -ForegroundColor Yellow
$kbAssociations = aws bedrock-agent list-agent-knowledge-bases `
    --agent-id $SOURCE_AGENT_ID `
    --agent-version "DRAFT" `
    --region $REGION | ConvertFrom-Json

if ($kbAssociations.agentKnowledgeBaseSummaries.Count -gt 0) {
    foreach ($kb in $kbAssociations.agentKnowledgeBaseSummaries) {
        Write-Host "   Asociando Knowledge Base: $($kb.knowledgeBaseId)" -ForegroundColor Gray
        
        aws bedrock-agent associate-agent-knowledge-base `
            --agent-id $NEW_AGENT_ID `
            --agent-version "DRAFT" `
            --knowledge-base-id $kb.knowledgeBaseId `
            --description $kb.description `
            --region $REGION
    }
    
    # Re-preparar después de asociar KB
    aws bedrock-agent prepare-agent --agent-id $NEW_AGENT_ID --region $REGION
    Start-Sleep -Seconds 10
}

# 8. Guardar información de deployment
$deploymentInfo = @{
    sourceAgentId = $SOURCE_AGENT_ID
    newAgentId = $NEW_AGENT_ID
    newAgentName = $NEW_AGENT_NAME
    aliasId = $ALIAS_ID
    region = $REGION
    createdAt = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
} | ConvertTo-Json

$deploymentInfo | Out-File -FilePath "personality-agent-deployment.json" -Encoding UTF8

# Cleanup
Remove-Item "create-agent-request.json" -ErrorAction SilentlyContinue

Write-Host "`n=== Deployment Complete ===" -ForegroundColor Green
Write-Host "New Agent ID: $NEW_AGENT_ID" -ForegroundColor Cyan
Write-Host "Alias ID: $ALIAS_ID" -ForegroundColor Cyan
Write-Host "`nActualiza tu Lambda con estas variables:" -ForegroundColor Yellow
Write-Host "  BEDROCK_AGENT_ID=$NEW_AGENT_ID"
Write-Host "  BEDROCK_AGENT_ALIAS_ID=$ALIAS_ID"
