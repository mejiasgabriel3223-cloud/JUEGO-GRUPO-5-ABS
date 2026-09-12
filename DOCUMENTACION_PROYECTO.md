# Running Time! - Documentacion tecnica

**Fecha de revision:** 2026-09-12  
**Estado:** prototipo jugable de cartas en Pygame

## 1. Resumen

El proyecto es un juego de cartas desarrollado con Python y Pygame. La implementacion actual incluye menu, entrada de nombre, records, mano de cartas, evaluacion de combinaciones, puntuacion, Jokers, descartes, reposicion, rondas y una animacion modular para las cartas jugadas.

El punto de entrada real es `main.py`. `game.py` conserva un controlador anterior compatible, pero el flujo actual basado en `states/` no lo utiliza.

## 2. Requisitos y ejecucion

- Python 3.10 o superior.
- Pygame 2.5 o superior.
- OpenCV opcional para el video de fondo del menu.

Dependencias de `requirements.txt`:

```text
pygame>=2.5
opencv-python-headless>=4.10.0
```

Instalacion en Windows:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py main.py
```

Si PowerShell bloquea la activacion:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

Tambien puede ejecutarse con:

```powershell
.venv\Scripts\python.exe main.py
```

## 3. Bucle principal

`main.py` inicializa Pygame, crea los estados y ejecuta este ciclo por frame:

```text
pygame.event.get()
        |
current_state.handle_events(events)
        |
current_state.update(dt)
        |
current_state.draw(screen)
        |
pygame.display.flip()
```

`handle_events()` y `update()` pueden devolver el nombre de un estado destino. `main.py` decide entonces si cambia de estado.

Estados registrados actualmente:

```text
MENU <-----------------------------+
  |                                |
  +--> PLAY -----------------------+
          |                        |
          +--> GAME_OVER ----------+
          +--> VICTORY (finaliza)
          +--> SHOP (reinicia ronda)
```

La transicion a `SHOP` se resuelve actualmente reiniciando la ronda. `GAME_OVER` activa ahora `GameOverState`, que guarda el record y permite reintentar o volver al menu. `VICTORY` sigue siendo un cierre temporal del programa porque todavia no existe un estado visual de victoria.

Las transiciones entre estados pasan por una funcion centralizada de `main.py`. Esta funcion llama a `exit()` en el estado anterior y a `enter()` en el nuevo estado, evitando dejar audio, animaciones o datos temporales activos.

## 4. Estados

### `states/base_state.py`

Define el contrato comun:

- `handle_events(events)`: procesa entradas.
- `update(dt)`: actualiza logica y puede devolver una transicion.
- `draw(screen)`: dibuja el estado.

### `states/menu_state.py`

`MenuState` gestiona las pantallas internas:

```text
PRINCIPAL
  +--> NAME_INPUT
  +--> RECORDS
  +--> REPLACE_PROMPT
```

Responsabilidades:

- Cargar la configuracion del menu.
- Mostrar logo y botones.
- Leer el nombre del jugador.
- Cargar y guardar `records.json`.
- Actualizar el video de fondo cuando OpenCV esta disponible.
- Devolver `PLAY` al confirmar el nombre.

Si el video no esta disponible, usa un fondo de color como fallback.

### `states/play_state.py`

Es el estado principal de la partida. Controla:

- Mano y seleccion de cartas.
- Evaluacion mediante `GameRules`.
- Activacion de Jokers.
- Score de la ronda.
- Manos y descartes disponibles.
- Reposicion y barajado.
- Objetivo y ronda actual.
- Integracion del sistema de animaciones.

Flujo de una jugada:

```text
seleccionar cartas
        |
SPACE o ENTER
        |
validar seleccion
        |
obtener la mejor mano
        |
guardar posiciones visuales
        |
evaluar y activar Jokers
        |
calcular resultado final
        |
actualizar score y manos
        |
iniciar animacion
        |
retirar y reponer cartas
```

Mientras una animacion esta activa, el estado bloquea la seleccion y las nuevas jugadas. `SPACE` avanza la animacion de cartas jugadas y `ESC` la cancela y solicita volver al menu.

### `states/gameover_state.py`

Lee el score y el nombre desde `context`, guarda el record y muestra controles para reintentar o volver al menu.

Flujo actual:

```text
PLAY devuelve GAME_OVER
        |
main.py cambia a GAME_OVER
        |
GameOverState.enter() guarda el record
        |
GameOverState.draw() muestra la pantalla
        |
ENTER/R -> PLAY
ESC     -> MENU
```

## 5. Arquitectura de modulos

```text
main.py
  |
  +--> states/
  |      +--> menu_state.py
  |      +--> play_state.py
  |      +--> gameover_state.py
  |      +--> base_state.py
  |
  +--> PlayState
         +--> entities/
         +--> Renderer.py
         +--> animaciones.py
