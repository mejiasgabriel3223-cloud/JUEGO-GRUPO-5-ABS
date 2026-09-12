"""
Módulo: gameover_state.py
Descripción: Estado de fin de juego (Game Over) ultra-seguro contra cierres.
"""

import json
from pathlib import Path
import pygame
from audio import get_audio_manager

BASE_DIR = Path(__file__).resolve().parent.parent


class GameOverState:
    """Estado que se activa al perder la partida."""

    def __init__(self, screen, context=None):
        self.screen = screen
        self.context = context if context is not None else {}
        self.audio = get_audio_manager()
        self.records_file = BASE_DIR / "records.json"

        self.score = 0
        self.player_name = "Jugador"
        self.fuentes = {}

    def obtener_fuente(self, tamano):
        """Gestiona la carga de la fuente de forma segura sin depender de módulos externos."""
        if tamano not in self.fuentes:
            # Garantizar que el módulo de fuentes de Pygame esté activo
            if not pygame.font.get_init():
                pygame.font.init()
            
            # Intenta usar la fuente del sistema o la predeterminada
            try:
                self.fuentes[tamano] = pygame.font.SysFont("Arial", tamano, bold=True)
            except Exception:
                self.fuentes[tamano] = pygame.font.Font(None, tamano)
                
        return self.fuentes[tamano]

    def enter(self):
        """Se ejecuta al entrar al Game Over."""
        self.audio.stop_music()
        try:
            self.score = self.context.get("score", 0) if self.context else 0
            self.player_name = self.context.get("player_name", "Jugador") if self.context else "Jugador"
            self._guardar_record()
        except Exception as e:
            print(f"Error en enter() de GameOverState: {e}")

    def exit(self):
        """Reinicia el acumulado del context al salir."""
        if self.context:
            self.context["score"] = 0
            self.context["round"] = 1

    def _guardar_record(self):
        """Guarda o actualiza el puntaje en el JSON sin interrumpir el juego si falla."""
        try:
            records = []
            if self.records_file.exists():
                try:
                    with open(self.records_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        records = data if isinstance(data, list) else []
                except Exception:
                    records = []

            existente = [r for r in records if str(r.get("name", "")).lower() == str(self.player_name).lower()]
            if existente:
                if self.score > existente[0].get("score", 0):
                    existente[0]["score"] = self.score
            else:
                records.append({"name": self.player_name, "score": self.score})

            records = sorted(records, key=lambda x: x.get("score", 0), reverse=True)

            self.records_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.records_file, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando records.json (ignorado para evitar cierre): {e}")

    def handle_events(self, events):
        """Maneja las entradas del teclado para reintentar o ir al menú."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_r):
                    return "PLAY"
                elif event.key == pygame.K_ESCAPE:
                    return "MENU"
        return None

    def update(self, dt=0):
        return None

    def draw(self, screen=None):
        """Renderiza la pantalla de Game Over."""
        target = screen if screen is not None else self.screen
        if target is None:
            return

        target.fill((15, 10, 20))
        centro_x = target.get_width() // 2

        # 1. Título
        fuente_titulo = self.obtener_fuente(60)
        render_titulo = fuente_titulo.render("GAME OVER", True, (220, 40, 40))
        target.blit(render_titulo, render_titulo.get_rect(center=(centro_x, 160)))

        # 2. Datos del jugador
        fuente_info = self.obtener_fuente(30)
        render_nombre = fuente_info.render(f"Jugador: {self.player_name}", True, (240, 240, 240))
        render_score = fuente_info.render(f"Puntaje Acumulado: {self.score}", True, (255, 215, 0))
        
        target.blit(render_nombre, render_nombre.get_rect(center=(centro_x, 260)))
        target.blit(render_score, render_score.get_rect(center=(centro_x, 310)))

        # 3. Navegación
        fuente_sub = self.obtener_fuente(22)
        render_reintentar = fuente_sub.render("Presiona ENTER o R para Reintentar", True, (200, 200, 200))
        render_menu = fuente_sub.render("Presiona ESC para volver al Menú Principal", True, (140, 140, 140))
        
        target.blit(render_reintentar, render_reintentar.get_rect(center=(centro_x, 440)))
        target.blit(render_menu, render_menu.get_rect(center=(centro_x, 485)))