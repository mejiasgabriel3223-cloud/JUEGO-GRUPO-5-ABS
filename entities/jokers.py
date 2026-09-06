"""Joker entities with probability-driven polymorphic effects."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import random
from typing import Iterable

from .entities import CardEntity, EntityCollection


class Joker(ABC):
    """Abstract strategy for modifying a set of cards.

    Every Joker has an activation probability. The caller does not need to
    know the concrete Joker type; it only asks ``activate``. Subclasses then
    apply different effects, demonstrating runtime polymorphism.
    """

    def __init__(self, name: str, probability: float = 1.0) -> None:
        if not 0.0 <= probability <= 1.0:
            raise ValueError("probability must be between 0 and 1")
        self.name = name
        self.probability = probability
        self.active = True

    @abstractmethod
    def apply(self, cards: Iterable[CardEntity]) -> bool:
        """Apply the concrete Joker effect and return whether it activated."""
        raise NotImplementedError

    def activate(self, cards: Iterable[CardEntity]) -> bool:
        if not self.active:
            return False
        if random.random() <= self.probability:
            return self.apply(cards)
        return False

    def to_dict(self) -> dict:
        return {"name": self.name, "probability": self.probability, "active": self.active}


@dataclass
class FlatChipsJoker(Joker):
    amount: int = 20
    probability: float = 1.0

    def __post_init__(self) -> None:
        Joker.__init__(self, "Chipster", self.probability)

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        for card in cards:
            card.apply_bonus(score_delta=self.amount)
        return True


@dataclass
class MultiplierJoker(Joker):
    amount: float = 1.0
    probability: float = 1.0

    def __post_init__(self) -> None:
        Joker.__init__(self, "Multiplier", self.probability)

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        for card in cards:
            card.apply_bonus(multiplier_delta=self.amount)
        return True


class RandomJokerPool:
    """Small collection of Jokers that can be sampled independently."""

    def __init__(self, jokers: Iterable[Joker] | None = None) -> None:
        self.jokers = list(jokers or [])

    def add(self, joker: Joker) -> None:
        self.jokers.append(joker)

    def activate_all(self, cards: EntityCollection[CardEntity]) -> list[str]:
        activated = []
        for joker in self.jokers:
            if joker.activate(cards):
                activated.append(joker.name)
        return activated

    def to_dict(self) -> list[dict]:
        return [joker.to_dict() for joker in self.jokers]
