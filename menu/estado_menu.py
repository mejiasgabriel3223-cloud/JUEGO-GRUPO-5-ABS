import pygame
import json
from pathlib import Path
from menu.gestor_config import GestorConfig
from menu.pantallas_menu import PantallaPrincipal, PantallaInputNombre, PantallaRecords, PantallaPromptRecord

BASE_DIR = Path(__file__).parent.parent 
IMAGENES_DIR = BASE_DIR / "assets"

class EstadoMenu:
    def __init__(self, pantalla):
        self.pantalla = pantalla
        self.config = GestorConfig.cargar_configuracion()
        self.senal_salida = None
        self.player_name = "Jugador"
        
        # Sistema de Records
        self.records_file = BASE_DIR / "records.json"
        self.records = self._cargar_records()
        self.pending_score = None
        self.pending_name = None
        self.pending_old_score = None

        # Cargar recursos base
        recursos = self.config.get("recursos", {})
        ruta_fondo = recursos.get("fondo", "")
        
        if ruta_fondo and not Path(ruta_fondo).is_absolute():
            ruta_fondo = str(BASE_DIR / ruta_fondo)

        self.fondo = None
        try:
            self.fondo = pygame.image.load(ruta_fondo).convert()
        except:
            self.fondo = pygame.Surface(pantalla.get_size())
            self.fondo.fill((20, 40, 80))

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
        self.pantallas[self.estado_actual].actualizar()

    def dibujar(self):
        if self.fondo:
            self.pantalla.blit(self.fondo, (0, 0))
        self.pantallas[self.estado_actual].dibujar(self.pantalla)