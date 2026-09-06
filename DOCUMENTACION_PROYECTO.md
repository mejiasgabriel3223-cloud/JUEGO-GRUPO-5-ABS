# Running Time! - Documentacion tecnica y estado del proyecto

Fecha de revision: 2026-09-04

## 1. Resumen ejecutivo

El proyecto es un prototipo de juego en Pygame. Actualmente puede iniciar, mostrar un menu, pedir un nombre, entrar a una pantalla de selector provisional, simular una partida, mostrar un game over y guardar records en `records.json`.

El juego jugable todavia no esta implementado. La clase `CarreraDeObstaculos` contiene un escenario de prueba minimo y conserva el nombre de un juego de obstaculos/carreras. Al mismo tiempo, el repositorio contiene un `Renderer` orientado a un juego de cartas estilo Balatro y un paquete de cartas espanolas. Estas dos lineas de desarrollo no estan integradas.

Estado general estimado: **prototipo funcional de flujo, con el nucleo jugable pendiente**.

## 2. Como se ejecuta actualmente

Punto de entrada: `main.py`.

Flujo de estados:

```text
MENU
  -> NAME_INPUT
  -> SELECTOR
  -> JUGANDO
  -> GAMEOVER
  -> MENU
```

### MENU

- `EstadoMenu` carga `menu_config.json`.
- Se muestran las opciones JUGAR, RECORDS, CREDITOS y SALIR.
- La navegacion se hace con flechas o W/S.
- ENTER ejecuta la opcion seleccionada.
- ESC cierra pantallas secundarias y vuelve al menu cuando corresponde.

### NAME_INPUT

- Permite escribir hasta 16 caracteres.
- BACKSPACE borra.
- ENTER guarda el nombre o usa `Jugador` si esta vacio.
- ESC cancela y vuelve al menu.

### SELECTOR

- Actualmente es `SelectorDummy`.
- ENTER selecciona siempre el texto `Personaje Falso`.
- No muestra personajes ni consume imagenes.

### JUGANDO

- La pantalla es un fondo verde con texto.
- El marcador se fija en 2500 al reiniciar.
- La tecla G fuerza un game over.
- ESC vuelve al menu.
- No hay obstaculos, movimiento, colisiones, reglas, enemigos, niveles ni victoria.

### GAMEOVER

- La pantalla muestra un mensaje provisional.
- ENTER reinicia la partida.
- ESC vuelve al menu y guarda el score dividido entre 10.
- La instruccion visible solo explica la ruta ESC; no se ofrece una accion para guardar y volver automaticamente.

## 3. Estado por componente

| Componente | Estado | Observacion |
|---|---|---|
| `main.py` | Funcional como orquestador | La maquina de estados funciona, pero depende de componentes simulados. |
| `menu/estado_menu.py` | Bien desarrollado | Gestiona estados, fondo, records y transiciones. |
| `menu/pantallas_menu.py` | Parcialmente desarrollado | Menu, entrada de nombre, records y creditos; contiene un error de clave en creditos. |
| `menu/gestor_config.py` | Funcional | Carga JSON y devuelve `{}` ante error. |
| `game.py` | Demo/provisional | No contiene el juego real; selector y partida son placeholders. |
| `audio.py` | Simulacion | Solo imprime mensajes; no inicializa mixer ni reproduce archivos. |
| `Renderer.py` | Modulo aislado | Tiene dibujo de cartas, HUD, jokers y consumibles, pero no es importado por el juego. |
| `settings.py` | Parcialmente util | Define pantalla y FPS; la fuente personalizada configurada no existe. |
| `menu_config.json` | Funcional con inconsistencias | Fondo configurado a una ruta inexistente y titulo vacio. |
| `records.json` | Funcional | Persiste records, pero acepta entradas duplicadas para el mismo nombre. |
| Assets | Abundantes pero desconectados | Hay cartas espanolas y cartas tipo poker, pero no se cargan desde `game.py`. |
| `README.md` | Insuficiente | Solo contiene el nombre del proyecto. |

## 4. Partes mejor elaboradas

### Menu modular

El menu esta separado en pantallas y un gestor de estado. Esto permite agregar pantallas sin concentrar toda la logica en `main.py`. La clase base `PantallaBase` tambien centraliza fuentes y texto centrado.

