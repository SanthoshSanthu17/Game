import json
from typing import Any, Dict, Optional
from shared.models import Card

def public_card_data(card: Optional[Card]) -> Optional[Dict[str, Any]]:
    """Converts a Card object into a JSON-safe public dictionary representation."""
    if card is None:
        return None
    return {
        "id": card.id,
        "name": card.name,
        "image": card.image,
        "rank": card.rank,
        "height": card.height,
        "weight": card.weight,
        "speed": card.speed,
        "power": card.power,
        "intelligence": card.intelligence,
        "defense": card.defense
    }

def serialize_message(msg_type: str, data: Optional[Dict[str, Any]] = None) -> str:
    """Serializes a message dictionary into a JSON string with an explicit type."""
    message = {"type": msg_type}
    if data:
        message.update(data)
    return json.dumps(message)

def parse_message(raw_data: str) -> Optional[Dict[str, Any]]:
    """Parses raw WebSocket text data into a dictionary, validating JSON and type presence."""
    try:
        parsed = json.loads(raw_data)
        if isinstance(parsed, dict) and "type" in parsed:
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    return None