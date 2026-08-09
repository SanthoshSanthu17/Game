import pygame
from typing import Optional, Dict, Any, List

from client.ui import Button, InputBox, CardView
from client.assets import assets
from client.network import GameClient


class ScreenManager:
    def __init__(self, screen: pygame.Surface, client: GameClient):
        self.screen = screen
        self.client = client
        self.current_screen = "menu"

        self.name_input = InputBox(0, 0, 250, 40, "Santhosh")
        self.room_input = InputBox(0, 0, 250, 40, "")

        self.btn_create = Button(
            0, 0, 250, 45, "CREATE ROOM"
        )

        self.btn_join = Button(
            0, 0, 250, 45, "JOIN ROOM"
        )

        self.menu_error = ""

        self.game_state: Optional[Dict[str, Any]] = None
        self.last_round_result: Optional[Dict[str, Any]] = None
        self.game_over_data: Optional[Dict[str, Any]] = None
        self.result_timer = 0

        self.stat_buttons: List[tuple[str, Button]] = []
        self._init_stat_buttons()

    def _init_stat_buttons(self):
        stats = [
            ("rank", "RANK"),
            ("height", "HEIGHT"),
            ("weight", "WEIGHT"),
            ("speed", "SPEED"),
            ("power", "POWER"),
            ("intelligence", "INTELLIGENCE"),
            ("defense", "DEFENSE"),
        ]

        for attr_key, attr_label in stats:
            self.stat_buttons.append(
                (
                    attr_key,
                    Button(
                        0,
                        0,
                        110,
                        32,
                        attr_label,
                        bg_color=(50, 60, 90),
                    ),
                )
            )

    def _get_game_layout(self, width: int, height: int) -> Dict[str, int]:
        """
        Calculate the complete game-screen layout from one place.

        The vertical flow is:

        Opponent card
            ↓
        VS / round-result banner
            ↓
        Own card
            ↓
        Turn indicator
            ↓
        Stat buttons
        """
        center_x = width // 2

        # Card size
        card_height = int(min(height * 0.28, 260))
        card_width = int(card_height * 0.70)

        # Keep the opponent card below the header.
        opponent_y = max(75, int(height * 0.08))

        # Fixed gap between the two cards.
        # This gap is large enough to contain either "VS"
        # or the round-result banner without touching either card.
        card_gap = 54

        # Player card
        player_y = (
            opponent_y
            + card_height
            + card_gap
        )

        # Center point of the space between the cards.
        vs_y = (
            opponent_y
            + card_height
            + card_gap // 2
        )

        # Turn message below the player's card.
        turn_y = player_y + card_height + 20

        # Stat buttons below the turn message.
        button_start_y = turn_y + 30

        return {
            "center_x": center_x,
            "card_width": card_width,
            "card_height": card_height,
            "opponent_y": opponent_y,
            "player_y": player_y,
            "vs_y": vs_y,
            "turn_y": turn_y,
            "button_start_y": button_start_y,
        }

    def _update_ui_positions(self, width: int, height: int):
        center_x = width // 2

        # Menu layout
        self.name_input.rect.x = center_x - 125
        self.name_input.rect.y = int(height * 0.28)

        self.btn_create.rect.x = center_x - 125
        self.btn_create.rect.y = int(height * 0.36)

        self.room_input.rect.x = center_x - 125
        self.room_input.rect.y = int(height * 0.48)

        self.btn_join.rect.x = center_x - 125
        self.btn_join.rect.y = int(height * 0.56)

        # Stat button layout
        button_width = 110
        button_height = 32

        spacing_x = 12
        spacing_y = 8

        first_row_count = 4
        second_row_count = 3

        first_row_width = (
            first_row_count * button_width
            + (first_row_count - 1) * spacing_x
        )

        second_row_width = (
            second_row_count * button_width
            + (second_row_count - 1) * spacing_x
        )

        first_row_x = center_x - first_row_width // 2
        second_row_x = center_x - second_row_width // 2

        # The game buttons must follow the actual card layout.
        game_layout = self._get_game_layout(width, height)
        start_y = game_layout["button_start_y"]

        for index, (_, button) in enumerate(self.stat_buttons):
            button.rect.width = button_width
            button.rect.height = button_height

            if index < 4:
                button.rect.x = (
                    first_row_x
                    + index * (button_width + spacing_x)
                )
                button.rect.y = start_y
            else:
                second_index = index - 4

                button.rect.x = (
                    second_row_x
                    + second_index * (button_width + spacing_x)
                )
                button.rect.y = (
                    start_y
                    + button_height
                    + spacing_y
                )

    def handle_event(self, event: pygame.event.Event):
        width = self.screen.get_width()
        height = self.screen.get_height()

        self._update_ui_positions(width, height)

        if self.current_screen == "menu":
            self.name_input.handle_event(event)
            self.room_input.handle_event(event)

            if self.btn_create.is_clicked(event):
                name = self.name_input.text.strip()

                if not name:
                    self.menu_error = "Please enter your name."
                    return

                self.menu_error = ""

                try:
                    self.client.connect()
                    self.client.create_room(name)
                    self.current_screen = "waiting"
                except Exception as exc:
                    self.menu_error = f"Connection error: {exc}"

            elif self.btn_join.is_clicked(event):
                name = self.name_input.text.strip()
                room_code = self.room_input.text.strip().upper()

                if not name or not room_code:
                    self.menu_error = "Enter name and room code."
                    return

                self.menu_error = ""

                try:
                    self.client.connect()
                    self.client.join_room(room_code, name)
                    self.current_screen = "waiting"
                except Exception as exc:
                    self.menu_error = f"Connection error: {exc}"

        elif self.current_screen == "game":
            if not self.game_state:
                return

            is_my_turn = (
                self.game_state.get("current_turn")
                == self.client.player_id
            )

            if is_my_turn:
                for attr_key, button in self.stat_buttons:
                    if button.is_clicked(event):
                        self.client.select_attribute(attr_key)

    def update(self):
        messages = self.client.poll_messages()

        for message in messages:
            message_type = message.get("type")

            if message_type == "ROOM_CREATED":
                self.current_screen = "waiting"

            elif message_type == "ROOM_JOINED":
                self.current_screen = "waiting"

            elif message_type == "GAME_STARTED":
                self.game_state = message
                self.last_round_result = None
                self.current_screen = "game"

            elif message_type == "ROUND_RESULT":
                self.last_round_result = message
                self.game_state = message.get("state")
                self.result_timer = pygame.time.get_ticks() + 3000

            elif message_type == "GAME_OVER":
                self.game_over_data = message
                self.current_screen = "game_over"

            elif message_type == "ERROR":
                self.menu_error = message.get(
                    "message",
                    "Server error",
                )

                if self.current_screen == "waiting":
                    self.current_screen = "menu"

            elif message_type == "PLAYER_DISCONNECTED":
                self.menu_error = "Opponent disconnected."
                self.current_screen = "menu"

    def draw(self, surface: pygame.Surface, mouse_pos: tuple):
        width = surface.get_width()
        height = surface.get_height()

        self._update_ui_positions(width, height)

        surface.fill((15, 18, 26))

        if self.current_screen == "menu":
            self._draw_menu(
                surface,
                width,
                height,
                mouse_pos,
            )

        elif self.current_screen == "waiting":
            self._draw_waiting(
                surface,
                width,
                height,
                mouse_pos,
            )

        elif self.current_screen == "game":
            self._draw_game(
                surface,
                width,
                height,
                mouse_pos,
            )

        elif self.current_screen == "game_over":
            self._draw_game_over(
                surface,
                width,
                height,
                mouse_pos,
            )

    def _draw_menu(
        self,
        surface: pygame.Surface,
        width: int,
        height: int,
        mouse_pos: tuple,
    ):
        center_x = width // 2

        title = assets.font_title.render(
            "BEN 10 GALACTIC BATTLE",
            True,
            (212, 175, 55),
        )

        surface.blit(
            title,
            title.get_rect(
                center=(center_x, int(height * 0.16))
            ),
        )

        name_label = assets.font_stat.render(
            "Player Name:",
            True,
            (200, 200, 200),
        )

        surface.blit(
            name_label,
            (
                self.name_input.rect.x,
                self.name_input.rect.y - 25,
            ),
        )

        self.name_input.draw(surface)
        self.btn_create.draw(surface, mouse_pos)

        room_label = assets.font_stat.render(
            "Room Code (to join):",
            True,
            (200, 200, 200),
        )

        surface.blit(
            room_label,
            (
                self.room_input.rect.x,
                self.room_input.rect.y - 25,
            ),
        )

        self.room_input.draw(surface)
        self.btn_join.draw(surface, mouse_pos)

        if self.menu_error:
            error_surface = assets.font_stat.render(
                self.menu_error,
                True,
                (255, 80, 80),
            )

            surface.blit(
                error_surface,
                error_surface.get_rect(
                    center=(center_x, int(height * 0.72))
                ),
            )

    def _draw_waiting(
        self,
        surface: pygame.Surface,
        width: int,
        height: int,
        mouse_pos: tuple,
    ):
        center_x = width // 2

        title = assets.font_title.render(
            "ROOM CREATED",
            True,
            (212, 175, 55),
        )

        surface.blit(
            title,
            title.get_rect(
                center=(center_x, int(height * 0.28))
            ),
        )

        code_text = (
            f"ROOM CODE: "
            f"{self.client.room_code or '------'}"
        )

        code_surface = assets.font_title.render(
            code_text,
            True,
            (255, 255, 255),
        )

        surface.blit(
            code_surface,
            code_surface.get_rect(
                center=(center_x, int(height * 0.38))
            ),
        )

        share_text = assets.font_stat.render(
            "Share this code with your friend",
            True,
            (180, 180, 200),
        )

        surface.blit(
            share_text,
            share_text.get_rect(
                center=(center_x, int(height * 0.46))
            ),
        )

        wait_text = assets.font_stat.render(
            "Waiting for opponent...",
            True,
            (100, 220, 100),
        )

        surface.blit(
            wait_text,
            wait_text.get_rect(
                center=(center_x, int(height * 0.54))
            ),
        )

    def _draw_game(
        self,
        surface: pygame.Surface,
        width: int,
        height: int,
        mouse_pos: tuple,
    ):
        if not self.game_state:
            return

        layout = self._get_game_layout(width, height)

        center_x = layout["center_x"]
        card_width = layout["card_width"]
        card_height = layout["card_height"]
        opponent_y = layout["opponent_y"]
        player_y = layout["player_y"]
        vs_y = layout["vs_y"]
        turn_y = layout["turn_y"]

        room_code = self.game_state.get(
            "room_code",
            "",
        )

        round_number = self.game_state.get(
            "round_number",
            1,
        )

        pot_size = self.game_state.get(
            "pot_size",
            0,
        )

        # Header
        header = assets.font_stat.render(
            (
                f"ROOM: {room_code}   |   "
                f"ROUND: {round_number}   |   "
                f"POT: {pot_size} cards"
            ),
            True,
            (212, 175, 55),
        )

        surface.blit(
            header,
            (30, 20),
        )

        # Opponent information
        opponent_name = self.game_state.get(
            "opponent_name",
            "Opponent",
        )

        opponent_cards = self.game_state.get(
            "opponent_card_count",
            26,
        )

        opponent_label = assets.font_stat.render(
            (
                f"OPPONENT: {opponent_name} "
                f"({opponent_cards} cards)"
            ),
            True,
            (200, 100, 100),
        )

        surface.blit(
            opponent_label,
            (30, 48),
        )

        # Player information
        # Keep this at the bottom-left, away from the card/buttons.
        player_name = self.game_state.get(
            "player_name",
            "You",
        )

        player_cards = self.game_state.get(
            "own_card_count",
            26,
        )

        player_label = assets.font_stat.render(
            (
                f"YOU: {player_name} "
                f"({player_cards} cards)"
            ),
            True,
            (100, 200, 255),
        )

        player_label_y = height - player_label.get_height() - 24

        surface.blit(
            player_label,
            (30, player_label_y),
        )

        # Determine whether the temporary round-result view is active.
        showing_result = (
            self.last_round_result is not None
            and pygame.time.get_ticks() < self.result_timer
        )

        # Opponent card
        opponent_active = self.game_state.get(
            "opponent_active_card"
        )

        show_opponent_card = False

        if showing_result:
            show_opponent_card = True

            if self.client.player_id == 1:
                opponent_active = (
                    self.last_round_result.get("p2_card")
                )
            else:
                opponent_active = (
                    self.last_round_result.get("p1_card")
                )

        CardView.render(
            surface,
            center_x - card_width // 2,
            opponent_y,
            card_width,
            card_height,
            opponent_active,
            is_hidden=not show_opponent_card,
        )

        # Own card
        own_active = self.game_state.get(
            "own_active_card"
        )

        if showing_result:
            if self.client.player_id == 1:
                own_active = (
                    self.last_round_result.get("p1_card")
                )
            else:
                own_active = (
                    self.last_round_result.get("p2_card")
                )

        CardView.render(
            surface,
            center_x - card_width // 2,
            player_y,
            card_width,
            card_height,
            own_active,
            is_hidden=False,
        )

        # Middle area between the cards.
        #
        # Normal state:
        #               VS
        #
        # Round result:
        #        YOU WIN / YOU LOSE
        #
        # The result banner occupies this middle area instead
        # of being drawn over either card.
        if showing_result:
            result = self.last_round_result

            winner = result.get("winner")
            is_tie = result.get("is_tie")

            if is_tie:
                message = "TIE! CARDS MOVED TO POT"
                color = (255, 255, 100)

            elif winner == self.client.player_id:
                message = "YOU WIN THIS ROUND!"
                color = (100, 255, 100)

            else:
                message = "YOU LOSE THIS ROUND!"
                color = (255, 100, 100)

            banner_width = min(520, width - 80)
            banner_height = 42

            banner_rect = pygame.Rect(
                center_x - banner_width // 2,
                vs_y - banner_height // 2,
                banner_width,
                banner_height,
            )

            pygame.draw.rect(
                surface,
                (20, 20, 30),
                banner_rect,
                border_radius=10,
            )

            pygame.draw.rect(
                surface,
                color,
                banner_rect,
                2,
                border_radius=10,
            )

            result_surface = assets.font_stat.render(
                message,
                True,
                color,
            )

            surface.blit(
                result_surface,
                result_surface.get_rect(
                    center=banner_rect.center
                ),
            )

        else:
            vs_surface = assets.font_title.render(
                "VS",
                True,
                (212, 175, 55),
            )

            surface.blit(
                vs_surface,
                vs_surface.get_rect(
                    center=(center_x, vs_y)
                ),
            )

        # Turn indicator
        is_my_turn = (
            self.game_state.get("current_turn")
            == self.client.player_id
        )

        if is_my_turn:
            turn_text = "YOUR TURN — CHOOSE A STAT"
            turn_color = (100, 255, 100)
        else:
            turn_text = "OPPONENT'S TURN..."
            turn_color = (255, 180, 100)

        turn_surface = assets.font_name.render(
            turn_text,
            True,
            turn_color,
        )

        surface.blit(
            turn_surface,
            turn_surface.get_rect(
                center=(center_x, turn_y)
            ),
        )

        # Attribute buttons
        for attr_key, button in self.stat_buttons:
            button.enabled = (
                is_my_turn
                and not showing_result
            )

            button.draw(
                surface,
                mouse_pos,
            )

    def _draw_game_over(
        self,
        surface: pygame.Surface,
        width: int,
        height: int,
        mouse_pos: tuple,
    ):
        if not self.game_over_data:
            return

        winner_id = self.game_over_data.get(
            "winner"
        )

        is_winner = (
            winner_id == self.client.player_id
        )

        if is_winner:
            title_text = "VICTORY! YOU WON THE GAME!"
            color = (100, 255, 100)
        else:
            title_text = "DEFEAT! OPPONENT WON."
            color = (255, 100, 100)

        title_surface = assets.font_title.render(
            title_text,
            True,
            color,
        )

        surface.blit(
            title_surface,
            title_surface.get_rect(
                center=(
                    width // 2,
                    height // 2,
                )
            ),
        )