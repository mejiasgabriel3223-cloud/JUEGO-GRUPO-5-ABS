import json
from pathlib import Path

import pygame

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None

from menu.gestor_config import GestorConfig
from menu.pantallas_menu import PantallaPrincipal, PantallaInputNombre, PantallaRecords, PantallaPromptRecord

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGENES_DIR = BASE_DIR / "assets"


class EstadoMenu:
    @staticmethod
    def _es_video(ruta):
        if not ruta:
            return False
        return str(ruta).lower().endswith((".mp4", ".avi", ".mov", ".webm"))

    @staticmethod
    def _fondo_por_defecto(pantalla):
        fondo = pygame.Surface(pantalla.get_size())
        fondo.fill((20, 40, 80))
        return fondo

    @staticmethod
    def _ajustar_fondo(surface, pantalla):
        if surface is None:
            return None

        target_w, target_h = pantalla.get_size()
        surface = surface.copy()
        src_w, src_h = surface.get_size()
        if src_w <= 0 or src_h <= 0:
            return surface

        scale = max(target_w / src_w, target_h / src_h)
        new_w = max(1, int(src_w * scale))
        new_h = max(1, int(src_h * scale))
        escalado = pygame.transform.smoothscale(surface, (new_w, new_h))

        canvas = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
        canvas.blit(escalado, escalado.get_rect(center=(target_w // 2, target_h // 2)))
        return canvas

    def _abrir_video(self, ruta):
        if cv2 is None:
            return None
        if not Path(ruta).exists():
            return None

        video = cv2.VideoCapture(ruta)
        if not video.isOpened():
            return None
        return video

    def __init__(self, pantalla):
        self.pantalla = pantalla
        self.config = GestorConfig.cargar_configuracion()
        self.senal_salida = None
        self.player_name = "Jugador"
        self.video = None
        self.video_frame = None

        # Sistema de Records
        self.records_file = BASE_DIR / "records.json"
        self.records = self._cargar_records()
        self.pending_score = None
        self.pending_name = None
        self.pending_old_score = None

        # Cargar recursos base
        recursos = self.config.get("recursos", {})
        ruta_fondo = GestorConfig.resolver_ruta(recursos.get("fondo", ""))

        self.fondo = None
        try:
            if ruta_fondo:
                if self._es_video(ruta_fondo):
                    self.video = self._abrir_video(ruta_fondo)
                    if self.video is None:
                        self.fondo = self._fondo_por_defecto(pantalla)
                else:
                    try:
                        self.fondo = pygame.image.load(ruta_fondo).convert()
                    except Exception:
                        self.fondo = self._fondo_por_defecto(pantalla)
        except Exception:
            self.fondo = self._fondo_por_defecto(pantalla)

        if self.fondo is not None:
            self.fondo = self._ajustar_fondo(self.fondo, pantalla)
        if self.video is None and self.fondo is None:
            self.fondo = self._fondo_por_defecto(pantalla)

        # Animaciones desactivadas temporalmente para evitar bloqueos
        self.animacion_jake = None
        self.animacion_finn = None

        # Diccionario de Pantallas Modulares
        self.pantallas = {
            "PRINCIPAL": PantallaPrincipal(self, self.config),
            "NAME_INPUT": PantallaInputNombre(self, self.config),
            "RECORDS": PantallaRecords(self, self.config),
            "REPLACE_PROMPT": PantallaPromptRecord(self, self.config)
        }
        self.estado_actual = "PRINCIPAL"

    def cambiar_estado(self, nombre_estado):
        if nombre_estado in self.pantallas:
            self.estado_actual = nombre_estado

    def _cargar_records(self):
        if not self.records_file.exists(): return []
        try:
            with open(self.records_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except: return []

    def _guardar_records(self):
        ordenados = sorted(self.records, key=lambda x: x.get("score", 0), reverse=True)
        self.records = ordenados
        with open(self.records_file, "w", encoding="utf-8") as f:
            json.dump(ordenados, f, indent=2, ensure_ascii=False)

    def finalizar_partida(self, score, player_name):
        if not player_name: return
        self.pending_score = score
        self.pending_name = player_name.strip() or "Jugador"
        self.records = self._cargar_records()

        existente = [e for e in self.records if str(e.get("name", "")).lower() == self.pending_name.lower()]
        if not existente:
            self.records.append({"name": self.pending_name, "score": score})
            self._guardar_records()
            self.cambiar_estado("PRINCIPAL")
            return

        self.pending_old_score = max(e.get("score", 0) for e in existente)
        self.cambiar_estado("REPLACE_PROMPT")

    def aplicar_prompt_record(self, reemplazar):
        if reemplazar:
            self.records = [e for e in self.records if str(e.get("name", "")).lower() != self.pending_name.lower()]
            self.records.append({"name": self.pending_name, "score": self.pending_score})
        else:
            self.records.append({"name": self.pending_name, "score": self.pending_score})

        self._guardar_records()
        self.cambiar_estado("PRINCIPAL")

    def manejar_eventos(self, eventos):
        self.pantallas[self.estado_actual].manejar_eventos(eventos)
        if self.senal_salida:
            res = self.senal_salida
            self.senal_salida = None
            return res
        return None

    def actualizar(self):
        if self.video is not None:
            try:
                ok, frame = self.video.read()
                if ok and frame is not None:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_surface = pygame.image.frombuffer(frame.tobytes(), (frame.shape[1], frame.shape[0]), "RGB")
                    self.video_frame = self._ajustar_fondo(frame_surface, self.pantalla)
                else:
                    self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            except Exception:
                pass
        self.pantallas[self.estado_actual].actualizar()

    def dibujar(self):
        if self.video_frame is not None:
            self.pantalla.blit(self.video_frame, (0, 0))
        elif self.fondo:
            self.pantalla.blit(self.fondo, (0, 0))
        self.pantallas[self.estado_actual].dibujar(self.pantalla)