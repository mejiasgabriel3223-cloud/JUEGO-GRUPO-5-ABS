# Animaciones - Guia de uso y extension

## 1. Objetivo

`animaciones.py` contiene la capa visual de las animaciones del juego. Su objetivo es separar:

- la logica de juego y puntuacion, que pertenece a `PlayState`;
- el dibujo base de la mesa, que pertenece a `Renderer`;
- el movimiento temporal y los efectos visuales, que pertenecen a `animaciones.py`.

La integracion actual no modifica `game.py`. El flujo activo utiliza:

```text
PlayState
   |
   +--> AnimationController
           |
           +--> PlayAnimation
           +--> RefillAnimation
```

`PlayState` solo inicia, actualiza, dibuja y cancela el controlador. Los detalles de fases, duraciones, interpolacion, cola y posiciones se mantienen dentro de este modulo.

## 2. API publica actual

### `AnimationController`

Es la fachada publica para el resto del juego. Centraliza el acceso a las animaciones y evita que `PlayState` dependa directamente de una clase concreta.

Metodos actuales:

| Metodo | Funcion |
|---|---|
| `play_cards(...)` | Inicia la animacion de cartas jugadas. |
| `refill_cards(...)` | Inicia la entrada horizontal de cartas nuevas. |
| `handle_event(event)` | Entrega un evento a la animacion activa. |
| `update(dt)` | Avanza la animacion usando el tiempo transcurrido. |
| `draw(renderer, screen)` | Dibuja la animacion en el frame actual. |
| `cancel()` | Cancela y limpia la animacion activa. |
| `active` | Indica si existe una animacion en curso. |
| `animated_card_ids` | Identidades de cartas que el controlador dibuja temporalmente. |

Ejemplo de uso desde un estado:

```python
self.animations.play_cards(
    cards,
    start_positions,
    result.name,
    result.total,
)

# En update(dt)
self.animations.update(dt)

# En draw(screen)
if self.animations.active:
    self.animations.draw(self.renderer, screen)
```

### `PlayAnimation`

Es la implementacion concreta de la animacion de una mano jugada. Actualmente:

1. recibe las cartas y sus posiciones originales;
2. mueve las cartas al centro de la pantalla;
3. muestra el valor de cada carta;
4. muestra el nombre de la combinacion y el total obtenido;
5. espera confirmacion del jugador;
6. mueve las cartas fuera de la pantalla;
7. libera sus referencias al finalizar.

### `RefillAnimation`

Es la implementacion de la reposicion visual de cartas. Recibe las nuevas cartas y sus posiciones finales dentro de la mano. Las dibuja inicialmente fuera del borde derecho y las desplaza horizontalmente hasta esos destinos.

Caracteristicas:

- Duracion actual: `0.65` segundos.
- Movimiento solo en el eje X.
- La coordenada Y se mantiene en la posicion final de la mano.
- No crea, elimina ni modifica la coleccion de cartas.
- Libera sus referencias al terminar o cancelarse.

## 3. Ciclo de vida

La animacion utiliza estas fases:

```text
inactive
   |
   +--> entering
           |
           +--> holding
                    |
                    +--> exiting
                              |
                              +--> finished
```

### `inactive`

No hay cartas que dibujar. `active` devuelve `False`.

### `entering`

Las cartas se desplazan desde sus posiciones originales hacia el centro. La duracion actual es `0.45` segundos.

### `holding`

Las cartas permanecen en el centro y se muestra el resultado. La pulsacion de `SPACE` inicia la salida.

### `exiting`

Las cartas se desplazan hacia el lado derecho de la pantalla. La duracion actual es `0.75` segundos.

### `finished`

La animacion elimina las cartas y sus posiciones. En el siguiente frame queda inactiva.

## 4. Como se integra con `PlayState`

### Inicio

`PlayState.play_selected()` sincroniza primero los `pygame.Rect` de la mano y guarda las posiciones de las cartas seleccionadas. Despues evalua la jugada, actualiza la puntuacion e inicia la animacion.

Es importante guardar las posiciones antes de retirar las cartas de `self.cards`:

