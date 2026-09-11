He actualizado el contenido documental considerando el código y archivos adjuntos. Sustituye `DOCUMENTACION_PROYECTO.md` por:

````markdown
# Running Time! — Documentación técnica

**Fecha de revisión:** 2026-09-10  
**Estado:** prototipo jugable de cartas en Pygame

## 1. Resumen

El proyecto es un juego de cartas desarrollado con Python y Pygame. Aunque conserva nombres heredados de un prototipo de carreras (`CarreraDeObstaculos`), la implementación actual utiliza:

- Cartas españolas y cartas tipo póker.
- Selección de cartas con el ratón.
- Evaluación de combinaciones.
- Sistema de puntuación y multiplicadores.
- Jokers con activación probabilística.
- Descarte y reposición de cartas.
- Tres rondas con objetivos progresivos.
- Menú, entrada de nombre, records y pantalla de game over.

El núcleo de cartas ya está conectado al flujo principal mediante `game.py` y `Renderer.py`.

## 2. Ejecución

### Requisitos

- Python 3.10 o superior.
- Pygame 2.5 o superior.

### Instalación en Windows

Desde la carpeta raíz del proyecto:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py main.py
```

Si PowerShell bloquea la activación:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

## 3. Flujo de estados

```text
MENU
  -> NAME_INPUT
  -> SELECTOR
  -> JUGANDO
  -> GAMEOVER
  -> MENU
```

### MENU

Gestionado por `menu/estado_menu.py`.

Incluye:

- Jugar.
- Records.
- Créditos.
- Salir.
- Navegación con flechas o W/S.
- Confirmación con ENTER.

### NAME_INPUT

Permite introducir el nombre del jugador.

- Máximo: 16 caracteres.
- BACKSPACE elimina caracteres.
- ENTER confirma.
- Si se deja vacío, se usa `Jugador`.
- ESC cancela.

### SELECTOR

Actualmente utiliza `SelectorDummy`.

No existe todavía un selector visual real de personajes. Al pulsar ENTER o ESPACIO se selecciona automáticamente `Player`.

### JUGANDO

La partida de cartas se controla desde `CarreraDeObstaculos`.

Características actuales:

- Mano inicial de 8 cartas.
- Se pueden seleccionar entre 1 y 5 cartas.
- Se pueden jugar manos con ESPACIO o ENTER.
- Se pueden descartar cartas con D.
- Las cartas jugadas o descartadas se reemplazan.
- La ronda tiene 4 manos y 3 descartes.
- El objetivo inicial es 100 puntos.
- Se juegan hasta 3 rondas.
- El objetivo aumenta en cada ronda.

### GAMEOVER

Se muestra cuando:

- Se agotan las manos disponibles.
- Se completan las rondas configuradas.

Controles:

- ENTER reinicia la partida.
- ESC vuelve al menú y guarda el resultado.

## 4. Controles

| Acción | Control |
|---|---|
| Navegar por el menú | Flechas o W/S |
| Confirmar menú | ENTER |
| Escribir nombre | Teclado |
| Borrar nombre | BACKSPACE |
| Seleccionar carta | Clic izquierdo |
| Jugar cartas | ESPACIO o ENTER |
| Descartar cartas | D |
| Volver al menú | ESC |
| Reiniciar game over | ENTER |

## 5. Arquitectura

```text
main.py
├── Máquina de estados
├── Inicialización de Pygame
├── Audio
├── EstadoMenu
└── CarreraDeObstaculos
    ├── Renderer
    ├── CardFactory
    ├── EntityCollection
    ├── GameRules
    └── RandomJokerPool
