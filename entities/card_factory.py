"""Create random card entities and connect them to existing visual assets."""

from __future__ import annotations

import random
from pathlib import Path
from uuid import uuid4

import pygame

from .entities import CardEntity, RANK_VALUES


class CardFactory:
    """Build card entities without owning or managing the deck itself.

    The factory has one responsibility: translate logical card data into a
    ``CardEntity`` that already contains its visual metadata. It can create
    single cards or batches, and because every creation is independent,
    duplicate rank/suit combinations are naturally allowed.
    """

    RANKS = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A")
    SUITS = ("C", "D", "H", "S")
    SUIT_SYMBOLS = {"C": "♣", "D": "♦", "H": "♥", "S": "♠"}

    def __init__(self, asset_root: str | Path = ".", card_size: tuple[int, int] = (90, 130)) -> None:
        """Configure the asset root and the default size of generated Rects."""
        self.asset_root = Path(asset_root)
        self.card_size = card_size

    def create_random_card(self, x: int = 0, y: int = 0) -> CardEntity:
        """Create one card by randomly choosing a rank and a suit."""
        # Each choice is independent, so repeated cards are possible.
        rank = random.choice(self.RANKS)
        suit = random.choice(self.SUITS)
        return self.create_card(rank, suit, x, y)

    def create_card(self, rank: str, suit: str, x: int = 0, y: int = 0) -> CardEntity:
        """Create one validated card with its Rect and asset path configured."""
        if rank not in self.RANKS or suit not in self.SUITS:
            raise ValueError("Invalid card rank or suit")

        # The factory owns Rect creation, while the Renderer remains responsible for drawing.
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
        """Create ``amount`` independent random cards in a standard Python list."""
        if amount < 0:
            raise ValueError("amount cannot be negative")
        return [self.create_random_card() for _ in range(amount)]

    def _resolve_asset(self, rank: str, suit: str) -> Path:
        """Resolve a card image path using the repository's existing asset naming.

        The current project stores dark card images in
        ``assets(beta)/cards/cards/dark``. The logical suit ``S`` represents
        spades, but the current asset filename uses ``P``; that translation is
        performed only here so the domain representation stays stable.
        """
        # Convert the logical spade code into the filename code used by the assets.
        asset_suit = "P" if suit == "S" else suit
        candidates = (
            self.asset_root / "assets(beta)" / "cards" / "cards" / "dark" / f"{rank}-{asset_suit}.png",
            self.asset_root / "assets(beta)" / "cards" / "cards" / "light" / f"{rank}-{asset_suit}.png",
            self.asset_root / "assets(beta)" / "cards" / "cards" / "dark" / f"{rank}{asset_suit}.png",
        )
        for candidate in candidates:
            if candidate.exists():
                return candidate
        # Return the preferred location even when the asset has not been found yet.
        return candidates[0]

    @staticmethod
    def _base_score(rank: str) -> int:
        """Return the default numeric score assigned from the card rank."""
        return RANK_VALUES[rank]
