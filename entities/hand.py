"""Entidad Mano: administra las cartas que el jugador tiene disponibles."""
from __future__ import annotations

from typing import Iterable, List

from .card import PlayingCard


class Hand:
    MAX_SIZE = 8
    MAX_PLAY = 5

    def __init__(self, cards: Iterable[PlayingCard] | None = None) -> None:
        self._cards: List[PlayingCard] = list(cards or [])
        self._validate_size()

    def __len__(self) -> int:
        return len(self._cards)

    @property
    def cards(self) -> tuple[PlayingCard, ...]:
        return tuple(self._cards)

    @property
    def selected_cards(self) -> tuple[PlayingCard, ...]:
        return tuple(card for card in self._cards if card.selected)

    def add(self, card: PlayingCard) -> bool:
        if len(self._cards) >= self.MAX_SIZE:
            return False
        self._cards.append(card)
        return True

    def add_many(self, cards: Iterable[PlayingCard]) -> int:
        added = 0
        for card in cards:
            if self.add(card):
                added += 1
        return added

    def toggle(self, index: int) -> bool:
        if not 0 <= index < len(self._cards):
            return False
        card = self._cards[index]
        if not card.selected and len(self.selected_cards) >= self.MAX_PLAY:
            return False
        card.toggle_selected()
        return True

    def remove_selected(self) -> List[PlayingCard]:
        selected = list(self.selected_cards)
        selected_ids = {card.entity_id for card in selected}
        self._cards = [card for card in self._cards if card.entity_id not in selected_ids]
        for card in selected:
            card.selected = False
        return selected

    def clear_selection(self) -> None:
        for card in self._cards:
            card.selected = False

    def _validate_size(self) -> None:
        if len(self._cards) > self.MAX_SIZE:
            raise ValueError(f"Una mano no puede tener mas de {self.MAX_SIZE} cartas")
