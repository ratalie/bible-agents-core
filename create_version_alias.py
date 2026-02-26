"""Create new version from DRAFT and new alias"""
import boto3
import json
import time
from botocore.config import Config

config = Config(region_name='us-east-1')
session = boto3.Session()

# Use raw HTTP to create agent version (not in SDK yet)
bedrock = session.client('bedrock-agent', config=config)

AGENT_ID = 'OPFJ6RWI2P'

# Try using the underlying API
endpoint = f'https://bedrock-agent.us-east-1.amazonaws.com'
url = f'/agents/{AGENT_ID}/agentversions/'

# Use requests with SigV4
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import requests

credentials = session.get_credentials().get_frozen_credentials()
region = 'us-east-1'
service = 'bedrock'

body = json.dumps({
    "description": "v4 - KJV default + personality + semantic memory"
})

request = AWSRequest(
    method='PUT',
    url=f'{endpoint}{url}',
    data=body,
    headers={'Content-Type': 'application/json'}
)
SigV4Auth(credentials, service, region).add_auth(request)

response = requests.put(
    request.url,
    headers=dict(request.headers),
    data=body
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")
