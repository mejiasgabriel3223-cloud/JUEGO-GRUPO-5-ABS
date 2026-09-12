# game.py
import pygame
import traceback
from states.menu_state import MenuState
from states.play_state import PlayState
from states.gameover_state import GameOverState  # Módulo sin guión bajo entre game y over
# from states.shop_state import ShopState  # Descomentar cuando agregues la tienda

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("Juego Grupo 5 ABS")
        self.clock = pygame.time.Clock()
        
        # Contexto compartido entre estados (dinero, puntuación, récords, etc.)
        self.context = {"money": 0, "score": 0, "round": 1, "player_name": "Jugador"}
        
        # Diccionario con todos los estados disponibles
        self.states = {
            "MENU": MenuState(self.screen, self.context),
            "PLAY": PlayState(self.screen, self.context),
            "GAME_OVER": GameOverState(self.screen, self.context),
            # "SHOP": ShopState(self.screen, self.context),
        }
        
        # Estado inicial
        self.active_state = self.states["MENU"]
        self.active_state.enter()  # Se ejecuta la entrada del estado inicial

    def change_state(self, next_state_key):
        """Ejecuta la salida del estado actual y la entrada del nuevo estado."""
        if hasattr(self.active_state, "exit"):
            self.active_state.exit()
            
        self.active_state = self.states[next_state_key]
        
        if hasattr(self.active_state, "enter"):
            self.active_state.enter()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    running = False

            try:
                # 1. Delegar eventos al estado activo
                next_state_key = self.active_state.handle_events(events)
                
                # 2. Actualizar lógica del estado activo (solo si no hubo cambio en handle_events)
                if not next_state_key:
                    next_state_key = self.active_state.update(dt)

                # 3. Transición de estado con ciclo de vida (enter / exit)
                if next_state_key and next_state_key in self.states:
                    self.change_state(next_state_key)

                # 4. Renderizar el estado activo
                self.active_state.draw(self.screen)
                
                # Garantiza la actualización del fotograma en pantalla
                pygame.display.flip()

            except Exception as e:
                print("\n" + "=" * 60)
                print("¡ERROR DETECTADO EN LA EJECUCIÓN DEL JUEGO!")
                print("=" * 60)
                traceback.print_exc()  # Muestra el archivo y la línea exacta del fallo
                print("=" * 60 + "\n")
                
                # Pausa para evitar que la terminal se cierre inmediatamente
                input("Presiona ENTER en la terminal para salir...")
                running = False

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()