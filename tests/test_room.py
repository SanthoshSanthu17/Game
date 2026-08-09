import unittest
import asyncio
from unittest.mock import Mock
from server.room import Room, RoomManager, RoomState, generate_room_code
from shared.game import PlayerId

class TestRoomAndManager(unittest.TestCase):
    def test_room_code_generation(self):
        code = generate_room_code(6)
        self.assertEqual(len(code), 6)
        for char in code:
            self.assertNotIn(char, "0O1I")

    def test_room_creation_and_player_joining(self):
        async def run_test():
            room = Room("ABC123")
            self.assertEqual(room.state, RoomState.WAITING)
            self.assertFalse(room.is_full())

            ws1 = Mock()
            pid1 = await room.add_player("Alice", ws1)
            self.assertEqual(pid1, PlayerId.PLAYER_1)
            self.assertEqual(room.state, RoomState.WAITING)
            self.assertFalse(room.is_full())

            ws2 = Mock()
            pid2 = await room.add_player("Bob", ws2)
            self.assertEqual(pid2, PlayerId.PLAYER_2)
            self.assertEqual(room.state, RoomState.READY)
            self.assertTrue(room.is_full())

            ws3 = Mock()
            with self.assertRaises(ValueError):
                await room.add_player("Charlie", ws3)

        asyncio.run(run_test())

    def test_room_manager(self):
        async def run_test():
            manager = RoomManager()
            room1 = await manager.create_room()
            room2 = await manager.create_room()

            self.assertNotEqual(room1.room_code, room2.room_code)
            
            fetched = await manager.get_room(room1.room_code)
            self.assertEqual(fetched, room1)

            await manager.remove_room(room1.room_code)
            self.assertIsNone(await manager.get_room(room1.room_code))

        asyncio.run(run_test())

    def test_independent_game_engines(self):
        async def run_test():
            manager = RoomManager()
            r1 = await manager.create_room()
            r2 = await manager.create_room()

            r1.start_game()
            r2.start_game()

            self.assertIsNotNone(r1.game_engine)
            self.assertIsNotNone(r2.game_engine)
            self.assertNotEqual(r1.game_engine, r2.game_engine)

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()