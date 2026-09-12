"""
Módulo: main.py
Descripción: Punto de entrada principal para el juego. Inicializa Pygame,
             gestiona la máquina de estados global (MenuState, PlayState)
             y controla el bucle principal de juego.
"""

import sys
import pygame

# Importación de configuraciones globales del proyecto
from settings import S_WIDTH, S_HEIGHT, FPS

# Importación de los estados de juego
from states.menu_state import MenuState
from states.play_state import PlayState
from states.gameover_state import GameOverState

def main() -> None:
    """Función principal que ejecuta el bucle de eventos y la máquina de estados."""
    # 1. Inicialización de los módulos internos de Pygame
    pygame.init()

    # 2. Creación de la superficie de la pantalla
    screen = pygame.display.set_mode((S_WIDTH, S_HEIGHT))
    
    # 3. Configuración del título de la ventana
    pygame.display.set_caption("Juego de Cartas - Balatro Style")

    # 4. Control de la tasa de refresco (FPS)
    clock = pygame.time.Clock()

    # 5. Diccionario de contexto global para compartir datos entre estados (puntuaciones, ronda, etc.)
    context = {"round": 1}

    # 6. Inicialización de la máquina de estados
    # Creamos las instancias de cada estado disponible
    menu_state = MenuState(screen=screen)
    play_state = PlayState(screen=screen, context=context)
    gameover_state = GameOverState(screen=screen, context=context)
    # Registro de estados en un diccionario para alternar fácilmente entre ellos
    states = {
        "MENU": menu_state,
        "PLAY": play_state,
        "GAME_OVER": gameover_state
    }

    # Asignamos MENU como el estado inicial de la aplicación
    current_state_key = "MENU"
    current_state = states[current_state_key]
    current_state.enter()  # Dispara la música/lógica de entrada del menú

    # 7. Control del bucle principal
    running = True

    while running:
        # Calcula el delta time (dt) en segundos
        dt = clock.tick(FPS) / 1000.0

        # Obtiene la lista de eventos ocurridos en este fotograma
        events = pygame.event.get()

        # Procesa eventos globales del sistema (como cerrar la ventana desde la X)
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        # --- GESTIÓN DE EVENTOS DEL ESTADO ACTIVO ---
        next_state_event = current_state.handle_events(events)

        # --- ACTUALIZACIÓN DE LÓGICA DEL ESTADO ACTIVO ---
        next_state_update = current_state.update(dt)

        # Priorizamos si handle_events o update solicitan un cambio de estado
        next_state = next_state_event or next_state_update

        # --- TRANSICIONES Y CAMBIOS DE ESTADO ---
        if next_state == "QUIT":
            running = False

        elif next_state == "PLAY" and current_state_key != "PLAY":
            # Guardamos el nombre ingresado en el menú dentro del contexto si es necesario
            if hasattr(menu_state, "player_name"):
                context["player_name"] = menu_state.player_name

            # Cambiamos al estado de juego
            current_state_key = "PLAY"
            current_state = states[current_state_key]
            current_state.enter()

        elif next_state == "MENU" and current_state_key != "MENU":
            # Volver al menú principal
            current_state_key = "MENU"
            current_state = states[current_state_key]
            current_state.enter()

        elif next_state == "SHOP":
            # Pasa a la siguiente ronda y reinicia los parámetros de la partida
            play_state.reset_round()

        elif next_state == "VICTORY":
            print("¡Felicidades! Has ganado la partida.")
            running = False

        elif next_state == "GAME_OVER":
            print("Game Over. Te has quedado sin manos.")
            running = False

        # --- RENDERIZADO DEL ESTADO ACTIVO ---
        current_state.draw(screen)

        # Muestra en pantalla el búfer dibujado
        pygame.display.flip()

    # Cierre de Pygame y finalización limpia del sistema
    pygame.quit()
    sys.exit()


# Punto de entrada de ejecución del script
if __name__ == "__main__":
    main()