# Ben 10 Alien Force Card Battle

## Project Purpose
An online 1v1 multiplayer card battle game inspired by Top Trumps. Two players compete using a fixed 52-card deck featuring characters from the Ben 10 universe. Players take turns choosing statistics to compare, with the goal of collecting all 52 cards.

## Current Implementation Status
**Phase 1 Complete:** The base project structure, shared models (`Card`, `PlayerState`), validation tests, and the definitive 52-card JSON roster have been created.

* **Networking is not implemented yet.**
* **Pygame UI is not implemented yet.**
* **Lobby is not implemented yet.**
* **Gameplay is not implemented yet.**
* **HD artwork is not included yet.**

## Architecture
- `client/`: Graphical interface using Pygame (Pending)
- `server/`: Authoritative game state and WebSocket handler (Pending)
- `shared/`: Constants, models, and shared logic utilized by both ends.
- `data/`: Authoritative fixed JSON definitions.

## Folder Structure