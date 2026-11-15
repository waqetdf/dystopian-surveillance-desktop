# Configuración v1

`backend/config.py::default_config()` documenta todos los valores predeterminados.
Guarda y aplica cambios desde Ajustes. Secciones del JSON:

| Clave | Contenido |
|---|---|
| `appearance` | `accent`, `background`, `font`, `border`, `gap`, `crt`, `interference`, `transitionMs`, `ambient`, `ambientIntensity` |
| `panels` | Lista de cámaras con ID, escena, rectángulo y reproducción |
| `profiles` | Objeto nombre → lista de paneles |
| `sceneOverrides` | Cambios personales de nombre, personalidad, conversaciones, eventos y aplicaciones |
| `dialogue` | `enabled`, `duration` por intervención, multiplicador `frequency` |
| `connection` | `enabled`, `seconds`, `interferenceSeconds`, `intensity` |
| `performance` | FPS, pausa, hardware, calidad de importación, ahorro y umbral de CPU |
| `apps` | Lista de accesos: `id`, `name`, `icon`, `argv` |
| `ai` | Activación, URL, modelo, límite de tokens, historial, contexto y adaptador |

Un panel:

```json
{"id":"cam-personal","scene":"alley","x":0,"y":0,"w":0.5,"h":0.6,
 "scale":1,"offsetX":0,"offsetY":0,"fit":"contain","loop":true,
 "muted":true,"speed":1}
```

`x/y/w/h` usan fracciones de pantalla. `contain` conserva toda la imagen, con
bandas cuando las proporciones difieren; `cover` recorta sin deformar. La escala
es 1–4 y los desplazamientos −1 a 1. Velocidad: 0.25–3. Hasta 24 paneles,
sin solapamiento. Al dividir uno se conserva su escena, que puedes sustituir.

## Paquetes de escenas

Una carpeta con `scene.json`, vídeo MP4/WebM/MKV y miniatura PNG/JPG/WebP. Importa
la carpeta desde Animaciones → Paquete; los paquetes no ejecutan scripts.
IDs únicos: letras, números, guiones y guiones bajos (máximo 64 caracteres).
Las rutas de medios deben permanecer dentro de la carpeta, incluso tras resolver
enlaces simbólicos. Ejemplo:

```json
{
  "id":"canal-nuevo","name":"Canal nuevo","category":"Ciudad",
  "video":"scene.webm","thumbnail":"thumbnail.png","license":"CC0-1.0",
  "personality":"Operador reservado y observador.",
  "dialogues":{"greeting":["Señal recibida."],"talk":["Primera frase.","Segunda frase."]},
  "events":[{"id":"bienvenida","trigger":"open","probability":1,
             "cooldown":60,"lines":["Bienvenido al canal."]}],
  "apps":["terminal","files","settings"]
}
```

Las categorías son libres en paquetes; el selector de la biblioteca muestra
las ocho categorías iniciales y «Todas». Los MP4 aportados conservan H.264/30 FPS/720×1280. Los cuatro fondos
externos se preparan como H.264/24 FPS/1280×720. No hay generador de escenarios. La decodificación entre fin y principio depende
de Qt/FFmpeg y del equipo, además de la continuidad visual del material.

## Conversaciones y eventos

Los diálogos locales son listas de texto. Se muestra una intervención cada
`dialogue.duration` segundos. El evento evalúa en orden las reglas elegibles.

| trigger | Condición adicional |
|---|---|
| `open` | Se abre la escena |
| `timer` | `after` segundos desde la apertura |
| `random` | Sorteo cada 3 segundos durante la apertura |
| `hour` | `hour` local, 0–23 |
| `memory` | `minVisits`, número de aperturas persistidas |
| `app` | `app`, ID del acceso ejecutado |

`probability` va de 0 a 1. `cooldown` impide repetir la misma regla demasiado
pronto. El multiplicador de frecuencia afecta al sorteo y a la espera. Una pausa
global entre mensajes evita que eventos consecutivos tapen las intervenciones.
Las visitas y esperas se conservan al reiniciar. Los eventos temporizados solo
se evalúan para la escena ampliada para reducir actividad y distracciones.

```json
[{"id":"recuerdo","trigger":"memory","minVisits":3,"probability":1,
  "cooldown":300,"lines":["Reconozco tu señal.","La ciudad te estaba esperando."]},
 {"id":"aviso","trigger":"timer","after":45,"probability":0.4,
  "cooldown":180,"lines":["Movimiento junto al andén."]}]
```

## Aplicaciones

```json
{"id":"editor","name":"Editor","icon":"✎","argv":["kate","/home/usuario/notas.txt"]}
```

Cada argumento es un elemento. No se expanden `$HOME`, `~`, `;`, `|`, `$(...)`
o redirecciones. Para usar un script, indica su ruta absoluta; debe ser ejecutable.
Selecciona las asociaciones en Aplicaciones y guarda. El orden se puede copiar
explícitamente desde la lista global a la escena elegida.
