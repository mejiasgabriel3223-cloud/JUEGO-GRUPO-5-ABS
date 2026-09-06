"""Entidades relacionadas con cartas de la baraja."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict
from uuid import uuid4

from .base import Entity


class Suit(str, Enum):
    CLUBS = "C"
    DIAMONDS = "D"
    HEARTS = "H"
    SPADES = "S"

    @property
    def symbol(self) -> str:
        return {
            Suit.CLUBS: "♣",
            Suit.DIAMONDS: "♦",
            Suit.HEARTS: "♥",
            Suit.SPADES: "♠",
        }[self]


class Rank(int, Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    @property
    def label(self) -> str:
        return {
            11: "J",
            12: "Q",
            13: "K",
            14: "A",
        }.get(self.value, str(self.value))


@dataclass
class PlayingCard(Entity):
    """Carta de poker.

    La carta conoce sus datos de dominio, pero no sabe nada de pygame.
    """

    rank: Rank
    suit: Suit
    bonus_chips: int = 0
    bonus_multiplier: int = 0
    selected: bool = False
    _id: str = field(default_factory=lambda: uuid4().hex, repr=False)

    @property
    def entity_id(self) -> str:
        return self._id

    @property
    def label(self) -> str:
        return f"{self.rank.label}{self.suit.symbol}"

    @property
    def base_chips(self) -> int:
        # Valor de fichas de una carta individual.
        return int(self.rank.value)

    @property
    def total_chips(self) -> int:
        return self.base_chips + self.bonus_chips

    def toggle_selected(self) -> bool:
        self.selected = not self.selected
        return self.selected

    def to_dict(self) -> Dict[str, Any]:
        # Se mantienen las claves rank/suit compatibles con Renderer.py.
        return {
            "id": self.entity_id,
            "rank": self.rank.label,
            "suit": self.suit.symbol,
            "selected": self.selected,
            "bonus_chips": self.bonus_chips,
            "bonus_multiplier": self.bonus_multiplier,
        }
