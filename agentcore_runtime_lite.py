import json
import os

def bible_companion(input_text: str, user_id: str = None, session_id: str = None):
    """
    Lightweight Bible Companion agent.
    """
    
    # Simple response for testing
    return f"Hello! I received: {input_text}"

# For AgentCore Runtime
def lambda_handler(event, context):
    """Handler for AgentCore Runtime."""
    
    # Extract input from event
    if isinstance(event, dict):
        input_text = event.get('prompt', 'Hello')
        user_id = event.get('sessionAttributes', {}).get('userId', 'default-user')
        session_id = event.get('sessionId', 'default-session')
    else:
        input_text = str(event)
        user_id = 'default-user'
        session_id = 'default-session'
    
    # Call main function
    response = bible_companion(input_text, user_id, session_id)
    
    return {
        'response': response,
        'status': 'success'
    }