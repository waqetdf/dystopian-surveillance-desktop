#!/usr/bin/env python3
"""User-scoped transactional deployment. --root is an isolated packaging test root."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SOURCE))
from backend.config import atomic_json

BEGIN='# BEGIN DYSTOPIAN SURVEILLANCE (managed)'
END='# END DYSTOPIAN SURVEILLANCE (managed)'


def digest(data):return hashlib.sha256(data).hexdigest()

def paths(root=None):
    if root:
        root=Path(root).resolve()
        return {'data':root/'data/dystopian-surveillance','config':root/'config',
                'state':root/'state/dystopian-surveillance','bin':root/'bin','applications':root/'data/applications'}
    return {'data':Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'dystopian-surveillance',
            'config':Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config'))),
            'state':Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))/'dystopian-surveillance',
            'bin':Path.home()/'.local/bin',
            'applications':Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'applications'}


def source_files():
    for folder in ('backend','qml','assets','tools','docs','packaging'):
        for p in sorted((SOURCE/folder).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.pyc'): yield p
    for name in ('install.sh','uninstall.sh','update.sh','README.md','LICENSE','ASSETS-LICENSE.md','VERSION'):
        yield SOURCE/name


def verify_assets(root):
    manifest=json.loads((root/'assets/checksums.json').read_text())
    for name,sha in manifest.items():
        p=(root/name).resolve()
        if not p.is_relative_to(root.resolve()) or digest(p.read_bytes())!=sha:raise ValueError(f'Integridad incorrecta: {name}')
    return len(manifest)


def shell_quote(s):return "'"+str(s).replace("'","'\"'\"'")+"'"

def desktop_quote(s):return '"'+str(s).replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$')+'"'


def install(root=None, yes=False):
    p=paths(root); manifest_path=p['state']/'install.json'
    old=json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    if old and old.get('status')!='installed':raise ValueError('Hay una transacción incompleta. Ejecuta uninstall.sh antes de reintentar.')
    count=verify_assets(SOURCE)
    files=list(source_files()); stamp=digest(b''.join(str(f.relative_to(SOURCE)).encode()+f.read_bytes() for f in files))[:16]
    release=p['data']/'releases'/stamp;current=p['data']/'current'
    launcher=p['bin']/'dsd'; hypr=p['config']/'hypr/hyprland.conf'; include=p['config']/'hypr/dystopian-surveillance.conf'
    if any('\n' in str(v) or '\r' in str(v) for v in p.values()): raise ValueError('Las rutas no pueden contener saltos de línea')
    # Hyprland config has its own syntax; disallow characters that would inject directives/expansions.
    if any(ch in str(include)+str(launcher) for ch in ('#','$',';','"')):raise ValueError('Ruta no compatible con la sintaxis de Hyprland')
    block=f'{BEGIN}\nsource = {include}\n{END}\n'
    body='#!/usr/bin/env bash\nset -euo pipefail\nexec python3 '+shell_quote(current/'tools/launcher.py')+' "$@"\n'
    managed={launcher:(body,0o755),include:(f'# Managed by Dystopian Surveillance Desktop\nexec-once = {shell_quote(launcher)} start\nbind = SUPER SHIFT, D, exec, {shell_quote(launcher)} settings\n',0o644),
             p['applications']/'dystopian-surveillance.desktop':(f'[Desktop Entry]\nType=Application\nName=Dystopian Surveillance · Ajustes\nComment=Centro de control del escritorio\nExec={desktop_quote(launcher)} settings\nIcon=video-display\nTerminal=false\nCategories=Settings;DesktopSettings;\n',0o644)}
    print(f'Recursos verificados: {count}. Versión: {(SOURCE/"VERSION").read_text().strip()}.')
    print(f'Instalar código en: {release}\nAcceso: {launcher}\nIntegración: {include}\nAñadir bloque source en: {hypr}\nLas preferencias y escenas personales se conservarán.')
    if not yes:
        if input('¿Aplicar estos cambios con copia de seguridad? [s/N] ').strip().lower() not in ('s','si','sí','y','yes'):raise ValueError('Instalación cancelada')
    p['state'].mkdir(parents=True,exist_ok=True,mode=0o700)
    backup=p['state']/'backups'/str(time.time_ns());backup.mkdir(parents=True,mode=0o700)
    entries=copy.deepcopy(old['entries']) if old else []
    old_entries={e['path']:e for e in entries}
    for path in managed:
        if path.is_symlink():raise ValueError(f'No se sobrescribe un enlace ajeno: {path}')
        previous=old_entries.get(str(path))
        if previous and path.exists() and digest(path.read_bytes())!=previous['after']:
            raise ValueError(f'Archivo gestionado modificado personalmente: {path}. Conserva tu copia y retíralo antes de reinstalar.')
    existing=hypr.read_text() if hypr.exists() else ''
    if BEGIN in existing and block not in existing:raise ValueError('El bloque Hyprland gestionado fue modificado; revísalo antes de reinstalar')
    if current.exists() or current.is_symlink():
        if not old or not current.is_symlink():raise ValueError(f'No se sobrescribe {current} sin un manifiesto de instalación previo')
    record={'version':1,'status':'installing','entries':entries,'hypr':str(hypr),'hyprBlock':block,
            'hyprExisted':old['hyprExisted'] if old else hypr.exists(),'current':str(current),
            'release':str(release),'previousRelease':str(current.resolve()) if current.exists() else None}
    atomic_json(manifest_path,record)
    rollback=[];previous_link=os.readlink(current) if current.is_symlink() else None
    try:
        if not release.exists():
            stage=release.with_name('.'+stamp+'.stage')
            if stage.exists():shutil.rmtree(stage)
            for src in files:
                dest=stage/src.relative_to(SOURCE);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
            verify_assets(stage);stage.rename(release)
        for path,(content,mode) in managed.items():
            before=path.read_bytes() if path.exists() else None
            rollback.append((path,before,path.stat().st_mode&0o777 if path.exists() else mode))
            if str(path) not in old_entries:
                bp=None
                if before is not None:
                    bp=backup/f'file-{len(entries)}';bp.write_bytes(before)
                entry={'path':str(path),'backup':str(bp) if bp else None,'mode':path.stat().st_mode&0o777 if path.exists() else mode,'after':digest(content.encode())}
                entries.append(entry)
            else:old_entries[str(path)]['after']=digest(content.encode())
            atomic_json(manifest_path,record)
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content);path.chmod(mode)
        if block not in existing:
            rollback.append((hypr,existing.encode() if hypr.exists() else None,0o644))
            if hypr.exists():shutil.copy2(hypr,backup/'hyprland.conf')
            hypr.parent.mkdir(parents=True,exist_ok=True)
            hypr.write_text(existing+('' if not existing or existing.endswith('\n') else '\n')+block)
        current.parent.mkdir(parents=True,exist_ok=True)
        temporary=current.with_name('current.new')
        if temporary.is_symlink():temporary.unlink()
        temporary.symlink_to(release);os.replace(temporary,current)
        record['status']='installed';atomic_json(manifest_path,record)
    except BaseException:
        for path,before,mode in reversed(rollback):
            if before is None:path.unlink(missing_ok=True)
            else:path.write_bytes(before);path.chmod(mode)
        if current.is_symlink():current.unlink()
        if previous_link:current.symlink_to(previous_link)
        if old:atomic_json(manifest_path,old)
        else:manifest_path.unlink(missing_ok=True)
        raise
    print('Instalación terminada. Ejecuta ~/.local/bin/dsd start o vuelve a entrar en Hyprland.\nAjustes: ~/.local/bin/dsd settings o SUPER+SHIFT+D. Diagnóstico: ~/.local/bin/dsd doctor.\nCopias: '+str(p['state']/'backups'))
    return record


def uninstall(root=None, yes=False, purge=False):
    p=paths(root);mp=p['state']/'install.json'
    if not mp.exists():print('No hay instalación registrada.');return
    m=json.loads(mp.read_text())
    if not yes and input('¿Retirar solo los archivos gestionados y conservar datos personales? [s/N] ').lower() not in ('s','si','sí','y','yes'):return
    leftovers=[]
    for e in reversed(m['entries']):
        path=Path(e['path'])
        if path.is_symlink() or (path.exists() and digest(path.read_bytes())!=e['after']):
            print('Conservado por cambios personales:',path);leftovers.append(e);continue
        if e['backup']:
            path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(e['backup'],path);path.chmod(e['mode'])
        else:path.unlink(missing_ok=True)
    hypr=Path(m['hypr'])
    if hypr.exists():
        contents=hypr.read_text();block=m['hyprBlock']
        if block in contents:
            result=contents.replace(block,'',1)
            if result or m['hyprExisted']:hypr.write_text(result)
            else:hypr.unlink()
        elif BEGIN in contents:print('Bloque Hyprland modificado conservado. Retíralo manualmente.');leftovers.append({'hypr':True})
    current=Path(m['current'])
    if current.is_symlink() and current.resolve().is_relative_to((p['data']/'releases').resolve()):current.unlink()
    # Remove only releases recorded by this install, including previous versions, with a known marker.
    releases=p['data']/'releases'
    if releases.exists():
        for folder in releases.iterdir():
            if folder.is_dir() and not folder.is_symlink() and len(folder.name)==16 and (folder/'tools/deploy.py').exists():shutil.rmtree(folder)
    mp.unlink()
    if leftovers:atomic_json(p['state']/'uninstall-preserved.json',leftovers)
    if purge:
        # --yes deliberately does not waive this separate destructive consent.
        if input('Escribe BORRAR para eliminar escenas importadas, configuración e historial: ')=='BORRAR':
            for folder in (p['config']/'dystopian-surveillance',p['data']/'scenes',p['data']/'bundled-media'):
                if folder.is_dir() and not folder.is_symlink():shutil.rmtree(folder)
            (p['state']/'characters.json').unlink(missing_ok=True)
    print('Desinstalación terminada. Preferencias, medios personales y copias conservados salvo confirmación de borrado.\nNo se desinstalan dependencias compartidas ni se borran credenciales del llavero.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['install','uninstall','verify'])
    parser.add_argument('--root',type=Path);parser.add_argument('--yes',action='store_true');parser.add_argument('--purge',action='store_true')
    a=parser.parse_args()
    try:
        if a.action=='verify':print(f'{verify_assets(SOURCE)} recursos verificados')
        elif a.action=='install':install(a.root,a.yes)
        else:uninstall(a.root,a.yes,a.purge)
    except Exception as e:print('ERROR:',e,file=sys.stderr);return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
