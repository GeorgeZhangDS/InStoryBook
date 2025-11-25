"""
WebSocket endpoints for real-time story generation updates
"""
import json
import uuid
import logging
from typing import Dict, Set
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_connections: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str, session_id: str):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if session_id not in self.session_connections:
            self.session_connections[session_id] = set()
        self.session_connections[session_id].add(connection_id)
    
    def disconnect(self, connection_id: str, session_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if session_id in self.session_connections:
            self.session_connections[session_id].discard(connection_id)
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]
    
    async def send_to_session(self, message: dict, session_id: str):
        if session_id in self.session_connections:
            for connection_id in list(self.session_connections[session_id]):
                if connection_id in self.active_connections:
                    try:
                        await self.active_connections[connection_id].send_json(message)
                    except Exception as e:
                        logger.error(f"Error sending message to {connection_id}: {e}")


manager = ConnectionManager()


def create_ws_message(event_type: str, session_id: str, data: dict) -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "type": event_type,
        "timestamp": datetime.now().timestamp(),
        "session_id": session_id,
        "data": data
    }


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    connection_id = str(uuid.uuid4())
    
    try:
        await manager.connect(websocket, connection_id, session_id)
        
        await manager.send_to_session(
            create_ws_message("session_ready", session_id, {"session_id": session_id}),
            session_id
        )
        
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type", "")
                theme = message.get("theme", "").strip()
                
                if message_type == "message" and theme:
                    from app.api.story import handle_websocket_message
                    await handle_websocket_message(session_id, theme)
                else:
                    logger.warning(f"Invalid message format: {message}")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON: {data}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await manager.send_to_session(
                    create_ws_message("error", session_id, {"error": str(e)}),
                    session_id
                )
    
    except WebSocketDisconnect:
        manager.disconnect(connection_id, session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(connection_id, session_id)
