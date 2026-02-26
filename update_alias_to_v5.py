import boto3

client = boto3.client('bedrock-agent', region_name='us-east-1')

AGENT_ID = 'NFL5LXYSUW'
ALIAS_ID = 'CKLXTRRBZA'  # Production alias

# Update alias to point to version 5
response = client.update_agent_alias(
    agentId=AGENT_ID,
    agentAliasId=ALIAS_ID,
    agentAliasName='Bible_App_GraceAI_Chat_Person_v2_v4',
    routingConfiguration=[{'agentVersion': '5'}]
)

print(f"✅ Alias updated!")
print(f"   Status: {response['agentAlias']['agentAliasStatus']}")
print(f"   Routing: {response['agentAlias']['routingConfiguration']}")
