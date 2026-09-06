"""Jokers: ejemplo directo de herencia y polimorfismo."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

from .base import Entity, ScoreContext


class Joker(Entity, ABC):
    """Clase abstracta para efectos que modifican la puntuacion."""

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description
        self.active = True

    @abstractmethod
    def apply(self, context: ScoreContext) -> ScoreContext:
        """Aplica el efecto del Joker."""
        raise NotImplementedError

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "description": self.description, "active": self.active}


@dataclass
class FlatChipsJoker(Joker):
    amount: int = 30

    def __init__(self, amount: int = 30) -> None:
        Joker.__init__(self, "Chipster", f"+{amount} fichas")
        self.amount = amount

    @property
    def entity_id(self) -> str:
        return "joker-chipster"

    def apply(self, context: ScoreContext) -> ScoreContext:
        if not self.active:
            return context
        return ScoreContext(context.chips + self.amount, context.multiplier)


@dataclass
class MultiplierJoker(Joker):
    amount: int = 2

    def __init__(self, amount: int = 2) -> None:
        Joker.__init__(self, "Multiplica", f"+{amount} Mult")
        self.amount = amount

    @property
    def entity_id(self) -> str:
        return "joker-multiplier"

    def apply(self, context: ScoreContext) -> ScoreContext:
        if not self.active:
            return context
        return ScoreContext(context.chips, context.multiplier + self.amount)
