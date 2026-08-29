# game.py
import pygame

class SelectorDummy:
    def handle_event(self, event):
        # Si presionas ENTER en el selector, elige un personaje y avanza
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            return "Personaje Falso"
        return None
        
    def draw(self, screen):
        screen.fill((50, 50, 150)) # Azulito para el selector
        font = pygame.font.Font(None, 40)
        texto = font.render("Pantalla Selector: Presiona ENTER para jugar", True, (255, 255, 255))
        screen.blit(texto, (100, 100))


class CarreraDeObstaculos:
    def __init__(self, screen):
        self.screen = screen
        self.sound_player = None
        self.player_name = "Jugador"
        self.personaje_actual = None
        self.score = 0
        self.selector = SelectorDummy()

    def reset_game(self):
        self.score = 2500 # Le ponemos 2500 puntos falsos (luego se divide entre 10 en el main)
        print("🎮 [Juego Falso] Juego reiniciado.")

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "MENU"
        return None

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_g]: # TRUCO: Presiona 'G' para forzar un Game Over
            return "GAMEOVER"
        return None

    def _update_record_summary(self):
        pass

    def draw(self):
        self.screen.fill((100, 200, 100)) # Verde para el juego
        font = pygame.font.Font(None, 40)
        texto = font.render(f"Jugando como: {self.player_name}", True, (255, 255, 255))
        instruccion = font.render("Presiona 'G' para simular GAME OVER, o 'ESC' para Menú", True, (255, 255, 255))
        self.screen.blit(texto, (50, 50))
        self.screen.blit(instruccion, (50, 150))

    def draw_gameover(self):
        # Cuando mueres, dibuja un texto rojo encima
        font = pygame.font.Font(None, 60)
        texto = font.render("¡GAME OVER FALSO!", True, (255, 0, 0))
        instruccion = font.render("Presiona ESC para volver al menú y guardar record", True, (255, 255, 255))
        self.screen.blit(texto, (50, 300))
        self.screen.blit(instruccion, (50, 380))