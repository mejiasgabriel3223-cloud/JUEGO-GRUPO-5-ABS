"""Nucleo jugable de cartas.

Mantiene el nombre CarreraDeObstaculos por compatibilidad con el main.py
existente, pero internamente implementa el juego de cartas del proyecto.
"""
from __future__ import annotations

import pygame

from Renderer import Renderer
from entities import (
    FlatChipsJoker,
    HandEvaluator,
    MultiplierJoker,
    Player,
    RoundState,
    StandardDeckFactory,
)


class SelectorDummy:
    """Selector provisional mantenido para no romper el flujo actual del menu."""

    def __init__(self) -> None:
        self.title_font = pygame.font.SysFont("Arial", 42, bold=True)
        self.font = pygame.font.SysFont("Arial", 24)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            return "Jugador"
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return None
        return None

    def draw(self, screen):
        screen.fill((35, 62, 50))
        title = self.title_font.render("Mesa de cartas", True, (255, 255, 255))
        prompt = self.font.render("ENTER o ESPACIO para comenzar", True, (230, 230, 230))
        help_text = self.font.render("ESC para volver al menu", True, (190, 200, 190))
        screen.blit(title, title.get_rect(center=(640, 250)))
        screen.blit(prompt, prompt.get_rect(center=(640, 330)))
        screen.blit(help_text, help_text.get_rect(center=(640, 380)))


class CardGame:
    """Controlador de alto nivel: orquesta entidades y renderer."""

    def __init__(self, screen):
        self.screen = screen
        self.renderer = Renderer(*screen.get_size(), screen=screen)
        self.sound_player = None
        self.player_name = "Jugador"
        self.personaje_actual = None
        self.player = Player(self.player_name)
        self.round_state = RoundState()
        self.selector = SelectorDummy()
        self.last_hand_name = "Carta alta"
        self.message = "Selecciona 1 a 5 cartas y presiona ESPACIO"
        self.running_round = False
        self.reset_game()

    @property
    def score(self) -> int:
        return self.player.round_score

    def reset_game(self):
        self.player = Player(self.player_name)
        self.player.jokers = [FlatChipsJoker(20), MultiplierJoker(2)]
        self.round_state = RoundState()
        self.last_hand_name = "Carta alta"
        self.message = "Selecciona 1 a 5 cartas y presiona ESPACIO"
        self._start_round()
        self.running_round = True

    def _start_round(self):
        self.player.reset_round_resources()
        self.player.deck = StandardDeckFactory.create()
        self.player.hand.add_many(self.player.deck.draw_many(self.player.hand.MAX_SIZE))

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "MENU"
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    return self.play_selected()
                if event.key == pygame.K_d:
                    return self.discard_selected()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._select_card_at(event.pos)
        return None

    def update(self, dt):
        if not self.running_round:
            return None

        if self.round_state.completed:
            return "GAMEOVER"

        if self.player.round_score >= self.round_state.target:
            self.round_state.advance()
            if self.round_state.completed:
                self.running_round = False
                self.message = "Victoria: has superado todas las rondas"
                return "GAMEOVER"
            self._start_round()
            self.message = f"Ronda superada. Nuevo objetivo: {self.round_state.target}"

        if self.player.hands_left <= 0 and self.player.round_score < self.round_state.target:
            self.running_round = False
            self.message = "No quedan manos: GAME OVER"
            return "GAMEOVER"
        return None

    def play_selected(self):
        selected = self.player.hand.selected_cards
        if not 1 <= len(selected) <= 5:
            self.message = "Debes seleccionar entre 1 y 5 cartas"
            return None
        if self.player.hands_left <= 0:
            self.message = "No quedan manos"
            return None

        best_cards = HandEvaluator.best_five(selected)
        hand_name, context = HandEvaluator.evaluate(best_cards)
        final_context = HandEvaluator.apply_jokers(context, self.player.jokers)
        self.player.last_chips = final_context.chips
        self.player.last_multiplier = final_context.multiplier
        self.player.round_score += final_context.score
        self.player.hands_left -= 1
        self.last_hand_name = hand_name

        self.player.hand.remove_selected()
        self._refill_hand()
        self.message = f"{hand_name}: +{final_context.score} puntos"
        return None

    def discard_selected(self):
        selected = self.player.hand.selected_cards
        if not selected:
            self.message = "Selecciona cartas para descartar"
            return None
        if self.player.discards_left <= 0:
            self.message = "No quedan descartes"
            return None
        self.player.hand.remove_selected()
        self.player.discards_left -= 1
        self._refill_hand()
        self.message = f"Descartaste {len(selected)} carta(s)"
        return None

    def _refill_hand(self):
        needed = self.player.hand.MAX_SIZE - len(self.player.hand)
        self.player.hand.add_many(self.player.deck.draw_many(needed))

    def _select_card_at(self, pos):
        spacing = 95
        start_x = (self.renderer.width - (len(self.player.hand.cards) * spacing)) // 2 + 100
        start_y = self.renderer.height - 160
        for index, _card in enumerate(self.player.hand.cards):
            x = start_x + index * spacing
            y = start_y - (20 if _card.selected else 0)
            rect = pygame.Rect(x, y, 90, 130)
            if rect.collidepoint(pos):
                self.player.hand.toggle(index)
                return

    def _update_record_summary(self):
        # Se mantiene este metodo porque main.py existente lo llama.
        # El guardado efectivo se realiza al volver al menu.
        return self.player.round_score

    def draw(self):
        self.renderer.clear()
        self.renderer.draw_hud_panel(
            score=self.player.round_score,
            target=self.round_state.target,
            mult=self.player.last_multiplier,
            chips=self.player.last_chips,
            hands=self.player.hands_left,
            discards=self.player.discards_left,
        )
        self.renderer.draw_joker_bar([joker.to_dict() for joker in self.player.jokers])
        self.renderer.draw_hand([card.to_dict() for card in self.player.hand.cards])
        self._draw_footer()

    def _draw_footer(self):
        font = pygame.font.SysFont("Arial", 21, bold=True)
        small = pygame.font.SysFont("Arial", 18)
        title = font.render(
            f"{self.last_hand_name} | Ante {self.round_state.ante} | Ronda {self.round_state.round_number}/{self.round_state.max_rounds}",
            True,
            (255, 255, 255),
        )
        message = small.render(self.message, True, (230, 230, 230))
        controls = small.render("Click: seleccionar | ESPACIO: jugar | D: descartar | ESC: menu", True, (190, 200, 200))
        self.screen.blit(title, (290, 165))
        self.screen.blit(message, (290, 195))
        self.screen.blit(controls, (290, 690))

    def draw_gameover(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        font = pygame.font.SysFont("Arial", 56, bold=True)
        small = pygame.font.SysFont("Arial", 24)
        title = font.render("GAME OVER", True, (255, 235, 235))
        score = small.render(f"Puntuacion: {self.player.round_score}", True, (255, 255, 255))
        help_text = small.render("ENTER reinicia | ESC vuelve al menu", True, (240, 240, 240))
        self.screen.blit(title, title.get_rect(center=(640, 280)))
        self.screen.blit(score, score.get_rect(center=(640, 350)))
        self.screen.blit(help_text, help_text.get_rect(center=(640, 410)))


# Compatibilidad con el main.py existente.
CarreraDeObstaculos = CardGame
