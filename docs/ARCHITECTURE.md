# Arquitectura

```
Quickshell / shell.qml
 ├─ PanelWindow por monitor · layer bottom · sin zona exclusiva
 │   └─ Dashboard → VideoPanel / menú de aplicaciones
 ├─ Settings · ventana normal Qt
 ├─ IpcHandler → settings / close / quit
 └─ Process / JSON Lines por stdin y stdout
     └─ backend/service.py (un proceso)
         ├─ config.py: esquema, validación, escritura atómica
         ├─ scenes.py: biblioteca y conversión de medios
         ├─ playback.py: copias con límite FPS, sin cambiar los originales
         ├─ events.py: eventos, visitas y colores ambientales
         ├─ ai.py: proveedor opcional y Secret Service
         └─ metrics.py: /proc y /sys, muestreo cada 3 segundos
```

La configuración reside en `$XDG_CONFIG_HOME/dystopian-surveillance/config.json`.
Los vídeos personales están en `$XDG_DATA_HOME/dystopian-surveillance/scenes`.
El estado privado y las copias están bajo
`$XDG_STATE_HOME/dystopian-surveillance`. Los valores XDG por defecto siguen la
especificación (`~/.config`, `~/.local/share`, `~/.local/state`).

La configuración e historial se escriben con permisos 0600 mediante archivo
temporal, fsync y rename. Se conserva `config.json.bak`. Una configuración
corrupta no se sobrescribe silenciosamente al arrancar: aparece un aviso.
Las API keys se guardan exclusivamente en Secret Service, por origen de URL.

El escritorio no abre ningún puerto TCP. La comunicación interna consiste en
líneas JSON; stdout del servicio está reservado al protocolo. Operaciones:
`state`, `save`, `open`, `close`, `talk`, `launch`, `import`, `pack`, `key`,
`ai`, `testAI`, `clearHistory`. Respuestas: `state`, `event`, `stats`, `notice`,
`error`, `settings`, `imported`. El importador y la consulta IA utilizan dos
hilos de trabajo como máximo; la interfaz no espera a que FFmpeg termine.

Las aplicaciones se lanzan con argumentos separados, sin `shell=True`, `eval`,
concatenación de un comando o expansión de variables. Un acceso puede ejecutar
un script elegido explícitamente por el usuario; ese script tiene sus permisos
habituales. Las escenas importadas no pueden introducir código ejecutable ni
accesos nuevos: se copian solo manifiesto y medios declarados.

FFmpeg/ffprobe reciben rutas locales y una lista de protocolos `file,pipe`.
Se comprueban tamaño, extensión y presencia de vídeo. No es una caja de arena
para vulnerabilidades del decodificador: mantén Qt/FFmpeg actualizados y usa
medios de procedencia confiable.

IA: no hay peticiones automáticas. HTTPS obligatorio, salvo localhost para
proveedores locales. Se rechazan redirecciones para no filtrar credenciales a
otro origen. El historial tiene un límite configurable; al borrarlo o desactivar
la IA se descartan respuestas pendientes. Una petición ya enviada no puede
retirarse del proveedor. Los errores no incluyen claves ni cuerpos HTTP.

El estado de selección está centralizado en AppState. Para cambiar de escena,
se cierra primero la anterior y se espera la transición antes de activar la
siguiente. El temporizador de señal pertenece al panel; una reconexión reinicia
ese temporizador sin reiniciar servicio, compositor o aplicaciones.

El instalador guarda versiones de código independientes y cambia un enlace
`current` al terminar. Un bloqueo flock evita duplicar la interfaz. El historial,
los medios y la configuración no viven en la carpeta versionada. Las operaciones
reversibles tienen una copia; una excepción revierte los archivos ya escritos.

El límite FPS de vídeo usa copias H.264 en `$XDG_CACHE_HOME/dystopian-surveillance/playback`.
Se crean fuera del hilo de interfaz y se reutilizan por ruta, tamaño, fecha y FPS.
Las conversaciones no regeneran ni transcodifican vídeos. Wayland sigue controlando
el refresco de la interfaz.
