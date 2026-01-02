"""
Script para probar el agente Bible_App_GraceAI_Chat_Person_Mem_Pers
y ver la memoria almacenada con AgentCore
"""
import boto3
import json
import uuid

# Configuración del agente
AGENT_ID = "MCP33AOQV8"
AGENT_ALIAS_ID = "IYFPFU7ZC4"  # Alias de producción
REGION = "us-east-1"

# Clientes
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=REGION)
bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)


def invoke_agent(session_id: str, input_text: str, memory_id: str = None):
    """Invoca el agente y retorna la respuesta"""
    
    params = {
        'agentId': AGENT_ID,
        'agentAliasId': AGENT_ALIAS_ID,
        'sessionId': session_id,
        'inputText': input_text,
    }
    
    # Si hay memory_id, lo incluimos para persistencia entre sesiones
    if memory_id:
        params['memoryId'] = memory_id
    
    try:
        response = bedrock_agent_runtime.invoke_agent(**params)
        
        # Leer la respuesta del stream
        full_response = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk_data = event['chunk']['bytes'].decode('utf-8')
                full_response += chunk_data
        
        return full_response
    
    except Exception as e:
        return f"Error: {str(e)}"


def get_agent_memory(agent_id: str, agent_alias_id: str, memory_id: str):
    """Obtiene la memoria almacenada para un usuario específico"""
    
    try:
        response = bedrock_agent_runtime.get_agent_memory(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            memoryId=memory_id,
            memoryType='SESSION_SUMMARY'
        )
        return response
    except Exception as e:
        return f"Error obteniendo memoria: {str(e)}"


def list_all_memories(agent_id: str, agent_alias_id: str, memory_id: str):
    """Lista todas las memorias de sesión para un usuario"""
    
    try:
        response = bedrock_agent_runtime.get_agent_memory(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            memoryId=memory_id,
            memoryType='SESSION_SUMMARY',
            maxItems=20
        )
        return response
    except Exception as e:
        return f"Error: {str(e)}"


def delete_agent_memory(agent_id: str, agent_alias_id: str, memory_id: str):
    """Elimina la memoria de un usuario específico"""
    
    try:
        response = bedrock_agent_runtime.delete_agent_memory(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            memoryId=memory_id
        )
        return "Memoria eliminada exitosamente"
    except Exception as e:
        return f"Error eliminando memoria: {str(e)}"


if __name__ == "__main__":
    print("=" * 60)
    print("PRUEBA DE AGENTE CON MEMORIA - AgentCore")
    print("=" * 60)
    
    # Usar un memory_id fijo para simular un usuario
    # En producción, esto sería el userId de tu app
    MEMORY_ID = "test-user-natalie-001"
    
    # Generar session_id único para esta conversación
    SESSION_ID = f"session-{uuid.uuid4().hex[:8]}"
    
    print(f"\nMemory ID (usuario): {MEMORY_ID}")
    print(f"Session ID: {SESSION_ID}")
    
    # 1. Primero, ver si hay memoria existente
    print("\n" + "-" * 40)
    print("1. MEMORIA EXISTENTE:")
    print("-" * 40)
    
    memory = list_all_memories(AGENT_ID, AGENT_ALIAS_ID, MEMORY_ID)
    if isinstance(memory, dict) and 'memoryContents' in memory:
        if memory['memoryContents']:
            for i, content in enumerate(memory['memoryContents'], 1):
                print(f"\n--- Sesión {i} ---")
                if 'sessionSummary' in content:
                    summary = content['sessionSummary']
                    print(f"Session ID: {summary.get('sessionId', 'N/A')}")
                    print(f"Inicio: {summary.get('sessionStartTime', 'N/A')}")
                    print(f"Resumen: {summary.get('summaryText', 'Sin resumen')[:500]}...")
        else:
            print("No hay memorias almacenadas para este usuario.")
    else:
        print(memory)
    
    # 2. Probar el agente
    print("\n" + "-" * 40)
    print("2. PROBANDO EL AGENTE:")
    print("-" * 40)
    
    test_message = "Hola, soy Maria y estoy pasando por un momento difícil en mi vida. ¿Puedes ayudarme?"
    print(f"\nUsuario: {test_message}")
    print("\nAgente respondiendo...")
    
    response = invoke_agent(SESSION_ID, test_message, MEMORY_ID)
    print(f"\nRespuesta del agente:\n{response}")
    
    # 3. Segunda pregunta en la misma sesión
    print("\n" + "-" * 40)
    print("3. SEGUNDA PREGUNTA (misma sesión):")
    print("-" * 40)
    
    test_message_2 = "¿Qué versículo me recomiendas para encontrar paz?"
    print(f"\nUsuario: {test_message_2}")
    print("\nAgente respondiendo...")
    
    response2 = invoke_agent(SESSION_ID, test_message_2, MEMORY_ID)
    print(f"\nRespuesta del agente:\n{response2}")
    
    print("\n" + "=" * 60)
    print("NOTA: La memoria se guarda al finalizar la sesión.")
    print("Ejecuta este script de nuevo para ver la memoria guardada.")
    print("=" * 60)
