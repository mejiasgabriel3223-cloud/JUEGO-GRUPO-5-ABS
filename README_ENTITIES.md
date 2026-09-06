# Entidades del proyecto

La carpeta `entities/` contiene el **modelo de dominio** del juego. La idea es que las reglas no dependan de Pygame: Pygame solamente coordina eventos y renderiza los datos.

## Arquitectura

```text
entities/
├── base.py       -> abstraccion Entity + ScoreContext
├── card.py       -> PlayingCard, Rank, Suit
├── deck.py       -> Deck[T] (plantilla/Generics)
├── hand.py       -> Hand
├── joker.py      -> Joker + implementaciones polimorficas
├── scoring.py    -> evaluacion de manos + recursion
├── player.py     -> Player
├── round.py      -> RoundState
├── factory.py    -> StandardDeckFactory
└── __init__.py
```

## Pilares de POO demostrados

### Abstraccion
`Entity` y `Joker` son clases abstractas. Obligan a las entidades concretas a exponer una interfaz comun.

### Clases y herencia
`FlatChipsJoker` y `MultiplierJoker` heredan de `Joker`.

### Encapsulamiento
`Deck` guarda las cartas en `_cards` y `Hand` en `_cards`; el resto del proyecto accede mediante operaciones controladas como `draw()`, `add()`, `toggle()` y `remove_selected()`.

### Polimorfismo
`HandEvaluator.apply_jokers()` llama `joker.apply(...)` sin comprobar el tipo concreto del Joker. Cada subclase decide como modificar el puntaje.

### Recursividad
`Deck.draw_many()` y `HandEvaluator._sum_chips_recursive()` usan recursion acotada para cumplir el requisito de la asignatura sin introducir recursion en el ciclo de Pygame.

### Plantillas / Generics
`Deck[T]` es una clase generica. Puede manejar `Deck[PlayingCard]` u otra entidad reutilizable.

## Integracion

El `game.py` mantiene el nombre `CarreraDeObstaculos` para no romper el `main.py` actual, pero ahora ese nombre es un alias de `CardGame`.

El renderer existente acepta diccionarios con las claves `rank`, `suit` y `selected`, por eso `PlayingCard.to_dict()` genera exactamente esa interfaz. Esto permite conectar el modelo nuevo sin reescribir `Renderer.py`.

## Flujo del juego

```text
MENU
  -> SELECTOR
  -> CardGame.reset_game()
  -> robo inicial de 8 cartas
  -> seleccionar 1..5 cartas
  -> evaluar jugada
  -> aplicar Jokers
  -> sumar score
  -> reponer mano
  -> comprobar objetivo/ronda
  -> GAMEOVER o siguiente ronda
```

## Pruebas

Las pruebas de `tests/test_entities.py` no necesitan Pygame y pueden ejecutarse con:

```bash
python -m unittest discover -s tests -v
```
