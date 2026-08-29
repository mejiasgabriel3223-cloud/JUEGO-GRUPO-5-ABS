import pygame
from pathlib import Path

# Configuración de directorios
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"

# Configuración de la pantalla
# (Si tu ventana original tenía otro tamaño, ajusta estos valores)
S_WIDTH = 1280 
S_HEIGHT = 720

# Fotogramas por segundo
FPS = 60

def load_game_font(tamano):
    """
    Carga la fuente personalizada del juego. 
    Si no encuentra el archivo, usa la fuente por defecto de Pygame 
    como sistema de seguridad (fallback) para que el juego no se cierre.
    """
    # IMPORTANTE: Cambia "tu_fuente.ttf" por el nombre real del archivo 
    # de texto que estabas usando en tu carpeta de assets.
    ruta_fuente = ASSETS_DIR / "tu_fuente.ttf" 
    
    try:
        return pygame.font.Font(ruta_fuente, tamano)
    except Exception:
        # Fuente por defecto en caso de que falle la ruta
        return pygame.font.Font(None, tamano)