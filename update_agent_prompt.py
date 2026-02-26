"""Update Bedrock Agent prompt to v2 with KJV default + personality support"""
import boto3
import json

client = boto3.client('bedrock-agent', region_name='us-east-1')

# Read new prompt
with open('agent_prompt_v2.txt', 'r', encoding='utf-8') as f:
    new_instruction = f.read()

# Get current agent config
response = client.get_agent(agentId='OPFJ6RWI2P')
agent = response['agent']

print(f"Agent: {agent['agentName']}")
print(f"Model: {agent['foundationModel']}")
print(f"Current instruction length: {len(agent.get('instruction', ''))}")
print(f"New instruction length: {len(new_instruction)}")

# Update agent
update_response = client.update_agent(
    agentId='OPFJ6RWI2P',
    agentName=agent['agentName'],
    foundationModel=agent['foundationModel'],
    agentResourceRoleArn=agent['agentResourceRoleArn'],
    instruction=new_instruction,
    description=agent.get('description', ''),
    idleSessionTTLInSeconds=agent.get('idleSessionTTLInSeconds', 1800),
)

print(f"\nAgent updated successfully!")
print(f"Status: {update_response['agent']['agentStatus']}")

# Prepare agent to apply changes
prepare_response = client.prepare_agent(agentId='OPFJ6RWI2P')
print(f"Agent prepared: {prepare_response['agentStatus']}")
print("\nDone! The agent now defaults to KJV and supports personality system.")
