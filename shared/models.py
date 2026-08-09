from dataclasses import dataclass
from shared.constants import BATTLE_ATTRIBUTES

@dataclass
class Card:
    """
    Represents a single character card in the game.
    Attributes must match the fixed 7-stat requirement.
    """
    id: int
    name: str
    image: str
    rank: int
    height: float
    weight: float
    speed: float
    power: int
    intelligence: int
    defense: int

    def get_stat(self, category: str) -> float | int:
        """
        Retrieves the numerical value of a valid battle attribute.
        Raises ValueError if attempting to access a non-battle attribute (like id or name).
        """
        if category not in BATTLE_ATTRIBUTES:
            raise ValueError(f"Invalid battle attribute requested: {category}")
        return getattr(self, category)

@dataclass
class PlayerState:
    """
    Lightweight representation of a player's core game state.
    """
    player_id: str
    name: str
    card_count: int