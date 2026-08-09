import asyncio
import json
import threading
import queue
from typing import Optional, Dict, Any
import websockets

class GameClient:
    """Thread-safe WebSocket client wrapper for Pygame integration."""
    def __init__(self, uri: str = "ws://localhost:8765"):
        self.uri = uri
        self.websocket = None
        self.room_code: Optional[str] = None
        self.player_id: Optional[int] = None
        self.connected = False
        self.incoming_messages = queue.Queue()
        
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()

    def _run_event_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def connect(self) -> None:
        future = asyncio.run_coroutine_threadsafe(self._async_connect(), self._loop)
        future.result(timeout=5.0)

    async def _async_connect(self):
        try:
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            self._loop.create_task(self._listen())
        except Exception as e:
            self.connected = False
            self.incoming_messages.put({"type": "ERROR", "message": f"Connection failed: {str(e)}"})

    async def _listen(self):
        try:
            async for raw_msg in self.websocket:
                try:
                    msg = json.loads(raw_msg)
                    if msg.get("type") == "ROOM_CREATED":
                        self.room_code = msg.get("room_code")
                        self.player_id = msg.get("player_id")
                    elif msg.get("type") == "ROOM_JOINED":
                        self.room_code = msg.get("room_code")
                        self.player_id = msg.get("player_id")
                    self.incoming_messages.put(msg)
                except json.JSONDecodeError:
                    pass
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            self.incoming_messages.put({"type": "PLAYER_DISCONNECTED", "message": "Connection closed by server."})

    def close(self) -> None:
        if self.websocket:
            asyncio.run_coroutine_threadsafe(self._async_close(), self._loop).result(timeout=3.0)

    async def _async_close(self):
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        self.connected = False

    def send_message(self, msg_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        if not self.connected or not self.websocket:
            return
        payload = {"type": msg_type}
        if data:
            payload.update(data)
        asyncio.run_coroutine_threadsafe(self._async_send(payload), self._loop)

    async def _async_send(self, payload: dict):
        if self.websocket:
            try:
                await self.websocket.send(json.dumps(payload))
            except Exception:
                self.connected = False

    def create_room(self, player_name: str) -> None:
        self.send_message("CREATE_ROOM", {"player_name": player_name})

    def join_room(self, room_code: str, player_name: str) -> None:
        self.send_message("JOIN_ROOM", {"room_code": room_code, "player_name": player_name})

    def select_attribute(self, attribute: str) -> None:
        self.send_message("SELECT_ATTRIBUTE", {"attribute": attribute})

    def poll_messages(self) -> list:
        msgs = []
        while not self.incoming_messages.empty():
            try:
                msgs.append(self.incoming_messages.get_nowait())
            except queue.Empty:
                break
        return msgs