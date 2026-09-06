"""Game-wide rules and hand scoring."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Sequence

from .entities import CardEntity


@dataclass(frozen=True)
class HandResult:
    """Immutable result of evaluating one played hand."""

    name: str
    score: int
    multiplier: float

    @property
    def total(self) -> int:
        return int(self.score * self.multiplier)


class GameRules:
    """Central source of global score and multiplier rules.

    ``score`` and ``multiplier`` are deliberately shared rule values. Changing
    them changes the base calculation for every future hand, while the cards
    retain their own mutable modifiers that Jokers can alter.
    """

    HAND_VALUES = {
        "High Card": (5, 1.0),
        "Pair": (10, 2.0),
        "Two Pair": (20, 2.0),
        "Three of a Kind": (30, 3.0),
        "Straight": (40, 4.0),
        "Flush": (45, 4.0),
        "Full House": (60, 6.0),
        "Four of a Kind": (80, 8.0),
        "Straight Flush": (100, 10.0),
    }

    def __init__(self, score: int = 0, multiplier: float = 1.0) -> None:
        self.score = int(score)
        self.multiplier = float(multiplier)

    def reset(self, score: int = 0, multiplier: float = 1.0) -> None:
        self.score = int(score)
        self.multiplier = float(multiplier)

    def evaluate(self, cards: Sequence[CardEntity]) -> HandResult:
        if not 1 <= len(cards) <= 5:
            raise ValueError("A played hand must contain between 1 and 5 cards")

        ranks = [self._rank_value(card.rank) for card in cards]
        suits = [card.suit for card in cards]
        counts = Counter(ranks)
        unique = sorted(set(ranks))
        flush = len(set(suits)) == 1 and len(cards) == 5
        straight = self._is_straight(unique) and len(cards) == 5

        if straight and flush:
            name = "Straight Flush"
        elif 4 in counts.values() and len(cards) == 5:
            name = "Four of a Kind"
        elif sorted(counts.values()) == [2, 3] and len(cards) == 5:
            name = "Full House"
        elif flush:
            name = "Flush"
        elif straight:
            name = "Straight"
        elif 3 in counts.values():
            name = "Three of a Kind"
        elif list(counts.values()).count(2) == 2:
            name = "Two Pair"
        elif 2 in counts.values():
            name = "Pair"
        else:
            name = "High Card"

        base_score, base_multiplier = self.HAND_VALUES[name]
        card_score = self._sum_card_score_recursive(cards)
        card_multiplier = sum(card.multiplier - 1.0 for card in cards)

        final_score = self.score + base_score + card_score
        final_multiplier = self.multiplier + base_multiplier - 1.0 + card_multiplier
        return HandResult(name, final_score, final_multiplier)

    def best_five(self, cards: Sequence[CardEntity]) -> tuple[CardEntity, ...]:
        if len(cards) <= 5:
            return tuple(cards)
        best = None
        best_total = -1
        for combination_ in combinations(cards, 5):
            result = self.evaluate(combination_)
            if result.total > best_total:
                best_total = result.total
                best = combination_
        return tuple(best or cards[:5])

    def _sum_card_score_recursive(self, cards: Sequence[CardEntity], index: int = 0) -> int:
        if index >= len(cards):
            return 0
        return int(cards[index].score) + self._sum_card_score_recursive(cards, index + 1)

    @staticmethod
    def _rank_value(rank: str) -> int:
        values = {str(value): value for value in range(2, 11)}
        values.update({"J": 11, "Q": 12, "K": 13, "A": 14})
        if rank not in values:
            raise ValueError(f"Unknown rank: {rank}")
        return values[rank]

    @staticmethod
    def _is_straight(unique_ranks: list[int]) -> bool:
        if len(unique_ranks) != 5:
            return False
        if unique_ranks == [2, 3, 4, 5, 14]:
            return True
        return unique_ranks == list(range(unique_ranks[0], unique_ranks[0] + 5))
