import unittest
from shared.protocol import public_card_data, serialize_message, parse_message
from shared.models import Card

class TestProtocol(unittest.TestCase):
    def test_public_card_data(self):
        card = Card(
            id=1, name="Humungousaur", image="humungousaur.png",
            rank=16, height=12.0, weight=2000.0, speed=40.0,
            power=95, intelligence=50, defense=90
        )
        data = public_card_data(card)
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["name"], "Humungousaur")
        self.assertEqual(data["rank"], 16)
        self.assertIsNone(public_card_data(None))

    def test_serialize_and_parse_message(self):
        raw = serialize_message("CREATE_ROOM", {"player_name": "Santhosh"})
        parsed = parse_message(raw)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["type"], "CREATE_ROOM")
        self.assertEqual(parsed["player_name"], "Santhosh")

    def test_parse_invalid_json(self):
        self.assertIsNone(parse_message("invalid json"))
        self.assertIsNone(parse_message('{"no_type": true}'))

if __name__ == "__main__":
    unittest.main()