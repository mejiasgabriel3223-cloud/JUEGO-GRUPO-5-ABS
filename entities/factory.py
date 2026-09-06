"""Fabrica para crear la baraja inicial sin acoplar al Game a los detalles."""
from __future__ import annotations

from .card import PlayingCard, Rank, Suit
from .deck import Deck


class StandardDeckFactory:
    @staticmethod
    def create() -> Deck[PlayingCard]:
        cards = [PlayingCard(rank, suit) for suit in Suit for rank in Rank]
        deck = Deck(cards)
        deck.shuffle()
        return deck
