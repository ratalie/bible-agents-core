"""
Script para probar el Lambda con AgentCore Memory
Ejecutar: python test_lambda_memory.py
"""
import boto3
import json
import time

# Configuración
LAMBDA_NAME = "gpbible-bedrock-processor-memory-test"
REGION = "us-east-1"
MEMORY_ID = "memory_bqdqb-jtj3lc48bl"

lambda_client = boto3.client('lambda', region_name=REGION)
agentcore_client = boto3.client('bedrock-agentcore', region_name=REGION)
logs_client = boto3.client('logs', region_name=REGION)


def invoke_lambda(user_id: str, conversation_id: str, message_id: str, text: str):
    """Invoca el Lambda con un mensaje de prueba"""
    
    payload = {
        "Records": [{
            "Sns": {
                "Message": json.dumps({
                    "conversationId": conversation_id,
                    "messageId": message_id,
                    "userId": user_id,
                    "text": text
                })
            }
        }]
    }
    
    print(f"\n📤 Enviando: {text[:50]}...")
    
    response = lambda_client.invoke(
        FunctionName=LAMBDA_NAME,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    
    if 'FunctionError' in response:
        print(f"⚠️  Lambda ejecutado con error (esperado si webhook no está configurado)")
    else:
        print(f"✅ Lambda ejecutado exitosamente")
    
    return result


def check_memory(user_id: str):
    """Verifica la memoria guardada para un usuario"""
    
    print(f"\n🔍 Verificando memoria para: {user_id}")
    
    try:
        # Listar sesiones
        sessions = agentcore_client.list_sessions(
            memoryId=MEMORY_ID,
            actorId=user_id
        )
        
        session_list = sessions.get('sessionSummaries', [])
        print(f"   Sesiones encontradas: {len(session_list)}")
        
        for session in session_list:
            session_id = session['sessionId']
            print(f"\n   📁 Sesión: {session_id}")
            
            # Listar eventos de la sesión
            events = agentcore_client.list_events(
                memoryId=MEMORY_ID,
                actorId=user_id,
                sessionId=session_id,
                maxResults=10
            )
            
            for event in events.get('events', []):
                payload = event.get('payload', [])
                if payload and payload[0].get('conversational'):
                    conv = payload[0]['conversational']
                    role = conv.get('role', 'UNKNOWN')
                    text = conv.get('content', {}).get('text', '')[:100]
                    print(f"      {role}: {text}...")
        
        return len(session_list)
        
    except Exception as e:
        print(f"   Error: {e}")
        return 0


def get_recent_logs(limit: int = 10):
    """Obtiene los logs más recientes del Lambda"""
    
    log_group = f"/aws/lambda/{LAMBDA_NAME}"
    
    try:
        streams = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        
        if not streams['logStreams']:
            print("No hay logs disponibles")
            return
        
        stream_name = streams['logStreams'][0]['logStreamName']
        
        events = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            limit=limit
        )
        
        print(f"\n📋 Últimos logs ({stream_name}):")
        print("-" * 60)
        
        for event in events['events']:
            msg = event['message'].strip()
            if any(x in msg for x in ['INFO', 'ERROR', 'Memory', 'memory', 'Fetching', 'saved', 'Found']):
                # Limpiar mensaje
                if '\t' in msg:
                    parts = msg.split('\t')
                    if len(parts) >= 3:
                        msg = parts[2]
                print(msg[:200])
        
    except Exception as e:
        print(f"Error obteniendo logs: {e}")


def run_test():
    """Ejecuta una prueba completa"""
    
    print("=" * 60)
    print("🧪 PRUEBA DE LAMBDA CON AGENTCORE MEMORY")
    print("=" * 60)
    
    # Usar un userId único para la prueba
    test_user = f"test-user-{int(time.time())}"
    
    # 1. Primera conversación (sin memoria previa)
    print("\n" + "=" * 60)
    print("1️⃣  PRIMERA CONVERSACIÓN (sin memoria previa)")
    print("=" * 60)
    
    invoke_lambda(
        user_id=test_user,
        conversation_id="conv-001",
        message_id="msg-001",
        text="Hola, estoy pasando por un momento difícil y necesito guía espiritual"
    )
    
    time.sleep(2)
    
    # 2. Verificar que se guardó la memoria
    print("\n" + "=" * 60)
    print("2️⃣  VERIFICANDO MEMORIA GUARDADA")
    print("=" * 60)
    
    sessions = check_memory(test_user)
    
    if sessions == 0:
        print("❌ No se guardó la memoria")
        return
    
    # 3. Segunda conversación (debería leer memoria)
    print("\n" + "=" * 60)
    print("3️⃣  SEGUNDA CONVERSACIÓN (con memoria)")
    print("=" * 60)
    
    invoke_lambda(
        user_id=test_user,
        conversation_id="conv-002",
        message_id="msg-002",
        text="¿Qué versículo me recomiendas para encontrar paz?"
    )
    
    time.sleep(2)
    
    # 4. Ver logs
    print("\n" + "=" * 60)
    print("4️⃣  LOGS DEL LAMBDA")
    print("=" * 60)
    
    get_recent_logs(15)
    
    # 5. Verificar memoria final
    print("\n" + "=" * 60)
    print("5️⃣  MEMORIA FINAL")
    print("=" * 60)
    
    check_memory(test_user)
    
    print("\n" + "=" * 60)
    print("✅ PRUEBA COMPLETADA")
    print("=" * 60)
    print(f"\nUsuario de prueba: {test_user}")
    print("Revisa los logs para ver '✅ Found previous conversations' en la segunda llamada")


if __name__ == "__main__":
    run_test()
