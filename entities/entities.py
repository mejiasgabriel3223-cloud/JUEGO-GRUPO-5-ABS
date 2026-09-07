"""Core domain entities and the dynamic collection used by the game."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, Iterable, Iterator, List, Optional, Sequence, TypeVar
from uuid import uuid4

T = TypeVar("T")

# Single source of truth for numeric rank values shared by the factory and rules.
RANK_VALUES = {str(value): value for value in range(2, 11)}
RANK_VALUES.update({"J": 11, "Q": 12, "K": 13, "A": 14})


class Entity(ABC):
    """Define the common abstraction shared by persistent game entities."""

    @property
    @abstractmethod
    def entity_id(self) -> str:
        """Return the identifier that distinguishes this entity instance."""
        raise NotImplementedError


@dataclass
class CardEntity(Entity):
    """Represent one playable card and all mutable values attached to it.

    Composition:
        - ``rank`` and ``suit`` identify the logical card.
        - ``score`` and ``multiplier`` store modifiers that Jokers can change.
        - ``asset_path`` stores the image location without loading the image.
        - ``rect`` stores the visual position/size assigned by the factory.

    Two cards may have the same rank and suit. They are still separate
    instances because ``_entity_id`` identifies the individual entity.
    """

    rank: str
    suit: str
    score: int = 0
    multiplier: float = 1.0
    selected: bool = False
    asset_path: str = ""
    rect: object = None
    _entity_id: str = field(default_factory=lambda: uuid4().hex, repr=False)

    @property
    def entity_id(self) -> str:
        """Return the unique identifier assigned to this card instance."""
        # The identifier is generated automatically for every card instance.
        return self._entity_id

    @property
    def code(self) -> str:
        """Return the compact card code used by other game components."""
        return f"{self.rank}{self.suit}"

    def reset_modifiers(self) -> None:
        """Reset card-specific score and multiplier changes to their defaults."""
        self.score = 0
        self.multiplier = 1.0

    def apply_bonus(self, score_delta: int = 0, multiplier_delta: float = 0.0) -> None:
        """Add score and multiplier changes without replacing the card object."""
        # Convert incoming values so every card keeps consistent numeric types.
        self.score += int(score_delta)
        self.multiplier += float(multiplier_delta)

    def toggle_selected(self) -> bool:
        """Toggle the selection flag and return its new state."""
        self.selected = not self.selected
        return self.selected

    def to_dict(self) -> dict:
        """Return renderer-friendly data while keeping rendering outside this module."""
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
    """Provide a dynamic generic array that intentionally accepts duplicates.

    The collection represents the project's main entity container. Its size
    can grow or shrink at runtime, which supports mechanics such as adding a
    duplicate card or reducing the available card pool after a pack effect.

    ``T`` is the generic type parameter. It makes the same structure reusable
    for cards or future entity types without duplicating the collection code.
    """

    def __init__(self, entities: Optional[Iterable[T]] = None) -> None:
        """Create the collection from an optional iterable of initial entities."""
        # Copy the input into a private list to protect internal state.
        self._items: List[T] = list(entities or [])

    def __len__(self) -> int:
        """Return the current number of entities stored in the collection."""
        return len(self._items)

    def __getitem__(self, index: int) -> T:
        """Return the entity located at ``index``."""
        return self._items[index]

    def __iter__(self) -> Iterator[T]:
        """Return an iterator so the collection can be used in ``for`` loops."""
        return iter(self._items)

    def add(self, entity: T) -> None:
        """Append one entity and increase the collection size by one."""
        self._items.append(entity)

    def add_many(self, entities: Iterable[T]) -> None:
        """Append every entity received from an iterable."""
        for entity in entities:
            self.add(entity)

    def remove_at(self, index: int) -> T:
        """Remove and return the entity at ``index``."""
        return self._items.pop(index)

    def remove(self, entity: T) -> None:
        """Remove the first matching entity from the collection."""
        self._items.remove(entity)

    def resize(self, target_size: int, factory=None) -> None:
        """Change collection length to ``target_size``.

        When growth is requested, ``factory`` must be a callable that creates
        one new entity. The growth branch uses recursion to demonstrate the
        required recursion pillar without coupling the collection to cards.
        """
        if target_size < 0:
            raise ValueError("target_size cannot be negative")
        if target_size < len(self):
            # Truncate the private list to shrink the collection.
            del self._items[target_size:]
            return
        if target_size == len(self):
            return
        if factory is None:
            raise ValueError("A factory is required when growing the collection")
        self._grow_recursive(target_size, factory)

    def _grow_recursive(self, target_size: int, factory) -> None:
        """Recursively create one entity until ``target_size`` is reached."""
        if len(self) >= target_size:
            return
        self.add(factory())
        # Continue until the requested dynamic size is reached.
        self._grow_recursive(target_size, factory)

    def shuffle(self) -> None:
        """Randomly reorder the entities in place."""
        import random

        random.shuffle(self._items)

    def clear(self) -> None:
        """Remove all entities while keeping the collection object usable."""
        self._items.clear()

    def copy(self) -> List[T]:
        """Return a shallow copy of the stored entities."""
        return list(self._items)
