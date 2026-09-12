"""
Módulo: systems/ante_system.py
Descripción: Gestor de Antes, Ciegas, Skips y Economía integrado con Bosses sin repetición.
"""

import random
from systems.bosses import get_random_boss_instance, BossBlind, BASE_ANTE_TARGETS

SKIP_TAGS_POOL = [
    {"name": "Etiqueta Económica", "effect": "add_money", "value": 15, "desc": "+$15 de oro directo"},
    {"name": "Etiqueta Cuponera", "effect": "free_shop", "value": 0, "desc": "Próxima tienda gratis"},
    {"name": "Etiqueta Mega-Sobre", "effect": "free_pack", "value": 0, "desc": "Sobre de cartas gratis en tienda"},
    {"name": "Etiqueta Dote", "effect": "money_per_hand", "value": 3, "desc": "+$3 por cada mano restante"},
]


class AnteManager:
    def __init__(self, max_antes: int = 8):
        self.max_antes = max_antes
        self.current_ante = 1
        self.current_blind_type = "small"  # 'small', 'big', 'boss'
        
        # Registro de jefes jugados en esta partida para evitar repeticiones
        self.seen_boss_ids = set()
        
        self.target_score = 0
        self.base_reward = 0
        self.active_boss: BossBlind | None = None
        
        self.pending_tags = []
        self.small_skip_tag = None
        self.big_skip_tag = None

        self._setup_ante()

    def _setup_ante(self):
        """Genera un Boss único y tags de skip para el Ante actual."""
        self.active_boss = get_random_boss_instance(self.seen_boss_ids)
        self.small_skip_tag = random.choice(SKIP_TAGS_POOL)
        self.big_skip_tag = random.choice(SKIP_TAGS_POOL)
        self._update_blind_parameters()

    def _update_blind_parameters(self):
        """Calcula el objetivo y recompensa según el tipo de ciega."""
        base_target = BASE_ANTE_TARGETS.get(self.current_ante, int(50000 * (1.5 ** (self.current_ante - 8))))
        
        if self.current_blind_type == "small":
            self.target_score = int(base_target * 1.0)
            self.base_reward = 3
        elif self.current_blind_type == "big":
            self.target_score = int(base_target * 1.5)
            self.base_reward = 4
        elif self.current_blind_type == "boss":
            # Delega el cálculo de puntaje a la instancia concreta de BossBlind
            self.target_score = self.active_boss.calculate_target_score(self.current_ante)
            self.base_reward = 5

    def get_current_blind_info(self) -> dict:
        """Información para la UI o el flujo del juego."""
        return {
            "ante": self.current_ante,
            "max_antes": self.max_antes,
            "blind_type": self.current_blind_type,
            "target_score": self.target_score,
            "base_reward": self.base_reward,
            "can_skip": self.current_blind_type != "boss",
            "skip_tag": self.small_skip_tag if self.current_blind_type == "small" else (self.big_skip_tag if self.current_blind_type == "big" else None),
            "boss_info": self.active_boss.to_dict() if self.current_blind_type == "boss" else None
        }

    def skip_blind(self) -> dict:
        """Omite la ciega actual (pequeña o grande) y entrega el tag correspondiente."""
        if self.current_blind_type == "boss":
            raise ValueError("No se puede saltar la Ciega Jefe.")

        applied_tag = self.small_skip_tag if self.current_blind_type == "small" else self.big_skip_tag
        self.pending_tags.append(applied_tag)
        self._advance_blind_pointer()
        return applied_tag

    def calculate_payout(self, remaining_hands: int, remaining_discards: int) -> dict:
        """Cálculo de dinero ganado al superar la ciega."""
        hand_bonus = remaining_hands * 1
        discard_bonus = remaining_discards * 1
        total_payout = self.base_reward + hand_bonus + discard_bonus

        return {
            "base_reward": self.base_reward,
            "hand_bonus": hand_bonus,
            "discard_bonus": discard_bonus,
            "total_payout": total_payout
        }

    def complete_blind(self):
        """Avanza el puntero de ciega tras ganar la ronda."""
        self._advance_blind_pointer()

    def _advance_blind_pointer(self):
        if self.current_blind_type == "small":
            self.current_blind_type = "big"
        elif self.current_blind_type == "big":
            self.current_blind_type = "boss"
        elif self.current_blind_type == "boss":
            self.current_ante += 1
            self.current_blind_type = "small"
            self._setup_ante()
            
        self._update_blind_parameters()

    def is_run_completed(self) -> bool:
        return self.current_ante > self.max_antes