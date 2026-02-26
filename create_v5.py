import boto3
import time

client = boto3.client('bedrock-agent', region_name='us-east-1')

AGENT_ID = 'NFL5LXYSUW'
ALIAS_ID = 'CKLXTRRBZA'

# Step 1: Get current DRAFT instruction to verify it has our fix
agent = client.get_agent(agentId=AGENT_ID)
instruction = agent['agent'].get('instruction', '')

if 'NEVER list, display, summarize, or acknowledge their profile' in instruction:
    print("✅ Fix is in DRAFT")
else:
    print("❌ Fix NOT found in DRAFT")
    exit(1)

# Step 2: Create a new alias that will force version creation
# Actually, let's try a different approach - update an existing alias
# by first getting the current routing config

alias = client.get_agent_alias(agentId=AGENT_ID, agentAliasId=ALIAS_ID)
print(f"\nCurrent alias routing: {alias['agentAlias']['routingConfiguration']}")

# Step 3: The trick is to prepare the agent again which should create a publishable state
print("\nPreparing agent...")
client.prepare_agent(agentId=AGENT_ID)
time.sleep(10)

# Check status
agent = client.get_agent(agentId=AGENT_ID)
print(f"Agent status: {agent['agent']['agentStatus']}")

# Step 4: Try to find if there's a way to publish
# Looking at the API, there's no direct create-version
# But we can try using the agent-action-group or knowledge-base association
# to trigger a version creation

print("\n⚠️ AWS Bedrock Agent API doesn't have create-agent-version")
print("You need to create version 5 from the AWS Console:")
print(f"  1. Go to: https://console.aws.amazon.com/bedrock/home?region=us-east-1#/agents/{AGENT_ID}")
print("  2. Click 'Create version' button")
print("  3. Then run: python update_alias_to_v5.py")
