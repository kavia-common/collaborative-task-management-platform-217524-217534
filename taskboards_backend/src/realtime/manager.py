import asyncio
from typing import Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    """
    Simple room-based websocket manager with presence.
    """
    def __init__(self) -> None:
        self.rooms: Dict[str, Set[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, room: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self.lock:
            self.rooms.setdefault(room, set()).add(websocket)
        await self.broadcast(room, {"type": "presence.join", "count": await self.count(room)})

    async def disconnect(self, room: str, websocket: WebSocket) -> None:
        async with self.lock:
            if room in self.rooms and websocket in self.rooms[room]:
                self.rooms[room].remove(websocket)
                if not self.rooms[room]:
                    del self.rooms[room]
        await self.broadcast(room, {"type": "presence.leave", "count": await self.count(room)})

    async def broadcast(self, room: str, message) -> None:
        async with self.lock:
            sockets = list(self.rooms.get(room, set()))
        for ws in sockets:
            try:
                await ws.send_json(message)
            except Exception:
                # best-effort
                try:
                    await ws.close()
                except Exception:
                    pass

    async def count(self, room: str) -> int:
        async with self.lock:
            return len(self.rooms.get(room, set()))
