# Validación

Resultados ejecutados el **15 de noviembre de 2026** en Debian 13:

| Prueba | Resultado |
|---|---|
| `python3 -m unittest discover -s tests -v` | **33 pruebas aprobadas** |
| `tools/test_ui.py`, Qt Quick con OpenGL sobre Xvfb | **Aprobado**: seis reproducciones reales, clics, selección única, geometría, diálogos, reconexión, ocho páginas, sustitución e importación de vídeo, persistencia |
| `tools/test_wayland.py`, Quickshell 0.3.0 + Qt 6.8.2 sobre Sway 1.10.1 headless | **Aprobado**: layer-shell real, servicio, cambio de escena, cierre, ventana de ajustes, IPC y salida limpia |
| `install.sh`, `update.sh`, `uninstall.sh` con `--test-root` | **Aprobado**: sin privilegios ni cambios al sistema anfitrión |
| Integridad de recursos y sintaxis de scripts | **Aprobado** |

Se utilizó un compositor Wayland real para la prueba de layer-shell. Sway no
sustituye una comprobación de Hyprland. La sesión de pruebas no tenía dispositivo
de audio ni GPU física: se usó renderizado Mesa por CPU. Las cifras de rendimiento
observadas en este entorno no se presentan como un benchmark de uso cotidiano.

## Comprobaciones automatizadas incluidas

- Esquema y persistencia; configuración corrupta, límites, solapamientos y perfiles.
- Eventos, probabilidades, tiempos de espera, hora, aplicaciones y memoria.
- Estados de desconexión/reconexión e interpolación ambiental.
- Ausencia de solicitudes IA mientras está desactivada.
- Argumentos literales de aplicaciones, sin intérprete de comandos.
- Medios reales: seis vídeos H.264 existentes comprobados localmente. La suite
  sin red verifica los dos MP4 incluidos; los cuatro externos son opcionales.
- Los seis menús y personajes siguen disponibles cuando faltan vídeos opcionales.
- Importación/transcodificación y paquetes sin ejecución de scripts.
- Integridad SHA-256 de los recursos distribuidos.
- Despliegue aislado, repetición idempotente, preservación de cambios personales,
  actualización, desinstalación, enlaces simbólicos y reversión ante fallo.
- Carga QML, reproducción, interacción de cámaras, un único menú, cuatro tamaños
  de ventana, diálogos, desconexión/reconexión, ajustes y persistencia.

## Validación pendiente obligatoria antes de declarar versión estable

En una máquina o VM Arch actualizada con GPU/controladores adecuados:

1. Instala desde un usuario limpio con `./install.sh`; reinicia sesión Hyprland.
2. Asigna vídeos a las seis cámaras y confirma reproducción sin errores durante 30 minutos.
3. Abre/cierra y cambia rápidamente de cámara. Nunca deben coexistir dos menús.
4. Abre terminal, navegador, archivos, mpv y htop. Comprueba teclado, foco,
   atajos, espacios de trabajo, fullscreen y ventanas superpuestas.
5. Prueba 1366×768, 1920×1080 y 2560×1440; escala 1, 1.25 y 2; dos monitores,
   desconexión de una pantalla y rotación vertical.
6. Edita distribución, guarda perfil, importa GIF y vídeo con audio, cambia
   encuadre/velocidad, guarda y reinicia. Verifica persistencia y sonido.
7. Usa temporizador de 5 segundos + interferencia; reconecta repetidamente.
8. Desactiva red: diálogos y aplicaciones locales siguen funcionando.
9. Comprueba IA con un proveedor elegido, credencial de prueba y Secret Service;
   borra historial/clave y desactiva. No deben salir solicitudes automáticas.
10. Compara CPU, RAM y decodificación GPU, modo ahorro, juegos y suspensión.
11. Actualiza y desinstala conservando una modificación personal en Hyprland.
12. Repite una instalación limpia. No debe haber entradas de autostart duplicadas.

## Límites explícitos

- El núcleo se instala sin descargar vídeos externos. Cuatro cámaras están listas
  para elegir vídeo desde Ajustes; la colección de terceros es opcional. Se
  observó HTTP 403 en GitHub Actions al intentar obtenerla, por lo que la CI
  no depende de esos proveedores y no se eluden sus restricciones.

- Las escenas siguen los dos vídeos anime/cyberpunk aportados posteriormente
  por el usuario. Se retiraron las ilustraciones procedurales iniciales.
- La pausa de oclusión detecta cámaras cubiertas por el menú y pantalla completa
  activada, no cualquier ventana parcialmente superpuesta.
- Los monitores comparten perfil; no hay diseños independientes por monitor.
- La telemetría de GPU está disponible solo con `gpu_busy_percent` en sysfs.
  No se presentan cifras ficticias cuando el controlador no lo expone.
- La velocidad, escala y encuadre se aplican al guardar; los controles de vídeo
  tienen «Previsualizar cambios». Importaciones limitadas a 5 minutos y 2 GiB.
- El audio está silenciado de fábrica y solo se permite en la escena ampliada.
- La aceleración de vídeo es una preferencia y puede caer a CPU según hardware.
- El límite FPS reduce los fotogramas de los vídeos existentes mediante copias
  locales en caché. Conserva los originales y no se repite al conversar. No
  limita el refresco de la interfaz: esa sincronización pertenece al compositor.
- La interfaz de IA admite mensajes tipo Chat Completions con campos configurables;
  no promete compatibilidad con protocolos de streaming, OAuth o APIs arbitrarias.
- Los editores de reglas y conversaciones son JSON validado dentro de la GUI.
- El instalador usa repositorios oficiales de Arch. No se ha ejecutado `pacman`
  ni modificado una sesión Hyprland real durante la construcción en Debian.
