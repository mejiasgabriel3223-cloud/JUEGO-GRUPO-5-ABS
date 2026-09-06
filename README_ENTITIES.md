# Entities — arquitectura rehecha del proyecto

## Objetivo

La primera versión de `entities/` estaba distribuida en demasiados módulos. Esta versión reduce la capa a **4 módulos funcionales** con responsabilidades claras:

```text
entities/
├── entities.py       # entidades del dominio + colección dinámica genérica
├── card_factory.py   # creación aleatoria de cartas + Rect + asset
├── jokers.py         # Jokers y probabilidades
├── rules.py          # score, multiplier y evaluación
└── __init__.py       # API pública del paquete
```

El diseño responde directamente a la necesidad del proyecto: tener una colección de cartas que pueda crecer, disminuir, contener duplicados y reorganizarse; Jokers independientes con probabilidad; y reglas globales que interactúan con atributos modificables de cada carta.

---

## 1. `entities.py`

### `Entity`

`Entity` es la abstracción base. Define el contrato `entity_id` para que cualquier entidad futura pueda identificarse de forma estable. Es una clase abstracta y por tanto no pretende representar un objeto concreto por sí misma.

### `CardEntity`

Representa una carta jugable. Sus atributos importantes son:

| Atributo | Función |
|---|---|
| `rank` | Valor visible de la carta (`2`...`10`, `J`, `Q`, `K`, `A`). |
| `suit` | Palo de la carta mediante su símbolo. |
| `score` | Puntaje base/modificador de esa instancia. |
| `multiplier` | Multiplicador propio de esa instancia. |
| `selected` | Estado de selección para jugar o descartar. |
| `asset_path` | Ruta esperada del asset asociado. |
| `rect` | `pygame.Rect` usado para ubicar la carta visualmente. |

El objeto **no carga la imagen** y no dibuja nada. Guarda la referencia del asset y el `Rect`; la presentación continúa siendo responsabilidad del `Renderer` existente. Esto evita que la entidad dependa de toda la interfaz.

Dos cartas pueden tener exactamente el mismo `rank` y `suit` y seguir siendo entidades distintas. Esto es intencional porque el arreglo del proyecto debe permitir duplicados.

`apply_bonus()` permite que un Joker altere una carta sin reemplazar la instancia.

### `EntityCollection[T]`

Es el nuevo arreglo dinámico del sistema. Utiliza `Generic[T]`, que actúa como la plantilla/genérico exigido por el proyecto.

Características:

- admite duplicados;
- puede crecer;
- puede disminuir;
- puede limpiarse;
- puede barajarse;
- puede recorrerse como una secuencia;
- puede reutilizarse para diferentes tipos de entidad.

El crecimiento de `resize()` utiliza una llamada recursiva controlada. Así la recursividad tiene una responsabilidad concreta: crear repetidamente entidades hasta alcanzar el tamaño solicitado.

Ejemplo:

```python
cards = EntityCollection()
cards.resize(8, factory.create_random_card)
cards.add(factory.create_card("A", "S"))
cards.add(factory.create_card("A", "S"))  # duplicado permitido
cards.resize(5)
cards.shuffle()
```

La idea representa un mazo flexible: una mecánica futura de paquetes puede aumentar o disminuir su tamaño y duplicar cartas sin cambiar la clase.

---

## 2. `card_factory.py`

### `CardFactory`

Este módulo tiene una única responsabilidad: **crear cartas**. No evalúa manos y no decide los efectos de los Jokers.

Cuando crea una carta:

1. escoge `rank` y `suit`;
2. calcula el valor inicial;
3. construye un `pygame.Rect`;
4. busca la ruta del asset en las ubicaciones conocidas;
5. devuelve un `CardEntity`.

La creación es aleatoria, por lo que puede producir la misma combinación más de una vez. Eso permite representar directamente el requisito de duplicación de cartas.

El método `create_random_collection(amount)` produce un lote de cartas independientes.

El factory busca primero rutas como:

```text
assets/cards/AS.png
assets/card/AS.png
assets/AS.png
assets(beta)/cards/AS.png
```

Si el archivo todavía no existe, conserva una ruta determinista. El juego no depende de que el asset exista para mantener la lógica de la carta.

---

## 3. `jokers.py`

### `Joker`

Es una clase abstracta que define el comportamiento común de todos los Jokers. Cada Joker tiene:

- `name`;
- `probability`;
- `active`;
- `apply()` abstracto;
- `activate()` común.

La probabilidad se representa como un valor entre `0.0` y `1.0`. Por ejemplo, `0.75` significa que el Joker intenta activarse con un 75 % de probabilidad cuando se evalúa.

### Polimorfismo

`FlatChipsJoker` y `MultiplierJoker` heredan de `Joker` y sobrescriben `apply()`:

```text
Joker
  ├── FlatChipsJoker
  └── MultiplierJoker
```

El código externo solo necesita llamar:

```python
joker.activate(cards)
```

No necesita conocer qué subclase está utilizando. Cada implementación produce un efecto diferente sobre las cartas.

### Modificación de cartas

`FlatChipsJoker` aumenta `card.score`.

`MultiplierJoker` aumenta `card.multiplier`.

Por tanto los Jokers modifican directamente los atributos definidos por cada entidad de carta, mientras `GameRules` sigue controlando las reglas globales.

`RandomJokerPool` agrupa los Jokers activos y permite ejecutar todos sus intentos de activación.

---

## 4. `rules.py`

### `GameRules`

Aquí está la fuente central de las reglas globales. Sus dos valores principales son:

```python
rules.score
rules.multiplier
```

