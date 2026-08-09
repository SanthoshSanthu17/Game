import pygame
from typing import Optional, Dict, Any

from client.assets import assets


class Button:
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        bg_color=(40, 45, 70),
        text_color=(255, 255, 255),
    ):
        self.rect = pygame.Rect(
            x,
            y,
            width,
            height,
        )

        self.text = text
        self.bg_color = bg_color
        self.text_color = text_color
        self.enabled = True

    def draw(
        self,
        surface: pygame.Surface,
        mouse_pos: tuple,
    ):
        is_hovered = (
            self.rect.collidepoint(mouse_pos)
            and self.enabled
        )

        if is_hovered:
            color = (
                min(self.bg_color[0] + 30, 255),
                min(self.bg_color[1] + 30, 255),
                min(self.bg_color[2] + 30, 255),
            )
        else:
            color = self.bg_color

        if not self.enabled:
            color = (30, 32, 45)

        pygame.draw.rect(
            surface,
            color,
            self.rect,
            border_radius=6,
        )

        border_color = (
            (212, 175, 55)
            if is_hovered and self.enabled
            else (100, 110, 140)
        )

        pygame.draw.rect(
            surface,
            border_color,
            self.rect,
            2,
            border_radius=6,
        )

        text_color = (
            self.text_color
            if self.enabled
            else (100, 100, 100)
        )

        text_surface = assets.font_stat.render(
            self.text,
            True,
            text_color,
        )

        surface.blit(
            text_surface,
            text_surface.get_rect(
                center=self.rect.center
            ),
        )

    def is_clicked(
        self,
        event: pygame.event.Event,
    ) -> bool:
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.enabled
            and self.rect.collidepoint(event.pos)
        ):
            return True

        return False


class InputBox:
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str = "",
    ):
        self.rect = pygame.Rect(
            x,
            y,
            width,
            height,
        )

        self.text = text
        self.active = False

    def handle_event(
        self,
        event: pygame.event.Event,
    ):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(
                event.pos
            )

        elif (
            event.type == pygame.KEYDOWN
            and self.active
        ):
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]

            elif event.key == pygame.K_RETURN:
                pass

            elif len(self.text) < 20:
                if event.unicode.isprintable():
                    self.text += event.unicode

    def draw(
        self,
        surface: pygame.Surface,
    ):
        border_color = (
            (212, 175, 55)
            if self.active
            else (80, 90, 120)
        )

        pygame.draw.rect(
            surface,
            (25, 30, 45),
            self.rect,
            border_radius=6,
        )

        pygame.draw.rect(
            surface,
            border_color,
            self.rect,
            2,
            border_radius=6,
        )

        text_surface = assets.font_stat.render(
            self.text,
            True,
            (255, 255, 255),
        )

        text_y = (
            self.rect.y
            + (self.rect.height - text_surface.get_height())
            // 2
        )

        surface.blit(
            text_surface,
            (
                self.rect.x + 12,
                text_y,
            ),
        )


