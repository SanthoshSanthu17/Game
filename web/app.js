let socket = null;
let playerId = null;
let roomCode = null;
let gameState = null;
let lastRoundResult = null;
let resultTimeout = null;
let cards = {};

const menuScreen = document.getElementById("menu-screen");
const waitingScreen = document.getElementById("waiting-screen");
const gameScreen = document.getElementById("game-screen");
const gameOverScreen = document.getElementById("game-over-screen");

const playerNameInput = document.getElementById("player-name");
const roomCodeInput = document.getElementById("room-code");
const menuMessage = document.getElementById("menu-message");

const waitingCode = document.getElementById("waiting-code");

const roomInfo = document.getElementById("room-info");
const opponentInfo = document.getElementById("opponent-info");
const playerInfo = document.getElementById("player-info");
const opponentCard = document.getElementById("opponent-card");
const ownCard = document.getElementById("own-card");
const turnMessage = document.getElementById("turn-message");
const resultBanner = document.getElementById("result-banner");
const gameOverMessage = document.getElementById("game-over-message");

function showScreen(screen) {
    menuScreen.classList.add("hidden");
    waitingScreen.classList.add("hidden");
    gameScreen.classList.add("hidden");
    gameOverScreen.classList.add("hidden");

    screen.classList.remove("hidden");
}

async function loadCards() {
    try {
        const response = await fetch("/data/cards.json");
        const data = await response.json();

        for (const card of data) {
            cards[card.name] = card;
        }
    } catch (error) {
        console.error("Unable to load cards.json:", error);
    }
}

function websocketUrl() {
    const protocol =
        window.location.protocol === "https:" ? "wss:" : "ws:";

    return `${protocol}//${window.location.host}`;
}

function connect() {
    return new Promise((resolve, reject) => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            resolve();
            return;
        }

        socket = new WebSocket(websocketUrl());

        socket.onopen = () => {
            resolve();
        };

        socket.onerror = () => {
            reject(new Error("Unable to connect to game server."));
        };

        socket.onclose = () => {
            if (gameScreen.classList.contains("hidden") === false) {
                showMenuError("Connection to server was lost.");
            }
        };

        socket.onmessage = event => {
            try {
                handleMessage(JSON.parse(event.data));
            } catch (error) {
                console.error("Invalid server message:", error);
            }
        };
    });
}

function send(type, data = {}) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        showMenuError("Not connected to server.");
        return;
    }

    socket.send(JSON.stringify({
        type,
        ...data
    }));
}

async function createRoom() {
    const name = playerNameInput.value.trim();

    if (!name) {
        showMenuError("Please enter your name.");
        return;
    }

    try {
        await connect();
        send("CREATE_ROOM", {
            player_name: name
        });
    } catch (error) {
        showMenuError(error.message);
    }
}

async function joinRoom() {
    const name = playerNameInput.value.trim();
    const code = roomCodeInput.value.trim().toUpperCase();

    if (!name || !code) {
        showMenuError("Enter your name and room code.");
        return;
    }

    try {
        await connect();
        send("JOIN_ROOM", {
            room_code: code,
            player_name: name
        });
    } catch (error) {
        showMenuError(error.message);
    }
}

function showMenuError(message) {
    menuMessage.textContent = message;
}

function handleMessage(msg) {
    switch (msg.type) {

        case "ROOM_CREATED":
            roomCode = msg.room_code;
            playerId = msg.player_id;

            waitingCode.textContent = roomCode;
            showScreen(waitingScreen);
            break;

        case "ROOM_JOINED":
            roomCode = msg.room_code;
            playerId = msg.player_id;

            waitingCode.textContent = roomCode;
            showScreen(waitingScreen);
            break;

        case "GAME_STARTED":
            gameState = msg;
            lastRoundResult = null;

            showScreen(gameScreen);
            renderGame();
            break;

        case "ROUND_RESULT":
            lastRoundResult = msg;
            gameState = msg.state;

            renderGame();
            showRoundResult(msg);

            clearTimeout(resultTimeout);

            resultTimeout = setTimeout(() => {
                lastRoundResult = null;
                renderGame();
            }, 3000);

            break;

        case "GAME_OVER":
            showGameOver(msg);
            break;

        case "PLAYER_DISCONNECTED":
            showMenuError("Opponent disconnected.");
            showScreen(menuScreen);
            break;

        case "ERROR":
            if (gameScreen.classList.contains("hidden")) {
                showMenuError(msg.message || "Server error.");
            } else {
                alert(msg.message || "Server error.");
            }
            break;
    }
}

function getCardImage(card) {
    if (!card) {
        return null;
    }

    if (card.image) {
        return `/assets/images/${card.image}`;
    }

    const localCard = cards[card.name];

    if (localCard && localCard.image) {
        return `/assets/images/${localCard.image}`;
    }

    return null;
}

