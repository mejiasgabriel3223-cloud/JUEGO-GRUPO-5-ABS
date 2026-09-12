"""Integration adapter between the existing game shell and the entity layer.

The existing ``main.py`` keeps using ``CarreraDeObstaculos`` for compatibility.
This module preserves that public interface while delegating card state,
scoring, dynamic collections and Joker behaviour to ``entities``.
"""

from __future__ import annotations

from pathlib import Path
import pygame

from Renderer import Renderer
# se exporta PlayAnimation para que main.py pueda acceder a la clase de animación

from animaciones import PlayAnimation
from entities import CardEntity, CardFactory, EntityCollection, GameRules, RandomJokerPool, FlatChipsJoker, MultiplierJoker


class SelectorDummy:
    """Compatibility selector expected by the existing menu state machine."""

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            return "Player"
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return None
        return None

    def draw(self, screen):
        screen.fill((35, 62, 50))
        title_font = pygame.font.SysFont("Arial", 42, bold=True)
        font = pygame.font.SysFont("Arial", 24)
        title = title_font.render("Card Table", True, (255, 255, 255))
        prompt = font.render("ENTER or SPACE to start", True, (230, 230, 230))
        help_text = font.render("ESC to return to menu", True, (190, 200, 190))
        screen.blit(title, title.get_rect(center=(640, 250)))
        screen.blit(prompt, prompt.get_rect(center=(640, 330)))
        screen.blit(help_text, help_text.get_rect(center=(640, 380)))


