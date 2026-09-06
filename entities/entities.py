"""Core game entities and the dynamic entity collection.

This module intentionally contains domain objects only. It does not import
pygame, load files, or know how the interface is drawn. The collection is a
small generic container that allows duplicates and can grow or shrink at
runtime, which is important for deck modifications.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, Iterable, Iterator, List, Optional, Sequence, TypeVar

T = TypeVar("T")


class Entity(ABC):
    """Abstract base class for every persistent game entity."""

    @property
    @abstractmethod
    def entity_id(self) -> str:
        """Return a stable identifier for the entity."""
        raise NotImplementedError


@dataclass
class CardEntity(Entity):
    """A single playable card.

    A card is identified by its rank and suit, but duplicates are allowed:
    two instances may represent the same rank/suit while remaining distinct
    entities. ``score`` and ``multiplier`` are mutable per-card modifiers and
    can be changed by Joker effects.

    The visual layer is represented by ``asset_path`` and ``rect``. The
    entity does not load the image itself; the card factory creates the Rect
    and the existing Renderer remains responsible for presentation.
    """

    rank: str
    suit: str
    score: int = 0
    multiplier: float = 1.0
    selected: bool = False
    asset_path: str = ""
    rect: object = None
    _entity_id: str = field(default="", repr=False)

    @property
    def entity_id(self) -> str:
        return self._entity_id or f"{self.rank}-{self.suit}"

    @property
    def code(self) -> str:
        """Return a stable visual code such as ``AS`` or ``10H``."""
        return f"{self.rank}{self.suit}"

    def reset_modifiers(self) -> None:
        """Restore the per-card score and multiplier modifiers."""
        self.score = 0
        self.multiplier = 1.0

    def apply_bonus(self, score_delta: int = 0, multiplier_delta: float = 0.0) -> None:
        """Modify this card without replacing the entity instance."""
        self.score += int(score_delta)
        self.multiplier += float(multiplier_delta)

    def toggle_selected(self) -> bool:
        self.selected = not self.selected
        return self.selected

    def to_dict(self) -> dict:
        """Return renderer-friendly data without importing the renderer."""
        return {
            "id": self.entity_id,
            "rank": self.rank,
            "suit": self.suit,
            "selected": self.selected,
            "score": self.score,
            "multiplier": self.multiplier,
            "asset_path": self.asset_path,
        }


class EntityCollection(Generic[T], Sequence[T]):
    """Dynamic generic entity array that explicitly permits duplicates.

    ``EntityCollection[T]`` is the reusable collection/"array of entities"
    requested by the project design. It supports runtime insertion,
    deletion, replacement, clearing and shuffling. No uniqueness rule is
    imposed, so adding a second Ace of Spades is valid and intentional.

    The generic type parameter is the project's template/generic mechanism:
    the same container can hold cards or another future entity type.
    """

    def __init__(self, entities: Optional[Iterable[T]] = None) -> None:
        self._items: List[T] = list(entities or [])

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index: int) -> T:
        return self._items[index]

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

    def add(self, entity: T) -> None:
        """Increase the collection size by one; duplicates are allowed."""
        self._items.append(entity)

    def add_many(self, entities: Iterable[T]) -> None:
        for entity in entities:
            self.add(entity)

    def remove_at(self, index: int) -> T:
        """Remove and return one element, decreasing the collection size."""
        return self._items.pop(index)

    def remove(self, entity: T) -> None:
        self._items.remove(entity)

    def resize(self, target_size: int, factory=None) -> None:
        """Grow or shrink the collection; growth uses a supplied factory.

        The growth branch uses recursion so the collection can be expanded by
        repeatedly creating one entity until the desired size is reached.
        Shrinking is iterative because removal is not naturally recursive.
        """
        if target_size < 0:
            raise ValueError("target_size cannot be negative")
        if target_size < len(self):
            del self._items[target_size:]
            return
        if target_size == len(self):
            return
        if factory is None:
            raise ValueError("A factory is required when growing the collection")
        self._grow_recursive(target_size, factory)

    def _grow_recursive(self, target_size: int, factory) -> None:
        if len(self) >= target_size:
            return
        self.add(factory())
        self._grow_recursive(target_size, factory)

    def shuffle(self) -> None:
        import random
        random.shuffle(self._items)

    def clear(self) -> None:
        self._items.clear()

    def copy(self) -> List[T]:
        return list(self._items)
