"""Opt-in HTTPS chat adapter. Secrets use org.freedesktop.secrets only."""
import json
import urllib.request
from urllib.parse import urlparse


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Redirección rechazada: configura la URL final del proveedor')


class Secrets:
    @staticmethod
    def collection():
        import secretstorage
        bus = secretstorage.dbus_init()
        col = secretstorage.get_default_collection(bus)
        if col.is_locked(): col.unlock()
        if col.is_locked(): raise RuntimeError('Desbloquea el llavero del sistema')
        return col

    def get(self, origin):
        col=self.collection()
        items=list(col.search_items({'application':'dystopian-surveillance','origin':origin}))
        return items[0].get_secret().decode() if items else ''

    def put(self, origin, key):
        col=self.collection()
        attrs={'application':'dystopian-surveillance','origin':origin}
        for item in col.search_items(attrs): item.delete()
        if key: col.create_item('Dystopian Surveillance · '+origin, attrs,key.encode(),replace=True)


class AIClient:
    def __init__(self, secrets=None): self.secrets=secrets or Secrets()

    def chat(self, config, scene, prompt, history):
        if not config['enabled']: raise ValueError('La IA está desactivada. No se ha enviado ningún dato.')
        u=urlparse(config['url'])
        if u.scheme!='https' and not (u.scheme=='http' and u.hostname in ('localhost','127.0.0.1','::1')):
            raise ValueError('Proveedor no seguro')
        origin=f'{u.scheme}://{u.netloc}'
        key=self.secrets.get(origin)
        messages=[{'role':'system','content':scene['personality']+'\n'+config['context']+'\nResponde en español y de forma breve.'}]
        limit=int(config['historyLimit'])
        if limit: messages+=history[-limit:]
        messages.append({'role':'user','content':prompt[:4000]})
        a=config['adapter']
        payload={a['modelField']:config['model'],a['messagesField']:messages,a['limitField']:int(config['maxTokens'])}
        headers={'Content-Type':'application/json'}
        if key: headers['Authorization']='Bearer '+key
        request=urllib.request.Request(config['url'],json.dumps(payload).encode(),headers,method='POST')
        opener=urllib.request.build_opener(NoRedirect())
        with opener.open(request, timeout=25) as r:
            data=r.read(1024*1024+1)
            if len(data)>1024*1024: raise ValueError('Respuesta del proveedor demasiado grande')
        result=json.loads(data)
        for segment in a['responsePath'].split('.'):
            result=result[int(segment)] if isinstance(result,list) else result[segment]
        if not isinstance(result,str): raise ValueError('La ruta de respuesta no contiene texto')
        return result[:4000]
