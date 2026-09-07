"""Public API for the entity layer used by the rest of the game."""

# Import the core entities that other modules can use directly.
from .entities import CardEntity, EntityCollection

# Import the factory that creates cards and assigns visual metadata.
from .card_factory import CardFactory

# Import the abstract Joker and the concrete polymorphic implementations.
from .jokers import Joker, FlatChipsJoker, MultiplierJoker, RandomJokerPool

# Import the global rules and immutable hand-result value object.
from .rules import GameRules, HandResult

__all__ = [
    "CardEntity",
    "EntityCollection",
    "CardFactory",
    "Joker",
    "FlatChipsJoker",
    "MultiplierJoker",
    "RandomJokerPool",
    "GameRules",
    "HandResult",
]
