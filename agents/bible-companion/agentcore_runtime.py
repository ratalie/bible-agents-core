from bedrock_agentcore.runtime import Agent, Memory
from bedrock_agentcore.tools import Tool
import json
import boto3
from datetime import datetime

# Initialize AgentCore Memory and DynamoDB
memory = Memory()
dynamodb = boto3.resource('dynamodb')
prefs_table = dynamodb.Table('bible-user-preferences')

@Agent(
    name="bible-companion",
    description="Personalized Bible companion with memory",
    memory=memory
)
def bible_companion(input_text: str, user_id: str, session_id: str):
    """
    Bible Companion agent with AgentCore Memory integration.
    """
    
    # Get user preferences and memory
    preferences = get_user_preferences(user_id)
    context = memory.get_context(user_id, session_id)
    
    # Check if first time today
    is_first_time = memory.is_first_interaction_today(user_id)
    
    # Generate personalized greeting
    greeting = generate_greeting(preferences, is_first_time, context)
    
    # Process user input with context
    response = process_spiritual_guidance(
        input_text, 
        preferences, 
        context,
        user_id
    )
    
    # Save interaction to memory
    memory.save_interaction(
        user_id=user_id,
        session_id=session_id,
        user_input=input_text,
        agent_response=response,
        metadata={
            "spiritual_themes": extract_themes(input_text, response),
            "verses_shared": extract_verses(response),
            "sentiment": analyze_sentiment(input_text)
        }
    )
    
    # Check if session should be summarized (every 10 interactions or on explicit end)
    if should_summarize_session(session_id):
        summarize_and_save_session(user_id, session_id)
    
    return f"{greeting}\n\n{response}"

@Tool(name="get_user_preferences")
def get_user_preferences(user_id: str) -> dict:
    """Get user preferences from DynamoDB."""
    try:
        response = prefs_table.get_item(Key={'userId': user_id})
        item = response.get('Item', {})
        return {
            "firstName": item.get("firstName", "Friend"),
            "bibleVersion": item.get("bibleVersion", "NIV"),
            "denomination": item.get("denomination"),
            "birthday": item.get("birthday")
        }
    except:
        return {"firstName": "Friend", "bibleVersion": "NIV"}

@Tool(name="save_user_preferences")
def save_user_preferences(user_id: str, preferences: dict):
    """Save user preferences to DynamoDB."""
    try:
        prefs_table.put_item(Item={"userId": user_id, **preferences})
        return {"success": True}
    except:
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

def process_spiritual_guidance(input_text: str, preferences: dict, context: dict, user_id: str) -> str:
    """Process spiritual guidance with memory context."""
    
    # Use AgentCore Memory to get relevant past conversations
    relevant_memories = memory.search_memories(
        user_id=user_id,
        query=input_text,
        limit=5
    )
    
    # Build context-aware prompt
    bible_version = preferences.get("bibleVersion", "NIV")
    denomination = preferences.get("denomination", "")
    
    context_prompt = f"""
    You are a compassionate Bible companion. 
    
    User preferences:
    - Bible version: {bible_version}
    - Denomination: {denomination}
    
    Relevant past conversations:
    {format_memories(relevant_memories)}
    
    Current question: {input_text}
    
    Provide personalized spiritual guidance that builds on past conversations.
    """
    
    # Here you'd call your LLM (Claude, GPT, etc.)
    # For now, returning a placeholder
    return generate_spiritual_response(context_prompt)

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