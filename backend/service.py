#!/usr/bin/env python3
"""One JSON-lines service per Quickshell instance; stdout is protocol only."""
from __future__ import annotations
import concurrent.futures
import copy
import datetime
import json
import os
import selectors
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.config import ConfigStore, atomic_json, default_config, xdg
from backend.scenes import Library
from backend.events import EventEngine, ambient_rgb
from backend.ai import AIClient
from backend.metrics import Metrics
from backend.playback import prepare_copies


class Service:
    def __init__(self, output=None, store=None, library=None):
        self.output=output or self.send
        self.store=store or ConfigStore(); self.library=library or Library()
        self.memory_path=xdg('state')/'characters.json'
        try: self.memory=json.loads(self.memory_path.read_text())
        except (OSError,ValueError): self.memory={}
        self.events=EventEngine(self.memory); self.metrics=Metrics(); self.ai=AIClient()
        self.active=None; self.jobs={}; self.pool=concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self.next_tick=0; self.dirty=False; self.next_save=0; self.ai_epoch=0
        self.children=[]
        self.playback_epoch=0
        self.schedule_playback()

    def schedule_playback(self):
        self.playback_epoch+=1;self.library.playback_urls={}
        fps=self.store.value['performance']['fps']
        scenes=list(self.library.items.values())
        if any(float(s.get('frameRate',30))>fps for s in scenes):
            job=self.pool.submit(prepare_copies,copy.deepcopy(scenes),fps)
            self.jobs[job]=('playback','',self.playback_epoch)
            self.output({'type':'notice','text':'Preparando copias locales con el límite FPS. Se reutilizarán en próximos arranques.'})

    @staticmethod
    def send(data):
        print(json.dumps(data,ensure_ascii=False,allow_nan=False),flush=True)

    def state(self):
        self.output({'type':'state','config':self.store.value,'scenes':list(self.library.resolved(self.store.value).values()),
                     'warnings':([self.store.warning] if self.store.warning else [])+self.library.warnings,
                     'defaults':default_config()})

    def scene(self,sid):
        if sid not in self.library.items: raise ValueError('Escena inexistente')
        return self.library.resolved(self.store.value)[sid]

    def emit_event(self, event):
        if event:
            self.dirty=True
            if self.store.value['dialogue']['enabled']: self.output({'type':'event',**event})

    def command(self,m):
        op=m.get('op'); c=self.store.value
        if op=='state': self.state()
        elif op=='save':
            before=c['performance']; self.store.save(m['config'])
            if not self.store.value['ai']['enabled']: self.ai_epoch+=1
            if before['fps']!=self.store.value['performance']['fps']:self.schedule_playback()
            if before!=self.store.value['performance']:
                self.output({'type':'notice','text':'FPS se aplica a los vídeos mediante copias locales; calidad a las próximas importaciones. El decodificador cambia al reiniciar el escritorio.'})
            self.state()
            if m.get("next"):
                if m["next"].get("op") not in ("key", "testAI"): raise ValueError("Acción encadenada inválida")
                self.command(m["next"])
        elif op=='open':
            self.scene(m['scene']); self.active=m['scene']; self.events.open(self.active)
            self.dirty=True
            self.emit_event(self.events.choose(self.scene(self.active),'open',c['dialogue']['frequency']))
        elif op=='close': self.active=None
        elif op=='talk':
            s=self.scene(m['scene']); lines=s['dialogues'].get('talk') or s['dialogues'].get('greeting') or ['Canal en silencio.']
            self.emit_event({'scene':s['id'],'lines':lines,'effect':'dialogue'})
        elif op=='launch':
            s=self.scene(m['scene']); aid=m['app']
            if aid not in s['apps']: raise ValueError('Aplicación no asociada a esta escena')
            app=next((a for a in c['apps'] if a['id']==aid),None)
            if not app: raise ValueError('Acceso directo inexistente')
            if app.get('internal')=='settings': self.output({'type':'settings'})
            else:
                argv=list(app['argv'])
                if not shutil.which(argv[0]):
                    fallback=next((a for a in app.get('alternatives',[]) if shutil.which(a)),None)
                    if fallback: argv[0]=fallback
                    else: raise ValueError(f'No está instalado: {argv[0]}. Edita el acceso en Configuración.')
                # argv is passed directly. No shell, command interpolation, eval or hyprctl exec.
                self.children.append(subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL,start_new_session=True,close_fds=True))
            self.emit_event(self.events.choose(s,'app',c['dialogue']['frequency'],app=aid))
        elif op in ('import','pack'):
            if any(v[0] in ('import','pack') for v in self.jobs.values()): raise ValueError('Ya hay una importación en curso')
            if op=='import': job=self.pool.submit(self.library.import_video,m['path'],m.get('name',''),m.get('category','Ciudad'),min(c['performance']['fps'],30),c['performance']['quality'])
            else: job=self.pool.submit(self.library.import_pack,m['path'])
            self.jobs[job]=(op,'',self.ai_epoch)
            self.output({'type':'notice','text':'Importando medios… Puede tardar varios minutos.'})
        elif op=='key':
            u=urlparse(c['ai']['url']); self.ai.secrets.put(f'{u.scheme}://{u.netloc}',m['key'])
            self.output({'type':'notice','text':'Credencial actualizada en el servicio de secretos.'})
        elif op=='clearHistory':
            self.ai_epoch+=1
            for state in self.memory.values(): state['history']=[]
            self.dirty=True; self.persist()
            self.output({'type':'notice','text':'Historial de IA borrado.'})
        elif op in ('ai','testAI'):
            if not c['ai']['enabled']: raise ValueError('Activa y guarda la IA para permitir conexiones al proveedor.')
            if any(v[0] in ('ai','testAI') for v in self.jobs.values()): raise ValueError('Ya hay una petición IA pendiente')
            s=self.scene(m.get('scene') or next(iter(self.library.items)))
            self.memory.setdefault(s['id'],{'visits':0,'cooldowns':{},'history':[]})
            prompt=m.get('text','Responde solamente: conexión correcta.')[:4000]
            history=self.memory[s['id']]['history'] if op=='ai' else []
            job=self.pool.submit(self.ai.chat,copy.deepcopy(c['ai']),s,prompt,copy.deepcopy(history))
            self.jobs[job]=(op,(s['id'],prompt),self.ai_epoch)
            self.output({'type':'notice','text':'Consultando el proveedor activado…'})
        else: raise ValueError('Operación desconocida')

    def persist(self):
        if self.dirty:
            atomic_json(self.memory_path,self.memory); self.dirty=False

    def tick(self):
        now=time.monotonic()
        self.children=[p for p in self.children if p.poll() is None]
        for job,(kind,info,epoch) in list(self.jobs.items()):
            if not job.done(): continue
            del self.jobs[job]
            try:
                result=job.result()
                if kind in ('import','pack'):
                    self.schedule_playback();self.state();self.output({'type':'imported','scene':result})
                elif kind=='playback':
                    if epoch==self.playback_epoch:
                        self.library.playback_urls=result;self.state();self.output({'type':'notice','text':'Límite FPS aplicado a los vídeos.'})
                elif epoch==self.ai_epoch and self.store.value['ai']['enabled']:
                    sid,prompt=info
                    if kind=='ai':
                        h=self.memory[sid]['history']; h.extend([{'role':'user','content':prompt},{'role':'assistant','content':result}])
                        limit=int(self.store.value['ai']['historyLimit'])
                        self.memory[sid]['history']=h[-limit:] if limit else []
                        self.dirty=True; self.emit_event({'scene':sid,'lines':[result],'effect':'dialogue'})
                    else: self.output({'type':'notice','text':result})
            except Exception as e:
                self.output({'type':'error','text':self.error_text(e)})
        if now>=self.next_tick:
            self.next_tick=now+3
            m=self.metrics.read()
            dt=datetime.datetime.now(); m['ambient']='#%02x%02x%02x'%ambient_rgb(dt.hour+dt.minute/60)
            self.output({'type':'stats',**m})
            if self.active:
                self.emit_event(self.events.choose(self.scene(self.active),'tick',self.store.value['dialogue']['frequency']))
        if now>=self.next_save: self.next_save=now+10; self.persist()

    @staticmethod
    def error_text(e):
        if isinstance(e,subprocess.CalledProcessError):
            return 'El conversor de vídeo falló. Comprueba que el archivo se reproduce con ffmpeg.'
        # Never return HTTP response bodies, request headers or credential payloads.
        if isinstance(e, (KeyError,TypeError)): return 'Formato no válido: '+str(e)[:200]
        return str(e)[:500]

    def run(self):
        self.state(); sel=selectors.DefaultSelector(); sel.register(sys.stdin,selectors.EVENT_READ)
        buffer=b''
        try:
            while True:
                for key,_ in sel.select(timeout=.2):
                    chunk=os.read(key.fd,65536)
                    if not chunk: return
                    buffer+=chunk
                    if len(buffer)>4*1024*1024: raise ValueError('Mensaje demasiado grande')
                    while b'\n' in buffer:
                        raw,buffer=buffer.split(b'\n',1)
                        try: self.command(json.loads(raw))
                        except Exception as e: self.output({'type':'error','text':self.error_text(e)})
                self.tick()
        finally:
            self.persist(); self.pool.shutdown(wait=True,cancel_futures=True)


if __name__=='__main__':
    Service().run()
