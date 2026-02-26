"""Create agent version using raw API call"""
import boto3
import json

session = boto3.Session(profile_name='gpbible')
client = session.client('bedrock-agent', region_name='us-east-1')

AGENT_ID = 'OPFJ6RWI2P'

# The SDK method might be available under a different name
# Let's check all available methods
methods = [m for m in dir(client) if not m.startswith('_') and 'agent' in m.lower()]
print("Available agent methods:")
for m in sorted(methods):
    print(f"  {m}")

# Try the meta endpoint
print("\nTrying to find create version...")
try:
    # Some SDKs have it as create_agent_version
    result = client.meta.service_model.operation_names
    version_ops = [op for op in result if 'version' in op.lower()]
    print(f"Version operations in service model: {version_ops}")
except Exception as e:
    print(f"Error: {e}")
