import random
import asyncio
from enum import Enum
from typing import Dict, Optional, List
from shared.game import GameEngine, GameStatus, PlayerId
from shared.data_loader import load_cards_from_json
from shared.protocol import public_card_data

ALLOWED_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

def generate_room_code(length: int = 6) -> str:
    """Generates a unique uppercase alphanumeric room code avoiding confusing characters (0, O, 1, I)."""
    return "".join(random.choices(ALLOWED_CHARS, k=length))

class RoomState(Enum):
    WAITING = "WAITING"
    READY = "READY"
    PLAYING = "PLAYING"
    FINISHED = "FINISHED"

class PlayerConnection:
    def __init__(self, player_id: PlayerId, player_name: str, websocket):
        self.player_id = player_id
        self.player_name = player_name
        self.websocket = websocket

class Room:
    def __init__(self, room_code: str):
        self.room_code = room_code
        self.state = RoomState.WAITING
        self.players: Dict[PlayerId, PlayerConnection] = {}
        self.game_engine: Optional[GameEngine] = None
        self._lock = asyncio.Lock()

    def is_full(self) -> bool:
        return len(self.players) >= 2

    async def add_player(self, player_name: str, websocket) -> PlayerId:
        async with self._lock:
            if self.is_full():
                raise ValueError("Room is full.")
            
            if PlayerId.PLAYER_1 not in self.players:
                pid = PlayerId.PLAYER_1
            else:
                pid = PlayerId.PLAYER_2
            
            self.players[pid] = PlayerConnection(pid, player_name, websocket)
            
            if len(self.players) == 2:
                self.state = RoomState.READY
            return pid

    async def remove_player(self, player_id: PlayerId) -> None:
        async with self._lock:
            if player_id in self.players:
                del self.players[player_id]
            if self.state in (RoomState.READY, RoomState.PLAYING):
                self.state = RoomState.FINISHED

    def start_game(self) -> None:
        cards = load_cards_from_json("data/cards.json")
        self.game_engine = GameEngine()
        self.game_engine.start_game(cards, shuffle=True)
        self.state = RoomState.PLAYING

    def get_game_state_payload(self, player_id: PlayerId) -> dict:
        if not self.game_engine:
            return {}
        
        is_p1 = (player_id == PlayerId.PLAYER_1)
        own_deck = self.game_engine.deck_p1 if is_p1 else self.game_engine.deck_p2
        opp_deck = self.game_engine.deck_p2 if is_p1 else self.game_engine.deck_p1
        
        own_name = self.players[PlayerId.PLAYER_1].player_name if is_p1 else self.players[PlayerId.PLAYER_2].player_name
        opp_name = self.players[PlayerId.PLAYER_2].player_name if is_p1 else self.players[PlayerId.PLAYER_1].player_name
        
        active_cards = self.game_engine.get_active_cards()
        own_active = None
        if active_cards:
            c1, c2 = active_cards
            own_active = public_card_data(c1 if is_p1 else c2)

        return {
            "room_code": self.room_code,
            "player_id": player_id.value,
            "player_name": own_name,
            "opponent_name": opp_name,
            "own_card_count": len(own_deck),
            "opponent_card_count": len(opp_deck),
            "own_active_card": own_active,
            "opponent_active_card": None,  # PRIVACY FIX: Never expose opponent active card in standard state payloads
            "current_turn": self.game_engine.current_turn.value,
            "round_number": self.game_engine.round_number,
            "game_status": self.game_engine.status.name,
            "pot_size": len(self.game_engine.pot)
        }

class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self._lock = asyncio.Lock()

    async def create_room(self) -> Room:
        async with self._lock:
            for _ in range(100):
                code = generate_room_code()
                if code not in self.rooms:
                    room = Room(code)
                    self.rooms[code] = room
                    return room
            raise RuntimeError("Failed to generate unique room code.")

    async def get_room(self, room_code: str) -> Optional[Room]:
        async with self._lock:
            return self.rooms.get(room_code.upper())

    async def remove_room(self, room_code: str) -> None:
        async with self._lock:
            if room_code.upper() in self.rooms:
                del self.rooms[room_code.upper()]