import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages active WebSocket connections grouped by video episode."""
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, episode_id: str, websocket: WebSocket):
        await websocket.accept()
        if episode_id not in self.active_connections:
            self.active_connections[episode_id] = set()
        self.active_connections[episode_id].add(websocket)
        logger.info(f"WebSocket client connected to episode {episode_id}. Total clients: {len(self.active_connections[episode_id])}")

    def disconnect(self, episode_id: str, websocket: WebSocket):
        if episode_id in self.active_connections:
            self.active_connections[episode_id].discard(websocket)
            if not self.active_connections[episode_id]:
                del self.active_connections[episode_id]
        logger.info(f"WebSocket client disconnected from episode {episode_id}.")

    async def broadcast(self, episode_id: str, message: dict):
        if episode_id not in self.active_connections:
            return

        dead_connections = set()
        for connection in list(self.active_connections[episode_id]):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Error broadcasting to a client, marking dead: {e}")
                dead_connections.add(connection)

        for dead in dead_connections:
            self.disconnect(episode_id, dead)

danmaku_manager = ConnectionManager()
