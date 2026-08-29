# main.py
import pygame
import sys
from settings import S_WIDTH, S_HEIGHT, FPS
from menu.estado_menu import EstadoMenu  # Importado desde el nuevo módulo modular
from game import CarreraDeObstaculos
from audio import SoundPlayer

def main():
    pygame.init()
    screen = pygame.display.set_mode((S_WIDTH, S_HEIGHT))
    # Actualizado con el nombre oficial de tu proyecto
    pygame.display.set_caption("Running Time!") 
    clock = pygame.time.Clock()

    sound_player = SoundPlayer()
    menu = EstadoMenu(screen)
    juego = CarreraDeObstaculos(screen)
    
    juego.sound_player = sound_player
    menu.sound_player = sound_player
    sound_player.play_menu_music()

    estado_actual = "MENU"
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0
        events = pygame.event.get()

        # 1. Procesamiento global de eventos (Cierre de ventana)
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        # 2. Máquina de Estados Principal
        if estado_actual == "MENU":
            # El menú modular retorna comandos como "JUGANDO" o "SALIR"
            resultado = menu.manejar_eventos(events)
            
            if resultado == "JUGANDO":
                # Usamos getattr para mayor seguridad al extraer el nombre del menú modular
                juego.player_name = getattr(menu, 'player_name', "Jugador")
                estado_actual = "SELECTOR" 
            elif resultado == "SALIR":
                running = False

            menu.actualizar()
            menu.dibujar()

        elif estado_actual == "SELECTOR":
            for event in events:
                personaje_elegido = juego.selector.handle_event(event)
                
                if personaje_elegido:
                    juego.personaje_actual = personaje_elegido
                    juego.reset_game()
                    sound_player.play_game_music(0) 
                    estado_actual = "JUGANDO"
                    
            juego.selector.draw(screen)

        elif estado_actual == "JUGANDO":
            resultado_eventos = juego.handle_events(events)
            if resultado_eventos == "MENU":
                estado_actual = "MENU"
                sound_player.play_menu_music()

            resultado_update = juego.update(dt)
            if resultado_update == "GAMEOVER":
                juego._update_record_summary()
                estado_actual = "GAMEOVER"
            elif resultado_update == "MENU":
                estado_actual = "MENU"
                score = juego.score // 10
                
                # Verificación de seguridad (Duck Typing) para el método de records
                if hasattr(menu, 'finalizar_partida'):
                    menu.finalizar_partida(score, juego.player_name)
                sound_player.play_menu_music()

            juego.draw()

        elif estado_actual == "GAMEOVER":
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        juego.reset_game()
                        sound_player.play_game_music(0)
                        estado_actual = "JUGANDO"
                    elif event.key == pygame.K_ESCAPE:
                        estado_actual = "MENU"
                        score = juego.score // 10
                        
                        if hasattr(menu, 'finalizar_partida'):
                            menu.finalizar_partida(score, juego.player_name)
                        sound_player.play_menu_music()

            juego.draw()
            juego.draw_gameover()

        # 3. Actualización de Pantalla (Renderizado final)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()