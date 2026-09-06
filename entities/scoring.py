"""Reglas de poker y calculo de puntaje."""
from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Iterable, Sequence

from .base import ScoreContext
from .card import PlayingCard, Rank
from .joker import Joker


HAND_BASE = {
    "Carta alta": (5, 1),
    "Pareja": (10, 2),
    "Doble pareja": (20, 2),
    "Trio": (30, 3),
    "Escalera": (40, 4),
    "Color": (45, 4),
    "Full": (60, 6),
    "Poker": (80, 8),
    "Escalera de color": (100, 10),
}


class HandEvaluator:
    """Evalua cinco cartas y produce un ScoreContext base."""

    @staticmethod
    def evaluate(cards: Sequence[PlayingCard]) -> tuple[str, ScoreContext]:
        if not 1 <= len(cards) <= 5:
            raise ValueError("Debes evaluar entre 1 y 5 cartas")

        ranks = [card.rank.value for card in cards]
        counts = Counter(ranks)
        unique = sorted(set(ranks))
        flush = len({card.suit for card in cards}) == 1
        straight = HandEvaluator._is_straight(unique, len(cards))

        if len(cards) == 5 and straight and flush:
            name = "Escalera de color"
        elif len(cards) == 5 and 4 in counts.values():
            name = "Poker"
        elif len(cards) == 5 and sorted(counts.values()) == [2, 3]:
            name = "Full"
        elif len(cards) == 5 and flush:
            name = "Color"
        elif len(cards) == 5 and straight:
            name = "Escalera"
        elif 3 in counts.values():
            name = "Trio"
        elif list(counts.values()).count(2) == 2:
            name = "Doble pareja"
        elif 2 in counts.values():
            name = "Pareja"
        else:
            name = "Carta alta"

        base_chips, multiplier = HAND_BASE[name]
        card_chips = HandEvaluator._sum_chips_recursive(cards)
        bonus_multiplier = sum(card.bonus_multiplier for card in cards)
        return name, ScoreContext(base_chips + card_chips, multiplier + bonus_multiplier)

    @staticmethod
    def apply_jokers(context: ScoreContext, jokers: Iterable[Joker]) -> ScoreContext:
        current = context
        for joker in jokers:
            # Polimorfismo: cada subclase implementa apply de manera distinta.
            current = joker.apply(current)
        return current

    @staticmethod
    def _sum_chips_recursive(cards: Sequence[PlayingCard], index: int = 0) -> int:
        """Suma recursivamente las fichas de las cartas."""
        if index >= len(cards):
            return 0
        return cards[index].total_chips + HandEvaluator._sum_chips_recursive(cards, index + 1)

    @staticmethod
    def _is_straight(unique_ranks: list[int], amount: int) -> bool:
        if amount < 5 or len(unique_ranks) != 5:
            return False
        if unique_ranks == [2, 3, 4, 5, 14]:
            return True
        return unique_ranks == list(range(unique_ranks[0], unique_ranks[0] + 5))

    @staticmethod
    def best_five(cards: Sequence[PlayingCard]) -> tuple[PlayingCard, ...]:
        """Busca la mejor combinacion de cinco cuando la mano tiene mas cartas."""
        if len(cards) <= 5:
            return tuple(cards)

        candidates = combinations(cards, 5)
        best = None
        best_score = -1
        for candidate in candidates:
            _, context = HandEvaluator.evaluate(candidate)
            if context.score > best_score:
                best = candidate
                best_score = context.score
        assert best is not None
        return tuple(best)
