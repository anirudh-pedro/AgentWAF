import json
from typing import Any
from fastapi import WebSocket, WebSocketDisconnect
from logger import get_logger
from .models import AuditEvent
from .publisher import AuditEventPublisher

logger = get_logger(__name__)


class ConnectionManager:
    """WebSocket Connection Manager managing real-time broadcast subscriptions."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []
        # Subscribe manager to AuditEventPublisher
        AuditEventPublisher.get_instance().subscribe(self.on_audit_event)

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register new client WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("New WebSocket client connected", extra={"active_clients": len(self.active_connections)})

    def disconnect(self, websocket: WebSocket) -> None:
        """Unregister client WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket client disconnected", extra={"active_clients": len(self.active_connections)})

    async def broadcast_json(self, message: dict[str, Any]) -> None:
        """Broadcast JSON message payload to all connected WebSockets."""
        disconnected: list[WebSocket] = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json.dumps(message))
            except Exception as exc:
                logger.warning("Failed to send text to WebSocket client", extra={"error": str(exc)})
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)

    def on_audit_event(self, event: AuditEvent) -> None:
        """Subscriber callback broadcasting real-time audit event updates."""
        try:
            import asyncio
            payload = {
                "type": "AUDIT_EVENT",
                "data": event.model_dump(),
            }
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.broadcast_json(payload))
            except RuntimeError:
                pass
        except Exception as exc:
            logger.exception("Error broadcasting audit event via WebSocket", extra={"error": str(exc)})


ws_manager = ConnectionManager()
