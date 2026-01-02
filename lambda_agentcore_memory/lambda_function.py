"""
Lambda Action Group para conectar Bedrock Agent con AgentCore Memory
"""
import boto3
import json
import time
import os
from datetime import datetime

# Configuración
MEMORY_ID = os.environ.get('MEMORY_ID', 'memory_bqdqb-jtj3lc48bl')
REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Cliente AgentCore
agentcore = boto3.client('bedrock-agentcore', region_name=REGION)


def lambda_handler(event, context):
    """
    Handler para Action Group de Bedrock Agent.
    Procesa llamadas a herramientas de memoria.
    """
    print(f"Event: {json.dumps(event)}")
    
    # Extraer información del evento de Bedrock Agent
    action_group = event.get('actionGroup', '')
    api_path = event.get('apiPath', '')
    http_method = event.get('httpMethod', '')
    parameters = event.get('parameters', [])
    request_body = event.get('requestBody', {})
    
    # Convertir parámetros a dict
    params = {p['name']: p['value'] for p in parameters}
    
    # Extraer body si existe
    body = {}
    if request_body and 'content' in request_body:
        body_content = request_body['content'].get('application/json', {})
        if 'properties' in body_content:
            body = {p['name']: p['value'] for p in body_content['properties']}
    
    # Router de acciones
    try:
        if api_path == '/getConversationMemory':
            result = get_conversation_memory(params.get('userId'), params.get('limit', 5))
        elif api_path == '/saveConversationEvent':
            result = save_conversation_event(
                body.get('userId'),
                body.get('sessionId'),
                body.get('message'),
                body.get('role', 'USER')
            )
        elif api_path == '/getUserMemorySummary':
            result = get_user_memory_summary(params.get('userId'))
        elif api_path == '/searchMemories':
            result = search_memories(
                params.get('userId'),
                params.get('query'),
                params.get('limit', 5)
            )
        elif api_path == '/deleteUserMemory':
            result = delete_user_memory(params.get('userId'))
        else:
            result = {"error": f"Unknown action: {api_path}"}
        
        return format_response(result)
        
    except Exception as e:
        print(f"Error: {e}")
        return format_response({"error": str(e)}, status_code=500)


def get_conversation_memory(user_id: str, limit: int = 5) -> dict:
    """
    Obtiene las memorias de conversación recientes de un usuario.
    """
    if not user_id:
        return {"error": "userId is required"}
    
    try:
        # Listar sesiones del usuario
        sessions_response = agentcore.list_sessions(
            memoryId=MEMORY_ID,
            actorId=user_id,
            maxResults=int(limit)
        )
        
        sessions = sessions_response.get('sessionSummaries', [])
        
        memories = []
        for session in sessions:
            session_id = session.get('sessionId')
            
            # Obtener eventos de cada sesión
            events_response = agentcore.list_events(
                memoryId=MEMORY_ID,
                actorId=user_id,
                sessionId=session_id,
                maxResults=20
            )
            
            events = events_response.get('eventSummaries', [])
            
            memories.append({
                "sessionId": session_id,
                "startTime": str(session.get('sessionStartTime', '')),
                "eventCount": len(events),
                "events": [format_event(e) for e in events[:5]]  # Últimos 5 eventos
            })
        
        return {
            "userId": user_id,
            "memoryCount": len(memories),
            "memories": memories
        }
        
    except agentcore.exceptions.ResourceNotFoundException:
        return {"userId": user_id, "memoryCount": 0, "memories": []}
    except Exception as e:
        print(f"Error getting memory: {e}")
        return {"userId": user_id, "memoryCount": 0, "memories": [], "note": str(e)}


