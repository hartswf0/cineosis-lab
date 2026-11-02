"""Serves /home/claude/serve with the test overlay (VP9 copies of the WarGames clips, the markov data) and byte ranges.
   python3 serve.py [port]  ->  http://127.0.0.1:PORT/cineosis-lab/lab/wg-film-test.html"""
import sys, os, io, http.server, functools, urllib.request
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
    def translate_path(self,path):
        real=super().translate_path(path); ov=real.replace('/home/claude/serve','/home/claude/serve-overlay',1)
        if os.path.isfile(ov): return ov
        if not os.path.isfile(real) and '/cineosis-lab/lab/' in real and any(k in real for k in ('/thumbs/','/seg/','/aspect/')):
            rel=real.split('/cineosis-lab/lab/',1)[1]
            try:
                d=urllib.request.urlopen('https://raw.githubusercontent.com/hartswf0/cineosis-lab/main/lab/'+rel,timeout=20).read()
                os.makedirs(os.path.dirname(ov),exist_ok=True); open(ov,'wb').write(d); return ov
            except Exception: pass
        return real
    def send_head(self):
        rng=self.headers.get('Range'); path=self.translate_path(self.path)
        if not rng or not os.path.isfile(path): return super().send_head()
        size=os.path.getsize(path); a,b=rng.replace('bytes=','').split('-'); a=int(a or 0); b=int(b) if b else size-1; b=min(b,size-1)
        f=open(path,'rb'); f.seek(a); self.send_response(206); self.send_header('Content-Type',self.guess_type(path)); self.send_header('Accept-Ranges','bytes')
        self.send_header('Content-Range','bytes %d-%d/%d'%(a,b,size)); self.send_header('Content-Length',str(b-a+1)); self.end_headers()
        d=f.read(b-a+1); f.close(); return io.BytesIO(d)
def start(port):
    import threading
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',port),functools.partial(Q,directory='/home/claude/serve'))
    threading.Thread(target=srv.serve_forever,daemon=True).start(); return srv
if __name__=='__main__':
    port=int(sys.argv[1]) if len(sys.argv)>1 else 8800
    http.server.ThreadingHTTPServer(('127.0.0.1',port),functools.partial(Q,directory='/home/claude/serve')).serve_forever()
