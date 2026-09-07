"""Probability-driven Joker entities and their polymorphic effects."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import random
from typing import Iterable

from .entities import CardEntity, EntityCollection


class Joker(ABC):
    """Define the common interface for every Joker effect.

    Every Joker has a probability between 0 and 1. The public ``activate``
    method handles probability checking, while subclasses implement ``apply``
    with their own effect. This allows the game to treat different Joker
    classes through one common interface and demonstrates polymorphism.
    """

    def __init__(self, name: str, probability: float = 1.0) -> None:
        """Create a Joker with a display name and activation probability."""
        if not 0.0 <= probability <= 1.0:
            raise ValueError("probability must be between 0 and 1")
        self.name = name
        self.probability = probability
        self.active = True

    @abstractmethod
    def apply(self, cards: Iterable[CardEntity]) -> bool:
        """Apply the concrete Joker effect and report whether it was applied."""
        raise NotImplementedError

    def activate(self, cards: Iterable[CardEntity]) -> bool:
        """Roll the probability and apply the Joker only when it activates."""
        if not self.active:
            return False
        # A probability of 1.0 always activates because random.random() is below 1.
        if random.random() <= self.probability:
            return self.apply(cards)
        return False

    def to_dict(self) -> dict:
        """Expose the Joker state in renderer-friendly plain data."""
        return {"name": self.name, "probability": self.probability, "active": self.active}


@dataclass
class FlatChipsJoker(Joker):
    """Add a fixed score amount to every card in the supplied collection."""

    amount: int = 20
    probability: float = 1.0

    def __post_init__(self) -> None:
        """Initialize the abstract Joker portion after dataclass fields are built."""
        super().__init__("Chipster", self.probability)

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        """Increase each card's score by ``amount`` and report success."""
        for card in cards:
            # The change is stored on the card so later rule calculations can see it.
            card.apply_bonus(score_delta=self.amount)
        return True


@dataclass
class MultiplierJoker(Joker):
    """Increase the multiplier attribute of every supplied card."""

    amount: float = 1.0
    probability: float = 1.0

    def __post_init__(self) -> None:
        """Initialize the abstract Joker portion after dataclass fields are built."""
        super().__init__("Multiplier", self.probability)

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        """Increase each card's multiplier by ``amount`` and report success."""
        for card in cards:
            # Multiplier changes are additive so multiple Jokers can stack.
            card.apply_bonus(multiplier_delta=self.amount)
        return True


class RandomJokerPool:
    """Group multiple Jokers and activate each one independently."""

    def __init__(self, jokers: Iterable[Joker] | None = None) -> None:
        """Create a pool from an optional iterable of Joker objects."""
        self.jokers = list(jokers or [])

    def add(self, joker: Joker) -> None:
        """Add one Joker to the pool."""
        self.jokers.append(joker)

    def activate_all(self, cards: EntityCollection[CardEntity]) -> list[str]:
        """Attempt to activate every Joker and return the names that triggered."""
        activated = []
        for joker in self.jokers:
            if joker.activate(cards):
                activated.append(joker.name)
        return activated

    def to_dict(self) -> list[dict]:
        """Return all Joker states as serializable dictionaries."""
        return [joker.to_dict() for joker in self.jokers]
