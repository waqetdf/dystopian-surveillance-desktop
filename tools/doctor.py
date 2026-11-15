#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.config import ConfigStore
from backend.scenes import Library
from tools.deploy import verify_assets


def main():
    errors=[]
    for binary in ('python3','ffmpeg','ffprobe','Hyprland','foot','xdg-open'):
        found=shutil.which(binary);print(f'{binary}: {found or "NO ENCONTRADO"}')
        if not found:errors.append(binary)
    qs=shutil.which('qs') or shutil.which('quickshell');print('Quickshell:',qs or 'NO ENCONTRADO')
    if not qs:errors.append('Quickshell')
    if qs:subprocess.run([qs,'--version'],check=False)
    try:print('Integridad:',verify_assets(ROOT),'recursos')
    except Exception as e:errors.append(str(e))
    library=Library();print('Escenas:',len(library.items))
    errors.extend(library.warnings)
    for sid,s in library.items.items():
        from urllib.parse import unquote,urlparse
        if not shutil.which('ffprobe'):break
        r=subprocess.run(['ffprobe','-v','error','-show_entries','stream=codec_name,width,height','-of','json',unquote(urlparse(s['videoUrl']).path)],capture_output=True,text=True)
        print(sid+': '+(r.stdout.strip() if r.returncode==0 else 'ERROR'))
        if r.returncode:errors.append(sid)
    config=ConfigStore()
    if config.warning:errors.append(config.warning)
    print('Wayland:',os.environ.get('WAYLAND_DISPLAY','sin sesión'));print('Hyprland:',bool(os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')))
    print('IA:','activada explícitamente' if config.value['ai']['enabled'] else 'desactivada')
    for e in errors:print('ERROR:',e)
    print('Doctor no certifica renderizado, foco o aceleración GPU. Sigue docs/VALIDATION.md dentro de Hyprland.')
    return 1 if errors else 0

if __name__=='__main__':raise SystemExit(main())
