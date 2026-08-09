import random
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional, Deque

from shared.models import Card
from shared.constants import BATTLE_ATTRIBUTES

class PlayerId(Enum):
    PLAYER_1 = 1
    PLAYER_2 = 2

class GameStatus(Enum):
    ACTIVE = 1
    GAME_OVER = 2

@dataclass
class RoundResult:
    attribute: str
    p1_card: Card
    p2_card: Card
    p1_value: Any
    p2_value: Any
    winner: Optional[PlayerId]
    is_tie: bool
    cards_won: List[Card]
    pot_size: int
    p1_card_count: int
    p2_card_count: int
    game_over: bool

class GameEngine:
    """
    Core deterministic rules engine for Ben 10 Card Battle.
    Completely isolated from UI, Pygame, and WebSockets.
    """
    def __init__(self, p1_name: str = "Player 1", p2_name: str = "Player 2"):
        self.p1_name = p1_name
        self.p2_name = p2_name
        self.deck_p1: Deque[Card] = deque()
        self.deck_p2: Deque[Card] = deque()
        self.pot: List[Card] = []
        self.current_turn: PlayerId = PlayerId.PLAYER_1
        self.round_number: int = 1
        self.status: GameStatus = GameStatus.ACTIVE
        self.winner: Optional[PlayerId] = None

    def start_game(self, cards: List[Card], shuffle: bool = True, rng: Optional[random.Random] = None) -> None:
        """Initializes the deck, shuffles, and distributes exactly 26 cards to each player."""
        if len(cards) != 52:
            raise ValueError(f"Game requires exactly 52 cards, got {len(cards)}")

        deck = cards.copy()
        if shuffle:
            if rng:
                rng.shuffle(deck)
            else:
                random.shuffle(deck)

        self.deck_p1 = deque(deck[:26])
        self.deck_p2 = deque(deck[26:])
        self.pot = []
        self.current_turn = PlayerId.PLAYER_1
        self.round_number = 1
        self.status = GameStatus.ACTIVE
        self.winner = None

    def get_active_cards(self) -> Optional[tuple[Card, Card]]:
        """Returns the current top cards without removing them."""
        if not self.deck_p1 or not self.deck_p2:
            return None
        return self.deck_p1[0], self.deck_p2[0]

    def play_round(self, attribute: str) -> RoundResult:
        """Executes a single round of comparison using the selected attribute."""
        if self.status == GameStatus.GAME_OVER:
            raise RuntimeError("Cannot play round: Game is already over.")

        attribute = attribute.lower()
        if attribute not in BATTLE_ATTRIBUTES:
            raise ValueError(f"Invalid attribute selected: '{attribute}'")

        if not self.deck_p1 or not self.deck_p2:
            raise RuntimeError("Missing active cards to play a round.")

        # Pop the active cards
        c1 = self.deck_p1.popleft()
        c2 = self.deck_p2.popleft()

        val1 = c1.get_stat(attribute)
        val2 = c2.get_stat(attribute)

        # Determine round winner
        round_winner = None
        if val1 == val2:
            round_winner = None
        elif attribute == "rank":
            # LOWER rank wins
            round_winner = PlayerId.PLAYER_1 if val1 < val2 else PlayerId.PLAYER_2
        else:
            # HIGHER value wins for all other stats
            round_winner = PlayerId.PLAYER_1 if val1 > val2 else PlayerId.PLAYER_2

        is_tie = (round_winner is None)
        cards_won = []

        if is_tie:
            self.pot.extend([c1, c2])
        else:
            # Winner takes newly played cards plus the pot
            cards_won = [c1, c2] + self.pot
            self.pot = []
            
            if round_winner == PlayerId.PLAYER_1:
                self.deck_p1.extend(cards_won)
                self.current_turn = PlayerId.PLAYER_1
            else:
                self.deck_p2.extend(cards_won)
                self.current_turn = PlayerId.PLAYER_2

        self.round_number += 1
        self._check_game_over()

        return RoundResult(
            attribute=attribute,
            p1_card=c1,
            p2_card=c2,
            p1_value=val1,
            p2_value=val2,
            winner=round_winner,
            is_tie=is_tie,
            cards_won=cards_won,
            pot_size=len(self.pot),
            p1_card_count=len(self.deck_p1),
            p2_card_count=len(self.deck_p2),
            game_over=(self.status == GameStatus.GAME_OVER)
        )

    def _check_game_over(self) -> None:
        """Determines if the win condition is met, handling empty deck edge-cases during ties."""
        if len(self.deck_p1) == 52:
            self.status = GameStatus.GAME_OVER
            self.winner = PlayerId.PLAYER_1
        elif len(self.deck_p2) == 52:
            self.status = GameStatus.GAME_OVER
            self.winner = PlayerId.PLAYER_2
        elif len(self.deck_p1) == 0 and len(self.deck_p2) > 0:
            # Player 1 ran out of cards during a tie string; Player 2 automatically wins the pot and the game.
            self.deck_p2.extend(self.pot)
            self.pot.clear()
            self.status = GameStatus.GAME_OVER
            self.winner = PlayerId.PLAYER_2
        elif len(self.deck_p2) == 0 and len(self.deck_p1) > 0:
            # Player 2 ran out of cards during a tie string; Player 1 automatically wins the pot and the game.
            self.deck_p1.extend(self.pot)
            self.pot.clear()
            self.status = GameStatus.GAME_OVER
            self.winner = PlayerId.PLAYER_1
        elif len(self.deck_p1) == 0 and len(self.deck_p2) == 0:
            # Absolute edge case: Total draw (both run out of cards exactly on a tie)
            self.status = GameStatus.GAME_OVER
            self.winner = None