```python
self._sync_card_rects()
start_positions = [
    (card.rect.x, card.rect.y)
    for card in best
    if card.rect is not None
]
```

### Bloqueo de entradas

Mientras `self.animations.active` es verdadero, `PlayState` no permite seleccionar ni jugar nuevas cartas. Solo entrega los eventos al controlador. `ESC` cancela la animacion y solicita volver al menu.

### Actualizacion

`PlayState.update(dt)` llama una vez por frame a:

```python
self.animations.update(dt)
```

`dt` esta expresado en segundos y procede del reloj principal de Pygame.

### Dibujo

El estado dibuja HUD y Jokers normalmente. Para la mano utiliza el controlador mientras la animacion esta activa:

```python
if self.animations.active:
    self.animations.draw(self.renderer, target_screen)
else:
    self.renderer.draw_hand(card_data)
```

### Reposicion de cartas

La logica de juego crea y agrega las cartas; la animacion solo recibe una copia de las referencias necesarias para dibujarlas. En `play_selected()` y `discard_selected()` el flujo es:

```text
crear new_cards
    |
agregar new_cards a self.cards
    |
barajar la mano
    |
sincronizar Rects finales
    |
AnimationController.refill_cards(new_cards, posiciones)
```

Los comentarios junto a este bloque en `PlayState` documentan deliberadamente la frontera entre responsabilidades: `PlayState` conoce la coleccion y las posiciones; `animaciones.py` conoce el movimiento y el dibujo.

La reposicion no comienza al mismo tiempo que `PlayAnimation`. `AnimationController` guarda la solicitud en `pending_refill` y la inicia automaticamente cuando `PlayAnimation` termina su salida.

Durante toda la secuencia, `PlayState` dibuja la mano normal y excluye las cartas animadas mediante `animated_card_ids`. Las cartas no seleccionadas permanecen visibles; las cartas jugadas y nuevas solo las dibuja su animacion correspondiente, evitando duplicados.

Los destinos de `RefillAnimation` se copian al iniciar. Por ello, las llamadas posteriores de `PlayState._sync_card_rects()` no cambian la trayectoria ni el punto final de las cartas que estan entrando.

El orden visual es:

```text
mano normal sin cartas nuevas
    |
cartas jugadas en el centro
    |
cartas nuevas entrando desde la derecha
    |
mano normal completa al finalizar
```

## 5. Como modificar la animacion existente

### Cambiar duraciones

Modificar las constantes de `PlayAnimation`:

```python
ENTRY_DURATION = 0.45
EXIT_DURATION = 0.75
```

Por ejemplo:

```python
ENTRY_DURATION = 0.7
EXIT_DURATION = 1.0
```

### Cambiar la posicion final

La posicion de destino se calcula en `draw()`. Para cambiar el centro, ajustar la logica de `center_x`, `center_y` o `target_start_x`.

### Cambiar el movimiento

La variable `eased` suaviza el movimiento usando una curva smoothstep:

```python
eased = progress * progress * (3.0 - 2.0 * progress)
```

Se puede sustituir por otra funcion local, por ejemplo:

```python
eased = progress * progress
```

Conviene mantener `progress` limitado entre `0.0` y `1.0` para evitar posiciones inesperadas.

### Cambiar textos y colores

El texto de cada carta se genera con:

```python
label = font.render(f"+{value}", True, (255, 225, 80))
```

El resultado global se genera con:

```python
f"{self.result_name}  |  +{self.total} puntos"
```

Estas lineas pueden cambiarse sin modificar `PlayState`.

## 6. Como agregar una animacion nueva

La forma recomendada es crear una nueva clase en `animaciones.py` con el mismo ciclo basico:

```python
class DiscardAnimation:
    def __init__(self):
        self.active = False
        self.elapsed = 0.0

    def start(self, cards):
        self.cards = list(cards)
        self.elapsed = 0.0
        self.active = bool(self.cards)

    def handle_event(self, event):
        pass

    def update(self, dt):
        if not self.active:
            return
        self.elapsed += max(0.0, dt)
        if self.elapsed >= 0.5:
            self.active = False

    def draw(self, renderer, screen):
        if not self.active:
            return
        # Dibujar el efecto de descarte aqui.
```

