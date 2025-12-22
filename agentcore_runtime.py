from bedrock_agentcore.runtime import Agent
import boto3
import pymysql
import os
import json
import time
from datetime import datetime

# Initialize AgentCore Memory client
agentcore_client = boto3.client('bedrock-agentcore', region_name='us-east-1')
MEMORY_ID = os.environ.get('MEMORY_ID', 'memory_bqdqb-jtj3lc48bl')

# MySQL connection
def get_mysql_connection():
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST', 'gpbible-prod-mysql.c4zg06smsewh.us-east-1.rds.amazonaws.com'),
        user=os.getenv('MYSQL_USER', 'admin'),
        password=os.getenv('MYSQL_PASSWORD', '87uW3y4oU59f'),
        database=os.getenv('MYSQL_DATABASE', 'gpbible'),
        port=int(os.getenv('MYSQL_PORT', 3306)),
        charset='utf8mb4'
    )

def bible_companion(input_text: str, user_id: str = None, session_id: str = None):
    """
    Bible Companion agent with AgentCore Memory integration.
    """
    
    # Extract user_id from session attributes if not provided
    if not user_id:
        user_id = "default-user"
    if not session_id:
        session_id = f"session-{int(time.time())}"
    
    # Get user preferences from MySQL
    preferences = get_user_preferences(user_id)
    
    # Get conversation context from AgentCore Memory
    context = get_memory_context(user_id, session_id)
    
    # Build enriched prompt with context
    enriched_prompt = build_contextual_prompt(input_text, preferences, context)
    
    # Generate response
    response = generate_spiritual_response(enriched_prompt)
    
    # Save interaction to AgentCore Memory
    save_to_memory(user_id, session_id, input_text, response)
    
    return response

def get_memory_context(user_id: str, session_id: str) -> dict:
    """Get conversation context from AgentCore Memory."""
    try:
        # Get recent events from this session
        events = agentcore_client.list_events(
            memoryId=MEMORY_ID,
            actorId=user_id,
            sessionId=session_id,
            maxResults=10
        )
        
        # Get long-term memories for this user
        memories = agentcore_client.retrieve_memory_records(
            memoryId=MEMORY_ID,
            namespace=f"customer-support/{user_id}/preferences",
            searchCriteria={
                "topK": 5
            }
        )
        
        return {
            "recent_events": events.get('events', []),
            "long_term_memories": memories.get('memoryRecords', [])
        }
    except Exception as e:
        print(f"Error getting memory context: {e}")
        return {"recent_events": [], "long_term_memories": []}

def save_to_memory(user_id: str, session_id: str, user_input: str, agent_response: str):
    """Save interaction to AgentCore Memory."""
    try:
        # Save user message
        agentcore_client.create_event(
            memoryId=MEMORY_ID,
            actorId=user_id,
            sessionId=session_id,
            eventTimestamp=int(time.time() * 1000),
            payload=[
                {
                    "conversational": {
                        "content": {"text": user_input},
                        "role": "USER"
                    }
                }
            ]
        )
        
        # Save agent response
        agentcore_client.create_event(
            memoryId=MEMORY_ID,
            actorId=user_id,
            sessionId=session_id,
            eventTimestamp=int(time.time() * 1000),
            payload=[
                {
                    "conversational": {
                        "content": {"text": agent_response},
                        "role": "ASSISTANT"
                    }
                }
            ]
        )
    except Exception as e:
        print(f"Error saving to memory: {e}")

@Tool(name="get_user_preferences")
def get_user_preferences(user_id: str) -> dict:
    """Get user preferences from MySQL with avatar info."""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # Get user basic data + avatar
        cursor.execute(
            """SELECT u.firstName, u.birthDate, u.avatarIa, a.name as avatarName
               FROM users u 
               LEFT JOIN ai_avatars a ON u.avatarIa = a.id
               WHERE u.id = %s""",
            (user_id,)
        )
        user_result = cursor.fetchone()
        
        # Get bible version and denomination from user_preferences
        cursor.execute(
            """SELECT bibleVersionId, denominationId 
               FROM user_preferences WHERE userId = %s""",
            (user_id,)
        )
        prefs_result = cursor.fetchone()
        
        conn.close()
        
        if user_result:
            return {
                "firstName": user_result.get("firstName", "Friend"),
                "bibleVersion": get_bible_version_name(prefs_result.get("bibleVersionId")) if prefs_result else "NIV",
                "denomination": get_denomination_name(prefs_result.get("denominationId")) if prefs_result else None,
                "birthday": user_result.get("birthDate"),
                "avatarName": user_result.get("avatarName")
            }
        else:
            return {"firstName": "Friend", "bibleVersion": "NIV"}
    except Exception as e:
        print(f"Error getting preferences: {e}")
        return {"firstName": "Friend", "bibleVersion": "NIV"}

def get_bible_version_name(version_id: int) -> str:
    """Get bible version name from ID."""
    if not version_id:
        return "NIV"
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT abbreviation FROM bible_versions WHERE id = %s", (version_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else "NIV"
    except:
        return "NIV"

def get_denomination_name(denom_id: str) -> str:
    """Get denomination name from ID."""
    if not denom_id:
        return None
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM denominations WHERE id = %s", (denom_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except:
        return None

