"""
Test AgentCore Runtime con Memory
"""
import boto3
import json

# Configuración
RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:124355682808:runtime/bible_companion-GrIcKjGWbo"
MEMORY_ID = "memory_bqdqb-jtj3lc48bl"
REGION = "us-east-1"

# Cliente AgentCore
client = boto3.client('bedrock-agentcore', region_name=REGION)

def test_invoke_runtime():
    """Probar invocación del runtime"""
    print("=" * 50)
    print("TEST: Invocar AgentCore Runtime")
    print("=" * 50)
    
    try:
        response = client.invoke_agent_runtime(
            agentRuntimeArn=RUNTIME_ARN,
            payload=json.dumps({
                "prompt": "Hola, soy Maria y necesito guía espiritual",
                "user_id": "test-user-maria",
                "session_id": "test-session-001"
            })
        )
        
        # Leer respuesta
        result = response['body'].read().decode('utf-8')
        print(f"Respuesta: {result}")
        return True
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return False

def test_memory_status():
    """Verificar estado de la memoria"""
    print("\n" + "=" * 50)
    print("TEST: Estado de AgentCore Memory")
    print("=" * 50)
    
    try:
        # Listar actores (usuarios)
        actors = client.list_actors(memoryId=MEMORY_ID)
        print(f"Actores en memoria: {len(actors.get('actorSummaries', []))}")
        
        for actor in actors.get('actorSummaries', []):
            print(f"  - {actor}")
        
        return True
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return False

def test_create_memory_event():
    """Crear un evento de memoria manualmente"""
    print("\n" + "=" * 50)
    print("TEST: Crear evento en memoria")
    print("=" * 50)
    
    import time
    
    try:
        response = client.create_event(
            memoryId=MEMORY_ID,
            actorId="test-user-maria",
            sessionId="test-session-001",
            eventTimestamp=int(time.time() * 1000),
            payload=[
                {
                    "conversational": {
                        "content": {"text": "Hola, soy Maria"},
                        "role": "USER"
                    }
                }
            ]
        )
        print(f"Evento creado: {response}")
        return True
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("\n🔍 Probando AgentCore...\n")
    
    # 1. Verificar memoria
    test_memory_status()
    
    # 2. Crear evento de prueba
    test_create_memory_event()
    
    # 3. Verificar memoria de nuevo
    test_memory_status()
    
    # 4. Invocar runtime
    test_invoke_runtime()
