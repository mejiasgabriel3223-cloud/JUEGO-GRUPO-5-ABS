"""Abstracciones base para las entidades del juego."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


class Entity(ABC):
    """Entidad de dominio abstracta.

    Toda entidad expone un identificador estable y una representacion apta para
    ser consumida por una capa externa como Pygame.
    """

    @property
    @abstractmethod
    def entity_id(self) -> str:
        """Identificador unico de la entidad."""
        raise NotImplementedError

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serializa la entidad sin acoplarla a Pygame."""
        raise NotImplementedError


@dataclass(frozen=True)
class ScoreContext:
    """Contexto inmutable usado por los Jokers para modificar el puntaje."""

    chips: int
    multiplier: int

    @property
    def score(self) -> int:
        return max(0, self.chips) * max(1, self.multiplier)
