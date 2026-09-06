"""Random card creation and visual metadata creation."""

from __future__ import annotations

import random
from pathlib import Path
from uuid import uuid4

import pygame

from .entities import CardEntity


class CardFactory:
    """Create random card entities and assign their visual Rect/asset metadata.

    The factory does not own the game deck. It only knows how to create a
    single card or a batch of cards. Because cards are created independently,
    repeated values are naturally possible.
    """

    RANKS = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A")
    SUITS = ("C", "D", "H", "S")
    SUIT_SYMBOLS = {"C": "♣", "D": "♦", "H": "♥", "S": "♠"}

    def __init__(self, asset_root: str | Path = ".", card_size: tuple[int, int] = (90, 130)) -> None:
        self.asset_root = Path(asset_root)
        self.card_size = card_size

    def create_random_card(self, x: int = 0, y: int = 0) -> CardEntity:
        rank = random.choice(self.RANKS)
        suit = random.choice(self.SUITS)
        return self.create_card(rank, suit, x, y)

    def create_card(self, rank: str, suit: str, x: int = 0, y: int = 0) -> CardEntity:
        if rank not in self.RANKS or suit not in self.SUITS:
            raise ValueError("Invalid card rank or suit")

        rect = pygame.Rect(x, y, *self.card_size)
        asset_path = self._resolve_asset(rank, suit)
        return CardEntity(
            rank=rank,
            suit=self.SUIT_SYMBOLS[suit],
            score=self._base_score(rank),
            multiplier=1.0,
            asset_path=str(asset_path),
            rect=rect,
            _entity_id=uuid4().hex,
        )

    def create_random_collection(self, amount: int) -> list[CardEntity]:
        if amount < 0:
            raise ValueError("amount cannot be negative")
        return [self.create_random_card() for _ in range(amount)]

    def _resolve_asset(self, rank: str, suit: str) -> Path:
        """Resolve a real card asset from the repository's existing assets.

        The current project stores card images under
        ``assets(beta)/cards/cards/dark`` and uses ``P`` for the spade suit.
        The factory accepts ``S`` at the domain level and maps it to ``P``
        only for the asset filename.
        """
        asset_suit = "P" if suit == "S" else suit
        candidates = (
            self.asset_root / "assets(beta)" / "cards" / "cards" / "dark" / f"{rank}-{asset_suit}.png",
            self.asset_root / "assets(beta)" / "cards" / "cards" / "light" / f"{rank}-{asset_suit}.png",
            self.asset_root / "assets(beta)" / "cards" / "cards" / "dark" / f"{rank}{asset_suit}.png",
        )
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]

    @staticmethod
    def _base_score(rank: str) -> int:
        values = {str(value): value for value in range(2, 11)}
        values.update({"J": 11, "Q": 12, "K": 13, "A": 14})
        return values[rank]
