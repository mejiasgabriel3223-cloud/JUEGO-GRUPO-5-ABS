"""
Módulo: menu_state.py
Descripción: Estado de Menú consolidado y autónomo.
             Usa fondo de video (assets/fondo_menu.mp4) y logo (assets/titulo.png).
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
import pygame
from audio import get_audio_manager

try:
    import cv2
except Exception:
    cv2 = None

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
CONFIG_DIR = BASE_DIR / "menu"


# =====================================================================
# GESTOR DE CONFIGURACIÓN
# =====================================================================

class GestorConfig:
    """Gestiona rutas y carga la configuración JSON con un fallback por defecto."""

    @staticmethod
    def cargar_configuracion():
        ruta_json = CONFIG_DIR / "menu_config.json"
        
        config_defecto = {
            "opciones_principal": [
                {"texto": "JUGAR", "accion": "JUGAR", "ancho": 180, "alto": 70},
                {"texto": "RECORDS", "accion": "PANTALLA_RECORDS", "ancho": 180, "alto": 70},
                {"texto": "SALIR", "accion": "SALIR", "ancho": 180, "alto": 70}
            ]
        }

        if not ruta_json.exists():
            return config_defecto

        try:
            with open(ruta_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not data.get("opciones_principal"):
                    data["opciones_principal"] = config_defecto["opciones_principal"]
                return data
        except Exception as e:
            print(f"Advertencia cargando {ruta_json}: {e}. Usando configuración por defecto.")
            return config_defecto


# =====================================================================
# PANTALLAS DEL MENÚ
# =====================================================================

class PantallaBase(ABC):
    """Clase base para subpantallas del menú."""

    def __init__(self, gestor_estado, config):
        self.gestor_estado = gestor_estado
        self.config = config
        self.fuentes = {}

    def obtener_fuente(self, tamano):
        if tamano not in self.fuentes:
            if not pygame.font.get_init():
                pygame.font.init()
            try:
                from settings import load_game_font
                self.fuentes[tamano] = load_game_font(tamano)
            except Exception:
                self.fuentes[tamano] = pygame.font.Font(None, tamano)
        return self.fuentes[tamano]

    def dibujar_texto_centrado(self, pantalla, texto, y, tamano, color):
        fuente = self.obtener_fuente(tamano)
        render = fuente.render(texto, True, color)
        rect = render.get_rect(center=(pantalla.get_width() // 2, y))
        pantalla.blit(render, rect)

    @abstractmethod
    def manejar_eventos(self, eventos):
        pass

    @abstractmethod
    def dibujar(self, pantalla):
        pass

    def actualizar(self):
        pass


class PantallaPrincipal(PantallaBase):
    """Pantalla inicial con botones interactivos."""

    def __init__(self, gestor_estado, config):
        super().__init__(gestor_estado, config)
        self.opciones = self.config.get("opciones_principal", [])
        self.indice_seleccionado = 0
        self.logo = None

        ruta_logo = ASSETS_DIR / "titulo.png"
        if ruta_logo.exists():
            try:
                img_original = pygame.image.load(str(ruta_logo)).convert_alpha()
                # Escalar el logo proporcionalmente (ejemplo: ancho máximo de 450px)
                ancho_max = 450
                ratio = ancho_max / img_original.get_width()
                alto_nuevo = int(img_original.get_height() * ratio)
                
                self.logo = pygame.transform.smoothscale(img_original, (ancho_max, alto_nuevo))
            except Exception as e:
                print(f"Error al cargar titulo.png: {e}")
                self.logo = None

    def _calcular_botones(self, pantalla):
        if pantalla is None or not self.opciones:
            return []

        centro_x = pantalla.get_width() // 2
        y_base = pantalla.get_height() - 90
        total = len(self.opciones)
        espacio = 210
        botones = []

        for index, opcion in enumerate(self.opciones):
            x = centro_x + (index - (total - 1) / 2) * espacio
            ancho = int(opcion.get("ancho", 180))
            alto = int(opcion.get("alto", 70))
            rect = pygame.Rect(0, 0, ancho, alto)
            rect.center = (x, y_base)
            botones.append((opcion, rect))

        return botones

    def manejar_eventos(self, eventos):
        pantalla = self.gestor_estado.pantalla
        botones = self._calcular_botones(pantalla)

        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_LEFT, pygame.K_a):
                    self.indice_seleccionado = (self.indice_seleccionado - 1) % len(self.opciones)
                elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                    self.indice_seleccionado = (self.indice_seleccionado + 1) % len(self.opciones)
                elif evento.key in (pygame.K_UP, pygame.K_w):
                    self.indice_seleccionado = (self.indice_seleccionado - 1) % len(self.opciones)
                elif evento.key in (pygame.K_DOWN, pygame.K_s):
                    self.indice_seleccionado = (self.indice_seleccionado + 1) % len(self.opciones)
                elif evento.key == pygame.K_RETURN:
                    self._ejecutar_accion()
            elif evento.type == pygame.MOUSEMOTION:
                for index, (_, rect) in enumerate(botones):
                    if rect.collidepoint(evento.pos):
                        self.indice_seleccionado = index
                        break
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                for index, (_, rect) in enumerate(botones):
                    if rect.collidepoint(evento.pos):
                        self.indice_seleccionado = index
                        self._ejecutar_accion()
                        break

    def _ejecutar_accion(self):
        if not self.opciones:
            return
        accion = self.opciones[self.indice_seleccionado].get("accion")
        if accion == "JUGAR":
            self.gestor_estado.cambiar_estado("NAME_INPUT")
        elif accion == "SALIR":
            self.gestor_estado.senal_salida = "SALIR"
        elif accion == "PANTALLA_RECORDS":
            self.gestor_estado.cambiar_estado("RECORDS")
        elif accion == "PANTALLA_TEXTO":
            opcion = self.opciones[self.indice_seleccionado]
            self.gestor_estado.pantallas["INFO_DINAMICA"] = PantallaTexto(
                self.gestor_estado, self.config, opcion.get("texto"), opcion.get("contenido", [])
            )
            self.gestor_estado.cambiar_estado("INFO_DINAMICA")

    def dibujar(self, pantalla):
        if self.logo:
            # Centrado en el eje X y ubicado perfectamente en el espacio superior
            rect_titulo = self.logo.get_rect(center=(pantalla.get_width() // 2, pantalla.get_height() // 2 - 80))
            pantalla.blit(self.logo, rect_titulo)
        else:
            self.dibujar_texto_centrado(pantalla, "CARD TRICK", 140, 72, (255, 255, 255))

        botones = self._calcular_botones(pantalla)
        for index, (opcion, rect) in enumerate(botones):
            seleccionado = self.indice_seleccionado == index
            
            color_texto = opcion.get("color_seleccionado", [255, 255, 255]) if seleccionado else opcion.get("color_normal", [200, 200, 200])
            color_fondo = opcion.get("fondo_seleccionado", [40, 40, 40, 200]) if seleccionado else opcion.get("fondo_normal", [10, 10, 10, 160])
            borde_color = opcion.get("borde_color", [255, 255, 255])
            borde_ancho = int(opcion.get("borde_ancho", 3)) if seleccionado else 1
            radio = int(opcion.get("radio", 12))

            panel = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(panel, color_fondo, panel.get_rect(), border_radius=radio)
            pygame.draw.rect(panel, borde_color, panel.get_rect(), width=borde_ancho, border_radius=radio)
            pantalla.blit(panel, rect.topleft)

            fuente = self.obtener_fuente(opcion.get("tamano_fuente", 32))
            render = fuente.render(str(opcion.get("texto")), True, color_texto)
            texto_rect = render.get_rect(center=rect.center)
            pantalla.blit(render, texto_rect)

class PantallaTexto(PantallaBase):
    """Pantalla genérica de texto informativo."""

    def __init__(self, gestor_estado, config, titulo, lineas_texto):
        super().__init__(gestor_estado, config)
        self.titulo = titulo
        self.lineas = lineas_texto

    def manejar_eventos(self, eventos):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                self.gestor_estado.cambiar_estado("PRINCIPAL")

    def dibujar(self, pantalla):
        self.dibujar_texto_centrado(pantalla, str(self.titulo), 120, 60, (255, 255, 255))
        for index, linea in enumerate(self.lineas):
            self.dibujar_texto_centrado(pantalla, str(linea), 250 + (index * 45), 32, (255, 255, 255))
        self.dibujar_texto_centrado(pantalla, "Presiona ESC para volver", 560, 26, (220, 220, 220))


class PantallaInputNombre(PantallaBase):
    """Pantalla para ingresar el nombre del jugador."""

    def __init__(self, gestor_estado, config):
        super().__init__(gestor_estado, config)
        self.texto_input = ""

    def manejar_eventos(self, eventos):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_BACKSPACE:
                    self.texto_input = self.texto_input[:-1]
                elif evento.key == pygame.K_ESCAPE:
                    self.texto_input = ""
                    self.gestor_estado.cambiar_estado("PRINCIPAL")
                elif evento.key == pygame.K_RETURN:
                    self.gestor_estado.player_name = self.texto_input.strip() or "Jugador"
                    self.texto_input = ""
                    self.gestor_estado.cambiar_estado("PRINCIPAL")
                    self.gestor_estado.senal_salida = "JUGANDO"
                elif evento.unicode and evento.unicode.isprintable() and len(self.texto_input) < 16:
                    self.texto_input += evento.unicode

    def dibujar(self, pantalla):
        self.dibujar_texto_centrado(pantalla, "Ingresa tu nombre", 140, 60, (255, 255, 255))

        fuente = self.obtener_fuente(40)
        prompt = fuente.render("Nombre:", True, (255, 255, 255))
        pantalla.blit(prompt, prompt.get_rect(center=(pantalla.get_width() // 2 - 110, 290)))

        name_surf = fuente.render(self.texto_input + "_", True, (255, 220, 100))
        pantalla.blit(name_surf, name_surf.get_rect(center=(pantalla.get_width() // 2 + 90, 290)))

        self.dibujar_texto_centrado(pantalla, "Presiona Enter para empezar", 420, 26, (220, 220, 220))


class PantallaRecords(PantallaBase):
    """Pantalla para consultar los récords."""

    def manejar_eventos(self, eventos):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                self.gestor_estado.cambiar_estado("PRINCIPAL")

    def dibujar(self, pantalla):
        self.dibujar_texto_centrado(pantalla, "Récords", 120, 60, (255, 255, 255))
        top_records = sorted(self.gestor_estado.records, key=lambda i: i.get("score", 0), reverse=True)[:8]

        if not top_records:
            self.dibujar_texto_centrado(pantalla, "Aún no hay récords guardados", 340, 32, (255, 255, 255))
        else:
            for index, entry in enumerate(top_records):
                linea = f"{index + 1}. {entry.get('name', 'Jugador')} - {entry.get('score', 0)}"
                self.dibujar_texto_centrado(pantalla, linea, 240 + index * 40, 32, (255, 255, 255))

        self.dibujar_texto_centrado(pantalla, "Presiona ESC para volver", 560, 26, (220, 220, 220))


class PantallaPromptRecord(PantallaBase):
    """Pantalla de confirmación para reemplazar récord."""

    def manejar_eventos(self, eventos):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_y, pygame.K_s):
                    self.gestor_estado.aplicar_prompt_record(True)
                elif evento.key in (pygame.K_n, pygame.K_ESCAPE):
                    self.gestor_estado.aplicar_prompt_record(False)

    def dibujar(self, pantalla):
        self.dibujar_texto_centrado(pantalla, "Nuevo Récord Detectado", 140, 60, (255, 255, 255))
        old = self.gestor_estado.pending_old_score
        old_text = f"Récord anterior: {old}" if old is not None else "Récord anterior: --"
        new_text = f"Puntaje actual: {self.gestor_estado.pending_score}"

        self.dibujar_texto_centrado(pantalla, old_text, 270, 32, (255, 255, 255))
        self.dibujar_texto_centrado(pantalla, new_text, 320, 32, (255, 215, 0))
        self.dibujar_texto_centrado(pantalla, "Presiona S para reemplazar o N para conservar", 420, 26, (220, 220, 220))


# =====================================================================
# CLASE PRINCIPAL DEL ESTADO DE MENÚ
# =====================================================================

class MenuState:
    """Gestor unificado del menú principal."""

    def __init__(self, screen, context=None):
        self.screen = screen
        self.pantalla = screen
        self.context = context if context is not None else {}
        self.audio = get_audio_manager()
        self.config = GestorConfig.cargar_configuracion()
        self.senal_salida = None
        self.player_name = "Jugador"

        # Récords JSON
        self.records_file = BASE_DIR / "records.json"
        self.records = self._cargar_records()
        self.pending_score = None
        self.pending_name = None
        self.pending_old_score = None

        # Video de fondo
        self.cap = None
        self.surface_video = None
        ruta_video = ASSETS_DIR / "fondo_menu.mp4"
        if cv2 and ruta_video.exists():
            try:
                self.cap = cv2.VideoCapture(str(ruta_video))
            except Exception as e:
                print(f"Error al inicializar fondo_menu.mp4: {e}")
                self.cap = None

        if not self.cap:
            self.surface_video = pygame.Surface(screen.get_size())
            self.surface_video.fill((15, 25, 45))

        # Registrar subpantallas
        self.pantallas = {
            "PRINCIPAL": PantallaPrincipal(self, self.config),
            "NAME_INPUT": PantallaInputNombre(self, self.config),
            "RECORDS": PantallaRecords(self, self.config),
            "REPLACE_PROMPT": PantallaPromptRecord(self, self.config)
        }
        self.estado_actual = "PRINCIPAL"

    def enter(self):
        self.senal_salida = None
        self.audio.play_menu_music()
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def exit(self):
        self.audio.stop_music()

    def cambiar_estado(self, nombre_estado):
        if nombre_estado in self.pantallas:
            self.estado_actual = nombre_estado

    def _cargar_records(self):
        if not self.records_file.exists():
            return []
        try:
            with open(self.records_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []

    def _guardar_records(self):
        ordenados = sorted(self.records, key=lambda x: x.get("score", 0), reverse=True)
        self.records = ordenados
        try:
            with open(self.records_file, "w", encoding="utf-8") as f:
                json.dump(ordenados, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando récords: {e}")

    def aplicar_prompt_record(self, reemplazar):
        if reemplazar:
            self.records = [e for e in self.records if str(e.get("name", "")).lower() != self.pending_name.lower()]
            self.records.append({"name": self.pending_name, "score": self.pending_score})
        else:
            self.records.append({"name": self.pending_name, "score": self.pending_score})

        self._guardar_records()
        self.cambiar_estado("PRINCIPAL")

    def handle_events(self, events):
        self.pantallas[self.estado_actual].manejar_eventos(events)
        if self.senal_salida:
            res = self.senal_salida
            self.senal_salida = None
            if res in ("JUGANDO", "jugar", "JUGAR"):
                self.context["player_name"] = self.player_name
                return "PLAY"
            elif res in ("SALIR", "salir", "QUIT"):
                pygame.quit()
                raise SystemExit
        return None

    def update(self, dt=0):
        # Actualizar frame de video si está activo
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                # Reiniciar el video al llegar al final
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()

            if ret:
                # Convertir BGR de OpenCV a RGB de Pygame y redimensionar a la pantalla
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (self.screen.get_width(), self.screen.get_height()))
                self.surface_video = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "RGB")

        self.pantallas[self.estado_actual].actualizar()
        return None

    def draw(self, screen=None):
        target_screen = screen if screen is not None else self.screen
        if self.surface_video:
            target_screen.blit(self.surface_video, (0, 0))
        self.pantallas[self.estado_actual].dibujar(target_screen)