```

### `main.py`

Es el punto de entrada.

Responsabilidades:

- Inicializar Pygame.
- Crear la ventana.
- Crear el reloj principal.
- Gestionar eventos globales.
- Cambiar entre estados.
- Guardar records al abandonar game over.

### `game.py`

Funciona como adaptador entre la máquina de estados existente y la nueva lógica de cartas.

La clase `CarreraDeObstaculos` conserva el nombre antiguo para mantener compatibilidad con `main.py`, pero actualmente representa el controlador de la partida de cartas.

Responsabilidades:

- Crear y reiniciar partidas.
- Gestionar cartas seleccionadas.
- Jugar y descartar cartas.
- Actualizar rondas y objetivos.
- Coordinar reglas, Jokers y renderer.
- Exponer el score al sistema de records.

### `Renderer.py`

Dibuja la interfaz de cartas:

- HUD.
- Puntuación.
- Objetivo.
- Fichas y multiplicador.
- Jokers.
- Mano de cartas.
- Cartas seleccionadas.
- Consumibles.

Actualmente dibuja cartas mediante texto (`rank` y `suit`), no mediante imágenes de los assets.

### `entities/entities.py`

Contiene:

- `Entity`.
- `CardEntity`.
- `EntityCollection`.

`EntityCollection` permite:

- Duplicados.
- Crecimiento y reducción.
- Eliminación.
- Barajado.
- Recorrido como secuencia.

### `entities/card_factory.py`

Crea cartas aleatorias y asigna:

- Rango.
- Palo.
- Score base.
- Multiplicador.
- `pygame.Rect`.
- Ruta esperada del asset.

### `entities/rules.py`

Evalúa las jugadas:

- High Card.
- Pair.
- Two Pair.
- Three of a Kind.
- Straight.
- Flush.
- Full House.
- Four of a Kind.
- Straight Flush.

El resultado se representa mediante `HandResult`.

### `entities/jokers.py`

Contiene Jokers polimórficos:

- `FlatChipsJoker`: aumenta el score de las cartas.
- `MultiplierJoker`: aumenta el multiplicador.
- `RandomJokerPool`: activa Jokers según probabilidad.

## 6. Puntuación

El resultado general sigue este modelo:

```text
puntuación total =
(score global + score de la combinación + score de las cartas)
× multiplicador
```

Los Jokers pueden modificar los valores de las cartas antes de la evaluación final.

El atributo `round_score` se utiliza como puntuación acumulada de la ronda actual.

## 7. Records

Los records se almacenan en `records.json`.

Formato:

```json
[
  {
    "name": "Jugador",
    "score": 250
  }
]
```

El menú:

- Carga los records al iniciar.
- Ordena por puntuación.
- Muestra los mejores resultados.
- Guarda el resultado al abandonar GAMEOVER con ESC.

### Problema actual

La puntuación se reinicia al comenzar cada ronda:

```python
self.round_score = 0
```

Por ello, al completar las tres rondas el score final puede no representar la puntuación total de la partida. Debe definirse si se necesita:

- `round_score`: puntuación de la ronda.
- `total_score`: puntuación acumulada de toda la partida.

## 8. Assets

La carpeta `assets(beta)` contiene:

```text
assets(beta)/
├── audio/
├── cards/
│   ├── dark/
│   └── light/
└── cartas_Españolas/
    └── Baraja_española_completa.xcf
