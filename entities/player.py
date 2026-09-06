"""Entidad Player: agrega baraja, mano, jokers y recursos del jugador."""
from __future__ import annotations

from typing import Any, Dict, List

from .base import Entity
from .card import PlayingCard
from .deck import Deck
from .hand import Hand
from .joker import Joker


class Player(Entity):
    def __init__(self, name: str = "Jugador") -> None:
        self.name = name.strip()[:16] or "Jugador"
        self.money = 4
        self.round_score = 0
        self.last_chips = 0
        self.last_multiplier = 1
        self.hands_left = 4
        self.discards_left = 3
        self.deck: Deck[PlayingCard] = Deck()
        self.hand = Hand()
        self.jokers: List[Joker] = []

    @property
    def entity_id(self) -> str:
        return f"player:{self.name.lower()}"

    def reset_round_resources(self) -> None:
        self.round_score = 0
        self.last_chips = 0
        self.last_multiplier = 1
        self.hands_left = 4
        self.discards_left = 3
        self.hand = Hand()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "money": self.money,
            "round_score": self.round_score,
            "last_chips": self.last_chips,
            "last_multiplier": self.last_multiplier,
            "hands_left": self.hands_left,
            "discards_left": self.discards_left,
            "hand": [card.to_dict() for card in self.hand.cards],
            "jokers": [joker.to_dict() for joker in self.jokers],
        }
