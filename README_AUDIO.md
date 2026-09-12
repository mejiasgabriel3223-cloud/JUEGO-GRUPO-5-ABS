# Audio - Guia de uso y extension

## 1. Objetivo

`audio.py` contiene el servicio de audio compartido del juego. Su diseño separa el mixer de Pygame de los states:

```text
MenuState / PlayState / GameOverState
                 |
                 +--> get_audio_manager()
                          |
                          +--> AudioManager
                                  +--> musica
                                  +--> efectos
                                  +--> volumen
                                  +--> manejo de errores
```

Los states solo solicitan acciones de audio. No conocen rutas, no cargan archivos directamente y no inicializan `pygame.mixer`.

## 2. Archivos actuales

La carpeta `assets(beta)/audio` contiene actualmente:

```text
MENUMUSIC.mp3
GAMEMUSIC.mp3
```

El modulo los registra con estos nombres logicos:

```python
AudioManager.MUSIC_FILES = {
    "menu": "MENUMUSIC.mp3",
    "game": "GAMEMUSIC.mp3",
}
```

Las rutas se calculan desde la ubicacion de `audio.py`, no desde el directorio actual de la terminal. Esto permite ejecutar el juego desde otra carpeta sin romper las rutas.

## 3. API publica

### Obtener el gestor compartido

```python
from audio import get_audio_manager

audio = get_audio_manager()
```

La funcion devuelve siempre la misma instancia durante la ejecucion. Asi se evita inicializar varios mixers o perder el estado del volumen al cambiar de state.

### Reproducir musica

```python
audio.play_music("menu")
audio.play_music("game")
```

Las pistas se reproducen en bucle por defecto. Tambien se puede indicar el numero de repeticiones:

```python
audio.play_music("menu", loops=0)
```

Metodos de conveniencia:

```python
audio.play_menu_music()
audio.play_game_music()
```

`play_game_music(bg_type=0)` conserva el argumento antiguo por compatibilidad, aunque actualmente la pista no depende de `bg_type`.

### Controlar musica

```python
audio.stop_music()
audio.pause_music()
audio.resume_music()
audio.set_music_volume(0.5)
```

El volumen se limita automaticamente al rango `0.0` a `1.0`.

### Reproducir efectos

```python
audio.play_sfx("card_select.wav")
```

El archivo debe existir en:

```text
assets(beta)/audio/card_select.wav
```

Los efectos se cargan bajo demanda y se guardan en una cache para no leer el archivo en cada evento.

## 4. Integracion con los states

### MenuState

Al entrar al menu:

```python
self.audio.play_menu_music()
```

Al salir:

```python
self.audio.stop_music()
```

### PlayState

Al entrar a la partida:

```python
self.audio.play_game_music()
```

Al salir se detiene la musica antes de que el siguiente state elija su pista.

### GameOverState

Al entrar al game over se detiene la musica porque todavia no existe una pista exclusiva para ese estado.

Para agregar una pista propia mas adelante:

```python
AudioManager.MUSIC_FILES = {
    "menu": "MENUMUSIC.mp3",
    "game": "GAMEMUSIC.mp3",
    "game_over": "GAMEOVERMUSIC.mp3",
}
```

Luego, desde `GameOverState.enter()`:

```python
self.audio.play_music("game_over")
```

## 5. Como agregar una nueva pista

1. Colocar el archivo en `assets(beta)/audio`.
2. Agregar el nombre logico en `MUSIC_FILES`.
3. Invocar `play_music("nombre_logico")` desde el state correspondiente.
4. Ejecutar la comprobacion de sintaxis y probar la transicion entre states.

Ejemplo:

```python
MUSIC_FILES = {
    "menu": "MENUMUSIC.mp3",
    "game": "GAMEMUSIC.mp3",
    "victory": "VICTORY.mp3",
}
```

No es necesario modificar `main.py` ni `game.py` para agregar la pista.

## 6. Como agregar un efecto de sonido

1. Agregar un archivo `.wav` u `.ogg` a `assets(beta)/audio`.
2. Desde el state, invocar `play_sfx()` cuando ocurre el evento.

Ejemplo para seleccionar una carta:

```python
self.audio.play_sfx("card_select.wav")
```

La llamada debe colocarse en el punto donde el state confirma que la seleccion cambio, no en `Renderer.py`. El renderer dibuja y el state decide que evento ocurrio.

Ejemplos de eventos posibles:

```text
card_select.wav       seleccion de carta
card_play.wav         jugada confirmada
discard.wav           descarte
joker.wav             Joker activado
round_clear.wav       ronda superada
game_over.wav         derrota
```

Actualmente estos archivos no existen; son nombres sugeridos para futuras incorporaciones.

## 7. Manejo de errores

`AudioManager` esta diseñado para que el audio sea opcional:

- Si el mixer falla, `enabled` queda en `False`.
- Si una pista no existe, `play_music()` devuelve `False`.
- Si un efecto no existe, `play_sfx()` devuelve `False`.
- Si Pygame rechaza un archivo, se informa y el juego continua.

Por eso los states no necesitan envolver cada llamada de audio en `try/except`.

Ejemplo de comprobacion opcional:

```python
if not self.audio.play_music("game"):
    self.message = "Audio no disponible"
```

No es obligatorio mostrar este mensaje al jugador; normalmente basta con continuar sin sonido.

## 8. Compatibilidad

El modulo conserva:

```python
SoundPlayer = AudioManager
```

Tambien mantiene:

```python
play_menu_music()
play_game_music(bg_type=0)
```

Esto evita romper codigo antiguo que importe `SoundPlayer`. El codigo nuevo debe preferir `get_audio_manager()` y `AudioManager`.

## 9. Reglas de diseño

1. No inicializar `pygame.mixer` desde un state.
2. No usar rutas relativas al directorio actual.
3. No cargar sonidos directamente desde `Renderer.py`.
4. Mantener las decisiones de eventos de audio en los states.
5. Mantener las rutas y nombres de archivos en `audio.py`.
6. Usar nombres logicos para las pistas.
7. Tratar el audio como una capacidad opcional.
8. Mantener `game.py` fuera de la nueva integracion.
9. Detener o cambiar la musica al entrar en un nuevo state.
10. Usar cache para efectos que se reproduzcan con frecuencia.

## 10. Validacion

Desde la raiz del proyecto:

```powershell
.venv\Scripts\python.exe -m py_compile audio.py states/menu_state.py states/play_state.py states/gameover_state.py
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

La prueba manual minima es:

1. Iniciar el juego.
2. Confirmar que el menu reproduce `MENUMUSIC.mp3`.
3. Entrar a jugar.
4. Confirmar que cambia a `GAMEMUSIC.mp3`.
5. Volver al menu y comprobar que la musica cambia otra vez.
6. Renombrar temporalmente una pista y confirmar que el juego sigue abriendo sin audio.

## 11. Futuras mejoras

El modulo puede ampliarse sin cambiar la arquitectura para incluir:

- Canal separado para musica y efectos.
- Fundidos entre pistas con `fadeout()` y `fade_ms`.
- Control de audio desde el menu.
- Lista de reproduccion.
- Pistas exclusivas para victoria y game over.
- Eventos de audio asociados a animaciones.
- Pruebas con mixer desactivado o archivos inexistentes.
