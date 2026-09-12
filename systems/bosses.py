"""
Módulo: systems/bosses.py
Descripción: Jerarquía de clases para Ciegas Jefe (La Aguja, El Gancho, La Muralla)
             con selección sin repetición por partida.
"""

from abc import ABC, abstractmethod
import random

# Tabla base de puntuaciones por Ante (1 a 8)
BASE_ANTE_TARGETS = {
    1: 300,
    2: 800,
    3: 2000,
    4: 5000,
    5: 11000,
    6: 20000,
    7: 35000,
    8: 50000
}


class BossBlind(ABC):
    """Clase base abstracta para las Ciegas Jefe."""

    def __init__(self, name: str, description: str, effect_id: str, score_multiplier: float = 2.0):
        self.name = name
        self.description = description
        self.effect_id = effect_id
        self.score_multiplier = score_multiplier

    def calculate_target_score(self, ante: int, custom_multiplier: float = 1.0) -> int:
        """Calcula el puntaje objetivo según el Ante y multiplicadores propios/externos."""
        base_score = BASE_ANTE_TARGETS.get(ante, int(50000 * (1.5 ** (ante - 8))))
        final_score = base_score * self.score_multiplier * custom_multiplier
        return int(final_score)

    @abstractmethod
    def apply_effect(self, game_state: dict) -> dict:
        """Aplica las modificaciones de reglas al estado del juego."""
        pass

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "effect_id": self.effect_id,
            "multiplier": self.score_multiplier
        }


# =============================================================================
# JEFES PERMITIDOS
# =============================================================================

class HookBoss(BossBlind):
    """El Gancho: Descarta 2 cartas al azar tras jugar una mano."""

    def __init__(self):
        super().__init__(
            name="El Gancho",
            description="Descarta 2 cartas al azar de tu mano tras jugar una mano",
            effect_id="hook",
            score_multiplier=2.0
        )

    def apply_effect(self, game_state: dict) -> dict:
        # Se ejecuta después de evaluar la mano en el loop de juego
        hand = game_state.get("hand", [])
        if len(hand) > 2:
            discarded = random.sample(hand, 2)
            game_state["hand"] = [c for c in hand if c not in discarded]
        else:
            game_state["hand"] = []
        return game_state


class WallBoss(BossBlind):
    """La Muralla: Puntuación requerida masiva (4.0x base)."""

    def __init__(self):
        super().__init__(
            name="La Muralla",
            description="Puntuación requerida extra grande",
            effect_id="wall",
            score_multiplier=4.0
        )

    def apply_effect(self, game_state: dict) -> dict:
        # No altera estado directamente; su efecto es puramente en la puntuación
        return game_state


class NeedleBoss(BossBlind):
    """La Aguja: Solo 1 mano disponible, puntuación reducida (0.6x)."""

    def __init__(self):
        super().__init__(
            name="La Aguja",
            description="Solo tienes 1 mano disponible esta ronda",
            effect_id="needle",
            score_multiplier=2.0
        )

    def calculate_target_score(self, ante: int, custom_multiplier: float = 0.6) -> int:
        return super().calculate_target_score(ante, custom_multiplier=custom_multiplier)

    def apply_effect(self, game_state: dict) -> dict:
        game_state["hands"] = 1
        return game_state


# Pool de clases disponibles
ALLOWED_BOSS_CLASSES = [HookBoss, WallBoss, NeedleBoss]


def get_random_boss_instance(seen_boss_ids: set) -> BossBlind:
    """
    Instancia un jefe aleatorio garantizando que no se repita 
    uno previamente usado en la misma partida.
    """
    available = [b for b in ALLOWED_BOSS_CLASSES if b().effect_id not in seen_boss_ids]
    
    # Si por alguna razón se usaron todos los jefes, reinicia el filtro
    if not available:
        seen_boss_ids.clear()
        available = ALLOWED_BOSS_CLASSES

    chosen_class = random.choice(available)
    instance = chosen_class()
    seen_boss_ids.add(instance.effect_id)
    return instance