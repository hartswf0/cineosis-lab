"""Cineosis Lab local server: static files + live archive search proxy + saving assignments.

    python3 server.py [port]      (default 8765)

The archive's search API sends no CORS headers, so the lab calls it through /api/search here.
Queries are cached in cache/live/ and spaced at least GAP seconds apart.
"""
import hashlib, json, os, sys, threading, time, urllib.error, urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")   # an expired stored Hugging Face token otherwise blocks public model downloads
LAB = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(LAB)
API = "https://www.movingimagearchive.com/api/search"
LIVE = os.path.join(LAB, "cache", "live")
ASSIGN = os.path.join(LAB, "assignments.json")
EDITS = os.path.join(LAB, "edits")            # montages saved back from CUT / the Cutting Room
REMOTE = os.path.join(LAB, "cache", "remote") # archive shots fetched on demand for editing
_corpus = {}

def corpus_url(sid):
    if not _corpus:
        try:
            _corpus.update(json.load(open(os.path.join(LAB, "cache", "corpus.json"))))
        except OSError:
            pass
    c = _corpus.get(sid)
    return c and c.get("videoUrl")
GAP = 2.5
_lock, _last = threading.Lock(), [0.0]
_clip, _clip_lock = {}, threading.Lock()

REC = os.path.join(LAB, "markov", "recordings")

def transcribe(data, ext):
    """A recording becomes timed language for the Shannon engine: whisper (small.en) with word timestamps.
    The audio is kept in markov/recordings/ so the page can play it as the film's clock. Local only."""
    os.makedirs(REC, exist_ok=True)
    name = hashlib.sha1(data).hexdigest()[:16] + ext
    path = os.path.join(REC, name)
    if not os.path.exists(path):
        open(path, "wb").write(data)
    cache = path + ".json"
    if os.path.exists(cache):
        return json.load(open(cache))
    import subprocess
    r = subprocess.run([sys.executable, os.path.join(LAB, "markov", "transcribe.py"), path, cache], capture_output=True, text=True, timeout=3600)
    if r.returncode != 0 or not os.path.exists(cache):
        raise RuntimeError((r.stderr or "whisper failed")[-300:])
    out = json.load(open(cache)); out["audio"] = "markov/recordings/" + name
    json.dump(out, open(cache, "w"))
    return out

def speak(body):
    """The poem spoken by Piper, phrase by phrase (markov/speak.py in its own process): returns the audio path and each phrase's times."""
    import subprocess
    phrases = [str(x)[:400] for x in body.get("phrases", [])][:400]
    voice = body.get("voice") if body.get("voice") in ("en_US-ryan-high", "en_US-lessac-medium") else "en_US-ryan-high"
    job = {"phrases": phrases, "gaps": [float(g) for g in body.get("gaps", [])][:400] or None, "voice": voice}
    key = hashlib.sha1(json.dumps(job, sort_keys=True).encode()).hexdigest()[:16]
    job["out"] = "markov/voice/live/" + key
    meta = os.path.join(LAB, job["out"] + ".json")
    if not os.path.exists(meta):
        os.makedirs(os.path.dirname(meta), exist_ok=True)
        jf = meta + ".job"; json.dump(job, open(jf, "w"))
        r = subprocess.run([os.path.join(LAB, ".venv", "bin", "python"), os.path.join(LAB, "markov", "speak.py"), jf], capture_output=True, text=True, timeout=900)
        os.remove(jf)
        if r.returncode != 0 or not os.path.exists(meta):
            raise RuntimeError((r.stderr or "piper failed")[-300:])
    out = json.load(open(meta)); out["audio"] = job["out"] + ".mp3"
    return out

def embed_texts(texts):
    """CLIP text embeddings for the Shannon engine's incoming language; loaded on first use."""
    with _clip_lock:
        if not _clip:
            import open_clip, torch
            os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")   # an expired stored token blocks even public downloads
            # OpenAI's ViT-B/32: the same model the pages run in the browser (transformers.js), so server and browser read words alike
            m, _, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval()
            _clip.update(m=m, tok=open_clip.get_tokenizer("ViT-B-32"), torch=torch)
        with _clip["torch"].no_grad():
            e = _clip["m"].encode_text(_clip["tok"](texts)).float(); e = e / e.norm(dim=-1, keepdim=True)
        return [[round(float(v), 5) for v in r] for r in e]