Despues se agrega al controlador:

```python
class AnimationController:
    def __init__(self):
        self.play_cards_animation = PlayAnimation()
        self.discard_animation = DiscardAnimation()
```

Y se expone una operacion publica:

```python
def discard_cards(self, cards):
    self.discard_animation.start(cards)
```

Si el juego necesita varias animaciones simultaneas, el controlador debe combinar sus estados en lugar de mantener una sola propiedad `active`. Una opcion sencilla es:

```python
@property
def active(self):
    return (
        self.play_cards_animation.active
        or self.discard_animation.active
    )
```

La misma idea puede utilizarse para:

- `joker_activation()`;
- `round_transition()`;
- `victory()`;
- `card_draw()`;
- `score_popup()`.

Para una nueva animacion de entrada de cartas, se recomienda seguir la firma de `refill_cards(cards, target_positions)` y crear otra clase especializada si el movimiento o la fase son diferentes.

## 7. Patron recomendado para futuras animaciones

Cada animacion nueva deberia tener, como minimo:

```text
constructor
start(...)
handle_event(event)
update(dt)
draw(renderer, screen)
cancel()
active
```

Responsabilidades de cada metodo:

- `start()`: recibe los datos necesarios y reinicia el estado interno.
- `handle_event()`: procesa solo eventos relevantes para esa animacion.
- `update(dt)`: modifica tiempos y fases; no dibuja.
- `draw()`: dibuja; no cambia la logica de la partida.
- `cancel()`: libera cartas, superficies y datos temporales.
- `active`: informa si debe bloquearse la interaccion del juego.

## 8. Reglas de diseño

1. No calcular puntuacion dentro de `animaciones.py`.
2. No retirar ni agregar cartas a `EntityCollection` desde una animacion.
3. No cambiar rondas, manos o descartes desde una animacion.
4. Recibir datos ya calculados por `PlayState`.
5. Usar `dt` para que la velocidad no dependa de los FPS.
6. Liberar referencias al terminar o cancelar.
7. Mantener `Renderer` como responsable del dibujo base de cartas.
8. Agregar metodos publicos al `AnimationController` antes de usarlos desde un estado.
9. Mantener `game.py` fuera de la nueva integracion.
10. Probar cada animacion con pygame inicializado y, cuando sea posible, con una superficie fuera de pantalla.

## 9. Pruebas manuales recomendadas

1. Iniciar el juego y entrar en `PLAY`.
2. Seleccionar una o varias cartas.
3. Pulsar `SPACE`.
4. Confirmar que las cartas se desplazan al centro.
5. Confirmar que el nombre de la jugada y los puntos aparecen.
6. Pulsar `SPACE` durante la fase de espera.
7. Confirmar que las cartas salen y la mano vuelve a estar disponible.
8. Pulsar `ESC` durante la animacion y comprobar que se cancela.
9. Intentar hacer clic o jugar otra mano mientras la animacion esta activa.
10. Reiniciar el estado y comprobar que no quedan cartas de una animacion anterior.

## 10. Validacion automatica

Desde la raiz del proyecto:

```powershell
.venv\Scripts\python.exe -m py_compile animaciones.py states/play_state.py
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

La suite actual valida principalmente `entities/`. Se recomienda agregar pruebas especificas para:

- transiciones `entering`, `holding`, `exiting` y `finished`;
- `cancel()`;
- avance por `dt`;
- bloqueo de entradas en `PlayState`;
- multiples animaciones en `AnimationController`.

## 11. Ejemplo de ampliacion futura

Para agregar una animacion de activacion de Joker, el flujo esperado seria:

```text
PlayState calcula Jokers activados
        |
AnimationController.joker_activation(names)
        |
JokerAnimation.start(names)
        |
update(dt)
        |
 draw(renderer, screen)
        |
finaliza y devuelve el control a PlayState
```

La regla importante es que `PlayState` solo indique que ocurrio la activacion. La forma en que aparece visualmente debe permanecer dentro de `animaciones.py`.
