import json
import boto3
import os
from datetime import datetime, date
from decimal import Decimal

# Initialize clients
dynamodb = boto3.resource('dynamodb')
bedrock_agent = boto3.client('bedrock-agent-runtime')

# Environment variables
USER_PREFS_TABLE = os.environ.get('USER_PREFS_TABLE', 'bible-user-preferences')
MEMORY_TABLE = os.environ.get('MEMORY_TABLE', 'bible-conversation-memory')
MEMORY_ID = os.environ.get('MEMORY_ID')  # AgentCore Memory ID

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def lambda_handler(event, context):
    """
    Enhanced Lambda handler with AgentCore Memory integration.
    """
    print(f"Event: {json.dumps(event)}")
    
    action_group = event.get('actionGroup', '')
    function = event.get('function', '')
    parameters = event.get('parameters', [])
    
    # Convert parameters list to dict
    params = {p['name']: p['value'] for p in parameters}
    
    # Route to appropriate handler
    if function == 'getUserPreferences':
        result = get_user_preferences(params.get('userId'))
    elif function == 'getConversationMemory':
        result = get_enhanced_memory(
            params.get('userId'),
            int(params.get('limit', 5))
        )
    elif function == 'saveSessionSummary':
        body = event.get('requestBody', {}).get('content', {}).get('application/json', {}).get('properties', [])
        body_params = {p['name']: p['value'] for p in body}
        result = save_enhanced_session(body_params)
    elif function == 'checkFirstTimeToday':
        result = check_first_time_today(params.get('userId'))
    elif function == 'retrieveMemory':
        result = retrieve_agentcore_memory(
            params.get('userId'),
            params.get('query', '')
        )
    else:
        result = {'error': f'Unknown function: {function}'}
    
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'function': function,
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': json.dumps(result, cls=DecimalEncoder)
                    }
                }
            }
        }
    }


def get_enhanced_memory(user_id: str, limit: int = 5) -> dict:
    """
    Retrieve both DynamoDB memories and AgentCore long-term memory.
    """
    if not user_id:
        return {'shortTerm': [], 'longTerm': []}
    
    # Get short-term memory from DynamoDB
    short_term = get_conversation_memory(user_id, limit)
    
    # Get long-term memory from AgentCore
    long_term = []
    if MEMORY_ID:
        try:
            response = bedrock_agent.retrieve_memory(
                memoryId=MEMORY_ID,
                memoryType='LONG_TERM',
                userId=user_id,
                maxItems=10
            )
            long_term = response.get('memories', [])
        except Exception as e:
            print(f"Error retrieving AgentCore memory: {e}")
    
    return {
        'shortTerm': short_term,
        'longTerm': long_term,
        'userId': user_id
    }


def save_enhanced_session(summary: dict) -> dict:
    """
    Save session to both DynamoDB and AgentCore Memory.
    """
    user_id = summary.get('userId')
    session_id = summary.get('sessionId')
    
    if not user_id or not session_id:
        return {'error': 'userId and sessionId are required'}
    
    # Save to DynamoDB (existing functionality)
    dynamo_result = save_session_summary(summary)
    
    # Save to AgentCore Memory for long-term retention
    agentcore_result = {'success': False}
    if MEMORY_ID:
        try:
            # Create memory content for long-term storage
            memory_content = create_memory_content(summary)
            
            response = bedrock_agent.put_memory(
                memoryId=MEMORY_ID,
                memoryType='LONG_TERM',
                userId=user_id,
                content=memory_content
            )
            agentcore_result = {'success': True, 'memoryId': response.get('memoryId')}
        except Exception as e:
            print(f"Error saving to AgentCore memory: {e}")
            agentcore_result = {'error': str(e)}
    
    return {
        'dynamodb': dynamo_result,
        'agentcore': agentcore_result,
        'sessionId': session_id
    }


def retrieve_agentcore_memory(user_id: str, query: str = '') -> dict:
    """
    Retrieve specific memories from AgentCore based on query.
    """
    if not MEMORY_ID or not user_id:
        return {'memories': []}
    
    try:
        params = {
            'memoryId': MEMORY_ID,
            'memoryType': 'LONG_TERM',
            'userId': user_id,
            'maxItems': 20
        }
        
        if query:
            params['query'] = query
        
        response = bedrock_agent.retrieve_memory(**params)
        return {
            'memories': response.get('memories', []),
            'query': query
        }
    except Exception as e:
        print(f"Error retrieving AgentCore memory: {e}")
        return {'error': str(e)}