```

También existen archivos de macOS que no deberían distribuirse:

```text
__MACOSX/
._*
.DS_Store
```

### Estado de integración

Los assets están presentes, pero el renderer actual no carga imágenes. La interfaz genera visualmente las cartas mediante rectángulos, texto y colores.

La baraja española está almacenada principalmente como archivo `.xcf`, que no es cargable directamente por Pygame. Se recomienda exportarla a PNG.

## 9. Configuración

### `settings.py`

Define:

- Resolución: `1280 × 720`.
- FPS: `60`.
- Directorio base.
- Directorio de assets.
- Carga de fuentes con fallback.

La fuente configurada es:

```text
assets/tu_fuente.ttf
```

Ese archivo no está confirmado en los assets adjuntos. Si no existe, se utiliza la fuente predeterminada de Pygame.

### `requirements.txt`

```text
pygame>=2.5
```

## 10. Audio

`audio.py` contiene `SoundPlayer`.

Actualmente el audio funciona como una capa de compatibilidad o simulación. Debe verificarse si:

- Inicializa realmente el mixer.
- Carga archivos desde `assets(beta)/audio`.
- Reproduce música y efectos.
- Gestiona errores de archivos inexistentes.

## 11. Pruebas

Existe:

```text
tests/test_entities.py
```

Debe ejecutarse con:

```powershell
py -m unittest discover -s tests -v
```

También puede utilizarse pytest si se incorpora como dependencia:

```powershell
py -m pytest -v
```

No se dispone de evidencia suficiente para confirmar que todas las pruebas actuales pasan correctamente.

## 12. Problemas detectados

### Prioridad alta

1. `SelectorDummy` no es un selector real.
2. ESC en el selector no cambia explícitamente al estado `MENU`.
3. La puntuación total de la partida no está separada de la puntuación de ronda.
4. El resultado de victoria puede terminar guardándose con una puntuación incorrecta.
5. Los assets de cartas no están integrados visualmente.
6. `game.py` conserva nombres heredados del prototipo de carreras.
7. `self.rules.apply_result` se crea dinámicamente dentro de `play_selected()` y debería eliminarse.
8. El renderer llama `present()` internamente, mezclando lógica de actualización y presentación.

### Prioridad media

1. Validar y limpiar `records.json`.
2. Evitar records duplicados según una política definida.
3. Sustituir excepciones generales por excepciones específicas.
4. Centralizar colores y fuentes.
5. Añadir mensajes de error para assets ausentes.
6. Separar la lógica del dominio de Pygame en `CardFactory`.
7. Añadir pruebas para puntuación, rondas, Jokers y persistencia.

### Prioridad baja

1. Añadir animaciones.
2. Añadir sonidos reales.
3. Añadir personajes visuales.
4. Añadir consumibles funcionales.
5. Crear un instalador o ejecutable.

## 13. Estado por componente

| Componente | Estado |
|---|---|
| `main.py` | Funcional |
| `game.py` | Juego de cartas jugable en estado prototipo |
| `Renderer.py` | Funcional, sin imágenes reales |
| `entities/` | Arquitectura de dominio implementada |
| `menu/` | Funcional, requiere revisión de configuración |
| `audio.py` | Pendiente de confirmar integración real |
| `settings.py` | Funcional con fallback de fuente |
| `records.json` | Funcional, sin validación completa |
| `assets/` | Insuficientes o no conectados |
| `assets(beta)/cards` | Presentes, no utilizados directamente |
| `tests/` | Existe una prueba, cobertura limitada |
| `README.md` | Insuficiente y guardado en UTF-16 |
| `README_INTEGRATION.md` | Documenta la integración de entities |
| `README_ENTITIES.md` | Documenta la arquitectura de entidades |

## 14. Recomendaciones

### Inmediatas

1. Renombrar `CarreraDeObstaculos` a un nombre relacionado con cartas, manteniendo un alias temporal.
2. Crear un selector de modo o eliminar la pantalla de personajes.
3. Separar `total_score` de `round_score`.
4. Corregir el guardado del score al completar una partida.
5. Integrar imágenes PNG de cartas.
6. Corregir el retorno desde SELECTOR mediante ESC.
7. Ejecutar y completar las pruebas automatizadas.

### Antes de entregar

- Actualizar `README.md`.
- Guardar el README en UTF-8.
- Añadir instrucciones de instalación.
- Eliminar `__MACOSX`, `.DS_Store` y archivos `._*`.
- Confirmar las rutas de assets.
- Definir una política para records duplicados.
- Añadir pruebas de integración del flujo completo.
- Confirmar que el audio funciona o documentarlo como simulación.

## 15. Veredicto

El proyecto evolucionó desde un prototipo de carreras hacia un juego de cartas. Actualmente existe una arquitectura funcional con entidades, reglas, Jokers, puntuación, renderer y flujo de menú.

El estado actual es:

> **Prototipo jugable de cartas con integración parcial de assets, records y audio.**

La prioridad ya no es implementar el núcleo básico de cartas, sino terminar la integración visual, corregir la puntuación global, completar las pruebas y eliminar los elementos heredados del prototipo de carreras.
````