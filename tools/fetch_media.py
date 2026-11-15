#!/usr/bin/env python3
"""Download declared wallpaper media for personal use, verify SHA-256, prepare locally.
No executable code is downloaded. Third-party raw videos are NOT redistributed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.config import atomic_json, xdg


def media_root():return Path(os.environ.get('DSD_MEDIA_DIR',str(xdg('data')/'bundled-media')))
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def acquire(item, destination, source_cache=None):
    target=destination/item['id'];receipt=target/'receipt.json'
    if receipt.exists():
        r=json.loads(receipt.read_text())
        if r['sourceSHA256']==item['sha256'] and all((target/n).is_file() and sha(target/n)==v for n,v in r['files'].items()):
            print(item['id']+': ya verificado',flush=True);return
        raise ValueError(f'El paquete local {target} fue modificado o cambió de versión. Conserva tu copia y retíralo antes de volver a descargar.')
    if target.exists():raise ValueError(f'No se sobrescribe la carpeta existente {target}')
    destination.mkdir(parents=True,exist_ok=True,mode=0o700)
    with tempfile.TemporaryDirectory(dir=destination,prefix='.'+item['id']+'-') as tmp:
        stage=Path(tmp);source=stage/'source.mp4'
        cached=Path(source_cache)/item['id']/'source.mp4' if source_cache else None
        if cached and cached.is_file() and sha(cached)==item['sha256']:shutil.copyfile(cached,source)
        else:
            print('Descargando '+item['page'],flush=True)
            subprocess.run(['curl','--fail','--location','--proto','=https','--proto-redir','=https',
                            '--max-filesize','104857600','--connect-timeout','20','--max-time','300','--retry','2',
                            '--silent','--show-error',item['url'],'-o',str(source)],check=True)
        if sha(source)!=item['sha256']:raise ValueError('El origen cambió. SHA-256 no coincide: '+item['page'])
        # Transcode the downloaded artwork; never synthesize scenes or replace content with stills.
        subprocess.run(['ffmpeg','-nostdin','-v','error','-i',str(source),'-map','0:v:0','-map','0:a:0?',
                        '-vf','scale=1280:720:force_original_aspect_ratio=decrease:force_divisible_by=2,fps=24',
                        '-c:v','libx264','-crf','21','-preset','fast','-pix_fmt','yuv420p','-c:a','aac',
                        '-movflags','+faststart',str(stage/'scene.mp4')],check=True,timeout=600)
        subprocess.run(['ffmpeg','-nostdin','-v','error','-ss','1','-i',str(stage/'scene.mp4'),'-frames:v','1',
                        '-vf','scale=320:-2',str(stage/'thumbnail.png')],check=True,timeout=60)
        source.unlink()
        atomic_json(stage/'receipt.json',{'sourceSHA256':item['sha256'],'page':item['page'],'license':item['license'],
                    'files':{name:sha(stage/name) for name in ('scene.mp4','thumbnail.png')}})
        stage.rename(target)
    print(item['id']+': preparado y verificado',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--destination',type=Path,default=media_root());p.add_argument('--source-cache',type=Path)
    a=p.parse_args();items=json.loads((ROOT/'assets/remote.json').read_text())
    print('Medios de terceros para este escritorio personal. Procedencia y hashes: assets/remote.json.\nNo se les atribuye una licencia de redistribución.',flush=True)
    try:
        for item in items:acquire(item,a.destination,a.source_cache)
    except (ValueError,OSError,subprocess.SubprocessError) as e:print('ERROR de medios:',e,file=sys.stderr);return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
