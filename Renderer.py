"""Renderer de la interfaz de cartas.

Puede reutilizar la superficie Pygame creada por main.py para evitar
reinicializaciones de display.
"""
import pygame

COLOR_BG = (24, 32, 38)
COLOR_PANEL_BG = (15, 20, 25)
COLOR_CARD_BG = (240, 240, 240)
COLOR_CARD_BORDER = (180, 50, 50)
COLOR_SELECTED = (255, 215, 0)
COLOR_JOKER_BG = (60, 60, 85)
COLOR_JOKER_ACTIVE = (140, 40, 200)
COLOR_TEXT_MAIN = (255, 255, 255)
COLOR_TEXT_DARK = (20, 20, 20)
COLOR_CHIPS = (80, 160, 255)
COLOR_MULT = (255, 80, 80)


class Renderer:
    """Clase principal de dibujado optimizada con cache de textos."""

    def __init__(self, screen_width=1280, screen_height=720, screen=None):
        pygame.font.init()
        self.width = screen_width
        self.height = screen_height
        self.screen = screen if screen is not None else pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Mesa de Juego - Estilo Balatro")

        self.font_main = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 36, bold=True)
        self._cache_score_val = None
        self._cache_score_surf = None
        self._cache_target_val = None
        self._cache_target_surf = None
        self._cache_chips_val = None
        self._cache_chips_surf = None
        self._cache_mult_val = None
        self._cache_mult_surf = None
        self._cache_stats_val = None
        self._cache_stats_surf = None
        self._card_text_cache = {}

    def clear(self):
        self.screen.fill(COLOR_BG)

    def draw_card(self, card_data, x, y, scale=1.0, is_selected=False):
        base_w, base_h = 90, 130
        w = int(base_w * scale)
        h = int(base_h * scale)
        offset_y = -20 if is_selected else 0
        card_rect = pygame.Rect(x, y + offset_y, w, h)
        shadow_rect = pygame.Rect(x + 3, y + offset_y + 3, w, h)
        pygame.draw.rect(self.screen, (10, 10, 15), shadow_rect, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_CARD_BG, card_rect, border_radius=6)
        border_color = COLOR_SELECTED if is_selected else COLOR_CARD_BORDER
        pygame.draw.rect(self.screen, border_color, card_rect, width=2, border_radius=6)

        rank = card_data.get("rank", "")
        suit = card_data.get("suit", "")
        card_key = (rank, suit)
        if card_key not in self._card_text_cache:
            self._card_text_cache[card_key] = self.font_main.render(f"{rank}{suit}", True, COLOR_TEXT_DARK)
        self.screen.blit(self._card_text_cache[card_key], (x + 8, y + offset_y + 8))

    def draw_joker(self, joker_data, x, y, is_active=False):
        rect = pygame.Rect(x, y, 80, 110)
        bg_color = COLOR_JOKER_ACTIVE if is_active else COLOR_JOKER_BG
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=8)
        pygame.draw.rect(self.screen, (220, 220, 250), rect, width=2, border_radius=8)
        name_str = joker_data.get("name", "Joker")[:8]
        txt_surface = self.font_main.render(name_str, True, COLOR_TEXT_MAIN)
        self.screen.blit(txt_surface, (x + 5, y + 40))

    def draw_consumable(self, item_data, x, y):
        rect = pygame.Rect(x, y, 65, 95)
        pygame.draw.rect(self.screen, (30, 120, 100), rect, border_radius=6)
        pygame.draw.rect(self.screen, (200, 240, 220), rect, width=2, border_radius=6)

    def draw_hud_panel(self, score, target, mult, chips, hands, discards):
        panel_rect = pygame.Rect(20, 20, 240, self.height - 40)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel_rect, border_radius=10)
        if target != self._cache_target_val:
            self._cache_target_val = target
            self._cache_target_surf = self.font_main.render(f"Objetivo: {target}", True, (250, 200, 50))
        if score != self._cache_score_val:
            self._cache_score_val = score
            self._cache_score_surf = self.font_big.render(f"{score}", True, COLOR_TEXT_MAIN)
        if chips != self._cache_chips_val:
            self._cache_chips_val = chips
            self._cache_chips_surf = self.font_main.render(f"Fichas: {chips}", True, COLOR_CHIPS)
        if mult != self._cache_mult_val:
            self._cache_mult_val = mult
            self._cache_mult_surf = self.font_main.render(f"Mult: X{mult}", True, COLOR_MULT)
        stats_tuple = (hands, discards)
        if stats_tuple != self._cache_stats_val:
            self._cache_stats_val = stats_tuple
            self._cache_stats_surf = self.font_main.render(f"Manos: {hands} | Desc: {discards}", True, (200, 200, 200))
        self.screen.blit(self._cache_target_surf, (35, 40))
        self.screen.blit(self._cache_score_surf, (35, 75))
        self.screen.blit(self._cache_chips_surf, (35, 140))
        self.screen.blit(self._cache_mult_surf, (35, 175))
        self.screen.blit(self._cache_stats_surf, (35, 230))

    def draw_joker_bar(self, jokers_list):
        start_x = 300
        for i, joker in enumerate(jokers_list):
            self.draw_joker(joker, start_x + i * 90, 30, is_active=joker.get("active", False))

    def draw_consumables_bar(self, consumables_list):
        start_x = 980
        for i, item in enumerate(consumables_list):
            self.draw_consumable(item, start_x + i * 75, 30)

    def draw_hand(self, cards_list):
        spacing = 95
        start_x = (self.width - (len(cards_list) * spacing)) // 2 + 100
        start_y = self.height - 160
        for i, card in enumerate(cards_list):
            pos_x = start_x + i * spacing
            self.draw_card(card, pos_x, start_y, is_selected=card.get("selected", False))

    def present(self):
        pygame.display.flip()
