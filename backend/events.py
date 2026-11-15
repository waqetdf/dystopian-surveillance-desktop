"""Offline event selection and connection state; injectable time/random for tests."""
import datetime
import random
import time


class EventEngine:
    def __init__(self, memory, rng=None, clock=None):
        self.memory = memory
        self.rng = rng or random.Random()
        self.clock = clock or time.time
        self.opened = {}
        self.last_message = {}

    def open(self, sid):
        state = self.memory.setdefault(sid, {'visits': 0, 'cooldowns': {}, 'history': []})
        state['visits'] += 1
        self.opened[sid] = self.clock()

    def choose(self, scene, trigger, frequency=1, app=None, hour=None):
        now = self.clock()
        sid = scene['id']
        state = self.memory.setdefault(sid, {'visits': 0, 'cooldowns': {}, 'history': []})
        if frequency <= 0 or now - self.last_message.get(sid, -1e20) < 10 / max(frequency, .1): return None
        for e in scene['events']:
            t = e['trigger']
            eligible = t == trigger
            if trigger == 'tick':
                eligible = t in ('timer', 'random', 'hour')
            if trigger == 'open' and t == 'memory': eligible = state['visits'] >= e.get('minVisits',2)
            if not eligible: continue
            if t == 'app' and e.get('app') != app: continue
            if t == 'timer' and now - self.opened.get(sid, now) < e.get('after',30): continue
            if t == 'hour' and (hour if hour is not None else datetime.datetime.now().hour) != e.get('hour',0): continue
            if now - state['cooldowns'].get(e['id'], -1e20) < e.get('cooldown',60) / max(frequency,.1): continue
            if self.rng.random() > min(1, e.get('probability',1) * frequency): continue
            state['cooldowns'][e['id']] = now
            self.last_message[sid] = now
            return {'scene': sid, 'lines': e['lines'], 'effect': e.get('effect','dialogue')}
        return None


def connection_phase(elapsed, settings):
    if not settings['enabled']: return 0
    return max(0, min(1, (elapsed - settings['seconds']) / settings['interferenceSeconds']))


def ambient_rgb(hour):
    stops = [(0,(24,38,55)),(5,(39,52,67)),(7,(104,116,127)),(11,(126,145,155)),
             (14,(158,166,171)),(18,(126,99,81)),(21,(34,62,78)),(24,(24,38,55))]
    hour %= 24
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if a <= hour <= b:
            t=(hour-a)/(b-a); t=t*t*(3-2*t)
            return tuple(round(x+(y-x)*t) for x,y in zip(ca,cb))