def archive_search(q):
    os.makedirs(LIVE, exist_ok=True)
    path = os.path.join(LIVE, hashlib.sha1(q.encode()).hexdigest() + ".json")
    if os.path.exists(path):
        return 200, json.load(open(path))
    with _lock:
        wait = _last[0] + GAP - time.time()
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        req = urllib.request.Request(API, data=json.dumps({"query": q}).encode(),
                                     headers={"content-type": "application/json", "user-agent": "cineosis-lab"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, {"error": "archive busy, try again in a moment" if e.code == 429 else f"archive error {e.code}"}
    json.dump(data, open(path, "w"))
    return 200, data

class Handler(SimpleHTTPRequestHandler):
    """Serves the project root (periodic table at /, lab at /lab/) — the same layout as GitHub Pages."""
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def translate_path(self, path):
        if path.split("?")[0].rstrip("/").endswith("deamer.txt"):   # the book's text is local-only
            return os.path.join(ROOT, "__not_served__")
        return super().translate_path(path)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store" if self.path.endswith((".json", ".html", ".js", ".css")) else "max-age=86400")
        super().end_headers()

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/assignments":
            return self._json(200, json.load(open(ASSIGN)) if os.path.exists(ASSIGN) else [])
        if self.path == "/api/edits":
            return self._json(200, sorted((json.load(open(os.path.join(EDITS, f))) for f in os.listdir(EDITS) if f.endswith(".json")),
                                          key=lambda e: e.get("ts", "")) if os.path.isdir(EDITS) else [])
        if self.path.startswith("/media/"):
            return self._media(self.path[len("/media/"):].split("?")[0])
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        if rng and rng.startswith("bytes=") and os.path.isfile(path):
            return self._range(path, rng)
        return super().do_GET()

    def _media(self, name):
        """/media/<shot id>.mp4 → a same-origin copy of any corpus shot, so editors can read it as a file and record
        their canvas (a cross-origin video would taint it). Local clips first; otherwise fetched once from the
        archive's CDN into cache/remote/."""
        sid = name[:-4] if name.endswith(".mp4") else name
        if not sid or any(ch not in "0123456789abcdef-" for ch in sid):   # shot ids only; no paths
            return self._json(400, {"error": "bad shot id"})
        local = os.path.join(LAB, "clips", sid + ".mp4")
        if not os.path.isfile(local):
            local = os.path.join(REMOTE, sid + ".mp4")
            if not os.path.isfile(local):
                url = corpus_url(sid)
                if not url:
                    return self._json(404, {"error": "unknown shot"})
                os.makedirs(REMOTE, exist_ok=True)
                try:
                    with urllib.request.urlopen(urllib.request.Request(url, headers={"user-agent": "cineosis-lab"}), timeout=60) as r:
                        data = r.read()
                except Exception as e:
                    return self._json(502, {"error": f"could not fetch shot: {e}"})
                tmp = local + ".part"
                open(tmp, "wb").write(data); os.replace(tmp, local)
        rng = self.headers.get("Range")
        if rng and rng.startswith("bytes="):
            return self._range(local, rng)
        size = os.path.getsize(local)
        self.send_response(200)
        self.send_header("Content-Type", "video/mp4"); self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(size)); self.end_headers()
        with open(local, "rb") as f:
            try:
                self.wfile.write(f.read())
            except (BrokenPipeError, ConnectionResetError):
                pass

    def _range(self, path, rng):
        """Serve a single byte range so video can seek (SimpleHTTPRequestHandler ignores Range)."""
        size = os.path.getsize(path)
        a, _, b = rng[6:].split(",")[0].partition("-")
        try:
            start = int(a) if a else max(0, size - int(b))
            end = int(b) if (a and b) else size - 1
        except ValueError:
            return super().do_GET()
        end = min(end, size - 1)
        if start > end or start >= size:
            self.send_response(416); self.send_header("Content-Range", f"bytes */{size}"); self.end_headers(); return
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        with open(path, "rb") as f:
            f.seek(start)
            left = end - start + 1
            while left > 0:
                chunk = f.read(min(1 << 16, left))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    return
                left -= len(chunk)

    def do_POST(self):
        n = int(self.headers.get("content-length", 0))
        if self.path.startswith("/api/transcribe"):
            if not n or n > 300 * 1024 * 1024:
                return self._json(400, {"error": "send one audio file under 300 MB"})
            ext = "." + (self.path.split("ext=")[-1] if "ext=" in self.path else "mp3")[:5].strip(".")
            try:
                return self._json(200, transcribe(self.rfile.read(n), ext))
            except Exception as e:
                return self._json(500, {"error": str(e)[:300]})
        if n < 0 or n > 1000000:
            return self._json(413, {"error": "request too large"})
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return self._json(400, {"error": "bad json"})
        if self.path == "/api/search":
            q = str(body.get("query", "")).strip()[:200]
            if not q:
                return self._json(400, {"error": "empty query"})
            code, data = archive_search(q)
            return self._json(code, data)
        if self.path == "/api/shannon/retrieve":
            texts = body.get("texts")
            if not isinstance(texts, list) or not 1 <= len(texts) <= 121 or any(not isinstance(t, str) or not t.strip() or len(t) > 4000 for t in texts):
                return self._json(400, {"error": "Provide 1–121 nonempty phrases, at most 4000 characters each."})
            try:
                from shannon.retrieval import retrieve
                return self._json(200, {"model": "ViT-B-32/laion2b_s34b_b79k", "rows": retrieve(texts)})
            except Exception as error:
                sys.stderr.write("Shannon retrieval: %s\n" % error)
                return self._json(503, {"error": "Text encoder unavailable. Install open_clip_torch and its matching model; cached studies remain available."})
        if self.path == "/api/speak":
            if not body.get("phrases"):
                return self._json(400, {"error": "phrases required"})
            try:
                return self._json(200, speak(body))
            except Exception as e:
                return self._json(500, {"error": str(e)[:300]})
        if self.path == "/api/embed":
            texts = [str(t)[:300] for t in body.get("texts", [])][:64]
            if not texts:
                return self._json(400, {"error": "texts required"})
            try:
                return self._json(200, {"emb": embed_texts(texts)})
            except Exception as e:                      # no open_clip in this python: the page falls back to its preset embeddings
                return self._json(501, {"error": str(e)[:200]})
        if self.path == "/api/assign":
            if not body.get("id") or not body.get("n"):
                return self._json(400, {"error": "id and n required"})
            rows = json.load(open(ASSIGN)) if os.path.exists(ASSIGN) else []
            row = {k: body.get(k) for k in ("id", "n", "note", "a", "b", "clip")}
            row["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            rows.append(row)
            json.dump(rows, open(ASSIGN, "w"), indent=1, ensure_ascii=False)
            return self._json(200, row)
        if self.path == "/api/edits":
            if not isinstance(body.get("clips"), list) or not body["clips"]:
                return self._json(400, {"error": "clips required"})
            os.makedirs(EDITS, exist_ok=True)
            body["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            name = time.strftime("%Y%m%d-%H%M%S") + "-" + str(body.get("tool", "edit"))[:12] + ".json"
            json.dump(body, open(os.path.join(EDITS, name), "w"), indent=1, ensure_ascii=False)
            return self._json(200, {"saved": name, "clips": len(body["clips"])})
        return self._json(404, {"error": "unknown endpoint"})

    def log_message(self, fmt, *args):
        if "/api/" in str(args[0] if args else ""):   # args[0] is not always the request line (errors pass codes)
            sys.stderr.write("%s\n" % (fmt % args))

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    print(f"Cineosis Lab on http://localhost:{port}/lab/  ·  periodic table on http://localhost:{port}/periodic-table.html", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
