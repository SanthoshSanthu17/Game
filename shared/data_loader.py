import json
from pathlib import Path
from typing import List
from shared.models import Card

def load_cards_from_json(filepath: str = "data/cards.json") -> List[Card]:
    """Loads and validates exactly 52 cards from the specified JSON file."""
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"Card data file not found: {filepath}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    cards = [Card(**item) for item in data]
    
    if len(cards) != 52:
        raise ValueError(f"Expected exactly 52 cards in {filepath}, found {len(cards)}")
        
    return cards