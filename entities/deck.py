"""Baraja generica y operaciones de robo."""
from __future__ import annotations

import random
from typing import Generic, Iterable, List, Optional, TypeVar

T = TypeVar("T")


class Deck(Generic[T]):
    """Contenedor generico de cartas.

    Generic[T] funciona como plantilla: la misma clase puede gestionar
    PlayingCard u otro tipo de entidad sin duplicar la logica.
    """

    def __init__(self, cards: Optional[Iterable[T]] = None) -> None:
        self._cards: List[T] = list(cards or [])

    def __len__(self) -> int:
        return len(self._cards)

    def is_empty(self) -> bool:
        return not self._cards

    def shuffle(self) -> None:
        random.shuffle(self._cards)

    def draw(self) -> T:
        if self.is_empty():
            raise IndexError("No quedan cartas en la baraja")
        return self._cards.pop()

    def draw_many(self, amount: int) -> List[T]:
        """Roba N cartas usando recursividad como parte del dominio.

        La recursividad aqui es deliberada y acotada por `amount`; la UI no
        depende de ella.
        """
        if amount <= 0 or self.is_empty():
            return []
        return [self.draw(), *self.draw_many(amount - 1)]

    def add(self, card: T) -> None:
        self._cards.append(card)

    def clear(self) -> None:
        self._cards.clear()

    def copy_cards(self) -> List[T]:
        return list(self._cards)
