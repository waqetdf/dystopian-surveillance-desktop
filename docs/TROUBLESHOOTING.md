# Diagnóstico y recuperación

1. Ejecuta `~/.local/bin/dsd doctor` dentro de Hyprland.
2. Arranca `~/.local/bin/dsd start` en una terminal para ver errores de Qt.
3. Revisa `hyprctl layers`: debe aparecer `dystopian-surveillance` en bottom.
4. Si hay otro fondo interactivo o barra, comprueba su capa y región de entrada.
   Este proyecto no desinstala Waybar ni otros componentes del escritorio.

**No aparece:** comprueba Quickshell (`qs --version`), `WAYLAND_DISPLAY`, la sesión
Hyprland y el `source` de integración. Las ventanas opacas normales cubren el
escritorio de forma intencionada. Usa una zona vacía o un espacio de trabajo vacío.

**Vídeo negro:** verifica `ffprobe assets/scenes/alley/scene.mp4`. Prueba sin
decodificación hardware y reinicia `dsd restart`. El renderizador software de
Qt Quick no representa VideoOutput en todas las versiones; usa OpenGL/Vulkan
compatibles. Las pruebas headless no equivalen a un controlador real.

**Aplicación no instalada:** Ajustes → Aplicaciones → edita la lista de argumentos.
El terminal usa foot y alternativas conocidas; mpv y htop se instalan de fábrica.
El navegador predeterminado se abre mediante xdg-open.

**Configuración inválida:** se conserva el original y se arranca con valores
predeterminados. Repara `~/.config/dystopian-surveillance/config.json` o restaura
`config.json.bak`. Los cambios se escriben solo al guardar.

**No guarda la clave IA:** comprueba que `org.freedesktop.secrets` esté disponible
y el llavero desbloqueado. GNOME Keyring depende del inicio de sesión; consulta
la guía de Arch para tu gestor de acceso. El escritorio funciona sin este servicio.

**Cambios personales en un archivo gestionado:** el instalador se detiene en vez
de sobrescribirlos. Conserva tu archivo y retira el destino en conflicto antes
de repetir. La desinstalación conserva esos archivos y deja constancia en
`~/.local/state/dystopian-surveillance/uninstall-preserved.json`.

**Recuperar la versión anterior:** consulta `previousRelease` en
`~/.local/state/dystopian-surveillance/install.json`. Con el escritorio detenido,
el código anterior permanece en `~/.local/share/dystopian-surveillance/releases`.
Puedes volver a ejecutar el instalador desde un checkout de la revisión anterior;
la configuración y los medios personales se mantienen.

**Proceso interrumpido durante instalación:** el registro marca `installing`.
Ejecuta `uninstall.sh`, revisa las copias bajo el directorio de estado y repite
la instalación. No borres las copias mientras quieras poder recuperar archivos.

**Quickshell tras actualizar:** `dsd restart` cierra la instancia anterior antes
de iniciar el código nuevo. Si la instancia anterior no responde al IPC por
haber cambiado de ruta, usa `qs list` para localizarla y `qs kill --help` para
cerrarla por su identificador, luego `dsd start`.