```

### `Renderer.py`

Dibuja el HUD, Jokers, mano y cartas. Recibe datos serializados mediante `CardEntity.to_dict()`. La representacion actual puede funcionar sin cargar todas las imagenes de los assets.

### `entities/`

Contiene la logica del dominio:

- `entities.py`: `Entity`, `CardEntity` y `EntityCollection`.
- `card_factory.py`: creacion aleatoria, `pygame.Rect` y rutas de assets.
- `rules.py`: combinaciones, scores, multiplicadores y `HandResult`.
- `jokers.py`: Jokers y activacion probabilistica.
- `__init__.py`: API publica.

`EntityCollection` permite duplicados, crecimiento, reduccion, eliminacion y barajado.

### `game.py`

Contiene `CarreraDeObstaculos`, un adaptador de una version anterior. Incluye una integracion propia de `PlayAnimation`, pero no forma parte del flujo activo basado en `states/`. Las nuevas animaciones deben agregarse en `animaciones.py` y conectarse desde `PlayState`.

## 6. Puntuacion

La evaluacion combina valores globales, la combinacion detectada y los modificadores de cada carta:

```text
score final = score global
           + score de la combinacion
           + score de cada carta

multiplicador final = multiplicador global
                    + multiplicador de cada carta

total = score final * multiplicador final
```

Los Jokers modifican cartas antes de la evaluacion final. `round_score` acumula los puntos de la ronda actual; todavia no existe un `total_score` separado para toda la partida.

## 7. Controles

| Accion | Control |
|---|---|
| Navegar menu | Flechas o W/S |
| Confirmar opcion | ENTER |
| Escribir nombre | Teclado |
| Borrar nombre | BACKSPACE |
| Seleccionar carta | Clic izquierdo |
| Jugar cartas | SPACE o ENTER |
| Descartar cartas | D |
| Avanzar animacion | SPACE |
| Cancelar animacion | ESC |
| Volver al menu | ESC |

## 8. Animaciones

`animaciones.py` contiene `PlayAnimation`, que muestra las cartas jugadas en el centro, y `RefillAnimation`, que introduce las cartas nuevas desde la esquina inferior derecha. `AnimationController` es la fachada que utiliza `PlayState`.

```text
PlayState
  +--> AnimationController
                                        +--> PlayAnimation
                                        +--> RefillAnimation
```

El estado solo informa las cartas y sus posiciones finales mediante `play_cards()` y `refill_cards()`. Las fases, duraciones, cola, interpolacion y dibujo permanecen en `animaciones.py`.

La reposicion se encola mientras las cartas jugadas estan en el centro. Cuando terminan de salir por la derecha, `AnimationController` inicia `RefillAnimation`. La mano normal continua visible y excluye temporalmente las cartas nuevas para evitar que aparezcan duplicadas.

La guia completa para modificar o agregar animaciones esta en [README_ANIMACIONES.md](README_ANIMACIONES.md).

## 9. Records, configuracion y assets

### Records

`records.json` contiene objetos con `name` y `score`. `MenuState` los carga, ordena y guarda.

### Configuracion

`settings.py` define:

- Resolucion: `1280 x 720`.
- Frecuencia objetivo: `60 FPS`.
- Directorio base y assets.
- Fuente con fallback de Pygame.

### Assets

Las carpetas principales son:

```text
assets/
assets(beta)/
  audio/
  cards/
  cartas_Españolas/
```

`CardFactory` conserva rutas de assets en las cartas. Los archivos `__MACOSX`, `._*` y `.DS_Store` son metadatos y no forman parte de la logica del juego.

## 10. Audio

`audio.py` contiene `AudioManager`, un servicio compartido y tolerante a fallos. Los states lo obtienen mediante `get_audio_manager()` y no inicializan el mixer directamente.

Integracion actual:

```text
MenuState      -> play_menu_music()
PlayState      -> play_game_music()
GameOverState  -> stop_music()
```

Las pistas disponibles son:

```text
assets(beta)/audio/MENUMUSIC.mp3
assets(beta)/audio/GAMEMUSIC.mp3
```

Si el mixer no puede inicializarse o falta un archivo, el juego continua sin audio. `play_sfx()` ya esta preparado para efectos futuros, aunque actualmente no hay archivos `.wav` u `.ogg` en la carpeta de audio.

La clase `SoundPlayer` se conserva como alias de compatibilidad. La guia para agregar pistas, efectos y nuevos eventos esta en [README_AUDIO.md](README_AUDIO.md).

## 11. Pruebas

La suite disponible esta en `tests/test_entities.py` y cubre colecciones, cartas, Jokers y reglas.

Ejecutar:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Comprobar sintaxis del sistema de animaciones:

```powershell
.venv\Scripts\python.exe -m py_compile animaciones.py states/play_state.py
```

Faltan pruebas de estados, transiciones, bloqueo de entradas y ciclo de vida de animaciones.

## 12. Limitaciones conocidas

1. `VICTORY` todavia no tiene una pantalla visual propia.
2. `SHOP` no es un estado independiente.
3. `round_score` no esta separado de un score total de partida.
4. `game.py` conserva nombres heredados y logica duplicada.
5. La cobertura automatizada se concentra en `entities/`.
6. La carga de imagenes de cartas no esta completamente integrada.

## 13. Recomendaciones

1. Conectar `GAME_OVER` con `GameOverState` en `main.py`.
2. Crear estados reales para tienda y victoria.
3. Separar `round_score` de `total_score`.
4. Agregar pruebas de `PlayState` y `AnimationController`.
5. Mantener `game.py` como compatibilidad temporal y no agregarle nueva logica.
6. Incorporar futuras animaciones mediante la API de `README_ANIMACIONES.md`.
