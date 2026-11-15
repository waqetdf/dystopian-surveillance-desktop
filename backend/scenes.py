"""Data-only scene packs and constrained ffmpeg imports. Packs never execute code."""
import json
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from .config import ROOT, SLUG, atomic_json, validate_event, xdg


def local_file(folder, name):
    p = (folder / name).resolve()
    if not p.is_relative_to(folder.resolve()) or not p.is_file():
        raise ValueError(f'Recurso fuera del paquete o inexistente: {name}')
    return p


class Library:
    def __init__(self, directory=None):
        self.directory = directory or xdg('data') / 'scenes'
        self.warnings = []
        self.items = {}
        self.playback_urls = {}
        self.reload()

    def reload(self):
        self.items = {}; self.warnings = []
        for base in (ROOT / 'assets/scenes', self.directory):
            for manifest in sorted(base.glob('*/scene.json')):
                try:
                    s = json.loads(manifest.read_text())
                    if not SLUG.fullmatch(s['id']) or s['id'] in self.items: raise ValueError('ID inválido/duplicado')
                    for k in ('name', 'personality', 'category'):
                        if not isinstance(s[k], str): raise ValueError('Metadatos inválidos')
                    for e in s['events']: validate_event(e)
                    if not isinstance(s['apps'], list) or not isinstance(s['dialogues'], dict): raise ValueError('Escena inválida')
                    media_folder = Path(os.environ.get('DSD_MEDIA_DIR',str(xdg('data')/'bundled-media'))) / s['id'] if s.get('remote') else manifest.parent
                    video=local_file(media_folder,s['video'])
                    if video.suffix.lower() not in ('.mp4','.webm','.mkv'): raise ValueError('Vídeo no compatible')
                    thumb=local_file(media_folder,s['thumbnail'])
                    s['videoUrl'] = video.as_uri(); s['thumbnailUrl'] = thumb.as_uri()
                    s['builtin'] = base == ROOT / 'assets/scenes'
                    self.items[s['id']] = s
                except (ValueError, KeyError, TypeError, OSError) as e:
                    self.warnings.append(f'{manifest}: {e}')

    def resolved(self, config):
        return {sid: {**s, **config['sceneOverrides'].get(sid,{}), 'videoUrl':self.playback_urls.get(sid,s['videoUrl'])} for sid,s in self.items.items()}

    def import_video(self, source, name, category, fps=24, quality=720):
        source = Path(source).expanduser().resolve(strict=True)
        if not source.is_file() or source.suffix.lower() not in ('.gif','.mp4','.webm','.mkv','.mov','.avi','.apng'):
            raise ValueError('Selecciona un vídeo, GIF o APNG local')
        if source.stat().st_size > 2 * 1024**3: raise ValueError('Límite de importación: 2 GiB')
        sid = 'import-' + uuid.uuid4().hex[:12]
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        with tempfile.TemporaryDirectory(dir=self.directory, prefix='.import-') as temp:
            d = Path(temp)
            probe = subprocess.run(['ffprobe','-v','error','-protocol_whitelist','file,pipe','-show_streams','-of','json',str(source)],
                                   capture_output=True, text=True, timeout=30, check=True)
            streams = json.loads(probe.stdout)['streams']
            if not any(s['codec_type']=='video' for s in streams): raise ValueError('El archivo no contiene vídeo')
            # A local protocol whitelist prevents playlist/URL imports from fetching remote resources.
            command = ['ffmpeg','-nostdin','-v','error','-protocol_whitelist','file,pipe','-i',str(source),
                       '-map','0:v:0','-map','0:a:0?','-t','300','-vf',
                       f'scale=w=min(iw\\,{int(quality)*2}):h=min(ih\\,{int(quality)}):force_original_aspect_ratio=decrease:force_divisible_by=2,fps={int(fps)}',
                       '-c:v','libx264','-crf','22','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(d/'scene.mp4')]
            subprocess.run(command,capture_output=True,timeout=600,check=True)
            subprocess.run(['ffmpeg','-nostdin','-v','error','-i',str(d/'scene.mp4'),'-frames:v','1',str(d/'thumbnail.png')],capture_output=True,timeout=30,check=True)
            scene = {'id':sid,'name':str(name)[:120] or source.stem,'category':str(category)[:80],
                     'video':'scene.mp4','thumbnail':'thumbnail.png','frameRate':int(fps),'personality':'Observador de la ciudad.',
                     'license':'Importación personal: conserva los derechos de su autor.',
                     'dialogues':{'greeting':['Canal personal conectado.'],'talk':['La ciudad nunca duerme.']},
                     'events':[{'id':'greet','trigger':'open','probability':1,'cooldown':60,'lines':['Canal personal conectado.']}],
                     'apps':['terminal','files','settings']}
            atomic_json(d/'scene.json',scene)
            d.rename(self.directory/sid)
        self.reload()
        return sid

    def import_pack(self, folder):
        folder=Path(folder).expanduser().resolve(strict=True)
        s=json.loads((folder/'scene.json').read_text())
        if not SLUG.fullmatch(s['id']) or s['id'] in self.items: raise ValueError('ID inválido o ya instalado')
        # Only the manifest and declared media are copied, never scripts or arbitrary paths.
        video=local_file(folder,s['video']); thumb=local_file(folder,s['thumbnail'])
        if video.suffix.lower() not in ('.mp4','.webm','.mkv') or thumb.suffix.lower() not in ('.png','.jpg','.webp'): raise ValueError('Formato de paquete inválido')
        for e in s['events']: validate_event(e)
        for k in ('name','category','personality','dialogues','apps'): s[k]
        self.directory.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=self.directory,prefix='.pack-') as tmp:
            d=Path(tmp); shutil.copy2(video,d/('video'+video.suffix)); shutil.copy2(thumb,d/('thumbnail'+thumb.suffix))
            s['video']='video'+video.suffix; s['thumbnail']='thumbnail'+thumb.suffix
            atomic_json(d/'scene.json',s); d.rename(self.directory/s['id'])
        self.reload()
        if s['id'] not in self.items: raise ValueError('Paquete inválido: '+ '; '.join(self.warnings))
        return s['id']
