"""Animaciones visuales de las jugadas del tablero."""

from __future__ import annotations

import pygame

from entities import CardEntity
from entities.entities import RANK_VALUES


class PlayAnimation:
	"""Mueve las cartas jugadas al centro y muestra su valor individual."""

	ENTRY_DURATION = 0.45
	EXIT_DURATION = 0.75

	def __init__(self):
		self.cards: list[CardEntity] = []
		self.start_positions: list[tuple[float, float]] = []
		self.elapsed = 0.0
		self.result_name = ""
		self.total = 0
		self.phase = "inactive"

	@property
	def active(self) -> bool:
		return bool(self.cards) and self.phase != "finished"

	def start(
		self,
		cards: list[CardEntity],
		start_positions: list[tuple[float, float]],
		result_name: str,
		total: int,
	) -> None:
		self.cards = list(cards)
		self.start_positions = list(start_positions)
		self.elapsed = 0.0
		self.result_name = result_name
		self.total = total
		self.phase = "entering"

	def cancel(self) -> None:
		self.cards = []
		self.start_positions = []
		self.elapsed = 0.0
		self.phase = "inactive"

	def handle_event(self, event) -> None:
		"""Inicia la salida cuando el jugador confirma con SPACE."""
		if (
			self.active
			and self.phase == "holding"
			and event.type == pygame.KEYDOWN
			and event.key == pygame.K_SPACE
		):
			self.phase = "exiting"
			self.elapsed = 0.0

	def update(self, dt: float) -> None:
		if not self.active:
			return

		self.elapsed += max(0.0, dt)
		if self.phase == "entering" and self.elapsed >= self.ENTRY_DURATION:
			self.phase = "holding"
			self.elapsed = 0.0
		elif self.phase == "exiting" and self.elapsed >= self.EXIT_DURATION:
			self.phase = "finished"
			self.cards = []
			self.start_positions = []

	def draw(self, renderer, screen) -> None:
		if not self.active:
			return

		if self.phase == "entering":
			progress = min(1.0, self.elapsed / self.ENTRY_DURATION)
		elif self.phase == "exiting":
			progress = min(1.0, self.elapsed / self.EXIT_DURATION)
		else:
			progress = 1.0
		eased = progress * progress * (3.0 - 2.0 * progress)
		card_width = 90
		spacing = 95
		center_x = screen.get_width() // 2
		center_y = screen.get_height() // 2 - 45
		target_start_x = center_x - ((len(self.cards) - 1) * spacing + card_width) // 2

		for index, card in enumerate(self.cards):
			start_x, start_y = self.start_positions[index]
			center_card_x = target_start_x + index * spacing
			if self.phase == "exiting":
				target_x = screen.get_width() + card_width + index * spacing
				target_y = center_y
				origin_x = center_card_x
				origin_y = center_y
			else:
				target_x = center_card_x
				target_y = center_y
				origin_x = start_x
				origin_y = start_y
			x = int(origin_x + (target_x - origin_x) * eased)
			y = int(origin_y + (target_y - origin_y) * eased)
			renderer.draw_card(card.to_dict(), x, y)

			value = RANK_VALUES.get(card.rank, card.rank)
			font = pygame.font.SysFont("Arial", 24, bold=True)
			label = font.render(f"+{value}", True, (255, 225, 80))
			label_rect = label.get_rect(center=(x + card_width // 2, y - 12))
			screen.blit(label, label_rect)

		title_font = pygame.font.SysFont("Arial", 28, bold=True)
		title = title_font.render(
			f"{self.result_name}  |  +{self.total} puntos",
			True,
			(255, 255, 255),
		)
		screen.blit(title, title.get_rect(center=(center_x, center_y - 90)))


class RefillAnimation:
	"""Introduce cartas nuevas desde la esquina inferior derecha."""

	DURATION = 0.65
	CARD_WIDTH = 90

	def __init__(self):
		self.cards: list[CardEntity] = []
		self.target_positions: list[tuple[float, float]] = []
		self.elapsed = 0.0

	@property
	def active(self) -> bool:
		return bool(self.cards)

	def start(
		self,
		cards: list[CardEntity],
		target_positions: list[tuple[float, float]],
	) -> None:
		self.cards = list(cards)
		self.target_positions = list(target_positions)
		self.elapsed = 0.0

		if len(self.cards) != len(self.target_positions):
			self.cancel()

	def cancel(self) -> None:
		self.cards = []
		self.target_positions = []
		self.elapsed = 0.0

	def update(self, dt: float) -> None:
		if not self.active:
			return

		self.elapsed += max(0.0, dt)
		if self.elapsed >= self.DURATION:
			self.cancel()

	def draw(self, renderer, screen) -> None:
		if not self.active:
			return

		progress = min(1.0, self.elapsed / self.DURATION)
		eased = progress * progress * (3.0 - 2.0 * progress)
		start_x = screen.get_width() + self.CARD_WIDTH

		for index, (card, (target_x, target_y)) in enumerate(
			zip(self.cards, self.target_positions)
		):
			# Todas las cartas conservan su Y final: el movimiento es horizontal.
			card_start_x = start_x + index * self.CARD_WIDTH
			x = int(card_start_x + (target_x - card_start_x) * eased)
			renderer.draw_card(card.to_dict(), x, int(target_y))


class AnimationController:
	"""Punto de entrada único para las animaciones visuales del juego."""

	def __init__(self):
		self.play_cards_animation = PlayAnimation()
		self.refill_animation = RefillAnimation()
		self.pending_refill: tuple[list[CardEntity], list[tuple[float, float]]] | None = None

	@property
	def active(self) -> bool:
		return self.play_cards_animation.active or self.refill_animation.active

	def play_cards(
		self,
		cards: list[CardEntity],
		start_positions: list[tuple[float, float]],
		result_name: str,
		total: int,
	) -> None:
		self.play_cards_animation.start(cards, start_positions, result_name, total)

	def refill_cards(
		self,
		cards: list[CardEntity],
		target_positions: list[tuple[float, float]],
	) -> None:
		# La reposicion espera a que las cartas jugadas terminen de salir.
		if self.play_cards_animation.active:
			self.pending_refill = (list(cards), list(target_positions))
		else:
			self.refill_animation.start(cards, target_positions)

	@property
	def hidden_card_ids(self) -> set[int]:
		"""Identidades de cartas que no debe dibujar la mano normal."""
		hidden_cards = {id(card) for card in self.refill_animation.cards}
		if self.pending_refill is not None:
			hidden_cards.update(id(card) for card in self.pending_refill[0])
		return hidden_cards

	def cancel(self) -> None:
		self.play_cards_animation.cancel()
		self.refill_animation.cancel()
		self.pending_refill = None

	def handle_event(self, event) -> None:
		self.play_cards_animation.handle_event(event)

	def update(self, dt: float) -> None:
		was_play_active = self.play_cards_animation.active
		self.play_cards_animation.update(dt)
		refill_started = False
		if was_play_active and not self.play_cards_animation.active:
			if self.pending_refill is not None:
				cards, target_positions = self.pending_refill
				self.refill_animation.start(cards, target_positions)
				self.pending_refill = None
				refill_started = True
		if not refill_started:
			self.refill_animation.update(dt)

	def draw(self, renderer, screen) -> None:
		self.play_cards_animation.draw(renderer, screen)
		self.refill_animation.draw(renderer, screen)
