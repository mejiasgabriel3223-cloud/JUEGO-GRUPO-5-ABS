"""Global game rules, hand evaluation, and final score calculation."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from typing import Sequence

from .entities import CardEntity


@dataclass(frozen=True)
class HandResult:
    """Store the immutable result produced by one hand evaluation."""

    name: str
    score: int
    multiplier: float

    @property
    def total(self) -> int:
        """Return the final score obtained by multiplying score and multiplier."""
        return int(self.score * self.multiplier)


class GameRules:
    """Centralize global score/multiplier values and poker-hand evaluation.

    ``score`` and ``multiplier`` act as the shared base values described by the
    project design. Cards retain their own mutable modifiers, so Jokers can
    change individual cards before this class calculates the final result.
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
        """Create the rule object with global base score and multiplier."""
        self.score = int(score)
        self.multiplier = float(multiplier)

    def reset(self, score: int = 0, multiplier: float = 1.0) -> None:
        """Replace the global score and multiplier with new base values."""
        self.score = int(score)
        self.multiplier = float(multiplier)

    def evaluate(self, cards: Sequence[CardEntity]) -> HandResult:
        """Identify a hand and combine global values with per-card modifiers.

        The method expects between 1 and 5 played cards. The returned
        ``HandResult`` contains the hand type, calculated score, multiplier,
        and a ``total`` property representing the final product.
        """
        if not 1 <= len(cards) <= 5:
            raise ValueError("A played hand must contain between 1 and 5 cards")

        # Convert logical ranks into numeric values for frequency/straight tests.
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
        # Recursive summation keeps per-card score changes separate from global rules.
        card_score = self._sum_card_score_recursive(cards)
        # A default card multiplier is 1.0, so only the added portion is summed.
        card_multiplier = sum(card.multiplier - 1.0 for card in cards)

        final_score = self.score + base_score + card_score
        final_multiplier = self.multiplier + base_multiplier - 1.0 + card_multiplier
        return HandResult(name, final_score, final_multiplier)

    def best_five(self, cards: Sequence[CardEntity]) -> tuple[CardEntity, ...]:
        """Return the five-card combination with the highest calculated total."""
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
        """Recursively add every card score until the sequence is exhausted."""
        if index >= len(cards):
            return 0
        # Add the current card and recursively process the next position.
        return int(cards[index].score) + self._sum_card_score_recursive(cards, index + 1)

    @staticmethod
    def _rank_value(rank: str) -> int:
        """Convert a rank label into its numeric comparison value."""
        values = {str(value): value for value in range(2, 11)}
        values.update({"J": 11, "Q": 12, "K": 13, "A": 14})
        if rank not in values:
            raise ValueError(f"Unknown rank: {rank}")
        return values[rank]

    @staticmethod
    def _is_straight(unique_ranks: list[int]) -> bool:
        """Return whether five unique ranks form a standard or wheel straight."""
        if len(unique_ranks) != 5:
            return False
        # Treat A-2-3-4-5 as the low ace straight.
        if unique_ranks == [2, 3, 4, 5, 14]:
            return True
        return unique_ranks == list(range(unique_ranks[0], unique_ranks[0] + 5))