function renderCard(card, hidden = false) {
    if (hidden || !card) {
        return `
            <div class="card hidden-card">
                <div class="hidden-inner">BEN 10</div>
            </div>
        `;
    }

    const image = getCardImage(card);

    const imageHtml = image
        ? `<img src="${image}" alt="${escapeHtml(card.name || "Card")}">`
        : `<span>CARD ART</span>`;

    return `
        <div class="card">

            <div class="card-header">
                <div class="card-name">${escapeHtml(card.name || "Unknown")}</div>
                <div class="rank-badge">Rk${card.rank ?? 0}</div>
            </div>

            <div class="card-image">
                ${imageHtml}
            </div>

            <div class="stats">
                ${statRow("Rank", card.rank)}
                ${statRow("Height", `${card.height ?? 0}ft`)}
                ${statRow("Weight", `${card.weight ?? 0} kg`)}
                ${statRow("Speed", `${card.speed ?? 0} km/h`)}
                ${statRow("Power", card.power)}
                ${statRow("Intelligence", card.intelligence)}
                ${statRow("Defense", card.defense)}
            </div>

        </div>
    `;
}

function statRow(label, value) {
    return `
        <div class="stat-row">
            <span class="stat-label">${label}:</span>
            <span class="stat-value">${value ?? 0}</span>
        </div>
    `;
}

function renderGame() {
    if (!gameState) {
        return;
    }

    roomInfo.textContent =
        `ROOM: ${gameState.room_code || roomCode}  |  ROUND: ${gameState.round_number || 1}  |  POT: ${gameState.pot_size || 0} cards`;

    opponentInfo.textContent =
        `OPPONENT: ${gameState.opponent_name || "Opponent"} (${gameState.opponent_card_count ?? 0} cards)`;

    playerInfo.textContent =
        `YOU: ${gameState.player_name || playerNameInput.value} (${gameState.own_card_count ?? 0} cards)`;

    let opponent = null;
    let own = gameState.own_active_card || null;

    const showingResult =
        lastRoundResult !== null;

    if (showingResult) {
        opponent = playerId === 1
            ? lastRoundResult.p2_card
            : lastRoundResult.p1_card;

        own = playerId === 1
            ? lastRoundResult.p1_card
            : lastRoundResult.p2_card;
    }

    opponentCard.innerHTML = renderCard(opponent, !opponent);

    ownCard.innerHTML = renderCard(own, false);

    const myTurn =
        Number(gameState.current_turn) === Number(playerId);

    if (showingResult) {
        turnMessage.textContent = "";
        turnMessage.className = "";
    } else if (myTurn) {
        turnMessage.textContent = "YOUR TURN — CHOOSE A STAT";
        turnMessage.className = "your-turn";
    } else {
        turnMessage.textContent = "OPPONENT'S TURN...";
        turnMessage.className = "opponent-turn";
    }

    const buttons = document.querySelectorAll("#stat-buttons button");

    buttons.forEach(button => {
        button.disabled = !myTurn || showingResult;
    });
}

function showRoundResult(result) {
    const winner = result.winner;
    const tie = result.is_tie;

    resultBanner.className.remove("hidden");
    resultBanner.classList.remove(
        "result-win",
        "result-lose",
        "result-tie"
    );

    if (tie) {
        resultBanner.textContent = "TIE! CARDS MOVED TO POT";
        resultBanner.classList.add("result-tie");
    } else if (Number(winner) === Number(playerId)) {
        resultBanner.textContent = "YOU WIN THIS ROUND!";
        resultBanner.classList.add("result-win");
    } else {
        resultBanner.textContent = "YOU LOSE THIS ROUND!";
        resultBanner.classList.add("result-lose");
    }

    setTimeout(() => {
        resultBanner.classList.add("hidden");
    }, 3000);
}

function showGameOver(data) {
    const winner = Number(data.winner);

    if (winner === Number(playerId)) {
        gameOverMessage.textContent = "VICTORY! YOU WON THE GAME!";
        gameOverMessage.style.color = "#64ff64";
    } else {
        gameOverMessage.textContent = "DEFEAT! OPPONENT WON.";
        gameOverMessage.style.color = "#ff6464";
    }

    showScreen(gameOverScreen);
}

function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = String(value);
    return div.innerHTML;
}

document.getElementById("create-room").addEventListener(
    "click",
    createRoom
);

document.getElementById("join-room").addEventListener(
    "click",
    joinRoom
);

document.querySelectorAll("#stat-buttons button").forEach(button => {
    button.addEventListener("click", () => {
        if (button.disabled) {
            return;
        }

        send("SELECT_ATTRIBUTE", {
            attribute: button.dataset.stat
        });
    });
});

roomCodeInput.addEventListener("input", () => {
    roomCodeInput.value = roomCodeInput.value
        .toUpperCase()
        .replace(/[^A-Z0-9]/g, "");
});

loadCards();