"""Estado de una ronda/ante."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class RoundState:
    ante: int = 1
    round_number: int = 1
    target: int = 300
    max_rounds: int = 4

    @property
    def completed(self) -> bool:
        return self.round_number > self.max_rounds

    def advance(self) -> None:
        self.round_number += 1
        if self.round_number > self.max_rounds:
            return
        self.ante += 1
        self.target = int(self.target * 2.25)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ante": self.ante,
            "round": self.round_number,
            "target": self.target,
            "max_rounds": self.max_rounds,
        }
