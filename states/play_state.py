"""
Módulo: states/play_state.py
Descripción: Estado principal de juego para la mesa de cartas.

Este estado conserva la interfaz existente de la máquina de estados y añade
únicamente las funciones necesarias para una partida coherente:
- mostrar puntaje acumulado y objetivo;
- recompensar al jugador al superar una ciega;
- entrar correctamente al StoreState;
- ordenar la mano por palo o por rango;
- conservar dinero y Jokers entre estados.
"""

from __future__ import annotations

from pathlib import Path

import pygame

from states.base_state import BaseState
from Renderer import Renderer
from animaciones import AnimationController
from audio import get_audio_manager
from entities import (
    CardEntity,
    CardFactory,
    EntityCollection,
    GameRules,
    RandomJokerPool,
)


class PlayState(BaseState):
    """Estado principal que administra una ciega y la mano actual del jugador."""

    MAX_HAND_SIZE = 8
    MAX_PLAY_SIZE = 5

    # Orden utilizado al organizar cartas por palo.
    # CardFactory convierte los códigos S/H/D/C a sus símbolos Unicode.
    # Debemos ordenar usando los valores reales almacenados en CardEntity.suit.
    SUIT_ORDER = {
        "♣": 0,
        "♦": 1,
        "♥": 2,
        "♠": 3,
    }

    def __init__(self, screen: pygame.Surface, context: dict | None = None) -> None:
        """Inicializa el estado conservando el contexto compartido de la partida."""
        super().__init__()
        self.screen = screen
        self.context = context if context is not None else {}
        self.audio = get_audio_manager()
        self.renderer = Renderer(*screen.get_size(), screen=screen)
        self.animations = AnimationController()
        self.rules = GameRules()
        self.card_factory = CardFactory(self._project_root())
        self.cards = EntityCollection[CardEntity]()

        self.message = "Selecciona de 1 a 5 cartas y presiona ESPACIO"
        self.last_hand_name = "High Card"
        self.round_number = int(self.context.get("round", 1))
        self.target = int(self.context.get("blind_target", 100 * self.round_number))
        self.hands_left = 4
        self.discards_left = 3
        self.round_score = 0
        self.jokers = RandomJokerPool()

        # Rects de los controles de ordenamiento, colocados debajo de la mano.
        self.sort_suit_rect = pygame.Rect(0, 0, 130, 24)
        self.sort_rank_rect = pygame.Rect(0, 0, 130, 24)

        self.reset_round()

    def enter(self):
        """Activa el estado y recupera desde context la ciega y los Jokers actuales."""
        self.audio.play_game_music()
        self.round_number = int(self.context.get("round", self.round_number))
        self.target = int(
            self.context.get("blind_target", 100 * self.round_number)
        )

        # La lista del contexto es la fuente persistente de los Jokers comprados.
        joker_list = self.context.setdefault("jokers", [])
        self.jokers = RandomJokerPool(joker_list)
        self.reset_round()

    def exit(self):
        """Cancela animaciones y detiene la música al abandonar la mesa."""
        self.animations.cancel()
        self.audio.stop_music()

    def _project_root(self) -> Path:
        """Obtiene la carpeta raíz del proyecto para localizar recursos."""
        return Path(__file__).resolve().parent.parent

    def reset_round(self) -> None:
        """Reinicia manos, descartes, puntaje y genera las cartas de la ciega."""
        self.hands_left = 4
        self.discards_left = 3
        self.round_score = 0
        self.rules.reset()
        self._start_round()
        self.message = f"Ciega: {self.context.get('blind_name', 'Actual')} | Objetivo: {self.target}"

    def _start_round(self) -> None:
        """Genera ocho cartas y las mezcla para iniciar la mano."""
        self.cards = EntityCollection[CardEntity](
            self.card_factory.create_random_collection(self.MAX_HAND_SIZE)
        )
        self.cards.shuffle()

    def _selected_cards(self) -> list[CardEntity]:
        """Devuelve las cartas marcadas por el jugador."""
        return [card for card in self.cards if card.selected]

    def _select_card_at(self, position: tuple[int, int]) -> None:
        """Selecciona o deselecciona la carta ubicada en la posición recibida."""
        self._sync_card_rects()
        for card in reversed(self.cards.copy()):
            if card.rect is not None and card.rect.collidepoint(position):
                selected_count = sum(1 for item in self.cards if item.selected)
                if not card.selected and selected_count >= self.MAX_PLAY_SIZE:
                    self.message = "No puedes seleccionar más de 5 cartas"
                    return
                card.toggle_selected()
                return

    def handle_events(self, events: list[pygame.event.Event]) -> str | None:
        """Procesa teclado y mouse, incluyendo los controles de ordenamiento."""
        for event in events:
            if self.animations.active:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.animations.cancel()
                    return "MENU"
                self.animations.handle_event(event)
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "MENU"
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self.play_selected()
                elif event.key == pygame.K_d:
                    self.discard_selected()
                elif event.key == pygame.K_s:
                    self.sort_by_suit()
                elif event.key == pygame.K_r:
                    self.sort_by_rank()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.sort_suit_rect.collidepoint(event.pos):
                    self.sort_by_suit()
                elif self.sort_rank_rect.collidepoint(event.pos):
                    self.sort_by_rank()
                else:
                    self._select_card_at(event.pos)

        return None

    def update(self, dt: float) -> str | None:
        """Actualiza animaciones y cambia a tienda o Game Over cuando corresponde."""
        self.animations.update(dt)

        # Espera a terminar la animación para que el jugador vea el resultado.
        if self.round_score >= self.target:
            if self.animations.active:
                return None
            self._prepare_store_transition()
            return "SHOP"

        if self.hands_left <= 0 and self.round_score < self.target:
            self.context["score"] = self.round_score
            return "GAME_OVER"

        return None

    def _prepare_store_transition(self) -> None:
        """Calcula la recompensa y guarda toda la información que necesita la tienda."""
        ante = int(self.context.get("ante", 1))
        base_reward = int(self.context.get("blind_reward", 4)) + max(0, ante - 1) * 2

        # El bono por recursos sobrantes es intencionalmente simple y transparente.
        hand_bonus = max(0, self.hands_left)
        discard_bonus = max(0, self.discards_left)
        total_reward = base_reward + hand_bonus + discard_bonus

        self.context["money"] = int(self.context.get("money", 0)) + total_reward
        self.context["round_reward"] = {
            "base": base_reward,
            "hands": hand_bonus,
            "discards": discard_bonus,
            "total": total_reward,
            "score": self.round_score,
            "target": self.target,
        }
        self.context["score"] = self.round_score

        # La siguiente entrada a PlayState debe utilizar la ciega elegida en tienda.
        self.context["round"] = self.round_number + 1
        self.context["blind_won"] = True
        self.context["is_boss_blind_won"] = bool(self.context.get("blind_is_boss", False))

        # El ante aumenta solo después de superar la ciega jefe.
        if self.context["is_boss_blind_won"]:
            self.context["ante"] = ante + 1
            self.context["blind_index"] = 0

    def play_selected(self) -> int | None:
        """Evalúa una mano, suma su puntuación y repone las cartas jugadas."""
        selected = self._selected_cards()
        if not 1 <= len(selected) <= self.MAX_PLAY_SIZE:
            self.message = "Selecciona entre 1 y 5 cartas"
            return None
        if self.hands_left <= 0:
            self.message = "No quedan manos disponibles"
            return None

        best = self.rules.best_five(selected)
        self._sync_card_rects()
        start_positions = [
            (card.rect.x, card.rect.y) for card in best if card.rect is not None
        ]

        # Los Jokers pueden modificar fichas/multiplicadores de las cartas.
        # Evaluamos la mano una vez después de aplicar esos efectos para que el
        # resultado usado por el HUD y la animación sea el resultado definitivo.
        activated = self.jokers.activate_all(EntityCollection(best))
        result = self.rules.evaluate(best)
        self.last_hand_name = result.name
        self.round_score += result.total
        self.hands_left -= 1

        self.animations.play_cards(
            list(best), start_positions, result.name, result.total
        )

        for card in selected:
            self.cards.remove(card)

        missing = self.MAX_HAND_SIZE - len(self.cards)
        new_cards = self.card_factory.create_random_collection(missing)
        self.cards.add_many(new_cards)
        self.cards.shuffle()
        self._sync_card_rects()
        refill_positions = [
            (card.rect.x, card.rect.y) for card in new_cards if card.rect is not None
        ]
        self.animations.refill_cards(new_cards, refill_positions)

        joker_text = f" | Jokers: {', '.join(activated)}" if activated else ""
        self.message = (
            f"{result.name}: {result.total} pts | "
            f"Acumulado: {self.round_score}/{self.target}{joker_text}"
        )
        return result.total

    def discard_selected(self) -> int | None:
        """Descarta cartas seleccionadas, consume un descarte y repone la mano."""
        selected = self._selected_cards()
        if not selected:
            self.message = "Selecciona cartas para descartar"
            return None
        if self.discards_left <= 0:
            self.message = "No quedan descartes"
            return None

        for card in selected:
            self.cards.remove(card)

        self.discards_left -= 1
        missing = self.MAX_HAND_SIZE - len(self.cards)
        new_cards = self.card_factory.create_random_collection(missing)
        self.cards.add_many(new_cards)
        self.cards.shuffle()
        self._sync_card_rects()
        refill_positions = [
            (card.rect.x, card.rect.y) for card in new_cards if card.rect is not None
        ]
        self.animations.refill_cards(new_cards, refill_positions)
        self.message = (
            f"Descartaste {len(selected)} cartas | "
            f"Acumulado: {self.round_score}/{self.target}"
        )
        return len(selected)

    def sort_by_suit(self) -> None:
        """Ordena las cartas por palo y luego por rango de mayor a menor."""
        cards = self.cards.copy()
        cards.sort(
            key=lambda card: (
                self.SUIT_ORDER.get(card.suit, 99),
                -self._rank_value(card.rank),
            )
        )
        self.cards = EntityCollection[CardEntity](cards)
        self._sync_card_rects()
        self.message = "Cartas organizadas por palo"

    def sort_by_rank(self) -> None:
        """Ordena las cartas por rango de mayor a menor y usa el palo como desempate."""
        cards = self.cards.copy()
        cards.sort(
            key=lambda card: (
                -self._rank_value(card.rank),
                self.SUIT_ORDER.get(card.suit, 99),
            )
        )
        self.cards = EntityCollection[CardEntity](cards)
        self._sync_card_rects()
        self.message = "Cartas organizadas por número"

    @staticmethod
    def _rank_value(rank: str) -> int:
        """Devuelve el valor numérico del rango para ordenar las cartas."""
        if rank == "A":
            return 14
        if rank == "K":
            return 13
        if rank == "Q":
            return 12
        if rank == "J":
            return 11
        return int(rank)

    def _sync_card_rects(self) -> None:
        """Sincroniza los Rect de las cartas con la distribución usada por Renderer."""
        spacing = 95
        start_x = (self.screen.get_width() - (len(self.cards) * spacing)) // 2 + 100
        start_y = self.screen.get_height() - 160
        for index, card in enumerate(self.cards):
            if card.rect:
                card.rect.x = start_x + index * spacing
                card.rect.y = start_y - (20 if card.selected else 0)

        # Los botones quedan inmediatamente debajo de la mano.
        self.sort_suit_rect = pygame.Rect(
            self.screen.get_width() // 2 - 140,
            self.screen.get_height() - 28,
            130,
            22,
        )
        self.sort_rank_rect = pygame.Rect(
            self.screen.get_width() // 2 + 10,
            self.screen.get_height() - 28,
            130,
            22,
        )

    def draw(self, screen: pygame.Surface | None = None) -> None:
        """Renderiza HUD, Jokers, mano, botones de orden y mensajes."""
        target_screen = screen or self.screen
        self._sync_card_rects()
        self.renderer.clear()

        selected_cards = self._selected_cards()
        result = self.rules.evaluate(selected_cards) if selected_cards else None
        chips = result.score if result else self.round_score
        mult = result.multiplier if result else self.rules.multiplier

        self.renderer.draw_hud_panel(
            self.round_score,
            self.target,
            mult,
            chips,
            self.hands_left,
            self.discards_left,
        )
        self.renderer.draw_joker_bar(self.jokers.to_dict())

        hidden_card_ids = self.animations.hidden_card_ids
        card_data = [
            card.to_dict() for card in self.cards if id(card) not in hidden_card_ids
        ]
        self.renderer.draw_hand(card_data)

        if self.animations.active:
            self.animations.draw(self.renderer, target_screen)

        self._draw_sort_buttons(target_screen)

        font = pygame.font.SysFont("Arial", 18, bold=True)
        text = font.render(self.message, True, (255, 255, 255))
        target_screen.blit(text, (300, target_screen.get_height() - 52))

    def _draw_sort_buttons(self, screen: pygame.Surface) -> None:
        """Dibuja las dos acciones para ordenar la mano."""
        button_data = (
            (self.sort_suit_rect, "ORDENAR PALO"),
            (self.sort_rank_rect, "ORDENAR NUMERO"),
        )
        font = pygame.font.SysFont("Arial", 13, bold=True)
        for rect, label in button_data:
            pygame.draw.rect(screen, (55, 55, 70), rect, border_radius=5)
            pygame.draw.rect(screen, (210, 210, 220), rect, width=1, border_radius=5)
            surface = font.render(label, True, (255, 255, 255))
            screen.blit(surface, surface.get_rect(center=rect.center))
