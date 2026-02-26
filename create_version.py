import boto3

client = boto3.client('bedrock-agent', region_name='us-east-1')

# The API doesn't have create-agent-version, but we can use the console
# or update the alias to point to a new version

# Let's check if there's a way via API
print("Checking available methods...")

# List current versions
versions = client.list_agent_versions(agentId='NFL5LXYSUW')
print("\nCurrent versions:")
for v in versions['agentVersionSummaries']:
    print(f"  - {v['agentVersion']}: {v['agentStatus']}")

# The workaround is to use prepare-agent which creates a new prepared version
# Then we need to manually create a version from the console or use a different approach

print("\nTo create version 5:")
print("1. Go to AWS Console > Bedrock > Agents > NFL5LXYSUW")
print("2. Click 'Create Version'")
print("3. Update alias CKLXTRRBZA to point to version 5")
print("\nOr use the test alias (TSTALIASID) which points to DRAFT")
