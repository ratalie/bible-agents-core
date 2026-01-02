import boto3
import time

client = boto3.client('bedrock-agent', region_name='us-east-1')

AGENT_ID = 'NFL5LXYSUW'
PROD_ALIAS_ID = 'CKLXTRRBZA'

# Workaround: Create a temporary alias which forces a version to be created
# Then update the production alias to use that version

print("Step 1: Creating temporary alias to force version creation...")

# First, let's see what versions exist
versions = client.list_agent_versions(agentId=AGENT_ID)
existing_versions = [v['agentVersion'] for v in versions['agentVersionSummaries'] if v['agentVersion'] != 'DRAFT']
print(f"Existing versions: {existing_versions}")

# The highest version number
max_version = max([int(v) for v in existing_versions])
print(f"Max version: {max_version}")

# Try creating alias with a specific version requirement
# This might trigger version creation
try:
    # Create a new alias - this should create a new version from DRAFT
    temp_alias = client.create_agent_alias(
        agentId=AGENT_ID,
        agentAliasName=f'temp-v{max_version + 1}-creator',
        description='Temporary alias to create new version'
    )
    print(f"Created temp alias: {temp_alias['agentAlias']['agentAliasId']}")
    
    # Wait for it to be ready
    time.sleep(5)
    
    # Check what version it created
    alias_info = client.get_agent_alias(
        agentId=AGENT_ID, 
        agentAliasId=temp_alias['agentAlias']['agentAliasId']
    )
    new_version = alias_info['agentAlias']['routingConfiguration'][0]['agentVersion']
    print(f"New version created: {new_version}")
    
    # Now update production alias to use this version
    print(f"\nStep 2: Updating production alias to version {new_version}...")
    client.update_agent_alias(
        agentId=AGENT_ID,
        agentAliasId=PROD_ALIAS_ID,
        agentAliasName='Bible_App_GraceAI_Chat_Person_v2_v4',
        routingConfiguration=[{'agentVersion': new_version}]
    )
    print("✅ Production alias updated!")
    
    # Delete temp alias
    print("\nStep 3: Cleaning up temp alias...")
    client.delete_agent_alias(
        agentId=AGENT_ID,
        agentAliasId=temp_alias['agentAlias']['agentAliasId']
    )
    print("✅ Temp alias deleted")
    
    print(f"\n🎉 Done! Production alias now points to version {new_version}")
    
except Exception as e:
    print(f"Error: {e}")