def create_memory_content(summary: dict) -> str:
    """
    Create structured memory content for AgentCore storage.
    """
    content_parts = []
    
    # Add key spiritual insights
    if summary.get('keyPoints'):
        content_parts.append(f"Key Points: {', '.join(summary['keyPoints'])}")
    
    if summary.get('spiritualThemes'):
        content_parts.append(f"Spiritual Themes: {', '.join(summary['spiritualThemes'])}")
    
    if summary.get('versesShared'):
        content_parts.append(f"Bible Verses Discussed: {', '.join(summary['versesShared'])}")
    
    if summary.get('userSentiment'):
        content_parts.append(f"User's Spiritual State: {summary['userSentiment']}")
    
    if summary.get('reflectionQuestions'):
        content_parts.append(f"Reflection Questions: {', '.join(summary['reflectionQuestions'])}")
    
    if summary.get('nextSteps'):
        content_parts.append(f"Spiritual Next Steps: {', '.join(summary['nextSteps'])}")
    
    return " | ".join(content_parts)


# Existing functions (unchanged)
def get_user_preferences(user_id: str) -> dict:
    """Retrieve user preferences from DynamoDB."""
    if not user_id:
        return {'error': 'userId is required'}
    
    table = dynamodb.Table(USER_PREFS_TABLE)
    
    try:
        response = table.get_item(Key={'userId': user_id})
        item = response.get('Item')
        
        if not item:
            return {
                'userId': user_id,
                'firstName': 'Friend',
                'bibleVersion': 'NIV',
                'denomination': None,
                'birthday': None,
                'avatarName': None
            }
        
        return {
            'userId': item.get('userId'),
            'firstName': item.get('firstName', 'Friend'),
            'bibleVersion': item.get('bibleVersion', 'NIV'),
            'denomination': item.get('denomination'),
            'birthday': item.get('birthday'),
            'avatarName': item.get('avatarName')
        }
    except Exception as e:
        print(f"Error getting user preferences: {e}")
        return {'error': str(e)}


def get_conversation_memory(user_id: str, limit: int = 5) -> list:
    """Retrieve recent conversation memories from DynamoDB."""
    if not user_id:
        return []
    
    table = dynamodb.Table(MEMORY_TABLE)
    
    try:
        response = table.query(
            KeyConditionExpression='userId = :uid',
            ExpressionAttributeValues={':uid': user_id},
            ScanIndexForward=False,
            Limit=limit
        )
        
        memories = []
        for item in response.get('Items', []):
            memories.append({
                'id': item.get('id'),
                'userId': item.get('userId'),
                'timestamp': item.get('timestamp'),
                'keyPoints': item.get('keyPoints', []),
                'spiritualThemes': item.get('spiritualThemes', []),
                'versesShared': item.get('versesShared', []),
                'userSentiment': item.get('userSentiment')
            })
        
        return memories
    except Exception as e:
        print(f"Error getting conversation memory: {e}")
        return []


def save_session_summary(summary: dict) -> dict:
    """Save conversation session summary to DynamoDB."""
    user_id = summary.get('userId')
    session_id = summary.get('sessionId')
    
    if not user_id or not session_id:
        return {'error': 'userId and sessionId are required'}
    
    table = dynamodb.Table(MEMORY_TABLE)
    
    try:
        item = {
            'userId': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            'id': f"{user_id}#{session_id}",
            'sessionId': session_id,
            'keyPoints': summary.get('keyPoints', []),
            'spiritualThemes': summary.get('spiritualThemes', []),
            'versesShared': summary.get('versesShared', []),
            'reflectionQuestions': summary.get('reflectionQuestions', []),
            'nextSteps': summary.get('nextSteps', []),
            'userSentiment': summary.get('userSentiment', 'neutral')
        }
        
        table.put_item(Item=item)
        return {'success': True, 'id': item['id']}
    except Exception as e:
        print(f"Error saving session summary: {e}")
        return {'error': str(e)}


def check_first_time_today(user_id: str) -> dict:
    """Check if this is the user's first conversation today."""
    if not user_id:
        return {'isFirstTimeToday': True}
    
    table = dynamodb.Table(MEMORY_TABLE)
    today = date.today().isoformat()
    
    try:
        response = table.query(
            KeyConditionExpression='userId = :uid AND begins_with(#ts, :today)',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':uid': user_id,
                ':today': today
            },
            Limit=1
        )
        
        has_talked_today = len(response.get('Items', [])) > 0
        return {'isFirstTimeToday': not has_talked_today}
    except Exception as e:
        print(f"Error checking first time today: {e}")
        return {'isFirstTimeToday': True}