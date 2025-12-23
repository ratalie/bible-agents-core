def bible_companion(event, context=None):
    """Ultra minimal Bible Companion for testing."""
    return "Hello from Bible Companion!"

def lambda_handler(event, context):
    """Handler for AgentCore Runtime."""
    return bible_companion(event, context)