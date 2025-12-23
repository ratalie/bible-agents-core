def handler(event, context):
    """
    Bible Companion handler following AgentCore template structure.
    """
    
    # Extract input from event
    user_input = ""
    if isinstance(event, dict):
        user_input = event.get('inputText', event.get('prompt', ''))
    else:
        user_input = str(event)
    
    # Simple Bible companion response
    response = f"Hello! I'm your Bible Companion. You said: '{user_input}'. How can I help you with spiritual guidance today?"
    
    return response