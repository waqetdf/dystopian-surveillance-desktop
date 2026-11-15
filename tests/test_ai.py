"""Local HTTP fixture only: never contacts a third-party AI provider."""
import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.ai import AIClient
from backend.config import default_config, validate


class MemorySecrets:
    def get(self, origin):return 'test-only-credential'


class AITests(unittest.TestCase):
    def test_opt_in_provider_payload_and_response_adapter(self):
        received=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                received.append((self.headers.get('Authorization'),json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
                body=json.dumps({'result':{'text':'Canal local confirmado.'}}).encode()
                self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        server=HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            c=default_config()['ai'];c.update(enabled=True,url=f'http://127.0.0.1:{server.server_port}/chat',historyLimit=1)
            c['adapter']['responsePath']='result.text'
            result=AIClient(MemorySecrets()).chat(c,{'personality':'Reservada.'},'Hola',[{'role':'user','content':'old'},{'role':'assistant','content':'recent'}])
            self.assertEqual(result,'Canal local confirmado.');auth,payload=received[0]
            self.assertEqual(auth,'Bearer test-only-credential');self.assertEqual(payload['messages'][1]['content'],'recent')
            self.assertNotIn('old',json.dumps(payload));self.assertEqual(payload['messages'][-1]['content'],'Hola')
        finally:server.shutdown();server.server_close();thread.join()
    def test_disabled_client_cannot_open_connection(self):
        c=default_config()['ai']
        with self.assertRaises(ValueError):AIClient(MemorySecrets()).chat(c,{'personality':'x'},'private',[])
    def test_credentials_are_rejected_in_config(self):
        for key in ('apiKey','api_key','key','secret','password','token'):
            c=default_config();c['ai'][key]='secret'
            with self.assertRaises(ValueError):validate(c)
    def test_redirect_cannot_leak_authorization(self):
        reached=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                self.send_response(302);self.send_header('Location','/destination');self.end_headers()
            def do_GET(self):reached.append(True);self.send_response(200);self.end_headers()
        server=HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            c=default_config()['ai'];c.update(enabled=True,url=f'http://127.0.0.1:{server.server_port}/chat')
            with self.assertRaises(ValueError):AIClient(MemorySecrets()).chat(c,{'personality':'x'},'private',[])
            self.assertEqual(reached,[])
        finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main()