class CarreraDeObstaculos:
    """Backward-compatible game controller powered by the new entities."""

    MAX_HAND_SIZE = 8
    MAX_PLAY_SIZE = 5

    def __init__(self, screen):
        self.screen = screen
        self.renderer = Renderer(*screen.get_size(), screen=screen)
        self.sound_player = None
        self.player_name = "Player"
        self.personaje_actual = None
        self.selector = SelectorDummy()
        self.running_round = False
        self.message = "Select 1 to 5 cards and press SPACE"
        self.last_hand_name = "High Card"
        self.round_number = 1
        self.target = 100
        self.hands_left = 4
        self.discards_left = 3
        self.round_score = 0
        self.rules = GameRules()
        self.card_factory = CardFactory(self._project_root())
        self.cards = EntityCollection[CardEntity]()
        self.jokers = RandomJokerPool()
        #se agrega la línea para inicializar la animación de juego
        self.play_animation = PlayAnimation()

        self.reset_game()

    @property
    def score(self) -> int:
        """Expose score for the existing main.py record handling."""
        return self.round_score

    @property
    def hand(self):
        """Compatibility alias for code that refers to the current card pool."""
        return self.cards

    def _project_root(self) -> Path:
        return Path(__file__).resolve().parent

    def reset_game(self):
        #se agrega la línea para cancelar la animación en curso al reiniciar el juego
        self.play_animation.cancel()

        self.round_number = 1
        self.target = 100
        self.hands_left = 4
        self.discards_left = 3
        self.round_score = 0
        self.rules.reset()
        self.jokers = RandomJokerPool([
            FlatChipsJoker(amount=5, probability=0.75),
            MultiplierJoker(amount=0.25, probability=0.60),
        ])
        self.running_round = True
        self._start_round()
        self.message = "Select 1 to 5 cards and press SPACE"

    def _start_round(self):
        self.cards = EntityCollection[CardEntity](
            self.card_factory.create_random_collection(self.MAX_HAND_SIZE)
        )
        self.cards.shuffle()

    def _select_card_at(self, position):
        self._sync_card_rects()
        for card in reversed(self.cards.copy()):
            if card.rect is not None and card.rect.collidepoint(position):
                selected_count = sum(1 for item in self.cards if item.selected)
                if not card.selected and selected_count >= self.MAX_PLAY_SIZE:
                    self.message = "You can select at most 5 cards"
                    return
                card.toggle_selected()
                return

    def _selected_cards(self) -> list[CardEntity]:
        return [card for card in self.cards if card.selected]

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "MENU"
                # Se agrega la verificación de si la animación está activa antes de permitir acciones de juego
                if self.play_animation.active:
                    self.play_animation.handle_event(event)
                    continue
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self.play_selected()
                elif event.key == pygame.K_d:
                    self.discard_selected()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Se agrega la verificación de si la animación está activa antes de permitir acciones de juego
                if self.play_animation.active:
                    continue
                self._select_card_at(event.pos)
        return None

    def update(self, dt):
        # Se agrega la actualización de la animación de juego en cada ciclo de actualización
        self.play_animation.update(dt)
        if not self.running_round:
            return "GAMEOVER"
        if self.round_score >= self.target:
            self.round_number += 1
            if self.round_number > 3:
                self.running_round = False
                self.message = "Victory: all rounds completed"
                return "GAMEOVER"
            self.target = 100 * self.round_number
            self.hands_left = 4
            self.discards_left = 3
            self.round_score = 0
            self.rules.reset()
            self._start_round()
            self.message = f"Round cleared. New target: {self.target}"
        elif self.hands_left <= 0:
            self.running_round = False
            self.message = "No hands left: GAME OVER"
            return "GAMEOVER"
        return None

    def play_selected(self):
        selected = self._selected_cards()
        if not 1 <= len(selected) <= self.MAX_PLAY_SIZE:
            self.message = "Select between 1 and 5 cards"
            return None
        if self.hands_left <= 0:
            self.message = "No hands left"
            return None

        best = self.rules.best_five(selected)
        # Se agrega la línea para sincronizar las posiciones de los Rects de las cartas antes de iniciar la animación
        self._sync_card_rects()
        start_positions = [(card.rect.x, card.rect.y) for card in best]

        self.rules.apply_result = self.rules.evaluate  # harmless adapter hook for integration
        self.rules.evaluate(best)  # validate and establish the base result
        activated = self.jokers.activate_all(EntityCollection(best))
        result = self.rules.evaluate(best)

        self.last_hand_name = result.name
        self.round_score += result.total
        self.hands_left -= 1
        # Se agrega la línea para iniciar la animación de juego con las cartas jugadas
        self.play_animation.start(list(best), start_positions, result.name, result.total)

        # Played cards leave the active array; new cards refill it to the
        # current hand size. The resulting collection is then randomized.
        for card in selected:
            self.cards.remove(card)
        missing = self.MAX_HAND_SIZE - len(self.cards)
        self.cards.add_many(self.card_factory.create_random_collection(missing))
        self.cards.shuffle()

        if activated:
            self.message = f"{result.name}: {result.total} points | Jokers: {', '.join(activated)}"
        else:
            self.message = f"{result.name}: {result.total} points"

        return result.total

    def discard_selected(self):
        selected = self._selected_cards()
        if not selected:
            self.message = "Select cards to discard"
            return None
        if self.discards_left <= 0:
            self.message = "No discards left"
            return None

        for card in selected:
            self.cards.remove(card)
        self.discards_left -= 1

        missing = self.MAX_HAND_SIZE - len(self.cards)
        self.cards.add_many(self.card_factory.create_random_collection(missing))
        self.cards.shuffle()
        self.message = f"Discarded {len(selected)} cards"
        return len(selected)

    def _sync_card_rects(self) -> None:
        """Keep entity Rects aligned with the existing Renderer hand layout."""
        spacing = 95
        start_x = (self.screen.get_width() - (len(self.cards) * spacing)) // 2 + 100
        start_y = self.screen.get_height() - 160
        for index, card in enumerate(self.cards):
            card.rect.x = start_x + index * spacing
            card.rect.y = start_y - (20 if card.selected else 0)

    def _card_dict(self, card: CardEntity) -> dict:
        data = card.to_dict()
        # Existing Renderer expects rank/suit text. CardEntity already stores
        # the suit symbol, so no renderer-side adaptation is necessary.
        return data

    def draw(self):
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
        self.renderer.draw_joker_bar([
            {"name": joker.name, "active": joker.active}
            for joker in self.jokers.jokers
        ])
#verifica si la animación de juego está activa y dibuja la animación si es así, de lo contrario dibuja la mano de cartas
        if self.play_animation.active:
            self.play_animation.draw(self.renderer, self.screen)
        else:
            card_data = [self._card_dict(card) for card in self.cards]
            self.renderer.draw_hand(card_data)
        font = pygame.font.SysFont("Arial", 22, bold=True)
        text = font.render(self.message, True, (255, 255, 255))
        self.screen.blit(text, (300, self.screen.get_height() - 40))
        self.renderer.present()

    def _update_record_summary(self):
        """Compatibility hook used by main.py when GAMEOVER is reached."""
        return self.round_score

    def draw_gameover(self):
        overlay_font = pygame.font.SysFont("Arial", 58, bold=True)
        info_font = pygame.font.SysFont("Arial", 28)
        title = overlay_font.render("GAME OVER", True, (255, 80, 80))
        info = info_font.render("ENTER to play again | ESC for menu", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(640, 300)))
        self.screen.blit(info, info.get_rect(center=(640, 370)))
