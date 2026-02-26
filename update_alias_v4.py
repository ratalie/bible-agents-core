"""Update alias to create new version from DRAFT"""
import boto3
import time

session = boto3.Session(profile_name='gpbible')
client = session.client('bedrock-agent', region_name='us-east-1')

AGENT_ID = 'OPFJ6RWI2P'

# Create a new alias - Bedrock should snapshot the DRAFT into a version
# Since we can't create versions directly, we create a new alias
# and let Bedrock handle versioning

# First, let's try updating the v3 alias to point to DRAFT
# This might auto-create a new version
try:
    print("Creating new alias KJV_Personality_v4...")
    response = client.create_agent_alias(
        agentId=AGENT_ID,
        agentAliasName='KJV_Personality_v4',
        description='v4 - KJV default + personality + semantic memory',
        routingConfiguration=[{
            'agentVersion': '3'  # Point to v3 for now
        }]
    )
    new_alias_id = response['agentAlias']['agentAliasId']
    print(f"Created alias: {new_alias_id}")
    
    # Now update the v3 alias to use the new DRAFT content
    # Actually, we need to update the existing v3 version
    # The only way is through the console or by updating the alias
    
except Exception as e:
    print(f"Error: {e}")

# Alternative: The TestAlias already points to DRAFT
# Just use TSTALIASID which always has the latest DRAFT
print("\n" + "=" * 60)
print("SOLUTION: Use TSTALIASID (points to DRAFT)")
print("The DRAFT already has the new prompt v2 (KJV + personalities)")
print("=" * 60)

# Verify DRAFT has the new prompt
agent = client.get_agent(agentId=AGENT_ID)['agent']
instruction = agent.get('instruction', '')
has_kjv = 'King James Version' in instruction
has_personality = 'Companion Personality System' in instruction
has_semantic = 'Memory Context' in instruction

print(f"\nDRAFT prompt verification:")
print(f"  KJV default: {'YES' if has_kjv else 'NO'}")
print(f"  Personality system: {'YES' if has_personality else 'NO'}")
print(f"  Memory context: {'YES' if has_semantic else 'NO'}")
print(f"  Prompt length: {len(instruction)} chars")

print(f"\nRecommendation:")
print(f"  Update Lambda env BEDROCK_AGENT_ALIAS_ID to: TSTALIASID")
print(f"  This alias always points to DRAFT (latest prompt)")