@Tool(name="save_user_preferences")
def save_user_preferences(user_id: str, preferences: dict):
    """Save user preferences to MySQL."""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        # Update user basic info
        if 'firstName' in preferences or 'birthday' in preferences:
            cursor.execute(
                "UPDATE users SET firstName = %s, birthDate = %s WHERE id = %s",
                (preferences.get('firstName'), preferences.get('birthday'), user_id)
            )
        
        # Update bible version preference
        if 'bibleVersion' in preferences:
            cursor.execute(
                """INSERT INTO `bible-versions-user` (user_id, bible_version) 
                   VALUES (%s, %s) ON DUPLICATE KEY UPDATE bible_version = VALUES(bible_version)""",
                (user_id, preferences.get('bibleVersion'))
            )
        
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        print(f"Error saving preferences: {e}")
        return {"success": False}

def generate_greeting(preferences: dict, is_first_time: bool, context: dict) -> str:
    """Generate personalized greeting."""
    name = preferences.get("firstName", "Friend")
    
    if is_first_time:
        return f"Good morning, {name}! How can I walk with you in faith today?"
    else:
        # Reference recent conversations
        recent_themes = context.get("recent_themes", [])
        if recent_themes:
            return f"Hello again, {name}! I remember we were discussing {recent_themes[0]}. How are you feeling about that today?"
        return f"Welcome back, {name}! What's on your heart today?"

def process_spiritual_guidance(enriched_prompt: str, preferences: dict, user_id: str) -> str:
    """Process spiritual guidance with enriched context from database."""
    
    # Use AgentCore Memory to get relevant past conversations
    relevant_memories = memory.search_memories(
        user_id=user_id,
        query=enriched_prompt,
        limit=5
    )
    
    # The enriched_prompt already contains all user context from DB
    # Now add memory context and send to LLM
    full_context = f"""
    {enriched_prompt}
    
    Relevant Past Conversations:
    {format_memories(relevant_memories)}
    
    Instructions: Follow your Bible Companion prompt exactly, using the user context provided above.
    """
    
    # Here you'd call your LLM with the full_context
    return generate_spiritual_response(full_context)

def extract_themes(input_text: str, response: str) -> list:
    """Extract spiritual themes from conversation."""
    # Simple keyword extraction - you could use LLM for better results
    themes = []
    spiritual_keywords = [
        "prayer", "faith", "forgiveness", "love", "hope", "trust", 
        "family", "relationships", "work", "anxiety", "depression",
        "gratitude", "worship", "service", "community"
    ]
    
    text = (input_text + " " + response).lower()
    for keyword in spiritual_keywords:
        if keyword in text:
            themes.append(keyword)
    
    return themes[:3]  # Top 3 themes

def extract_verses(response: str) -> list:
    """Extract Bible verses mentioned in response."""
    import re
    # Simple regex to find Bible references
    verse_pattern = r'\b\d*\s*[A-Za-z]+\s+\d+:\d+(?:-\d+)?\b'
    verses = re.findall(verse_pattern, response)
    return verses

def analyze_sentiment(text: str) -> str:
    """Analyze user's spiritual/emotional sentiment."""
    # Simple sentiment analysis - you could use AWS Comprehend
    positive_words = ["blessed", "grateful", "joy", "peace", "hope", "love"]
    negative_words = ["struggling", "worried", "anxious", "sad", "lost", "angry"]
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "struggling"
    else:
        return "neutral"

def format_memories(memories: list) -> str:
    """Format memories for context."""
    if not memories:
        return "No previous conversations found."
    
    formatted = []
    for memory in memories:
        formatted.append(f"- {memory.get('summary', '')}")
    
    return "\n".join(formatted)

def should_summarize_session(session_id: str) -> bool:
    """Check if session should be summarized."""
    interaction_count = memory.get_session_interaction_count(session_id)
    return interaction_count % 10 == 0  # Every 10 interactions

def summarize_and_save_session(user_id: str, session_id: str):
    """Summarize session and save to long-term memory."""
    # Get session interactions
    interactions = memory.get_session_interactions(session_id)
    
    # Create summary
    summary = create_session_summary(interactions)
    
    # Save to long-term memory
    memory.save_long_term_memory(
        user_id=user_id,
        content=summary,
        metadata={"session_id": session_id, "timestamp": datetime.now().isoformat()}
    )

def create_session_summary(interactions: list) -> str:
    """Create concise session summary."""
    if not interactions:
        return "No interactions in session"
    
    themes = set()
    verses = set()
    key_points = []
    
    for interaction in interactions:
        metadata = interaction.get('metadata', {})
        themes.update(metadata.get('spiritual_themes', []))
        verses.update(metadata.get('verses_shared', []))
        
        # Extract key points from user input
        user_input = interaction.get('user_input', '')
        if len(user_input) > 50:  # Significant input
            key_points.append(user_input[:100] + "..." if len(user_input) > 100 else user_input)
    
    summary_parts = []
    if themes:
        summary_parts.append(f"Themes: {', '.join(list(themes)[:3])}")
    if verses:
        summary_parts.append(f"Verses: {', '.join(list(verses)[:3])}")
    if key_points:
        summary_parts.append(f"Key discussion: {key_points[0]}")
    
    return " | ".join(summary_parts)

def generate_spiritual_response(prompt: str) -> str:
    """Generate spiritual response using LLM."""
    # Placeholder - integrate with your preferred LLM
    return "I'm here to walk with you in faith. Let me share some thoughts and a relevant Bible verse..."

if __name__ == "__main__":
    # Test the agent
    response = bible_companion(
        input_text="I'm struggling with anxiety about work",
        user_id="user123",
        session_id="session456"
    )
    print(response)