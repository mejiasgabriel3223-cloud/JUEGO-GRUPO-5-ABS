"""
Módulo: states/play_state.py
Descripción: Estado principal de juego (PlayState) para la gestión de partidas.
             Maneja la mesa de juego, interacción con cartas, evaluación de manos,
             activación de Jokers y transición de estados hacia la Tienda o Game Over.
"""

from __future__ import annotations

from pathlib import Path
import pygame

# Importación de la clase padre abstracta para estados
from states.base_state import BaseState

# Importación del renderizador de interfaz gráfica
from Renderer import Renderer

# Importaciones de entidades del dominio del juego (cartas, jokers, reglas)
from entities import (
    CardEntity, 
    CardFactory, 
    EntityCollection, 
    GameRules, 
    RandomJokerPool, 
    FlatChipsJoker, 
    MultiplierJoker
)


class PlayState(BaseState):
    """
    Estado activo del bucle de juego principal.

    Administra la ronda en curso, el puntaje acumulado, la selección de cartas de la mano,
    el descarte, las interacciones con el módulo de reglas (`GameRules`) y la aplicación
    de efectos de Jokers.
    """

    # Constantes de configuración de la mesa de juego
    MAX_HAND_SIZE = 8   # Límite máximo de cartas permitidas simultáneamente en la mano
    MAX_PLAY_SIZE = 5   # Límite máximo de cartas permitidas para jugar o descartar en un turno

    def __init__(self, screen: pygame.Surface, context: dict | None = None) -> None:
        """
        Inicializa el PlayState con la pantalla de juego y el contexto global.

        Args:
            screen (pygame.Surface): Pantalla sobre la cual se dibuja la escena.
            context (dict | None, optional): Estado global persistente (dinero, ronda, etc.).
        """
        # Llamada al constructor de la clase base BaseState
        super().__init__()
        
        # Referencias a la pantalla principal y al contexto de datos persistentes
        self.screen = screen
        self.context = context if context is not None else {}
        
        # Inicialización del subsistema gráfico pasando las dimensiones de la ventana
        self.renderer = Renderer(*screen.get_size(), screen=screen)
        
        # Instanciación del evaluador de combinaciones de póker y puntuación
        self.rules = GameRules()
        
        # Fábrica de cartas configurada con la ruta raíz del proyecto para recursos
        self.card_factory = CardFactory(self._project_root())
        
        # Colección contenedora de las entidades de cartas de la mano actual
        self.cards = EntityCollection[CardEntity]()
        
        # Atributos de estado textual e historial de la jugada
        self.message: str = "Select 1 to 5 cards and press SPACE"
        self.last_hand_name: str = "High Card"
        
        # Lectura del número de ronda desde el contexto compartido (por defecto 1)
        self.round_number: int = self.context.get("round", 1)
        
        # Definición del puntaje objetivo para superar la ronda actual
        self.target: int = 100 * self.round_number
        
        # Recursos disponibles para el jugador durante la ronda
        self.hands_left: int = 4        # Cantidad de intentos de jugada restantes
        self.discards_left: int = 3     # Cantidad de descartes de cartas restantes
        self.round_score: int = 0       # Puntaje acumulado en la ronda en curso
        
        # Pool de Jokers configurados con sus correspondientes probabilidades y valores
        self.jokers = RandomJokerPool([
            FlatChipsJoker(amount=5, probability=0.75),
            MultiplierJoker(amount=0.25, probability=0.60),
        ])
        
        # Preparación inicial de la mano y reseteo de la ronda
        self.reset_round()

    def enter(self):
        """Método de entrada al estado de juego llamado por game.py/main.py."""
        if hasattr(self, "context") and self.context:
            self.player_name = self.context.get("player_name", "Jugador")
            # Si venimos de un Game Over o inicio nuevo, leemos o preparamos el acumulado
            self.round_number = self.context.get("round", 1)
            self.target = 100 * self.round_number

        # Reinicia los contadores de la mesa de juego para la partida
        self.reset_round()

    def exit(self):
        """Método de salida del estado de juego llamado por main.py."""
        # Aquí puedes pausar/detener la música del nivel si aplica
        pass

    def _project_root(self) -> Path:
        """
        Obtiene la ruta raíz del proyecto para la carga de recursos gráficos y de audio.

        Returns:
            Path: Objeto Path apuntando al directorio raíz del proyecto.
        """
        # Resuelve la ruta absoluta del directorio padre del directorio actual de estados
        return Path(__file__).resolve().parent.parent

    def reset_round(self) -> None:
        """
        Reinicia los parámetros de la ronda actual y genera una nueva mano de cartas.
        """
        # Restablece los contadores de recursos de la ronda a sus valores iniciales
        self.hands_left = 4
        self.discards_left = 3
        self.round_score = 0
        
        # Limpia cualquier modificador o estado previo guardado en el motor de reglas
        self.rules.reset()
        
        # Genera el mazo/mano inicial de cartas aleatorias
        self._start_round()
        
        # Actualiza el mensaje en pantalla informando la ronda y la meta a alcanzar
        self.message = f"Round {self.round_number}. Target: {self.target}"

    def _start_round(self) -> None:
        """
        Genera una colección aleatoria de cartas del tamaño `MAX_HAND_SIZE` y las mezcla.
        """
        # Crea la colección de cartas requerida mediante la fábrica de cartas
        self.cards = EntityCollection[CardEntity](
            self.card_factory.create_random_collection(self.MAX_HAND_SIZE)
        )
        # Mezlca aleatoriamente las cartas en la colección generada
        self.cards.shuffle()

    def _select_card_at(self, position: tuple[int, int]) -> None:
        """
        Procesa el clic en pantalla para seleccionar o deseleccionar una carta de la mano.

        Args:
            position (tuple[int, int]): Coordenadas (x, y) del clic del mouse.
        """
        # Recalcula los recuadros de colisión visual de las cartas antes de verificar el clic
        self._sync_card_rects()
        
        # Itera la lista en orden inverso para priorizar las cartas renderizadas al frente
        for card in reversed(self.cards.copy()):
            # Verifica si el clic ocurrió dentro de las coordenadas de la carta actual
            if card.rect is not None and card.rect.collidepoint(position):
                # Cuenta cuántas cartas están marcadas como seleccionadas actualmente
                selected_count = sum(1 for item in self.cards if item.selected)
                
                # Previene seleccionar más del límite máximo de cartas permitido
                if not card.selected and selected_count >= self.MAX_PLAY_SIZE:
                    self.message = f"You can select at most {self.MAX_PLAY_SIZE} cards"
                    return
                
                # Invierte el estado de selección de la carta (true/false)
                card.toggle_selected()
                return

    def _selected_cards(self) -> list[CardEntity]:
        """
        Obtiene la lista de cartas actualmente seleccionadas por el jugador.

        Returns:
            list[CardEntity]: Cartas con la propiedad `selected == True`.
        """
        # Filtra y retorna solo las cartas que tienen la propiedad 'selected' activada
        return [card for card in self.cards if card.selected]

    def handle_events(self, events: list[pygame.event.Event]) -> str | None:
        """
        Procesa los eventos de Pygame asignados al PlayState.

        Args:
            events (list[pygame.event.Event]): Lista de eventos Pygame del frame actual.

        Returns:
            str | None: Nombre del nuevo estado al que migrar si aplica, o None.
        """
        # Recorre la cola de eventos capturados por Pygame
        for event in events:
            # Evalúa eventos de pulsación de teclas del teclado
            if event.type == pygame.KEYDOWN:
                # Tecla ESCAPE: solicita salir al menú principal/pausa
                if event.key == pygame.K_ESCAPE:
                    return "MENU"
                
                # Teclas ESPACIO o ENTER: ejecuta la acción de jugar la mano seleccionada
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self.play_selected()
                
                # Tecla D: ejecuta la acción de descartar las cartas seleccionadas
                elif event.key == pygame.K_d:
                    self.discard_selected()
            
            # Evalúa clics del ratón (botón 1 = Clic Izquierdo)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Llama a la selección de cartas pasando la posición actual del puntero
                self._select_card_at(event.pos)
                
        # Continúa en el estado actual sin transiciones
        return None

    def update(self, dt: float) -> str | None:
        """
        Actualiza la lógica de juego y evalúa condiciones de victoria o derrota.
        """
        # 1. Comprobación de condición de victoria de la ronda
        if self.round_score >= self.target:
            self.round_number += 1
            
            if self.round_number > 3:
                self.context["score"] = self.round_score
                return "VICTORY"
            
            self.context["round"] = self.round_number
            self.context["score"] = self.round_score
            return "SHOP"

        # 2. Comprobación de condición de derrota (sin intentos de mano y puntaje insuficiente)
        if self.hands_left <= 0 and self.round_score < self.target:
            # Guardamos la puntuación alcanzada para que GameOverState la registre
            self.context["score"] = self.round_score
            # Retornamos el nombre del estado
            return "GAME_OVER"

        return None

    def play_selected(self) -> int | None:
        """
        Evalúa y procesa la mano seleccionada por el jugador.

        Returns:
            int | None: Puntaje obtenido en la jugada, o None si la jugada no fue válida.
        """
        # Obtiene la lista de entidades de cartas marcadas
        selected = self._selected_cards()
        
        # Revalida que la cantidad de cartas seleccionadas esté en el rango permitido (1 a 5)
        if not 1 <= len(selected) <= self.MAX_PLAY_SIZE:
            self.message = f"Select between 1 and {self.MAX_PLAY_SIZE} cards"
            return None
        
        # Previene jugar si ya no le quedan manos disponibles al jugador
        if self.hands_left <= 0:
            self.message = "No hands left"
            return None

        # Obtiene la mejor combinación de 5 cartas según las reglas de póker
        best = self.rules.best_five(selected)
        
        # Realiza una evaluación previa de la mano
        self.rules.evaluate(best)
        
        # Dispara el chequeo y cálculo de puntos extra por Jokers activos
        activated = self.jokers.activate_all(EntityCollection(best))
        
        # Obtiene el resultado final calculando fichas * multiplicadores finales
        result = self.rules.evaluate(best)

        # Guarda el nombre de la jugada realizada (ej: "Flush", "Pair")
        self.last_hand_name = result.name
        
        # Suma los puntos calculados de la mano al acumulado de la ronda
        self.round_score += result.total
        
        # Descuenta un intento de mano al jugador
        self.hands_left -= 1

        # Elimina de la mano las cartas que acaban de ser jugadas
        for card in selected:
            self.cards.remove(card)
            
        # Determina cuántas cartas faltan para reponer la mano al máximo
        missing = self.MAX_HAND_SIZE - len(self.cards)
        
        # Genera nuevas cartas y las agrega a la mano activa
        self.cards.add_many(self.card_factory.create_random_collection(missing))
        
        # Mezcla las cartas de la mano para desordenarlas
        self.cards.shuffle()

        # Genera el mensaje de estado para el HUD mostrando jugada, puntos y Jokers que actuaron
        if activated:
            self.message = f"{result.name}: {result.total} pts | Jokers: {', '.join(activated)}"
        else:
            self.message = f"{result.name}: {result.total} pts"

        # Retorna los puntos obtenidos en esta jugada
        return result.total

    def discard_selected(self) -> int | None:
        """
        Descarta las cartas seleccionadas y repone la mano con nuevas cartas.

        Returns:
            int | None: Cantidad de cartas descartadas, o None si la acción fue inválida.
        """
        # Obtiene las cartas seleccionadas para descarte
        selected = self._selected_cards()
        
        # Cancela el proceso si no hay cartas seleccionadas
        if not selected:
            self.message = "Select cards to discard"
            return None
        
        # Cancela el proceso si el jugador ya no tiene descartes permitidos
        if self.discards_left <= 0:
            self.message = "No discards left"
            return None

        # Remueve cada carta seleccionada de la colección de la mano
        for card in selected:
            self.cards.remove(card)
            
        # Resta una oportunidad al contador de descartes
        self.discards_left -= 1

        # Calcula la cantidad de cartas faltantes en la mano
        missing = self.MAX_HAND_SIZE - len(self.cards)
        
        # Crea e inserta cartas aleatorias de reemplazo
        self.cards.add_many(self.card_factory.create_random_collection(missing))
        
        # Mezcla la mano resultante
        self.cards.shuffle()
        
        # Actualiza el mensaje informativo en la interfaz gráfica
        self.message = f"Discarded {len(selected)} cards"
        
        # Devuelve la cantidad total de cartas descartadas
        return len(selected)

    def _sync_card_rects(self) -> None:
        """
        Sincroniza la posición y rectángulos de colisión (`pygame.Rect`) de las cartas
        con la disposición visual generada por el `Renderer`.
        """
        # Distancia en píxeles entre cada carta
        spacing = 95
        
        # Calcula la posición X inicial para centrar dinámicamente las cartas en pantalla
        start_x = (self.screen.get_width() - (len(self.cards) * spacing)) // 2 + 100
        
        # Define la posición Y base para alinear las cartas en la parte inferior
        start_y = self.screen.get_height() - 160
        
        # Asigna a cada carta su nueva coordenada X e Y según su índice y si está seleccionada
        for index, card in enumerate(self.cards):
            if card.rect:
                # Asigna posición horizontal escalonada
                card.rect.x = start_x + index * spacing
                
                # Desplaza verticalmente 20px hacia arriba si la carta está seleccionada
                card.rect.y = start_y - (20 if card.selected else 0)

    def draw(self, screen: pygame.Surface | None = None) -> None:
        """
        Renderiza los elementos gráficos del PlayState (HUD, barra de Jokers, mano y mensajes).

        Args:
            screen (pygame.Surface | None, optional): Superficie sobre la que se dibujará.
                                                     Si es None, usa `self.screen`.
        """
        # Asigna la superficie de destino (usa la por defecto si no recibe parámetro)
        target_screen = screen or self.screen
        
        # Actualiza las posiciones visuales/hitboxes de las cartas antes de dibujar
        self._sync_card_rects()
        
        # Limpia el frame anterior en el búfer de renderizado
        self.renderer.clear()
        
        # Obtiene las cartas seleccionadas y evalúa una vista previa de la mano para el HUD
        selected_cards = self._selected_cards()
        result = self.rules.evaluate(selected_cards) if selected_cards else None
        
        # Determina las fichas y el multiplicador a desplegar en los paneles del HUD
        chips = result.score if result else self.round_score
        mult = result.multiplier if result else self.rules.multiplier
        
        # Dibuja la barra de información con puntos, metas, multiplicadores y recursos
        self.renderer.draw_hud_panel(
            self.round_score,
            self.target,
            mult,
            chips,
            self.hands_left,
            self.discards_left,
        )
        
        # Dibuja la barra superior con el estado de los Jokers activos
        self.renderer.draw_joker_bar([
            {"name": joker.name, "active": joker.active}
            for joker in self.jokers.jokers
        ])

        # Convierte las cartas a diccionarios serializados para consumo del Renderer
        card_data = [card.to_dict() for card in self.cards]
        
        # Renderiza las imágenes/texturas de las cartas de la mano
        self.renderer.draw_hand(card_data)
        
        # Crea la tipografía y renderiza la superficie del texto de mensajes informativos
        font = pygame.font.SysFont("Arial", 22, bold=True)
        text = font.render(self.message, True, (255, 255, 255))
        
        # Dibuja la superficie del texto sobre la pantalla en las coordenadas especificadas
        target_screen.blit(text, (300, target_screen.get_height() - 40))
        
        # Ejecuta la presentación/flip final del renderizador
       # self.renderer.present()