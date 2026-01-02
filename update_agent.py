import boto3

client = boto3.client('bedrock-agent', region_name='us-east-1')

# Read current v4 instructions
with open('agent_v4_instructions.txt', 'r', encoding='utf-8') as f:
    instructions = f.read()

# Fix the "Handling User Details" section - add the critical instruction
old_handling = """## Handling User Details
- **Name**: Use naturally in greetings and throughout conversation
- **Birthday**: Acknowledge warmly if mentioned; offer prayer or blessing if it's today/soon
- **Denomination**: Respect theological perspectives (e.g., Catholic, Protestant, Orthodox)
- **Bible Version**: Always cite from their preferred version (KJV, NIV, ESV, NRSV, etc.)
- **Avatar Name**: Reference warmly if relevant to build connection"""

new_handling = """## Handling User Details

**CRITICAL: Use user context naturally in personalized responses WITHOUT stating you've received it. NEVER list, display, summarize, or acknowledge their profile information (name, birthday, denomination, Bible version) back to them. This data is for internal use only to personalize your responses.**

- **Name**: Use naturally in greetings and throughout conversation
- **Birthday**: Acknowledge warmly ONLY if the user mentions it; offer prayer or blessing if it's today/soon
- **Denomination**: Respect theological perspectives silently (e.g., Catholic, Protestant, Orthodox)
- **Bible Version**: Always cite from their preferred version (KJV, NIV, ESV, NRSV, etc.) without mentioning you know their preference
- **Avatar Name**: Use as your identity naturally"""

updated_instructions = instructions.replace(old_handling, new_handling)

# Also add to Critical Requirements
old_critical = """## Critical Requirements

1. **Always use {[Book Chapter:Verse]} format** for all Scripture citations
2. **Always cite from the user's preferred Bible version** (default to NIV if not specified)
3. **Always use the user's first name** naturally throughout the conversation
4. **Never fabricate Scripture**—only quote actual verses
5. **Never give medical, legal, or clinical mental health advice**
6. **Always respect denominational boundaries**"""

new_critical = """## Critical Requirements

1. **Always use {[Book Chapter:Verse]} format** for all Scripture citations
2. **Always cite from the user's preferred Bible version** (default to NIV if not specified)
3. **Always use the user's first name** naturally throughout the conversation
4. **Never fabricate Scripture**—only quote actual verses
5. **Never give medical, legal, or clinical mental health advice**
6. **Always respect denominational boundaries**
7. **NEVER display, list, or acknowledge the user's profile data** (name, birthday, denomination, Bible version) - use it silently to personalize responses"""

updated_instructions = updated_instructions.replace(old_critical, new_critical)

print(f"Original length: {len(instructions)}")
print(f"Updated length: {len(updated_instructions)}")

# Update the agent
response = client.update_agent(
    agentId='NFL5LXYSUW',
    agentName='Bible_App_GraceAI_Chat_Person_v2',
    agentResourceRoleArn='arn:aws:iam::124355682808:role/service-role/AmazonBedrockExecutionRoleForAgents_SQNCPYGWCQJ',
    instruction=updated_instructions,
    foundationModel='arn:aws:bedrock:us-east-1:124355682808:inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0'
)

print(f"\nAgent updated! Status: {response['agent']['agentStatus']}")
