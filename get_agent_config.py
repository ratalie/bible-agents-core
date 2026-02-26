"""Get Bedrock Agent config"""
import boto3
import json

client = boto3.client('bedrock-agent', region_name='us-east-1')
response = client.get_agent(agentId='OPFJ6RWI2P')

agent = response['agent']
print("=" * 60)
print(f"Agent: {agent.get('agentName')}")
print(f"Model: {agent.get('foundationModel')}")
print("=" * 60)
print("\nINSTRUCTION:")
print(agent.get('instruction', 'N/A'))
print("\n" + "=" * 60)

# Save full config
with open('agent_config.json', 'w', encoding='utf-8') as f:
    json.dump(response, f, indent=2, default=str, ensure_ascii=False)
print("Full config saved to agent_config.json")
