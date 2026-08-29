import pygame
from abc import ABC, abstractmethod

class PantallaBase(ABC):
    def __init__(self, gestor_estado, config):
        self.gestor_estado = gestor_estado
        self.config = config
        self.fuentes = {}

    def obtener_fuente(self, tamano):
        if tamano not in self.fuentes:
            from settings import load_game_font
            try:
                self.fuentes[tamano] = load_game_font(tamano)
            except:
                self.fuentes[tamano] = pygame.font.Font(None, tamano)
        return self.fuentes[tamano]

    def dibujar_texto_centrado(self, pantalla, texto, y, tamano, color):
        fuente = self.obtener_fuente(tamano)
        render = fuente.render(texto, True, color)
        rect = render.get_rect(center=(pantalla.get_width() // 2, y))
        pantalla.blit(render, rect)

    @abstractmethod
    def manejar_eventos(self, eventos): pass

    @abstractmethod
    def dibujar(self, pantalla): pass

    def actualizar(self): pass


class PantallaPrincipal(PantallaBase):
    def __init__(self, gestor_estado, config):
        super().__init__(gestor_estado, config)
        self.opciones = self.config.get("opciones_principal", [])
        self.indice_seleccionado = 0
        
        ruta_logo = self.config.get("recursos", {}).get("titulo", "")
        self.logo = None
        try:
            raw_logo = pygame.image.load(ruta_logo).convert_alpha()
            self.logo = raw_logo.subsurface(raw_logo.get_bounding_rect()).copy()
        except: pass

    def manejar_eventos(self, eventos):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_UP, pygame.K_w):
                    self.indice_seleccionado = (self.indice_seleccionado - 1) % len(self.opciones)
                elif evento.key in (pygame.K_DOWN, pygame.K_s):
                    self.indice_seleccionado = (self.indice_seleccionado + 1) % len(self.opciones)
                elif evento.key == pygame.K_RETURN:
                    self._ejecutar_accion()

    def _ejecutar_accion(self):
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
            rect_titulo = self.logo.get_rect(midtop=(pantalla.get_width() // 2, 0))
            pantalla.blit(self.logo, rect_titulo)

        start_y = 340
        for index, opcion in enumerate(self.opciones):
            color = opcion.get("color_seleccionado") if index == self.indice_seleccionado else opcion.get("color_normal")
            self.dibujar_texto_centrado(pantalla, opcion.get("texto"), start_y + (index * 58), opcion.get("tamano_fuente", 46), color)


class PantallaTexto(PantallaBase):
    def __init__(self, gestor_estado, config, titulo, lineas_texto):
        super().__init__(gestor_estado, config)
        self.titulo = titulo
        self.lineas = lineas_texto

    def manejar_eventos(self, eventos):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                self.gestor_estado.cambiar_estado("PRINCIPAL")

    def dibujar(self, pantalla):
        self.dibujar_texto_centrado(pantalla, self.titulo, 120, 82, (255,255,255))
        for index, linea in enumerate(self.lineas):
            self.dibujar_texto_centrado(pantalla, linea, 250 + (index * 45), 32, (255,255,255))
        self.dibujar_texto_centrado(pantalla, "Presiona ESC para volver", 560, 26, (220, 220, 220))


class PantallaInputNombre(PantallaBase):
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
        self.dibujar_texto_centrado(pantalla, "Ingresa tu nombre", 140, 82, (255,255,255))
        
        fuente = self.obtener_fuente(46)
        prompt = fuente.render("Nombre:", True, (255, 255, 255))
        pantalla.blit(prompt, prompt.get_rect(center=(pantalla.get_width() // 2 - 110, 290)))

        name_surf = fuente.render(self.texto_input + "_", True, (255, 220, 100))
        pantalla.blit(name_surf, name_surf.get_rect(center=(pantalla.get_width() // 2 + 90, 290)))

        self.dibujar_texto_centrado(pantalla, "Presiona Enter para empezar", 420, 26, (220, 220, 220))


class PantallaRecords(PantallaBase):
    def manejar_eventos(self, eventos):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                self.gestor_estado.cambiar_estado("PRINCIPAL")

    def dibujar(self, pantalla):
        self.dibujar_texto_centrado(pantalla, "Records", 120, 82, (255,255,255))
        top_records = sorted(self.gestor_estado.records, key=lambda i: i.get("score", 0), reverse=True)[:8]

        if not top_records:
            self.dibujar_texto_centrado(pantalla, "Aun no hay records guardados", 340, 32, (255,255,255))
        else:
            for index, entry in enumerate(top_records):
                linea = f"{index + 1}. {entry.get('name', 'Jugador')} - {entry.get('score', 0)}"
                self.dibujar_texto_centrado(pantalla, linea, 300 + index * 40, 32, (255,255,255))
                
        self.dibujar_texto_centrado(pantalla, "Presiona ESC para volver", 560, 26, (220, 220, 220))


class PantallaPromptRecord(PantallaBase):
    def manejar_eventos(self, eventos):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_y, pygame.K_s):
                    self.gestor_estado.aplicar_prompt_record(True)
                elif evento.key in (pygame.K_n, pygame.K_ESCAPE):
                    self.gestor_estado.aplicar_prompt_record(False)

    def dibujar(self, pantalla):
        self.dibujar_texto_centrado(pantalla, "Guardar record", 140, 82, (255,255,255))
        old = self.gestor_estado.pending_old_score
        old_text = f"Record anterior: {old}" if old is not None else "Record anterior: --"
        new_text = f"Puntaje actual: {self.gestor_estado.pending_score}"
        
        self.dibujar_texto_centrado(pantalla, old_text, 290, 32, (255,255,255))
        self.dibujar_texto_centrado(pantalla, new_text, 340, 32, (255,255,255))
        self.dibujar_texto_centrado(pantalla, "Presiona S para reemplazar o N para conservar", 410, 26, (220, 220, 220))