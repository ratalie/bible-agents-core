import json
import boto3
import os
from datetime import datetime, date
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
VERSES_TABLE = os.environ.get('VERSES_TABLE', 'bible-daily-verses')

# KJV Bible verses cache (you can expand this or use an API)
KJV_VERSES = {
    "John 3:16": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
    "Psalm 23:1": "The Lord is my shepherd; I shall not want.",
    "Philippians 4:13": "I can do all things through Christ which strengtheneth me.",
    "Jeremiah 29:11": "For I know the thoughts that I think toward you, saith the Lord, thoughts of peace, and not of evil, to give you an expected end.",
    "Romans 8:28": "And we know that all things work together for good to them that love God, to them who are the called according to his purpose.",
    "Proverbs 3:5-6": "Trust in the Lord with all thine heart; and lean not unto thine own understanding. In all thy ways acknowledge him, and he shall direct thy paths.",
    "Isaiah 41:10": "Fear thou not; for I am with thee: be not dismayed; for I am thy God: I will strengthen thee; yea, I will help thee; yea, I will uphold thee with the right hand of my righteousness.",
    "Zephaniah 3:17": "The Lord thy God in the midst of thee is mighty; he will save, he will rejoice over thee with joy; he will rest in his love, he will joy over thee with singing.",
}


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def lambda_handler(event, context):
    """
    Lambda handler for Verse of the Day agent actions.
    """
    print(f"Event: {json.dumps(event)}")
    
    action_group = event.get('actionGroup', '')
    function = event.get('function', '')
    parameters = event.get('parameters', [])
    
    # Convert parameters list to dict
    params = {p['name']: p['value'] for p in parameters}
    
    # Route to appropriate handler
    if function == 'getVerseOfTheDay':
        result = get_verse_of_the_day(params.get('date'))
    elif function == 'getVerseByReference':
        result = get_verse_by_reference(params.get('reference'))
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


def get_verse_of_the_day(date_str: str = None) -> dict:
    """
    Get the scheduled verse(s) for a specific date.
    Falls back to a default verse if none scheduled.
    """
    if not date_str:
        date_str = date.today().isoformat()
    
    table = dynamodb.Table(VERSES_TABLE)
    
    try:
        response = table.get_item(Key={'date': date_str})
        item = response.get('Item')
        
        if item:
            return {
                'date': date_str,
                'references': item.get('references', []),
                'theme': item.get('theme')
            }
        
        # Fallback: return a default verse based on day of year
        day_of_year = datetime.strptime(date_str, '%Y-%m-%d').timetuple().tm_yday
        default_verses = list(KJV_VERSES.keys())
        default_ref = default_verses[day_of_year % len(default_verses)]
        
        return {
            'date': date_str,
            'references': [default_ref],
            'theme': None
        }
    except Exception as e:
        print(f"Error getting verse of the day: {e}")
        return {
            'date': date_str,
            'references': ['John 3:16'],
            'theme': None
        }


def get_verse_by_reference(reference: str) -> dict:
    """
    Get verse text by reference.
    Uses local cache or external API.
    """
    if not reference:
        return {'error': 'reference is required'}
    
    # Normalize reference
    reference = reference.strip()
    
    # Check local cache first
    if reference in KJV_VERSES:
        return {
            'reference': reference,
            'text': KJV_VERSES[reference],
            'version': 'KJV'
        }
    
    # For production, you would call a Bible API here
    # Example: api.bible, bible-api.com, etc.
    
    # For now, return a placeholder
    return {
        'reference': reference,
        'text': f'[Verse text for {reference} - integrate with Bible API]',
        'version': 'KJV'
    }
