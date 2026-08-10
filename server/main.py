import asyncio

from server.server import GameServer


HOST = "0.0.0.0"
PORT = 8765


async def main():
    server = GameServer(
        host=HOST,
        port=PORT,
    )

    print(f"Ben 10 Galactic Battle server running on port {PORT}")
    print(f"Local game: http://localhost:{PORT}/web/")

    await server.start()


if __name__ == "__main__":
    asyncio.run(main())