# Procedencia y derechos de los medios

El código fuente es MIT. **Los vídeos no están cubiertos por MIT ni por CC0.**
No se distribuyen escenas generadas por este proyecto.

## Archivos aportados por el usuario

En este repositorio privado se incorporan, por petición del usuario, los dos
archivos que proporcionó para su escritorio personal, sin modificar el vídeo:

| Escena | Archivo original |
|---|---|
| Café de neón (`alley`) | `ModernReyAnime_pindown.io_1794763429.mp4` |
| Terraza violeta (`apartment`) | `From Klickpin.com- Unique Neutral Outfit Ideas You Need Right Now-pin-id-1115837245185601377.mp4` |

Los nombres de archivo no acreditan autoría ni licencia. No se facilitó una
licencia para redistribuirlos públicamente. Se conserva su SHA-256 en cada
manifiesto. Las miniaturas son fotogramas de esos mismos vídeos.

## Selección adicional encontrada en la web

Los cuatro vídeos adicionales **no se incluyen como archivos en Git**. El
instalador los descarga desde el proveedor para el escritorio personal del
usuario, verifica el SHA-256 del original y crea una copia H.264 local a 720p/24
FPS. La descarga no ejecuta programas del proveedor. No se retiran marcas de agua.

| Escena | Página del proveedor |
|---|---|
| Yumi · Azotea | https://motionbgs.com/yumi-on-the-roof |
| Tokio eléctrico | https://motionbgs.com/cyberpunk-tokyo-city |
| Apartamento de Lucy | https://motionbgs.com/lucys-apartment |
| Emily · Distrito neón | https://motionbgs.com/emily-in-the-cyberpunk-city |

Las páginas ofrecen descarga como fondo de escritorio. Su guía incluye Linux:
https://motionbgs.com/page/faq . No se ha verificado una licencia abierta ni de
redistribución de estos clips; por eso el repositorio contiene solo referencias,
metadatos de escena y hashes. Sus personajes y obras conservan los derechos de
sus respectivos titulares. El proveedor describe estas animaciones como fan art.

`assets/remote.json` registra páginas, enlaces de descarga, tamaños y SHA-256.
Cada instalación guarda un `receipt.json` con la procedencia y los hashes de las
copias preparadas. Si cambia un archivo remoto, la instalación se detiene; no
acepta silenciosamente el contenido nuevo.

La disponibilidad de los enlaces depende del proveedor. Ante una retirada,
puedes importar otro vídeo desde Ajustes; el programa no intenta eludir controles
de acceso. No publiques el paquete privado de medios como una biblioteca libre.
