"""Local FPS-limited video copies, cached once per source and limit.
The renderer still follows the compositor; decoding follows these media copies.
"""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlparse
from .config import xdg


def prepare_copies(scenes, fps, cache=None):
    cache=cache or xdg('cache')/'playback'; cache.mkdir(parents=True,exist_ok=True,mode=0o700)
    urls={}
    for scene in scenes:
        if not scene.get('videoUrl') or float(scene.get('frameRate',30)) <= fps:continue
        source=Path(unquote(urlparse(scene['videoUrl']).path));st=source.stat()
        key=hashlib.sha256(f'{source}:{st.st_size}:{st.st_mtime_ns}:{int(fps)}'.encode()).hexdigest()
        dest=cache/(key+'.mp4')
        if not dest.is_file():
            with tempfile.TemporaryDirectory(dir=cache,prefix='.prepare-') as tmp:
                output=Path(tmp)/'video.mp4'
                subprocess.run(['ffmpeg','-nostdin','-v','error','-i',str(source),'-map','0:v:0','-map','0:a:0?',
                                '-vf',f'fps={int(fps)}','-c:v','libx264','-preset','fast','-crf','21','-threads','2',
                                '-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(output)],
                               check=True,capture_output=True,timeout=600)
                output.rename(dest)
        urls[scene['id']]=dest.as_uri()
    return urls
