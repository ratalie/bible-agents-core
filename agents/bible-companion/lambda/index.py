import json
import boto3
import os
from datetime import datetime, date
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
USER_PREFS_TABLE = os.environ.get('USER_PREFS_TABLE', 'bible-user-preferences')
MEMORY_TABLE = os.environ.get('MEMORY_TABLE', 'bible-conversation-memory')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def lambda_handler(event, context):
    """
    Lambda handler for Bible Companion agent actions.
    Routes to appropriate function based on actionGroup and function.
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
        result = get_conversation_memory(
            params.get('userId'),
            int(params.get('limit', 5))
        )
    elif function == 'saveSessionSummary':
        # For POST, body comes from requestBody
        body = event.get('requestBody', {}).get('content', {}).get('application/json', {}).get('properties', [])
        body_params = {p['name']: p['value'] for p in body}
        result = save_session_summary(body_params)
    elif function == 'checkFirstTimeToday':
        result = check_first_time_today(params.get('userId'))
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


def get_user_preferences(user_id: str) -> dict:
    """Retrieve user preferences from DynamoDB."""
    if not user_id:
        return {'error': 'userId is required'}
    
    table = dynamodb.Table(USER_PREFS_TABLE)
    
    try:
        response = table.get_item(Key={'userId': user_id})
        item = response.get('Item')
        
        if not item:
            # Return defaults if user not found
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
            ScanIndexForward=False,  # Most recent first
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
        
        # Also update daily interaction tracking
        mark_user_talked_today(user_id)
        
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


def mark_user_talked_today(user_id: str):
    """Mark that user has talked today (implicit in save_session_summary)."""
    # This is handled by the timestamp in save_session_summary
    pass
