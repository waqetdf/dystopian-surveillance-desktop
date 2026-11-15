#!/usr/bin/env python3
"""Integration smoke test on an existing Wayland compositor.
Uses an isolated QML config + XDG directories; never changes the user's settings.
Requires qs/quickshell on PATH. A temporary desktop layer and settings window appear.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    qs=shutil.which('qs') or shutil.which('quickshell')
    if not qs or not os.environ.get('WAYLAND_DISPLAY'):
        print('Necesita Quickshell y una sesión Wayland.');return 2
    errors=[]
    with tempfile.TemporaryDirectory(prefix='dsd-wayland-') as d:
        d=Path(d);shutil.copytree(ROOT/'qml',d/'qml')
        env=os.environ.copy();env['DSD_ROOT']=str(ROOT);env['QT_QPA_PLATFORM']='wayland';env['QT_QUICK_CONTROLS_STYLE']='Basic'
        data=Path(env.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))
        env.setdefault('DSD_MEDIA_DIR',str(data/'dystopian-surveillance/bundled-media'))
        env.update(XDG_CONFIG_HOME=str(d/'config'),XDG_DATA_HOME=str(d/'data'),XDG_STATE_HOME=str(d/'state'),XDG_CACHE_HOME=str(d/'cache'))
        log=d/'log';f=log.open('w');proc=subprocess.Popen([qs,'-p',str(d/'qml')],env=env,stdout=f,stderr=subprocess.STDOUT)
        def call(method,*args):
            r=subprocess.run([qs,'ipc','-p',str(d/'qml'),'call','control',method,*args],env=env,capture_output=True,text=True,timeout=5)
            if r.returncode:raise RuntimeError(r.stderr or r.stdout)
            return r.stdout.strip()
        def status():return json.loads(call('status'))
        try:
            deadline=time.monotonic()+15
            while time.monotonic()<deadline:
                if proc.poll() is not None:raise RuntimeError('Quickshell terminó: '+log.read_text())
                try:
                    if status()['ready']:break
                except (RuntimeError,ValueError):pass
                time.sleep(.2)
            assert status()['ready'];assert status()['panels']==6
            call('open','cam-1');time.sleep(.5);assert status()['activePanel']=='cam-1'
            call('open','cam-2');time.sleep(.5);assert status()['activePanel']=='cam-2'
            call('close');time.sleep(.2);assert status()['activePanel']==''
            call('settings');time.sleep(.8);assert status()['settings'] is True
            call('quit');proc.wait(timeout=10);assert proc.returncode==0
            output=log.read_text()
            for token in ('TypeError','ReferenceError','Unable to assign','Could not create attached','Failed to load configuration'):
                if token in output:errors.append(token)
            assert not errors,output
            artifact=os.environ.get('DSD_WAYLAND_LOG')
            if artifact:Path(artifact).write_text(output)
            print('PASS: real Quickshell + Wayland layer-shell load, service, scene switching, single selection, close, settings IPC and clean exit')
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:proc.kill();proc.wait()
            f.close()
    return 0

if __name__=='__main__':raise SystemExit(main())
