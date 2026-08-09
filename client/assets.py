import os
import pygame
from typing import Dict, Optional
from shared.data_loader import load_cards_from_json
from shared.models import Card

class AssetManager:
    """Manages loading card images and fonts with graceful fallbacks."""
    def __init__(self):
        pygame.font.init()
        self.images: Dict[str, pygame.Surface] = {}
        self.cards_data: Dict[str, Card] = {}
        self._load_cards()
        self._init_fonts()

    def _load_cards(self):
        try:
            cards = load_cards_from_json("data/cards.json")
            for card in cards:
                self.cards_data[card.name] = card
                self._load_image_for_card(card)
        except Exception:
            pass

    def _load_image_for_card(self, card: Card):
        path = os.path.join("assets", "images", card.image)
        if os.path.isfile(path):
            try:
                img = pygame.image.load(path)
                self.images[card.name] = img
            except Exception:
                self.images[card.name] = None
        else:
            self.images[card.name] = None

    def _init_fonts(self):
        try:
            self.font_title = pygame.font.SysFont("Arial", 24, bold=True)
            self.font_name = pygame.font.SysFont("Arial", 20, bold=True)
            self.font_stat = pygame.font.SysFont("Arial", 16)
            self.font_badge = pygame.font.SysFont("Arial", 14, bold=True)
            self.font_button = pygame.font.SysFont("Arial", 18, bold=True)
        except Exception:
            self.font_title = pygame.font.Font(None, 24)
            self.font_name = pygame.font.Font(None, 20)
            self.font_stat = pygame.font.Font(None, 16)
            self.font_badge = pygame.font.Font(None, 14)
            self.font_button = pygame.font.Font(None, 18)

    def get_image(self, card_name: str) -> Optional[pygame.Surface]:
        return self.images.get(card_name)

    def get_card(self, card_name: str) -> Optional[Card]:
        return self.cards_data.get(card_name)

assets = AssetManager()