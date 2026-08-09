import unittest
import random
from unittest.mock import Mock
from shared.game import GameEngine, PlayerId, GameStatus
from shared.models import Card

class TestGameEngine(unittest.TestCase):
    def _create_mock_card(self, c_id: int, stat_val: int) -> Mock:
        """Helper to create a deterministic mocked Card to isolate the test from JSON data."""
        card = Mock(spec=Card)
        card.id = c_id
        card.name = f"Card {c_id}"
        # Override get_stat to return stat_val for any attribute
        card.get_stat.side_effect = lambda attr: stat_val
        return card

    def setUp(self):
        self.engine = GameEngine("P1", "P2")
        # Generate exactly 52 mock cards
        self.cards = [self._create_mock_card(i, i) for i in range(1, 53)]

    def test_game_initialization(self):
        self.engine.start_game(self.cards, shuffle=False)
        self.assertEqual(len(self.engine.deck_p1), 26)
        self.assertEqual(len(self.engine.deck_p2), 26)
        self.assertEqual(len(self.engine.pot), 0)
        self.assertEqual(self.engine.status, GameStatus.ACTIVE)
        self.assertEqual(self.engine.current_turn, PlayerId.PLAYER_1)

    def test_invalid_initialization(self):
        with self.assertRaises(ValueError):
            self.engine.start_game(self.cards[:50]) # Missing 2 cards

    def test_invalid_attribute(self):
        self.engine.start_game(self.cards, shuffle=False)
        with self.assertRaises(ValueError):
            self.engine.play_round("favorite_color") # Invalid stat

    def test_comparison_higher_wins(self):
        # We want P1 to win: P1 stat > P2 stat
        self.cards[0].get_stat.side_effect = lambda attr: 100
        self.cards[26].get_stat.side_effect = lambda attr: 50
        self.engine.start_game(self.cards, shuffle=False)
        
        result = self.engine.play_round("power")
        self.assertEqual(result.winner, PlayerId.PLAYER_1)
        self.assertFalse(result.is_tie)

    def test_comparison_lower_wins_rank(self):
        # We want P1 to win: P1 rank < P2 rank
        self.cards[0].get_stat.side_effect = lambda attr: 5
        self.cards[26].get_stat.side_effect = lambda attr: 10
        self.engine.start_game(self.cards, shuffle=False)
        
        result = self.engine.play_round("rank")
        self.assertEqual(result.winner, PlayerId.PLAYER_1)
        
    def test_winner_receives_cards_and_becomes_chooser(self):
        self.cards[0].get_stat.side_effect = lambda attr: 100
        self.cards[26].get_stat.side_effect = lambda attr: 50
        self.engine.start_game(self.cards, shuffle=False)
        
        c1 = self.engine.deck_p1[0]
        c2 = self.engine.deck_p2[0]
        
        result = self.engine.play_round("speed")
        self.assertEqual(result.winner, PlayerId.PLAYER_1)
        self.assertEqual(len(self.engine.deck_p1), 27) # 25 original left + 2 won
        self.assertEqual(len(self.engine.deck_p2), 25)
        self.assertEqual(self.engine.current_turn, PlayerId.PLAYER_1) # Winner chooses next
        
        # Verify cards went to the back
        self.assertEqual(self.engine.deck_p1[-2], c1)
        self.assertEqual(self.engine.deck_p1[-1], c2)

    def test_tie_creates_pot(self):
        self.cards[0].get_stat.side_effect = lambda attr: 50
        self.cards[26].get_stat.side_effect = lambda attr: 50
        self.engine.start_game(self.cards, shuffle=False)
        
        c1 = self.engine.deck_p1[0]
        c2 = self.engine.deck_p2[0]
        
        result = self.engine.play_round("power")
        self.assertTrue(result.is_tie)
        self.assertIsNone(result.winner)
        self.assertEqual(len(self.engine.pot), 2)
        self.assertIn(c1, self.engine.pot)
        self.assertIn(c2, self.engine.pot)
        self.assertEqual(len(self.engine.deck_p1), 25)
        self.assertEqual(len(self.engine.deck_p2), 25)

    def test_winner_takes_pot(self):
        # Ensure tie for round 1
        self.cards[0].get_stat.side_effect = lambda attr: 50
        self.cards[26].get_stat.side_effect = lambda attr: 50
        # Ensure P2 wins round 2
        self.cards[1].get_stat.side_effect = lambda attr: 20
        self.cards[27].get_stat.side_effect = lambda attr: 80
        
        self.engine.start_game(self.cards, shuffle=False)
        self.engine.play_round("height") # Tie
        self.assertEqual(len(self.engine.pot), 2)
        
        result = self.engine.play_round("defense")
        self.assertEqual(result.winner, PlayerId.PLAYER_2)
        self.assertEqual(len(self.engine.pot), 0)
        self.assertEqual(len(result.cards_won), 4) # 2 new cards + 2 pot cards
        self.assertEqual(len(self.engine.deck_p2), 28) # 24 remaining + 4 won
        self.assertEqual(self.engine.current_turn, PlayerId.PLAYER_2)

    def test_multiple_ties_work_correctly(self):
        # Ties
        self.cards[0].get_stat.side_effect = lambda attr: 50
        self.cards[26].get_stat.side_effect = lambda attr: 50
        self.cards[1].get_stat.side_effect = lambda attr: 60
        self.cards[27].get_stat.side_effect = lambda attr: 60
        # P1 Wins
        self.cards[2].get_stat.side_effect = lambda attr: 90
        self.cards[28].get_stat.side_effect = lambda attr: 10
        
        self.engine.start_game(self.cards, shuffle=False)
        self.engine.play_round("weight") # POT: 2
        self.engine.play_round("weight") # POT: 4
        self.assertEqual(len(self.engine.pot), 4)
        
        self.engine.play_round("intelligence") # Winner takes all
        self.assertEqual(len(self.engine.pot), 0)
        self.assertEqual(len(self.engine.deck_p1), 29) # 23 + 6 won (2 active + 4 pot)
        self.assertEqual(len(self.engine.deck_p2), 23)

    def test_card_count_invariant_randomized(self):
        """Verifies the sum of (P1_deck + P2_deck + POT) ALWAYS equals 52."""
        rng = random.Random(42) # Controlled random
        self.engine.start_game(self.cards, shuffle=True, rng=rng)
        
        attrs = ["rank", "height", "weight", "speed", "power", "intelligence", "defense"]
        for _ in range(50):
            if self.engine.status == GameStatus.GAME_OVER:
                break
            attr = rng.choice(attrs)
            self.engine.play_round(attr)
            total = len(self.engine.deck_p1) + len(self.engine.deck_p2) + len(self.engine.pot)
            self.assertEqual(total, 52) # The ultimate invariant check

    def test_game_over(self):
        self.engine.start_game(self.cards, shuffle=False)
        
        # Rig the decks so P1 has 51 cards and P2 has 1 card
        p2_last = self.engine.deck_p2.pop()
        self.engine.deck_p1.extend(self.engine.deck_p2)
        self.engine.deck_p2.clear()
        self.engine.deck_p2.append(p2_last)
        
        self.assertEqual(len(self.engine.deck_p1), 51)
        self.assertEqual(len(self.engine.deck_p2), 1)
        
        # Guarantee P1 wins the final hand
        self.engine.deck_p1[0].get_stat.side_effect = lambda attr: 100
        p2_last.get_stat.side_effect = lambda attr: 10
        
        result = self.engine.play_round("power")
        
        self.assertEqual(result.winner, PlayerId.PLAYER_1)
        self.assertTrue(result.game_over)
        self.assertEqual(self.engine.status, GameStatus.GAME_OVER)
        self.assertEqual(self.engine.winner, PlayerId.PLAYER_1)
        self.assertEqual(len(self.engine.deck_p1), 52)
        self.assertEqual(len(self.engine.deck_p2), 0)

if __name__ == "__main__":
    unittest.main()