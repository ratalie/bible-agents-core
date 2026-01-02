"""
Test de personalidades del Bible Companion
Prueba los 4 companions predefinidos
"""
import boto3
import json
import time

sns = boto3.client('sns', region_name='us-east-1')
TOPIC_ARN = "arn:aws:sns:us-east-1:124355682808:bible-companion-personality-topic"

def test_companion(companion_name, user_message, age=35, spiritual_tier=5):
    """Envía mensaje de prueba con un companion específico"""
    
    message = {
        "conversationId": f"test-{companion_name}-{int(time.time())}",
        "messageId": f"msg-{int(time.time())}",
        "userId": f"test-user-{companion_name}",
        "text": user_message,
        "userProfile": {
            "isPremium": False,
            "selectedCompanion": companion_name,
            "age": age,
            "spiritualData": {
                "spiritual_stage_name": "Growing",
                "spiritual_score_percent": 65,
                "spiritual_tier": spiritual_tier,
                "last_survey_at": "2025-10-01T00:00:00Z"
            }
        }
    }
    
    print(f"\n{'='*60}")
    print(f"🎭 Testing: {companion_name.upper()}")
    print(f"📝 Message: {user_message}")
    print(f"👤 Age: {age} | Spiritual Tier: {spiritual_tier}")
    print(f"{'='*60}")
    
    response = sns.publish(
        TopicArn=TOPIC_ARN,
        Message=json.dumps(message),
        Subject=f"Test {companion_name}"
    )
    
    print(f"✅ Sent! MessageId: {response['MessageId']}")
    return response

if __name__ == "__main__":
    # Mensaje de prueba
    test_message = "Estoy pasando por un momento difícil en mi trabajo y no sé qué hacer. ¿Qué dice la Biblia sobre esto?"
    
    print("\n🚀 INICIANDO PRUEBAS DE PERSONALIDADES\n")
    
    # Test cada companion con diferentes perfiles
    companions = [
        ("caleb", 25, 3),   # Joven, explorando fe
        ("ruth", 35, 5),    # Adulto, creciendo
        ("solomon", 50, 7), # Guía, madurando
        ("miriam", 70, 9),  # Legacy, floreciendo
    ]
    
    for companion, age, tier in companions:
        test_companion(companion, test_message, age, tier)
        time.sleep(2)  # Esperar entre mensajes
    
    print("\n" + "="*60)
    print("✅ Todas las pruebas enviadas!")
    print("📋 Revisa CloudWatch Logs para ver las respuestas")
    print("   Log Group: /aws/lambda/bible-companion-personality")
    print("="*60)
