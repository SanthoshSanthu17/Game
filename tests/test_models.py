import json
import os
import pytest
from shared.models import Card, PlayerState
from shared.constants import BATTLE_ATTRIBUTES, TOTAL_CARDS

def test_card_creation_and_attributes():
    """Verify that a Card is created successfully and attributes map correctly."""
    card = Card(
        id=99, name="TestAlien", image="test.png", rank=25,
        height=6.5, weight=120.0, speed=50.0,
        power=85, intelligence=90, defense=80
    )
    
    assert card.id == 99
    assert card.name == "TestAlien"
    
    # Test valid battle attributes access
    assert card.get_stat("rank") == 25
    assert card.get_stat("height") == 6.5
    assert card.get_stat("weight") == 120.0
    assert card.get_stat("speed") == 50.0
    assert card.get_stat("power") == 85
    assert card.get_stat("intelligence") == 90
    assert card.get_stat("defense") == 80

def test_invalid_get_stat():
    """Verify get_stat raises ValueError for non-battle attributes."""
    card = Card(
        id=99, name="TestAlien", image="test.png", rank=25,
        height=6.5, weight=120.0, speed=50.0,
        power=85, intelligence=90, defense=80
    )
    
    # "id" is an object field but NOT a battle attribute
    with pytest.raises(ValueError):
        card.get_stat("id")
        
    with pytest.raises(ValueError):
        card.get_stat("name")
        
    with pytest.raises(ValueError):
        card.get_stat("invalid_stat_name")

def test_player_state_creation():
    """Verify PlayerState instantiation."""
    state = PlayerState(player_id="p_123", name="Player One", card_count=26)
    assert state.player_id == "p_123"
    assert state.name == "Player One"
    assert state.card_count == 26

def test_cards_json_integrity():
    """Verify the integrity of the 52-card dataset."""
    filepath = os.path.join(os.path.dirname(__file__), "..", "data", "cards.json")
    with open(filepath, "r", encoding="utf-8") as f:
        cards = json.load(f)
        
    # Check total card count
    assert len(cards) == TOTAL_CARDS
    
    ids = set()
    names = set()
    ranks = set()
    
    for card in cards:
        # Check that all base and battle attributes exist
        assert "id" in card
        assert "name" in card
        assert "image" in card
        
        for attr in BATTLE_ATTRIBUTES:
            assert attr in card, f"Missing attribute {attr} in card {card.get('name')}"
            
        ids.add(card["id"])
        names.add(card["name"])
        ranks.add(card["rank"])
        
        # Check value constraints for standard game stats
        assert 1 <= card["power"] <= 100
        assert 1 <= card["intelligence"] <= 100
        assert 1 <= card["defense"] <= 100
        
    # Check uniqueness constraints
    assert len(ids) == TOTAL_CARDS, "Card IDs must be unique"
    assert len(names) == TOTAL_CARDS, "Card names must be unique"
    
    # Check Rank constraints (exactly 1 through 52)
    assert len(ranks) == TOTAL_CARDS, "Card ranks must be unique"
    assert min(ranks) == 1, "Minimum rank must be 1"
    assert max(ranks) == TOTAL_CARDS, f"Maximum rank must be {TOTAL_CARDS}"