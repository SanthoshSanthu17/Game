import asyncio
import http
import logging
import mimetypes
import os
from pathlib import Path
from typing import Optional

import websockets
from websockets.server import WebSocketServerProtocol

from server.room import RoomManager, RoomState
from shared.protocol import parse_message, serialize_message, public_card_data
from shared.constants import BATTLE_ATTRIBUTES
from shared.game import PlayerId, GameStatus


logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class GameServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.room_manager = RoomManager()

    async def process_request(self, path, request_headers):
        """
        Serve the web application through the same port as the WebSocket server.
        WebSocket upgrade requests return None and continue normally.
        """

        if request_headers.get("Upgrade", "").lower() == "websocket":
            return None

        clean_path = path.split("?", 1)[0]

        if clean_path == "/":
            clean_path = "/web/"

        if clean_path == "/web":
            clean_path = "/web/"

        if clean_path.endswith("/"):
            clean_path += "index.html"

        relative_path = clean_path.lstrip("/")

        requested_file = (PROJECT_ROOT / relative_path).resolve()

        try:
            requested_file.relative_to(PROJECT_ROOT)
        except ValueError:
            return (
                http.HTTPStatus.FORBIDDEN,
                [("Content-Type", "text/plain; charset=utf-8")],
                b"Forbidden",
            )

        if not requested_file.is_file():
            return (
                http.HTTPStatus.NOT_FOUND,
                [("Content-Type", "text/plain; charset=utf-8")],
                b"Not Found",
            )

        try:
            body = requested_file.read_bytes()
        except OSError:
            return (
                http.HTTPStatus.INTERNAL_SERVER_ERROR,
                [("Content-Type", "text/plain; charset=utf-8")],
                b"Internal Server Error",
            )

        content_type, _ = mimetypes.guess_type(str(requested_file))

        if content_type is None:
            content_type = "application/octet-stream"

        headers = [
            ("Content-Type", content_type),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-cache"),
        ]

        return (
            http.HTTPStatus.OK,
            headers,
            body,
        )

    async def handle_client(
        self,
        websocket: WebSocketServerProtocol,
    ) -> None:

        current_room_code: Optional[str] = None
        current_player_id: Optional[PlayerId] = None

        try:
            async for raw_message in websocket:

                msg = parse_message(raw_message)

                if not msg:
                    await websocket.send(
                        serialize_message(
                            "ERROR",
                            {
                                "message": (
                                    "Invalid JSON or missing message type."
                                )
                            },
                        )
                    )
                    continue

                msg_type = msg.get("type")

                if msg_type == "CREATE_ROOM":

                    player_name = msg.get("player_name")

                    if (
                        not player_name
                        or not isinstance(player_name, str)
                    ):
                        await websocket.send(
                            serialize_message(
                                "ERROR",
                                {
                                    "message": (
                                        "Missing or invalid player_name."
                                    )
                                },
                            )
                        )
                        continue

                    room = await self.room_manager.create_room()

                    current_room_code = room.room_code

                    current_player_id = await room.add_player(
                        player_name,
                        websocket,
                    )

                    await websocket.send(
                        serialize_message(
                            "ROOM_CREATED",
                            {
                                "room_code": current_room_code,
                                "player_id": current_player_id.value,
                            },
                        )
                    )

                elif msg_type == "JOIN_ROOM":

                    room_code = msg.get("room_code")
                    player_name = msg.get("player_name")

                    if (
                        not room_code
                        or not player_name
                        or not isinstance(room_code, str)
                        or not isinstance(player_name, str)
                    ):
                        await websocket.send(
                            serialize_message(
                                "ERROR",
                                {
                                    "message": (
                                        "Missing room_code or player_name."
                                    )
                                },
                            )
                        )
                        continue

                    room = await self.room_manager.get_room(room_code)

                    if not room:
                        await websocket.send(
                            serialize_message(
                                "ERROR",
                                {
                                    "message": "Room not found.",
                                },
                            )
                        )
                        continue

                    if room.is_full():
                        await websocket.send(
                            serialize_message(
                                "ERROR",
                                {
                                    "message": "Room is full.",
                                },
                            )
                        )
                        continue

                    if room.state != RoomState.WAITING:
                        await websocket.send(
                            serialize_message(
                                "ERROR",
                                {
                                    "message": (
                                        "Room is not open for joining."
                                    )
                                },
                            )
                        )
                        continue

                    current_room_code = room.room_code

                    try:
                        current_player_id = await room.add_player(
                            player_name,
                            websocket,
                        )

                    except ValueError as e:
                        await websocket.send(
                            serialize_message(
                                "ERROR",
                                {
                                    "message": str(e),
                                },
                            )
                        )
                        continue

                    await websocket.send(
                        serialize_message(
                            "ROOM_JOINED",
                            {
                                "room_code": current_room_code,
                                "player_id": current_player_id.value,
                            },
                        )
                    )

                    if room.state == RoomState.READY:

                        room.start_game()

                        for pid, pconn in room.players.items():

                            state_payload = room.get_game_state_payload(
                                pid
                            )

                            await pconn.websocket.send(
                                serialize_message(
                                    "GAME_STARTED",
                                    state_payload,
                                )
                            )

                elif msg_type == "SELECT_ATTRIBUTE":

                    if (
                        not current_room_code
                        or not current_player_id
                    ):
                        await websocket.send(
                            serialize_message(
                                "ERROR",
                                {
                                    "message": (
                                        "Not in an active room."
                                    )
                                },
                            )
                        )
                        continue

                    room = await self.room_manager.get_room(
                        current_room_code
                    )

                    if (
                        not room
                        or room.state != RoomState.PLAYING
                        or not room.game_engine
                    ):
                        await websocket.send(
                            serialize_message(
                                "ERROR",
                                {
                                    "message": (
                                        "Game is not currently playing."
                                    )
                                },
                            )
                        )
                        continue

                    engine = room.game_engine

                    if engine.status == GameStatus.GAME_OVER:
                        await websocket.send(
                            serialize_message(
                                "ERROR",
                                {
                                    "message": (
                                        "Game is already over."
                                    )
                                },
                            )
                        )
                        continue

                    if engine.current_turn != current_player_id:
                        await websocket.send(
                            serialize_message(
                                "ERROR",
                                {
                                    "message": "Not your turn.",
                                },
                            )
                        )
                        continue

                    attribute = msg.get("attribute")

                    if (
                        not attribute
                        or not isinstance(attribute, str)
                    ):
                        await websocket.send(
                            serialize_message(
                                "ERROR",
                                {
                                    "message": "Missing attribute.",
                                },
                            )
                        )
                        continue

                    attribute = attribute.lower()

                    if attribute not in BATTLE_ATTRIBUTES:
                        await websocket.send(
                            serialize_message(
                                "ERROR",
                                {
                                    "message": (
                                        f"Invalid attribute: {attribute}"
                                    )
                                },
                            )
                        )
                        continue

                    async with room._lock:

                        if engine.status == GameStatus.GAME_OVER:
                            continue

                        try:
                            round_result = engine.play_round(
                                attribute
                            )

                        except Exception as e:
                            await websocket.send(
                                serialize_message(
                                    "ERROR",
                                    {
                                        "message": str(e),
                                    },
                                )
                            )
                            continue

                        for pid, pconn in room.players.items():

                            result_data = {
                                "attribute": round_result.attribute,
                                "p1_card": public_card_data(
                                    round_result.p1_card
                                ),
                                "p2_card": public_card_data(
                                    round_result.p2_card
                                ),
                                "p1_value": round_result.p1_value,
                                "p2_value": round_result.p2_value,
                                "winner": (
                                    round_result.winner.value
                                    if round_result.winner
                                    else None
                                ),
                                "is_tie": round_result.is_tie,
                                "pot_size": round_result.pot_size,
                                "p1_card_count": (
                                    round_result.p1_card_count
                                ),
                                "p2_card_count": (
                                    round_result.p2_card_count
                                ),
                                "game_over": round_result.game_over,
                                "state": (
                                    room.get_game_state_payload(pid)
                                ),
                            }

                            await pconn.websocket.send(
                                serialize_message(
                                    "ROUND_RESULT",
                                    result_data,
                                )
                            )

                        if round_result.game_over:

                            room.state = RoomState.FINISHED

                            winner_id = (
                                engine.winner.value
                                if engine.winner
                                else None
                            )

                            for pid, pconn in room.players.items():

                                await pconn.websocket.send(
                                    serialize_message(
                                        "GAME_OVER",
                                        {
                                            "winner": winner_id,
                                            "p1_card_count": len(
                                                engine.deck_p1
                                            ),
                                            "p2_card_count": len(
                                                engine.deck_p2
                                            ),
                                        },
                                    )
                                )

                else:

                    await websocket.send(
                        serialize_message(
                            "ERROR",
                            {
                                "message": (
                                    f"Unknown message type: {msg_type}"
                                )
                            },
                        )
                    )

        except websockets.exceptions.ConnectionClosed:
            pass

        finally:

            if current_room_code and current_player_id:

                room = await self.room_manager.get_room(
                    current_room_code
                )

                if room:

                    await room.remove_player(
                        current_player_id
                    )

                    for pid, pconn in room.players.items():

                        try:
                            await pconn.websocket.send(
                                serialize_message(
                                    "PLAYER_DISCONNECTED",
                                    {
                                        "message": (
                                            "Opponent disconnected. "
                                            "Game interrupted."
                                        )
                                    },
                                )
                            )

                        except Exception:
                            pass

                    if len(room.players) == 0:
                        await self.room_manager.remove_room(
                            current_room_code
                        )

    async def start(self):

        async with websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            process_request=self.process_request,
        ):

            print(
                f"HTTP + WebSocket server: "
                f"http://{self.host}:{self.port}"
            )

            await asyncio.Future()


def run_server():
    server = GameServer()
    asyncio.run(server.start())