class CardView:
    @staticmethod
    def render(
        surface: pygame.Surface,
        x: int,
        y: int,
        width: int,
        height: int,
        card_data: Optional[Dict[str, Any]],
        is_hidden: bool = False,
    ):
        card_rect = pygame.Rect(
            x,
            y,
            width,
            height,
        )

        # Card background
        pygame.draw.rect(
            surface,
            (20, 24, 38),
            card_rect,
            border_radius=10,
        )

        # Gold card border
        pygame.draw.rect(
            surface,
            (212, 175, 55),
            card_rect,
            3,
            border_radius=10,
        )

        # Hidden opponent card
        if is_hidden or not card_data:
            back_rect = card_rect.inflate(
                -12,
                -12,
            )

            pygame.draw.rect(
                surface,
                (30, 36, 56),
                back_rect,
                border_radius=8,
            )

            pygame.draw.rect(
                surface,
                (212, 175, 55),
                back_rect,
                1,
                border_radius=8,
            )

            text_surface = assets.font_title.render(
                "BEN 10",
                True,
                (212, 175, 55),
            )

            surface.blit(
                text_surface,
                text_surface.get_rect(
                    center=card_rect.center
                ),
            )

            return

        name = card_data.get(
            "name",
            "Unknown",
        )

        rank = card_data.get(
            "rank",
            0,
        )

        # --------------------------------------------------
        # Responsive card measurements
        # --------------------------------------------------

        padding_x = max(
            8,
            int(width * 0.05),
        )

        header_h = max(
            26,
            int(height * 0.12),
        )

        inner_width = max(
            20,
            width - (padding_x * 2),
        )

        # --------------------------------------------------
        # Header
        # --------------------------------------------------

        name_surface = assets.font_name.render(
            name,
            True,
            (255, 255, 255),
        )

        maximum_name_width = max(
            20,
            width - padding_x * 2 - 55,
        )

        if name_surface.get_width() > maximum_name_width:
            name_surface = pygame.transform.smoothscale(
                name_surface,
                (
                    maximum_name_width,
                    name_surface.get_height(),
                ),
            )

        surface.blit(
            name_surface,
            (
                x + padding_x,
                y + 6,
            ),
        )

        # Rank badge
        rank_text = f"Rk{rank}"

        rank_surface = assets.font_stat.render(
            rank_text,
            True,
            (255, 255, 255),
        )

        badge_width = max(
            34,
            rank_surface.get_width() + 8,
        )

        badge_height = max(
            18,
            header_h - 10,
        )

        badge_rect = pygame.Rect(
            x + width - badge_width - padding_x,
            y + 6,
            badge_width,
            badge_height,
        )

        pygame.draw.rect(
            surface,
            (180, 40, 40),
            badge_rect,
            border_radius=4,
        )

        pygame.draw.rect(
            surface,
            (212, 175, 55),
            badge_rect,
            1,
            border_radius=4,
        )

        surface.blit(
            rank_surface,
            rank_surface.get_rect(
                center=badge_rect.center
            ),
        )

        # Header separator
        divider_y = y + header_h

        pygame.draw.line(
            surface,
            (212, 175, 55),
            (
                x + padding_x,
                divider_y,
            ),
            (
                x + width - padding_x,
                divider_y,
            ),
            1,
        )

        # --------------------------------------------------
        # Statistics
        # --------------------------------------------------

        stats = [
            (
                "Rank",
                card_data.get("rank", 0),
            ),
            (
                "Height",
                f"{card_data.get('height', 0)}ft",
            ),
            (
                "Weight",
                f"{card_data.get('weight', 0)} kg",
            ),
            (
                "Speed",
                f"{card_data.get('speed', 0)} km/h",
            ),
            (
                "Power",
                card_data.get("power", 0),
            ),
            (
                "Intelligence",
                card_data.get("intelligence", 0),
            ),
            (
                "Defense",
                card_data.get("defense", 0),
            ),
        ]

        number_of_stats = len(stats)

        # Space after header.
        content_height = max(
            20,
            height - header_h - 10,
        )

        # Reserve approximately 42% of content for statistics.
        # The row height is bounded so it remains readable.
        row_h = int(
            content_height
            * 0.42
            / number_of_stats
        )

        row_h = max(
            15,
            min(22, row_h),
        )

        stats_height = (
            number_of_stats * row_h
        )

        # Remaining space goes to artwork.
        art_h = (
            content_height
            - stats_height
            - 10
        )

        # Keep artwork positive without allowing
        # it to consume the statistics area.
        art_h = max(
            1,
            art_h,
        )

        art_rect = pygame.Rect(
            x + padding_x,
            divider_y + 5,
            inner_width,
            art_h,
        )

        # --------------------------------------------------
        # Artwork container
        # --------------------------------------------------

        pygame.draw.rect(
            surface,
            (15, 18, 28),
            art_rect,
            border_radius=6,
        )

        pygame.draw.rect(
            surface,
            (60, 70, 100),
            art_rect,
            1,
            border_radius=6,
        )

        image = assets.get_image(name)

        if image:
            image_width, image_height = (
                image.get_size()
            )

            if image_width > 0 and image_height > 0:
                container_width = max(
                    1,
                    art_rect.width - 4,
                )

                container_height = max(
                    1,
                    art_rect.height - 4,
                )

                image_ratio = (
                    image_width / image_height
                )

                container_ratio = (
                    container_width
                    / container_height
                )

                if image_ratio > container_ratio:
                    scaled_width = container_width
                    scaled_height = max(
                        1,
                        int(
                            scaled_width
                            / image_ratio
                        ),
                    )
                else:
                    scaled_height = container_height
                    scaled_width = max(
                        1,
                        int(
                            scaled_height
                            * image_ratio
                        ),
                    )

                scaled_image = (
                    pygame.transform.smoothscale(
                        image,
                        (
                            scaled_width,
                            scaled_height,
                        ),
                    )
                )

                image_rect = (
                    scaled_image.get_rect(
                        center=art_rect.center
                    )
                )

                surface.blit(
                    scaled_image,
                    image_rect,
                )

        else:
            placeholder = assets.font_stat.render(
                "CARD ART",
                True,
                (150, 165, 190),
            )

            surface.blit(
                placeholder,
                placeholder.get_rect(
                    center=art_rect.center
                ),
            )

        # --------------------------------------------------
        # Statistics rows
        # --------------------------------------------------

        stats_start_y = (
            art_rect.bottom + 4
        )

        for index, (label, value) in enumerate(stats):
            row_y = (
                stats_start_y
                + index * row_h
            )

            label_surface = assets.font_stat.render(
                f"{label}:",
                True,
                (190, 190, 205),
            )

            value_color = (
                (255, 100, 100)
                if label == "Rank"
                else (255, 255, 255)
            )

            value_surface = assets.font_stat.render(
                str(value),
                True,
                value_color,
            )

            label_y = (
                row_y
                + (
                    row_h
                    - label_surface.get_height()
                )
                // 2
            )

            value_y = (
                row_y
                + (
                    row_h
                    - value_surface.get_height()
                )
                // 2
            )

            surface.blit(
                label_surface,
                (
                    x + padding_x + 2,
                    label_y,
                ),
            )

            surface.blit(
                value_surface,
                (
                    x
                    + width
                    - padding_x
                    - value_surface.get_width()
                    - 2,
                    value_y,
                ),
            )

            if index < number_of_stats - 1:
                divider = (
                    row_y + row_h
                )

                pygame.draw.line(
                    surface,
                    (35, 42, 65),
                    (
                        x + padding_x,
                        divider,
                    ),
                    (
                        x + width - padding_x,
                        divider,
                    ),
                    1,
                )