### Configuracion externa

Las opciones principales y sus colores viven en `menu_config.json`, en lugar de estar completamente fijadas en Python. Esta es una buena base para personalizar el menu.

### Persistencia de records

`EstadoMenu` carga y guarda `records.json`, ordena por score y muestra los ocho primeros. Tambien contempla el caso de que el mismo nombre ya exista y pregunta si se debe reemplazar.

### Separacion inicial de responsabilidades

- `main.py`: ciclo principal y estados globales.
- `game.py`: estado del juego.
- `audio.py`: servicio de sonido.
- `menu/`: menu y pantallas.
- `Renderer.py`: representacion visual de cartas.
- `settings.py`: constantes globales.

La separacion aun no esta completa, pero la direccion estructural es razonable.

### Renderer de cartas

`Renderer.py` tiene trabajo preliminar de calidad superior al resto del nucleo jugable: cachea textos, dibuja cartas seleccionadas, HUD, jokers y consumibles, y mantiene una paleta coherente. Su principal problema no es interno, sino que no tiene consumidores.

## 5. Funcionalidades en progreso o simuladas

1. **Juego principal**: es la prioridad absoluta. La clase se llama `CarreraDeObstaculos`, pero el contenido no implementa una carrera.
2. **Selector de personajes**: existe solo como pantalla azul y respuesta fija.
3. **Audio**: no hay archivos de sonido conectados ni reproduccion real.
4. **Cartas**: los assets estan presentes, pero no existe baraja, mano, robo, descarte ni evaluacion de jugadas.
5. **Renderer**: es una base visual sin integracion con el ciclo del juego.
6. **Animaciones del menu**: `animacion_jake` y `animacion_finn` quedan en `None`.
7. **Fuente personalizada**: `settings.py` busca `assets/tu_fuente.ttf`, que no existe; siempre se usa la fuente por defecto.
8. **Records al terminar**: solo se actualizan cuando el usuario abandona GAMEOVER con ESC; `_update_record_summary()` esta vacio.

## 6. Incoherencias y riesgos detectados

### Criticas para la integracion

- **Dominio mezclado**: el nombre y la logica actual hablan de una carrera de obstaculos, mientras que `Renderer.py` y los assets sugieren un juego de cartas. Antes de seguir implementando hay que decidir cual es el producto final.
- **Renderer no conectado**: `main.py` instancia y usa directamente `CarreraDeObstaculos`; nunca importa `Renderer`.
- **Assets no conectados**: las carpetas `assets(beta)/cards` y `assets(beta)/cartas_Espanolas` no aparecen en el codigo de carga.
- **Selector falso**: `SelectorDummy` confirma que esta parte es una prueba, no una funcionalidad terminada.

### Errores funcionales concretos

- **Creditos con clave incorrecta**: `menu_config.json` define `texto_pantalla`, pero `PantallaPrincipal` lee `texto`. La ruta se abre, pero el titulo recibido queda como `None` y la pantalla puede mostrar `None` en lugar de `Creditos`.
- **Fondo configurado inexistente**: `menu_config.json` apunta a `assets/Fondo pista.jpeg`, pero el inventario actual de `assets` solo contiene `launcher_cover.jpeg`. El programa cae silenciosamente al fondo azul de respaldo.
- **Titulo/logo vacio**: `recursos.titulo` es una cadena vacia, por lo que el menu no carga ningun logo.
- **Manejo de excepciones demasiado amplio**: varios `except:` ocultan errores de rutas, formatos o datos. Esto hace que una funcionalidad parezca funcionar aunque haya caido al fallback.
- **Records no validados**: un JSON con scores no numericos o nombres invalidos puede producir ordenamientos o pantallas incorrectas.
- **Records duplicados**: cuando el jugador elige conservar un record, se agrega otra entrada con el mismo nombre sin limite de cantidad.
- **Persistencia incompleta del game over**: `_update_record_summary()` no hace nada y la partida no se registra hasta pulsar ESC.
- **Puntuacion artificial**: el score se fija en 2500 y luego se transforma a 250 en `main.py`; no representa una regla del juego.
- **Inicializacion duplicada de Pygame**: `main.py` inicializa Pygame y `Renderer` tambien lo haria si se usara. No es un fallo actual porque Renderer esta aislado, pero debe resolverse al integrarlo.

