"""Versioned, validated settings; atomic writes and XDG paths."""
from __future__ import annotations
import copy
import json
import math
import os
import re
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')
CATEGORIES = ['Ciudad', 'Interiores', 'Personajes', 'Industrial', 'Naturaleza distópica', 'Transporte', 'Tecnología', 'Escenas nocturnas']


def xdg(kind: str) -> Path:
    defaults = {'config': '.config', 'data': '.local/share', 'state': '.local/state', 'cache': '.cache'}
    return Path(os.environ.get(f'XDG_{kind.upper()}_HOME', str(Path.home() / defaults[kind]))) / 'dystopian-surveillance'


def atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def default_config():
    specs = [('alley', 0, 0, .30, 1), ('apartment', .30, 0, .24, .80),
             ('rooftop', .30, .80, .24, .20), ('station', .54, 0, .46, .40),
             ('laboratory', .54, .40, .46, .36), ('market', .54, .76, .46, .24)]
    return {
        'version': 1,
        'appearance': {'accent': '#83a6ae', 'background': '#10171c', 'font': 'DejaVu Sans Mono',
                       'border': 1, 'gap': 6, 'crt': False, 'interference': True,
                       'transitionMs': 260, 'ambient': True, 'ambientIntensity': 0.06},
        'panels': [{'id': f'cam-{i+1}', 'scene': s, 'x': x, 'y': y, 'w': w, 'h': h,
                    'scale': 1, 'offsetX': 0, 'offsetY': 0, 'fit': 'contain' if s in ('alley','apartment') else 'cover', 'loop': True,
                    'muted': True, 'speed': 1} for i, (s,x,y,w,h) in enumerate(specs)],
        'profiles': {}, 'sceneOverrides': {},
        'dialogue': {'enabled': True, 'duration': 7, 'frequency': 1},
        'connection': {'enabled': True, 'seconds': 120, 'interferenceSeconds': 5, 'intensity': 0.75},
        'performance': {'fps': 30, 'pauseHidden': True, 'hardwareDecode': True,
                        'quality': 720, 'powerSave': False, 'autoPowerSave': True, 'cpuThreshold': 85},
        'apps': [
            {'id': 'terminal', 'name': 'Terminal', 'icon': '>_', 'argv': ['foot'], 'alternatives': ['kitty', 'alacritty', 'konsole', 'xterm']},
            {'id': 'browser', 'name': 'Navegador', 'icon': '◎', 'argv': ['xdg-open', 'https://archlinux.org']},
            {'id': 'files', 'name': 'Archivos', 'icon': '▤', 'argv': ['xdg-open', str(Path.home())]},
            {'id': 'media', 'name': 'Multimedia', 'icon': '▶', 'argv': ['mpv', '--player-operation-mode=pseudo-gui']},
            {'id': 'monitor', 'name': 'Procesos', 'icon': '▥', 'argv': ['foot', '-e', 'htop']},
            {'id': 'settings', 'name': 'Configuración', 'icon': '⚙', 'argv': [], 'internal': 'settings'}],
        'ai': {'enabled': False, 'url': 'https://api.openai.com/v1/chat/completions',
               'model': 'gpt-4.1-mini', 'maxTokens': 160, 'historyLimit': 12, 'context': '',
               'adapter': {'modelField': 'model', 'messagesField': 'messages',
                           'limitField': 'max_tokens', 'responsePath': 'choices.0.message.content'}}
    }


def merge(base, supplied):
    out = copy.deepcopy(base)
    for k, v in supplied.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def number(v, lo, hi, label):
    if isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v) or not lo <= v <= hi:
        raise ValueError(f'{label}: debe estar entre {lo} y {hi}')


def validate_panels(panels):
    if not isinstance(panels, list) or not 1 <= len(panels) <= 24:
        raise ValueError('Se necesitan entre 1 y 24 paneles')
    seen = set()
    for p in panels:
        if not SLUG.fullmatch(p['id']) or p['id'] in seen or not SLUG.fullmatch(p['scene']):
            raise ValueError('Identificador de panel/escena inválido o duplicado')
        seen.add(p['id'])
        for k in ('x', 'y'): number(p[k], 0, 1, k)
        for k in ('w', 'h'): number(p[k], 0.06, 1, k)
        if p['x'] + p['w'] > 1.000001 or p['y'] + p['h'] > 1.000001:
            raise ValueError('Un panel sale del monitor')
        number(p['scale'], 1, 4, 'Escala')
        number(p['offsetX'], -1, 1, 'Posición X')
        number(p['offsetY'], -1, 1, 'Posición Y')
        number(p['speed'], 0.25, 3, 'Velocidad')
        if p['fit'] not in ('contain', 'cover'): raise ValueError('Encuadre inválido')
        for k in ('loop', 'muted'):
            if not isinstance(p[k], bool): raise ValueError(f'{k} debe ser booleano')
    for i, a in enumerate(panels):
        for b in panels[i+1:]:
            if min(a['x']+a['w'], b['x']+b['w']) - max(a['x'], b['x']) > 0.00001 and min(a['y']+a['h'], b['y']+b['h']) - max(a['y'], b['y']) > 0.00001:
                raise ValueError(f'Los paneles {a["id"]} y {b["id"]} se solapan')