def save_conversation_event(user_id: str, session_id: str, message: str, role: str = "USER") -> dict:
    """
    Guarda un evento de conversación en AgentCore Memory.
    """
    if not user_id or not message:
        return {"error": "userId and message are required"}
    
    if not session_id:
        session_id = f"session-{int(time.time())}"
    
    try:
        # Crear timestamp en formato ISO 8601
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        response = agentcore.create_event(
            memoryId=MEMORY_ID,
            actorId=user_id,
            sessionId=session_id,
            eventTimestamp=timestamp,
            payload=[
                {
                    "conversational": {
                        "content": {"text": message},
                        "role": role.upper()
                    }
                }
            ]
        )
        
        return {
            "success": True,
            "eventId": response.get('eventId'),
            "userId": user_id,
            "sessionId": session_id
        }
        
    except Exception as e:
        print(f"Error saving event: {e}")
        return {"success": False, "error": str(e)}


def get_user_memory_summary(user_id: str) -> dict:
    """
    Obtiene un resumen de la memoria del usuario.
    """
    if not user_id:
        return {"error": "userId is required"}
    
    try:
        # Buscar memorias de largo plazo
        memories_response = agentcore.retrieve_memory_records(
            memoryId=MEMORY_ID,
            namespace=f"/users/{user_id}",
            maxResults=10
        )
        
        records = memories_response.get('memoryRecordSummaries', [])
        
        return {
            "userId": user_id,
            "recordCount": len(records),
            "records": [
                {
                    "namespace": r.get('namespace'),
                    "content": r.get('content', {}).get('text', '')[:200]
                }
                for r in records
            ]
        }
        
    except Exception as e:
        print(f"Error getting summary: {e}")
        return {"userId": user_id, "recordCount": 0, "records": []}


def search_memories(user_id: str, query: str, limit: int = 5) -> dict:
    """
    Busca en las memorias del usuario usando búsqueda semántica.
    """
    if not user_id or not query:
        return {"error": "userId and query are required"}
    
    try:
        response = agentcore.retrieve_memory_records(
            memoryId=MEMORY_ID,
            namespace=f"/users/{user_id}",
            searchCriteria={
                "semanticQuery": {
                    "text": query
                },
                "topK": int(limit)
            }
        )
        
        records = response.get('memoryRecordSummaries', [])
        
        return {
            "userId": user_id,
            "query": query,
            "resultCount": len(records),
            "results": [
                {
                    "content": r.get('content', {}).get('text', ''),
                    "score": r.get('score', 0)
                }
                for r in records
            ]
        }
        
    except Exception as e:
        print(f"Error searching: {e}")
        return {"userId": user_id, "query": query, "resultCount": 0, "results": []}


def delete_user_memory(user_id: str) -> dict:
    """
    Elimina toda la memoria de un usuario (para GDPR, etc.).
    """
    if not user_id:
        return {"error": "userId is required"}
    
    try:
        # Listar y eliminar todas las sesiones
        sessions = agentcore.list_sessions(
            memoryId=MEMORY_ID,
            actorId=user_id,
            maxResults=100
        )
        
        deleted_count = 0
        for session in sessions.get('sessionSummaries', []):
            # Eliminar eventos de la sesión
            events = agentcore.list_events(
                memoryId=MEMORY_ID,
                actorId=user_id,
                sessionId=session['sessionId'],
                maxResults=100
            )
            
            for event in events.get('eventSummaries', []):
                agentcore.delete_event(
                    memoryId=MEMORY_ID,
                    actorId=user_id,
                    sessionId=session['sessionId'],
                    eventId=event['eventId']
                )
                deleted_count += 1
        
        return {
            "success": True,
            "userId": user_id,
            "deletedEvents": deleted_count
        }
        
    except Exception as e:
        print(f"Error deleting: {e}")
        return {"success": False, "error": str(e)}


def format_event(event: dict) -> dict:
    """Formatea un evento para la respuesta."""
    return {
        "eventId": event.get('eventId'),
        "timestamp": str(event.get('eventTimestamp', '')),
        "type": event.get('payloadType', 'unknown')
    }


def format_response(body: dict, status_code: int = 200) -> dict:
    """
    Formatea la respuesta para Bedrock Agent Action Group.
    """
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': 'AgentCoreMemory',
            'apiPath': '/response',
            'httpMethod': 'POST',
            'httpStatusCode': status_code,
            'responseBody': {
                'application/json': {
                    'body': json.dumps(body)
                }
            }
        }
    }