## 7. Evidencia de codigo heredado o de otro prototipo

Hay evidencia directa, no solo una sospecha:

- El historial Git registra `Renderer.py` en un commit separado y lo describe como modulo de cartas.
- `Renderer.py` usa la etiqueta visual `Estilo Balatro`.
- `game.py` conserva `CarreraDeObstaculos`, `SelectorDummy` y textos como `Juego Falso`.
- Los assets incluyen cartas espanolas y cartas con palos abreviados C/D/H/P.
- La ejecucion actual solo muestra un juego falso de pantalla verde.

Conclusion: el repositorio combina al menos dos prototipos o fases de trabajo. No hay evidencia de que el sistema de cartas haya sido conectado al juego de carreras.

## 8. Pruebas realizadas en esta revision

- Compilacion de todos los modulos Python con `python -m compileall -q`: correcta.
- Ejecucion previa de `main.py`: termina sin error de proceso, pero eso solo demuestra que el bucle basico puede arrancar y cerrarse.
- Revision estatica de imports, rutas, estados, configuracion, recursos y referencias textuales.
- Revision del historial Git de los commits visibles.

No existe una suite automatizada de pruebas. Tampoco hay pruebas de juego, pruebas de records, pruebas de carga de recursos ni pruebas del flujo completo de estados.

## 9. Prioridad recomendada de trabajo

### Bloque 1: decidir el producto

Elegir una sola direccion:

- Juego de carreras/obstaculos: conservar `game.py` y reemplazar o retirar el Renderer y los assets de cartas.
- Juego de cartas: conservar `Renderer.py` y los assets, y reescribir `game.py` alrededor de baraja, mano, turnos, puntuacion y reglas.

No conviene seguir agregando pantallas hasta tomar esta decision.

### Bloque 2: corregir la base comun

- Arreglar `texto_pantalla` versus `texto`.
- Corregir o retirar la ruta del fondo.
- Definir una estrategia para fuentes y assets.
- Reemplazar `except:` por excepciones especificas y mensajes de diagnostico.
- Definir el momento exacto en que se guarda un record.
- Crear pruebas de transiciones de estados y records.

### Bloque 3: implementar el nucleo elegido

Para cartas: modelo de carta, baraja, mano, seleccion, descarte, jugadas, score, turnos y conexion con `Renderer`.

Para carreras: jugador, movimiento, obstaculos, colisiones, dificultad, camara, derrota, reinicio y conexion con un renderer dedicado.

### Bloque 4: entrega

- Actualizar `README.md` con instalacion y controles.
- Limpiar `__pycache__`, `.DS_Store` y metadatos `__MACOSX` del paquete versionado.
- Agregar un archivo de dependencias, al menos `pygame` con una version compatible.
- Agregar pruebas y un checklist manual de aceptacion.

## 10. Controles actuales

- Menu: flechas o W/S, ENTER.
- Entrada de nombre: texto, BACKSPACE, ENTER, ESC.
- Selector: ENTER.
- Juego: G fuerza game over, ESC vuelve al menu.
- Game over: ENTER reinicia, ESC guarda y vuelve al menu.
- Creditos y records: ESC vuelve al menu.

## 11. Definicion de terminado sugerida

El proyecto no deberia considerarse terminado hasta que:

- El tipo de juego este decidido y reflejado en nombres, textos y assets.
- El flujo principal no dependa de clases `Dummy`, mensajes `Falso` ni scores artificiales.
- Los recursos usados existan y se validen al iniciar.
- El juego tenga una regla de victoria o derrota real.
- El Renderer utilizado sea el mismo que se prueba visualmente.
- Los records se guarden una sola vez por partida y tengan una politica definida.
- Existan pruebas automatizadas para reglas y persistencia.
- `README.md` permita instalar, ejecutar y entender el proyecto sin conocimiento previo.

## 12. Veredicto

La parte mas madura es el menu con configuracion y records. La parte visual de cartas tiene una buena base aislada. La parte menos elaborada, y la que impide llamar al proyecto un juego completo, es el nucleo de partida. El siguiente paso correcto no es optimizar ni pulir el menu: es decidir entre carreras y cartas y conectar una implementacion real a la maquina de estados existente.