Cambiar `GameRules.score` cambia el puntaje base aplicado a las siguientes evaluaciones. Cambiar `GameRules.multiplier` cambia el multiplicador base de las siguientes evaluaciones.

Esto evita guardar las reglas globales en cada carta. Cada carta, en cambio, conserva sus propios valores `score` y `multiplier`, que los Jokers pueden alterar.

### Flujo del cálculo

```text
GameRules global
      +
valor de la combinación
      +
score individual de las cartas
      +
multiplier individual de las cartas
      ↓
HandResult
      ↓
total = score × multiplier
```

### Combinaciones soportadas

- High Card
- Pair
- Two Pair
- Three of a Kind
- Straight
- Flush
- Full House
- Four of a Kind
- Straight Flush

La suma del `score` individual de las cartas se realiza mediante recursividad en `_sum_card_score_recursive()`.

### `HandResult`

Es un resultado inmutable de una evaluación. Contiene `name`, `score`, `multiplier` y calcula `total`. Esto permite separar el resultado de una jugada de la entidad de carta.

---

## 5. Composición general

La composición de la nueva solución es:

```text
CardFactory
    │
    ├── crea CardEntity
    │      ├── rank
    │      ├── suit
    │      ├── score
    │      ├── multiplier
    │      ├── asset_path
    │      └── Rect
    │
    ▼
EntityCollection[CardEntity]
    │
    ├── permite duplicados
    ├── aumenta/disminuye
    └── shuffle()
    │
    ├───────────────┐
    ▼               ▼
GameRules       RandomJokerPool
    │               │
    │               ├── Joker
    │               ├── FlatChipsJoker
    │               └── MultiplierJoker
    │
    └──────► evalúa cartas ◄────── modifica cartas
```

---

## 6. Pilares de POO usados

### Abstracción
`Entity` y `Joker` definen contratos generales sin implementar un objeto concreto completo.

### Clases y herencia
`FlatChipsJoker` y `MultiplierJoker` heredan de `Joker`.

### Encapsulamiento
La colección mantiene su lista interna `_items`. El resto del programa trabaja con operaciones como `add`, `remove_at`, `resize`, `shuffle` y `clear`, en lugar de manipular libremente la lista interna.

### Polimorfismo
Diferentes subclases de `Joker` responden al mismo método `apply()` con efectos distintos.

### Recursividad
Se utiliza en dos responsabilidades concretas:

1. `EntityCollection._grow_recursive()` para aumentar el arreglo hasta un tamaño objetivo.
2. `GameRules._sum_card_score_recursive()` para acumular el score de las cartas.

### Plantillas / Generics
`EntityCollection[T]` permite declarar colecciones como `EntityCollection[CardEntity]` sin crear una clase distinta por cada tipo.

---

## 7. Integración con el proyecto existente

La capa nueva no reemplaza el shell del proyecto. El `main.py` sigue creando `CarreraDeObstaculos` y sigue trabajando con los métodos que ya esperaba.

La modificación de integración está concentrada en `game.py`. Ese archivo funciona como adaptador entre:

```text
main.py
   ↓
game.py
   ↓
entities/
   ↓
Renderer.py
```

`Renderer.py` no necesita conocer `GameRules`, `Joker` ni `EntityCollection`; recibe los datos que ya esperaba (`rank`, `suit`, `selected`, etc.).

No se modifican `main.py`, `audio.py`, `menu/`, `settings.py` ni los assets.

---

## 8. Flujo de una ronda

```text
reset_game()
   ↓
CardFactory crea cartas aleatorias
   ↓
EntityCollection[CardEntity]
   ↓
shuffle()
   ↓
Jugador selecciona cartas
   ↓
GameRules evalúa combinación
   ↓
RandomJokerPool prueba probabilidades
   ↓
Jokers modifican score/multiplier de las cartas
   ↓
GameRules vuelve a evaluar
   ↓
HandResult.total
   ↓
se actualiza el score de la ronda
   ↓
la siguiente ronda vuelve a reorganizar el arreglo
```

---

## 9. Por qué esta arquitectura tiene mayor cohesión

Cada módulo agrupa elementos que cambian por la misma razón:

- `entities.py`: estructura y comportamiento base de las entidades.
- `card_factory.py`: creación y metadata visual de cartas.
- `jokers.py`: reglas de activación y efectos de Jokers.
- `rules.py`: evaluación y cálculo global.

No existe un módulo dedicado exclusivamente a una clase mínima como `Player`, `Round`, `Hand` o `Scoring`. Eso evita repartir una responsabilidad pequeña entre muchos archivos.

El acoplamiento con Pygame queda limitado a `card_factory.py` y al adaptador `game.py`, que son precisamente las fronteras necesarias para conectar lógica y presentación. Las reglas, Jokers y entidades principales no dependen del `Renderer`.

---

## 10. Extensión futura

El diseño permite añadir mecánicas sin volver a fragmentar el proyecto. Por ejemplo:

**Duplicar cartas:** simplemente añadir otra instancia de `CardEntity` al `EntityCollection`.

**Paquete que reduce el mazo:** llamar `resize()` con un objetivo menor o eliminar entidades concretas.

**Paquete que aumenta el mazo:** llamar `resize()` con un factory.

**Nuevo Joker:** crear otra subclase de `Joker` que implemente `apply()`.

**Nuevo modificador de cartas:** ampliar `CardEntity` o utilizar `apply_bonus()`.

**Modificar la economía global:** ampliar `GameRules` sin mover la responsabilidad a las cartas.

Esto mantiene el sistema escalable sin volver a crear módulos innecesarios.
