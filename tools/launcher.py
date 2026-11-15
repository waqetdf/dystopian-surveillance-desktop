#!/usr/bin/env python3
"""Single-instance launcher and Quickshell IPC. Run as the logged-in user."""
import fcntl
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).absolute().parents[1]
sys.path.insert(0,str(ROOT))
from backend.config import ConfigStore, xdg


def main():
    action=sys.argv[1] if len(sys.argv)>1 else 'start'
    if action=='doctor':
        from tools.doctor import main as doctor
        return doctor()
    qs=shutil.which('qs') or shutil.which('quickshell')
    if not qs:print('No se encuentra Quickshell. Ejecuta install.sh.',file=sys.stderr);return 1
    command=[qs,'-p',str(ROOT/'qml')]
    if action=='open':
        if len(sys.argv)!=3:print('Uso: dsd open cam-1');return 2
        return subprocess.call([qs,'ipc','-p',str(ROOT/'qml'),'call','control','open',sys.argv[2]])
    if action=='status':return subprocess.call([qs,'ipc','-p',str(ROOT/'qml'),'call','control','status'])
    if action in ('settings','stop','restart','close'):
        method={'settings':'settings','stop':'quit','restart':'quit','close':'close'}[action]
        result=subprocess.run([qs,'ipc','-p',str(ROOT/'qml'),'call','control',method],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if action in ('stop','close'):return result.returncode
        if action=='settings' and result.returncode==0:return 0
    if action not in ('start','settings','restart'):print('Uso: dsd start|settings|close|stop|restart|status|doctor');return 2
    if os.geteuid()==0:print('No ejecutes la interfaz como root.');return 1
    if not os.environ.get('WAYLAND_DISPLAY'):print('Inicia sesión en Hyprland/Wayland primero.');return 1
    state=xdg('state');state.mkdir(parents=True,exist_ok=True,mode=0o700)
    lock=open(state/'desktop.lock','w')
    try:fcntl.flock(lock,fcntl.LOCK_EX | (0 if action=='restart' else fcntl.LOCK_NB))
    except BlockingIOError:print('El escritorio ya está en ejecución.');return 0
    config=ConfigStore().value
    env=os.environ.copy();env['QT_QUICK_CONTROLS_STYLE']='Basic';env['DSD_ROOT']=str(ROOT)
    env['QT_QPA_PLATFORM']='wayland';env['DSD_SETTINGS']='1' if action=='settings' else '0'
    env['QT_QUICK_CONTROLS_HOVER_ENABLED']='1'
    if not config['performance']['hardwareDecode']:env['QT_FFMPEG_DECODING_HW_DEVICE_TYPES']=','
    return subprocess.call(command,env=env,pass_fds=(lock.fileno(),))

if __name__=='__main__':raise SystemExit(main())
