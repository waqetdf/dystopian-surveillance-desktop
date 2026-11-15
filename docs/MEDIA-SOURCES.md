# Selección visual

La referencia actual son los **dos MP4 aportados por el usuario**: ilustración
anime con ciudad nocturna, personajes persistentes, señales luminosas y neón
azul/violeta. Sustituye a la propuesta inicial de escenas procedurales.

Los archivos aportados son 720×1280, H.264, 30 FPS, con audio. Duran aproximadamente
5 y 30 segundos. Se conservan íntegros; el audio comienza silenciado. El mosaico
reserva dos paneles verticales diferentes para evitar recortar a los personajes.

Para ampliar la biblioteca se buscaron y se inspeccionaron estos vídeos existentes:

- [Yumi on the Roof](https://motionbgs.com/yumi-on-the-roof): azotea y señalización azul.
- [Cyberpunk Tokyo City](https://motionbgs.com/cyberpunk-tokyo-city): vista urbana industrial, cian y magenta.
- [Lucy's Apartment](https://motionbgs.com/lucys-apartment): interior en penumbra y skyline de neón.
- [Emily in the Cyberpunk City](https://motionbgs.com/emily-in-the-cyberpunk-city): personaje y callejón con anuncios luminosos.

Se verificó que son vídeos reproducibles; se extrajeron fotogramas para comprobar
la afinidad visual. Las versiones de escritorio se obtienen de sus páginas
originales con hashes fijados. El código no crea ni genera nuevos escenarios.

## Preparar los vídeos para desarrollo

```bash
python3 tools/fetch_media.py
python3 tools/preview.py
```

Para otra ubicación, exporta `DSD_MEDIA_DIR=/ruta/privada/medios` antes de ejecutar
ambos comandos. `install.sh` prepara los cuatro vídeos automáticamente en
`~/.local/share/dystopian-surveillance/bundled-media`. Necesita internet solo
para la descarga inicial; después todo el escritorio funciona sin conexión.

La copia preparada se conserva entre actualizaciones y la descarga idempotente
comprueba el recibo antes de reutilizarla. El directorio de medios no forma parte
de las versiones de código ni se borra con una desinstalación normal.

Consulta [ASSETS-LICENSE.md](../ASSETS-LICENSE.md). «Descarga gratuita» no implica
permiso para volver a publicar los archivos como recursos de un proyecto libre.
