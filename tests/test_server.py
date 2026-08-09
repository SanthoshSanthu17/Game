import unittest
import asyncio
import json
import websockets
from server.server import GameServer

class TestGameServerIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 8768
        cls.server = GameServer(host="127.0.0.1", port=cls.port)
        
        async def start_server():
            async with websockets.serve(cls.server.handle_client, "127.0.0.1", cls.port):
                await asyncio.Future()

        def run_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(start_server())
            except asyncio.CancelledError:
                pass

        import threading
        cls.server_thread = threading.Thread(target=run_loop, daemon=True)
        cls.server_thread.start()
        import time
        time.sleep(0.5)

    def test_full_gameplay_flow(self):
        async def run_client_flow():
            uri = f"ws://127.0.0.1:{self.port}"
            
            async with websockets.connect(uri) as ws1:
                async with websockets.connect(uri) as ws2:
                    
                    await ws1.send(json.dumps({"type": "CREATE_ROOM", "player_name": "Santhosh"}))
                    res1 = json.loads(await ws1.recv())
                    self.assertEqual(res1["type"], "ROOM_CREATED")
                    room_code = res1["room_code"]
                    self.assertEqual(res1["player_id"], 1)

                    await ws2.send(json.dumps({"type": "JOIN_ROOM", "room_code": room_code, "player_name": "Teammate"}))
                    res2 = json.loads(await ws2.recv())
                    self.assertEqual(res2["type"], "ROOM_JOINED")
                    self.assertEqual(res2["player_id"], 2)

                    start1 = json.loads(await ws1.recv())
                    start2 = json.loads(await ws2.recv())
                    self.assertEqual(start1["type"], "GAME_STARTED")
                    self.assertEqual(start2["type"], "GAME_STARTED")
                    self.assertNotIn("deck", start1)
                    
                    # PRIVACY VERIFICATION: Opponent active card must be hidden in start states
                    self.assertIsNone(start1.get("opponent_active_card"))
                    self.assertIsNone(start2.get("opponent_active_card"))

                    async with websockets.connect(uri) as ws3:
                        await ws3.send(json.dumps({"type": "JOIN_ROOM", "room_code": room_code, "player_name": "Intruder"}))
                        err_res = json.loads(await ws3.recv())
                        self.assertEqual(err_res["type"], "ERROR")
                        self.assertIn("full", err_res["message"].lower())

                    await ws2.send(json.dumps({"type": "SELECT_ATTRIBUTE", "attribute": "power"}))
                    turn_err = json.loads(await ws2.recv())
                    self.assertEqual(turn_err["type"], "ERROR")
                    self.assertIn("turn", turn_err["message"].lower())

                    await ws1.send(json.dumps({"type": "SELECT_ATTRIBUTE", "attribute": "nonexistent"}))
                    attr_err = json.loads(await ws1.recv())
                    self.assertEqual(attr_err["type"], "ERROR")

                    await ws1.send("not json at all")
                    mal_err = json.loads(await ws1.recv())
                    self.assertEqual(mal_err["type"], "ERROR")

                    await ws1.send(json.dumps({"type": "SELECT_ATTRIBUTE", "attribute": "power"}))
                    
                    round_res1 = json.loads(await ws1.recv())
                    round_res2 = json.loads(await ws2.recv())
                    
                    self.assertEqual(round_res1["type"], "ROUND_RESULT")
                    self.assertEqual(round_res2["type"], "ROUND_RESULT")
                    self.assertEqual(round_res1["attribute"], "power")
                    
                    # During ROUND_RESULT, both players receive their respective opponent card comparison data
                    self.assertIsNotNone(round_res1["p2_card"])
                    self.assertIsNotNone(round_res2["p1_card"])

        asyncio.run(run_client_flow())

    def test_invalid_room_join(self):
        async def run_client():
            uri = f"ws://127.0.0.1:{self.port}"
            async with websockets.connect(uri) as ws:
                await ws.send(json.dumps({"type": "JOIN_ROOM", "room_code": "ZZ99ZZ", "player_name": "Ghost"}))
                res = json.loads(await ws.recv())
                self.assertEqual(res["type"], "ERROR")
                self.assertIn("not found", res["message"].lower())

        asyncio.run(run_client())

    def test_player_disconnect(self):
        async def run_client():
            uri = f"ws://127.0.0.1:{self.port}"
            async with websockets.connect(uri) as ws1:
                await ws1.send(json.dumps({"type": "CREATE_ROOM", "player_name": "Alice"}))
                res1 = json.loads(await ws1.recv())
                room_code = res1["room_code"]

                async with websockets.connect(uri) as ws2:
                    await ws2.send(json.dumps({"type": "JOIN_ROOM", "room_code": room_code, "player_name": "Bob"}))
                    await ws2.recv() # ROOM_JOINED
                    await ws1.recv() # GAME_STARTED
                    await ws2.recv() # GAME_STARTED

                msg = json.loads(await ws1.recv())
                self.assertEqual(msg["type"], "PLAYER_DISCONNECTED")

        asyncio.run(run_client())

if __name__ == "__main__":
    unittest.main()