def validate(c):
    if c['version'] != 1: raise ValueError('Versión de configuración no compatible')
    if any(k.lower() in ('key','apikey','api_key','token','secret','password') for k in c['ai']):
        raise ValueError('Las credenciales deben guardarse exclusivamente en el llavero')
    validate_panels(c['panels'])
    for name, panels in c['profiles'].items():
        if not isinstance(name, str) or not 1 <= len(name) <= 80: raise ValueError('Nombre de perfil inválido')
        validate_panels(panels)
    a = c['appearance']
    for k in ('accent', 'background'):
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', a[k]): raise ValueError('Color: usa #RRGGBB')
    number(a['ambientIntensity'], 0, 0.6, 'Ambiente')
    number(a['border'], 0, 5, 'Borde'); number(a['gap'], 0, 24, 'Separación')
    number(a['transitionMs'], 0, 1500, 'Transición')
    number(c['connection']['seconds'], 5, 86400, 'Desconexión')
    number(c['connection']['interferenceSeconds'], 1, 60, 'Interferencia')
    number(c['connection']['intensity'], 0, 1, 'Estática')
    number(c['dialogue']['duration'], 2, 60, 'Duración diálogo')
    number(c['dialogue']['frequency'], 0, 5, 'Frecuencia')
    number(c['performance']['fps'], 10, 60, 'FPS')
    number(c['performance']['quality'], 216, 2160, 'Calidad')
    number(c['performance']['cpuThreshold'], 10, 100, 'Umbral CPU')
    number(c['ai']['maxTokens'], 16, 2048, 'Tokens')
    number(c['ai']['historyLimit'], 0, 100, 'Historial')
    from urllib.parse import urlparse
    u = urlparse(c['ai']['url'])
    if u.scheme != 'https' and not (u.scheme == 'http' and u.hostname in ('localhost', '127.0.0.1', '::1')):
        raise ValueError('IA: usa HTTPS, o HTTP exclusivamente en localhost')
    if not u.hostname or u.username or u.password: raise ValueError('URL de IA inválida')
    for value in c['ai']['adapter'].values():
        if not isinstance(value, str) or not value or len(value) > 120: raise ValueError('Adaptador IA inválido')
    for group, keys in [('appearance', ('crt','interference','ambient')), ('dialogue', ('enabled',)),
                        ('connection', ('enabled',)), ('ai', ('enabled',)),
                        ('performance', ('pauseHidden','hardwareDecode','powerSave','autoPowerSave'))]:
        for k in keys:
            if not isinstance(c[group][k], bool): raise ValueError(f'{k} debe ser booleano')
    seen = set()
    for app in c['apps']:
        if not SLUG.fullmatch(app['id']) or app['id'] in seen: raise ValueError('ID de aplicación inválido/duplicado')
        seen.add(app['id'])
        argv = app['argv']
        if not isinstance(argv, list) or (not argv and app.get('internal') != 'settings'):
            raise ValueError('Comando: usa una lista JSON de argumentos')
        if len(argv)>100 or any(not isinstance(x,str) or '\0' in x or len(x)>8192 for x in argv):
            raise ValueError('Argumentos inválidos')
        if app.get('internal') not in (None, 'settings'): raise ValueError('Acción interna desconocida')
    for sid, scene in c['sceneOverrides'].items():
        if not SLUG.fullmatch(sid): raise ValueError('Escena inválida')
        if any(k not in ('name','personality','dialogues','events','apps') for k in scene):
            raise ValueError('Propiedad de escena no editable')
        for k in ('name','personality'):
            if k in scene and (not isinstance(scene[k],str) or len(scene[k])>4000): raise ValueError('Texto inválido')
        for lines in scene.get('dialogues', {}).values():
            if not isinstance(lines,list) or any(not isinstance(s,str) or len(s)>2000 for s in lines): raise ValueError('Diálogos inválidos')
        for event in scene.get('events', []): validate_event(event)
        if any(app not in seen for app in scene.get('apps', [])): raise ValueError('Aplicación asociada inexistente')
    return c


def validate_event(e):
    if not SLUG.fullmatch(e['id']): raise ValueError('ID de evento inválido')
    if e['trigger'] not in ('open','timer','random','hour','app','memory'): raise ValueError('Disparador inválido')
    number(e.get('probability',1),0,1,'Probabilidad')
    number(e.get('cooldown',60),0,86400,'Espera')
    number(e.get('after',30),0,86400,'Retardo')
    number(e.get('hour',0),0,23,'Hora')
    number(e.get('minVisits',2),1,10000,'Visitas')
    if not isinstance(e.get('lines'),list) or not e['lines'] or any(not isinstance(s,str) or len(s)>2000 for s in e['lines']):
        raise ValueError('El evento necesita texto')


class ConfigStore:
    def __init__(self, directory=None):
        self.path = (directory or xdg('config')) / 'config.json'
        self.warning = ''
        self.value = default_config()
        if self.path.exists():
            try:
                self.value = validate(merge(self.value, json.loads(self.path.read_text())))
            except (ValueError, KeyError, TypeError) as e:
                # Preserve corrupt input for recovery; never silently overwrite it on startup.
                self.warning = f'Configuración inválida: {e}. Se usan valores predeterminados hasta guardar.'

    def save(self, value):
        checked = validate(merge(default_config(), value))
        if self.path.exists():
            backup = self.path.with_suffix('.json.bak')
            backup.write_bytes(self.path.read_bytes()); backup.chmod(0o600)
        atomic_json(self.path, checked)
        self.value = checked
