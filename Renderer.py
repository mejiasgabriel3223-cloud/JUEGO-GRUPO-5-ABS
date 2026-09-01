"""
Módulo: renderer.py
Descripción: Encargado exclusivamente de la representación gráfica 2D del juego.
            Implementa un enfoque pasivo e independiente con optimización
            de Render/Text Caching para evitar regenerar imágenes de fuentes
            en cada frame.
"""

import pygame

# -----------------------------------------------------------------------------
# PALETA DE COLORES (Estilo mesa de cartas / Balatro)
# -----------------------------------------------------------------------------
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
    """Clase principal de dibujado optimizada con Caché de Textos."""

    def __init__(self, screen_width=1280, screen_height=720):
        """Inicializa Pygame, crea la ventana principal, carga fuentes y configura
        las variables de caché de superficies de texto.
        """
        pygame.init()
        pygame.font.init()

        self.width = screen_width
        self.height = screen_height

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Mesa de Juego - Estilo Balatro")

        self.font_main = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 36, bold=True)

        # ---------------------------------------------------------------------
        # VARIABLES DE CACHÉ DE TEXTO (Para evitar font.render a 60 FPS)
        # Guardan el último valor recibido y la superficie pre-renderizada en RAM.
        # ---------------------------------------------------------------------
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

        # Caché para nombres de cartas (evita re-renderizar texto dentro de la mano)
        # Formato de diccionario: {(rank, suit): pygame.Surface}
        self._card_text_cache = {}

    def clear(self):
        """Limpia todo el canvas rellenándolo con el color base del fondo."""
        self.screen.fill(COLOR_BG)

    # =========================================================================
    # COMPONENTES ATÓMICOS (Dibujo de elementos individuales)
    # =========================================================================

    def draw_card(self, card_data, x, y, scale=1.0, is_selected=False):
        """Dibuja una carta individual en la pantalla utilizando caché para el
        texto.
        """
        base_w, base_h = 90, 130
        w = int(base_w * scale)
        h = int(base_h * scale)

        offset_y = -20 if is_selected else 0
        card_rect = pygame.Rect(x, y + offset_y, w, h)

        # 1. Sombra
        shadow_rect = pygame.Rect(x + 3, y + offset_y + 3, w, h)
        pygame.draw.rect(self.screen, (10, 10, 15), shadow_rect, border_radius=6)

        # 2. Fondo de la carta
        pygame.draw.rect(self.screen, COLOR_CARD_BG, card_rect, border_radius=6)

        # 3. Borde
        border_color = COLOR_SELECTED if is_selected else COLOR_CARD_BORDER
        pygame.draw.rect(
            self.screen, border_color, card_rect, width=2, border_radius=6
        )

        # 4. Obtención / Creación de texto mediante Caché
        rank = card_data.get("rank", "")
        suit = card_data.get("suit", "")
        card_key = (rank, suit)

        # Si el texto de esta carta exacta no ha sido renderizado antes, se crea y guarda
        if card_key not in self._card_text_cache:
            label = f"{rank}{suit}"
            self._card_text_cache[card_key] = self.font_main.render(
                label, True, COLOR_TEXT_DARK
            )

        # Dibuja la superficie de texto reutilizada
        txt_surface = self._card_text_cache[card_key]
        self.screen.blit(txt_surface, (x + 8, y + offset_y + 8))

    def draw_joker(self, joker_data, x, y, is_active=False):
        """Renderiza una carta de Comodín / Joker."""
        rect = pygame.Rect(x, y, 80, 110)
        bg_color = COLOR_JOKER_ACTIVE if is_active else COLOR_JOKER_BG

        pygame.draw.rect(self.screen, bg_color, rect, border_radius=8)
        pygame.draw.rect(
            self.screen, (220, 220, 250), rect, width=2, border_radius=8
        )

        name_str = joker_data.get("name", "Joker")[:5]
        # Nota: Los Jokers se pueden cachear igual si sus nombres son estáticos
        txt_surface = self.font_main.render(name_str, True, COLOR_TEXT_MAIN)
        self.screen.blit(txt_surface, (x + 5, y + 40))

    def draw_consumable(self, item_data, x, y):
        """Renderiza un consumible (Tarot o Planeta)."""
        rect = pygame.Rect(x, y, 65, 95)
        pygame.draw.rect(self.screen, (30, 120, 100), rect, border_radius=6)
        pygame.draw.rect(
            self.screen, (200, 240, 220), rect, width=2, border_radius=6
        )

    # =========================================================================
    # ENSAMBLADORES DE INTERFAZ Y ZONAS (Con Caché de Superficies)
    # =========================================================================

    def draw_hud_panel(self, score, target, mult, chips, hands, discards):
        """Dibuja el panel lateral con comprobación de caché para cada indicador.

        font.render() solo se ejecuta si el dato recibido cambia respecto al
        frame anterior.
        """
        panel_rect = pygame.Rect(20, 20, 240, self.height - 40)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel_rect, border_radius=10)

        # --- CACHÉ: OBJETIVO ---
        if target != self._cache_target_val:
            self._cache_target_val = target
            self._cache_target_surf = self.font_main.render(
                f"Objetivo: {target}", True, (250, 200, 50)
            )

        # --- CACHÉ: PUNTAJE ACTUAL ---
        if score != self._cache_score_val:
            self._cache_score_val = score
            self._cache_score_surf = self.font_big.render(
                f"{score}", True, COLOR_TEXT_MAIN
            )

        # --- CACHÉ: FICHAS ---
        if chips != self._cache_chips_val:
            self._cache_chips_val = chips
            self._cache_chips_surf = self.font_main.render(
                f"Fichas: {chips}", True, COLOR_CHIPS
            )

        # --- CACHÉ: MULTIPLICADOR ---
        if mult != self._cache_mult_val:
            self._cache_mult_val = mult
            self._cache_mult_surf = self.font_main.render(
                f"Mult: X{mult}", True, COLOR_MULT
            )

        # --- CACHÉ: MANOS Y DESCARTES ---
        stats_tuple = (hands, discards)
        if stats_tuple != self._cache_stats_val:
            self._cache_stats_val = stats_tuple
            self._cache_stats_surf = self.font_main.render(
                f"Manos: {hands} | Desc: {discards}", True, (200, 200, 200)
            )

        # Operaciones BLIT (Ultra rápidas en Pygame, sin costo de reconstrucción por CPU)
        self.screen.blit(self._cache_target_surf, (35, 40))
        self.screen.blit(self._cache_score_surf, (35, 75))
        self.screen.blit(self._cache_chips_surf, (35, 140))
        self.screen.blit(self._cache_mult_surf, (35, 175))
        self.screen.blit(self._cache_stats_surf, (35, 230))

    def draw_joker_bar(self, jokers_list):
        """Dibuja la barra superior donde se alojan los Jokers equipados."""
        start_x = 300
        y = 30

        for i, joker in enumerate(jokers_list):
            pos_x = start_x + (i * 90)
            is_active = joker.get("active", False)
            self.draw_joker(joker, pos_x, y, is_active=is_active)

    def draw_consumables_bar(self, consumables_list):
        """Dibuja el espacio superior derecho para guardar consumibles."""
        start_x = 980
        y = 30

        for i, item in enumerate(consumables_list):
            pos_x = start_x + (i * 75)
            self.draw_consumable(item, pos_x, y)

    def draw_hand(self, cards_list):
        """Renderiza la mano de cartas centrada horizontalmente."""
        spacing = 95
        start_x = (self.width - (len(cards_list) * spacing)) // 2 + 100
        start_y = self.height - 160

        for i, card in enumerate(cards_list):
            pos_x = start_x + (i * spacing)
            is_selected = card.get("selected", False)
            self.draw_card(card, pos_x, start_y, is_selected=is_selected)

    def present(self):
        """Envía el buffer renderizado a la ventana principal."""
        pygame.display.flip()