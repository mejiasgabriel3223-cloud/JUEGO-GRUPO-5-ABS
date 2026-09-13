"""
Módulo: states/store_state.py
Descripción: Tienda entre ciegas con resumen de recompensa, compra/venta de
Jokers, rerrolleo y selección de la siguiente ciega.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
import random

import pygame

from entities import Joker, FlatChipsJoker, MultiplierJoker
from states.base_state import BaseState


@dataclass(frozen=True)
class JokerOffer:
    """Representa un Joker disponible para compra junto con su precio."""

    joker: Joker
    price: int
    slot: int


@dataclass(frozen=True)
class BlindOption:
    """Representa una ciega seleccionable antes de volver a PlayState."""

    name: str
    target: int
    ante: int
    blind_index: int
    is_boss: bool = False


class StoreFlatJoker(Joker):
    """Joker de tienda que agrega fichas a cada carta jugada."""

    def __init__(self, name: str, amount: int, probability: float = 1.0) -> None:
        super().__init__(name, probability)
        self.amount = amount
        self.description = f"+{amount} fichas por carta"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        """Aplica el bono de fichas a todas las cartas recibidas."""
        for card in cards:
            card.apply_bonus(score_delta=self.amount)
        return True


class StoreMultiplierJoker(Joker):
    """Joker de tienda que aumenta el multiplicador de cada carta."""

    def __init__(self, name: str, amount: float, probability: float = 1.0) -> None:
        super().__init__(name, probability)
        self.amount = amount
        self.description = f"+{amount:g} Mult por carta"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        """Aumenta el multiplicador de cada carta recibida."""
        for card in cards:
            card.apply_bonus(multiplier_delta=self.amount)
        return True


class StoreState(BaseState):
    """Gestiona las tres pantallas internas del descanso entre ciegas."""

    SUMMARY = "SUMMARY"
    SHOP = "SHOP"
    BLIND_SELECT = "BLIND_SELECT"
    MAX_JOKERS = 5
    REROLL_COST = 5

    def __init__(self, screen: pygame.Surface, context: dict[str, Any] | None = None) -> None:
        """Inicializa la tienda y prepara el contexto persistente."""
        super().__init__()
        self.screen = screen
        self.context = context if context is not None else {}
        self.phase = self.SUMMARY
        self.message = ""
        self.selected_owned_index: int | None = None
        self.offers: list[JokerOffer] = []
        self.blind_options: list[BlindOption] = []
        self._prepare_persistent_values()
        self._build_buttons()

    def _prepare_persistent_values(self) -> None:
        """Crea las claves persistentes de economía, ante y ciegas si no existen."""
        self.context.setdefault("money", 0)
        self.context.setdefault("jokers", [])
        self.context.setdefault("ante", 1)
        self.context.setdefault("blind_index", 0)
        self.context.setdefault("selected_blind", None)
        self.context.setdefault("blind_target", 100)
        self.context.setdefault("blind_name", "Ciega pequeña")
        self.context.setdefault("blind_is_boss", False)
        self.context.setdefault(
            "round_reward", {"base": 0, "hands": 0, "discards": 0, "total": 0}
        )

    @property
    def money(self) -> int:
        """Devuelve el dinero persistente disponible."""
        return int(self.context.get("money", 0))

    @property
    def jokers(self) -> list[Joker]:
        """Devuelve la lista persistente de Jokers comprados."""
        return self.context.setdefault("jokers", [])

    def enter(self) -> None:
        """Entra siempre mostrando primero el resumen y genera ofertas nuevas."""
        self.phase = self.SUMMARY
        self.selected_owned_index = None
        self.message = "Ciega superada"
        self.context["selected_blind"] = None
        self._generate_offers()
        self._generate_blind_options()
        self._build_buttons()

    def exit(self) -> None:
        """Limpia la selección temporal de venta al salir de la tienda."""
        self.selected_owned_index = None

    def _build_buttons(self) -> None:
        """Construye los Rect usados por mouse en cada fase."""
        width = self.screen.get_width()
        height = self.screen.get_height()
        self.accept_rect = pygame.Rect(width // 2 - 110, height - 90, 220, 50)
        self.reroll_rect = pygame.Rect(width - 250, height - 90, 105, 50)
        self.continue_rect = pygame.Rect(width // 2 - 110, height - 90, 220, 50)
        self.sell_rect = pygame.Rect(width - 250, height - 150, 105, 50)
        self.offer_rects = [
            pygame.Rect(width // 2 - 270, 190, 220, 230),
            pygame.Rect(width // 2 + 50, 190, 220, 230),
        ]
        self.owned_rects = [
            pygame.Rect(40 + index * 145, 475, 125, 105)
            for index in range(self.MAX_JOKERS)
        ]
        self.blind_rects = [
            pygame.Rect(width // 2 - 350, 205, 210, 230),
            pygame.Rect(width // 2 - 105, 205, 210, 230),
            pygame.Rect(width // 2 + 140, 205, 210, 230),
        ]

    def _generate_offers(self) -> None:
        """Genera exactamente dos ofertas de Joker independientes."""
        ante = max(1, int(self.context.get("ante", 1)))
        choices = [
            (lambda: (StoreFlatJoker("Cargador", 10 + ante * 3), 5 + ante)),
            (lambda: (StoreFlatJoker("Acumulador", 20 + ante * 4), 8 + ante * 2)),
            (lambda: (StoreMultiplierJoker("Impulso", 1.0), 7 + ante)),
            (lambda: (StoreMultiplierJoker("Potenciador", 2.0), 10 + ante * 2)),
            (lambda: (FlatChipsJoker(amount=15 + ante * 5), 6 + ante)),
            (lambda: (MultiplierJoker(amount=0.5), 8 + ante)),
        ]

        self.offers = []
        for slot in range(2):
            creator = random.choice(choices)
            joker, price = creator()
            # El precio queda guardado para poder calcular una venta posterior.
            setattr(joker, "shop_price", price)
            self.offers.append(JokerOffer(joker, price, slot))

    def _generate_blind_options(self) -> None:
        """Genera dos ciegas normales y una ciega jefe usando el ante actual."""
        ante = max(1, int(self.context.get("ante", 1)))
        base_target = 100 * ante
        blind_index = int(self.context.get("blind_index", 0))
        self.blind_options = [
            BlindOption("Ciega pequeña", base_target, ante, blind_index, False),
            BlindOption("Ciega grande", base_target + 50, ante, blind_index + 1, False),
            BlindOption("JEFE", base_target + 150, ante, 2, True),
        ]

    def handle_events(self, events: list[pygame.event.Event]) -> str | None:
        """Procesa botones, teclado y selección de ofertas/ciegas."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "MENU"
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    result = self._activate_primary_action()
                    if result:
                        return result
                elif event.key == pygame.K_r and self.phase == self.SHOP:
                    self._reroll()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                result = self._handle_mouse_click(event.pos)
                if result:
                    return result
        return None

    def _activate_primary_action(self) -> str | None:
        """Avanza de resumen a tienda, de tienda a ciegas o a la partida."""
        if self.phase == self.SUMMARY:
            self.phase = self.SHOP
            self.message = "Compra, vende o rerrollea Jokers"
            return None
        if self.phase == self.SHOP:
            self.phase = self.BLIND_SELECT
            self.message = "Selecciona la siguiente ciega"
            return None
        return self._continue_to_play()

    def _handle_mouse_click(self, position: tuple[int, int]) -> str | None:
        """Resuelve un clic según la fase actual."""
        if self.phase == self.SUMMARY:
            if self.accept_rect.collidepoint(position):
                self.phase = self.SHOP
                self.message = "Compra, vende o rerrollea Jokers"
            return None

        if self.phase == self.SHOP:
            for offer in self.offers:
                if self.offer_rects[offer.slot].collidepoint(position):
                    self._buy_offer(offer.slot)
                    return None

            for index, rect in enumerate(self.owned_rects):
                if index < len(self.jokers) and rect.collidepoint(position):
                    self.selected_owned_index = index
                    self.message = f"Seleccionado: {self.jokers[index].name}"
                    return None

            if self.sell_rect.collidepoint(position):
                self._sell_selected()
            elif self.reroll_rect.collidepoint(position):
                self._reroll()
            elif self.continue_rect.collidepoint(position):
                self.phase = self.BLIND_SELECT
                self.message = "Selecciona la siguiente ciega"
            return None

        for index, rect in enumerate(self.blind_rects):
            if rect.collidepoint(position):
                option = self.blind_options[index]
                self.context["selected_blind"] = option
                self.message = f"Seleccionada: {option.name}"
                return None

        if self.continue_rect.collidepoint(position):
            return self._continue_to_play()
        return None

    def _buy_offer(self, slot: int) -> None:
        """Compra una oferta si hay dinero y espacio disponible para Jokers."""
        if slot >= len(self.offers):
            return
        if len(self.jokers) >= self.MAX_JOKERS:
            self.message = "No puedes llevar más de 5 Jokers"
            return

        offer = self.offers[slot]
        if self.money < offer.price:
            self.message = f"Dinero insuficiente: necesitas ${offer.price}"
            return

        self.context["money"] = self.money - offer.price
        self.jokers.append(offer.joker)
        self.offers.pop(slot)
        self._reindex_offers()
        self.message = f"Compraste {offer.joker.name} por ${offer.price}"

    def _sell_selected(self) -> None:
        """Vende el Joker seleccionado por aproximadamente la mitad del precio pagado."""
        index = self.selected_owned_index
        if index is None or index >= len(self.jokers):
            self.message = "Selecciona un Joker para venderlo"
            return

        joker = self.jokers.pop(index)
        purchase_price = int(getattr(joker, "shop_price", 4))
        sell_value = max(1, purchase_price // 2)
        self.context["money"] = self.money + sell_value
        self.selected_owned_index = None
        self.message = f"Vendiste {joker.name} por ${sell_value}"

    def _reroll(self) -> None:
        """Regenera las dos ofertas descontando el coste del rerrolleo."""
        if self.money < self.REROLL_COST:
            self.message = f"Necesitas ${self.REROLL_COST} para rerrollear"
            return
        self.context["money"] = self.money - self.REROLL_COST
        self._generate_offers()
        self.message = f"Rerrolleo realizado por ${self.REROLL_COST}"

    def _reindex_offers(self) -> None:
        """Reasigna los slots visuales de las ofertas después de una compra."""
        self.offers = [
            JokerOffer(offer.joker, offer.price, index)
            for index, offer in enumerate(self.offers)
        ]

    def _continue_to_play(self) -> str:
        """Guarda la ciega elegida y devuelve la transición al PlayState."""
        selected = self.context.get("selected_blind")
        if selected is None:
            selected = self.blind_options[0]

        self.context["selected_blind"] = selected
        self.context["blind_index"] = selected.blind_index
        self.context["ante"] = selected.ante
        self.context["blind_target"] = selected.target
        self.context["blind_name"] = selected.name
        self.context["blind_is_boss"] = selected.is_boss
        return "PLAY"

    def update(self, dt: float) -> str | None:
        """Mantiene la tienda activa sin lógica por frame adicional."""
        return None

    def draw(self, screen: pygame.Surface | None = None) -> None:
        """Dibuja el resumen, la tienda o la selección de ciegas."""
        target = screen or self.screen
        target.fill((24, 32, 38))
        self._draw_header(target)
        if self.phase == self.SUMMARY:
            self._draw_summary(target)
        elif self.phase == self.SHOP:
            self._draw_shop(target)
        else:
            self._draw_blind_select(target)
        self._draw_message(target)

    def _draw_header(self, screen: pygame.Surface) -> None:
        """Dibuja el título y el dinero disponible."""
        title_font = pygame.font.SysFont("Arial", 42, bold=True)
        money_font = pygame.font.SysFont("Arial", 26, bold=True)
        screen.blit(title_font.render("TIENDA", True, (255, 215, 0)), (50, 35))
        screen.blit(
            money_font.render(f"Dinero: ${self.money}", True, (255, 255, 255)),
            (self.screen.get_width() - 230, 45),
        )

    def _draw_summary(self, screen: pygame.Surface) -> None:
        """Dibuja el desglose del dinero obtenido por la ciega."""
        reward = self.context.get("round_reward", {})
        font = pygame.font.SysFont("Arial", 30, bold=True)
        small = pygame.font.SysFont("Arial", 24)
        lines = [
            "CIEGA SUPERADA",
            f"Recompensa base: +${reward.get('base', 0)}",
            f"Manos sobrantes: +${reward.get('hands', 0)}",
            f"Descartes sobrantes: +${reward.get('discards', 0)}",
            f"Total ganado: +${reward.get('total', 0)}",
        ]
        for index, line in enumerate(lines):
            use_font = font if index in (0, 4) else small
            surface = use_font.render(line, True, (255, 255, 255))
            screen.blit(
                surface,
                surface.get_rect(center=(self.screen.get_width() // 2, 170 + index * 55)),
            )
        self._draw_button(screen, self.accept_rect, "ACEPTAR")

    def _draw_shop(self, screen: pygame.Surface) -> None:
        """Dibuja dos ofertas de Joker, Jokers propios y acciones de tienda."""
        font = pygame.font.SysFont("Arial", 22, bold=True)
        small = pygame.font.SysFont("Arial", 18)

        for slot, rect in enumerate(self.offer_rects):
            pygame.draw.rect(screen, (60, 60, 85), rect, border_radius=12)
            pygame.draw.rect(screen, (220, 220, 250), rect, width=2, border_radius=12)
            if slot < len(self.offers):
                offer = self.offers[slot]
                description = str(getattr(offer.joker, "description", "Efecto especial"))
                screen.blit(font.render(offer.joker.name, True, (255, 255, 255)), (rect.x + 18, rect.y + 30))
                screen.blit(small.render(description[:24], True, (230, 230, 230)), (rect.x + 18, rect.y + 78))
                screen.blit(small.render(f"Precio: ${offer.price}", True, (255, 215, 0)), (rect.x + 18, rect.y + 155))
            else:
                screen.blit(small.render("Vendido", True, (160, 160, 160)), (rect.x + 70, rect.y + 105))

        screen.blit(font.render("Tus Jokers", True, (255, 255, 255)), (40, 435))
        for index, rect in enumerate(self.owned_rects):
            if index >= len(self.jokers):
                break
            joker = self.jokers[index]
            color = (140, 40, 200) if index == self.selected_owned_index else (60, 60, 85)
            pygame.draw.rect(screen, color, rect, border_radius=8)
            pygame.draw.rect(screen, (220, 220, 250), rect, width=2, border_radius=8)
            screen.blit(small.render(joker.name[:14], True, (255, 255, 255)), (rect.x + 8, rect.y + 22))
            screen.blit(small.render("CLICK para vender", True, (210, 210, 210)), (rect.x + 8, rect.y + 65))

        self._draw_button(screen, self.reroll_rect, f"REROLL ${self.REROLL_COST}")
        self._draw_button(screen, self.sell_rect, "VENDER")
        self._draw_button(screen, self.continue_rect, "CONTINUAR")

    def _draw_blind_select(self, screen: pygame.Surface) -> None:
        """Dibuja dos ciegas normales y la ciega jefe."""
        font = pygame.font.SysFont("Arial", 24, bold=True)
        small = pygame.font.SysFont("Arial", 20)
        selected = self.context.get("selected_blind")
        for index, option in enumerate(self.blind_options):
            rect = self.blind_rects[index]
            color = (100, 35, 35) if option.is_boss else (45, 70, 85)
            if selected is option:
                color = (115, 100, 35)
            pygame.draw.rect(screen, color, rect, border_radius=12)
            pygame.draw.rect(screen, (240, 240, 240), rect, width=2, border_radius=12)
            screen.blit(font.render(option.name, True, (255, 255, 255)), (rect.x + 24, rect.y + 35))
            screen.blit(small.render(f"Objetivo: {option.target}", True, (230, 230, 230)), (rect.x + 24, rect.y + 95))
            screen.blit(small.render("Jefe" if option.is_boss else "Normal", True, (255, 190, 190) if option.is_boss else (190, 220, 230)), (rect.x + 24, rect.y + 135))
        self._draw_button(screen, self.continue_rect, "JUGAR")

    def _draw_message(self, screen: pygame.Surface) -> None:
        """Dibuja el mensaje contextual de la tienda."""
        font = pygame.font.SysFont("Arial", 18)
        surface = font.render(self.message, True, (225, 225, 225))
        screen.blit(surface, (50, self.screen.get_height() - 30))

    @staticmethod
    def _draw_button(screen: pygame.Surface, rect: pygame.Rect, text: str) -> None:
        """Dibuja un botón reutilizable con texto centrado."""
        pygame.draw.rect(screen, (55, 55, 70), rect, border_radius=8)
        pygame.draw.rect(screen, (220, 220, 220), rect, width=2, border_radius=8)
        font = pygame.font.SysFont("Arial", 18, bold=True)
        surface = font.render(text, True, (255, 255, 255))
        screen.blit(surface, surface.get_rect(center=rect.center))
