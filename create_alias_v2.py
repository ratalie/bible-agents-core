"""Create new version and alias for the updated agent prompt"""
import boto3
import time

client = boto3.client('bedrock-agent', region_name='us-east-1')
AGENT_ID = 'OPFJ6RWI2P'

# 1. Check agent is prepared
print("Checking agent status...")
agent = client.get_agent(agentId=AGENT_ID)['agent']
status = agent['agentStatus']
print(f"Agent status: {status}")

if status == 'PREPARING':
    print("Waiting for agent to finish preparing...")
    while status == 'PREPARING':
        time.sleep(3)
        agent = client.get_agent(agentId=AGENT_ID)['agent']
        status = agent['agentStatus']
    print(f"Agent status: {status}")

# 2. Create new version
print("\nCreating new version...")
version_response = client.create_agent_version(
    agentId=AGENT_ID,
    description='v2 - KJV default + personality system + life stage + spiritual depth'
)
new_version = version_response['agentVersion']['version']
print(f"Created version: {new_version}")

# Wait for version to be ready
time.sleep(5)

# 3. Create new alias pointing to new version
print("\nCreating new alias...")
alias_response = client.create_agent_alias(
    agentId=AGENT_ID,
    agentAliasName='KJV_Personality_v2',
    description='KJV default, personality system, semantic memory',
    routingConfiguration=[{
        'agentVersion': new_version
    }]
)

new_alias_id = alias_response['agentAlias']['agentAliasId']
new_alias_name = alias_response['agentAlias']['agentAliasName']
print(f"Created alias: {new_alias_name} (ID: {new_alias_id})")

# 4. List all aliases
print("\n" + "=" * 60)
print("ALL ALIASES:")
print("=" * 60)
aliases = client.list_agent_aliases(agentId=AGENT_ID)
for alias in aliases['agentAliasSummaries']:
    detail = client.get_agent_alias(agentId=AGENT_ID, agentAliasId=alias['agentAliasId'])
    routing = detail['agentAlias'].get('routingConfiguration', [])
    version = routing[0].get('agentVersion', '?') if routing else '?'
    print(f"  {alias['agentAliasName']}")
    print(f"    ID: {alias['agentAliasId']}")
    print(f"    Version: {version}")
    print(f"    Status: {alias.get('agentAliasStatus')}")
    print()

print("=" * 60)
print(f"NEW ALIAS ID: {new_alias_id}")
print(f"Update your Lambda env var BEDROCK_AGENT_ALIAS_ID to: {new_alias_id}")
print("=" * 60)
