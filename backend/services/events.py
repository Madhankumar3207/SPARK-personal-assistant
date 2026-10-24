"""Small WebSocket event broadcaster shared with the voice worker."""
import asyncio

from fastapi import WebSocket


class EventHub:
    def __init__(self):
        self.connections: set[WebSocket] = set()
        self.lock = asyncio.Lock()
        self.loop = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.connections.add(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self.lock:
            self.connections.discard(websocket)

    async def broadcast(self, event: dict):
        async with self.lock:
            connections = tuple(self.connections)
        stale = []
        for connection in connections:
            try:
                await connection.send_json(event)
            except Exception:
                stale.append(connection)
        if stale:
            async with self.lock:
                for connection in stale:
                    self.connections.discard(connection)

    def publish(self, event: dict):
        if self.loop is not None and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.broadcast(event), self.loop)


events = EventHub()
