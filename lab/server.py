"""Cineosis Lab local server: static files + live archive search proxy + saving assignments.

    python3 server.py [port]      (default 8765)

The archive's search API sends no CORS headers, so the lab calls it through /api/search here.
Queries are cached in cache/live/ and spaced at least GAP seconds apart.
"""
import hashlib, json, os, sys, threading, time, urllib.error, urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

LAB = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(LAB)
API = "https://www.movingimagearchive.com/api/search"
LIVE = os.path.join(LAB, "cache", "live")
ASSIGN = os.path.join(LAB, "assignments.json")
EDITS = os.path.join(LAB, "edits")            # montages saved back from CUT / the Cutting Room
REMOTE = os.path.join(LAB, "cache", "remote") # archive shots fetched on demand for editing
_corpus = {}
_shannon = {}
_shannon_lock = threading.Lock()

def shannon_status():
    try:
        ids = _shannon.get("ids")
        if ids is None:
            ids = json.load(open(os.path.join(LAB, "cache", "emb_ids.json")))
        return {"embedded": len(ids), "model": "ViT-B-32 laion2b_s34b_b79k", "loaded": bool(_shannon)}
    except Exception as e:
        return {"embedded": 0, "model": "unavailable", "loaded": False, "error": str(e)}

def shannon_load():
    if _shannon:
        return
    with _shannon_lock:
        if _shannon:
            return
        import numpy as np, torch, open_clip
        ids = json.load(open(os.path.join(LAB, "cache", "emb_ids.json")))
        emb = np.load(os.path.join(LAB, "cache", "emb.npy")).astype(np.float32)
        emb /= np.linalg.norm(emb, axis=1, keepdims=True) + 1e-9
        corpus = json.load(open(os.path.join(LAB, "cache", "corpus.json")))
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        model, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
        model = model.to(device).eval()
        tok = open_clip.get_tokenizer("ViT-B-32")
        _shannon.update({"np": np, "torch": torch, "ids": ids, "emb": emb, "corpus": corpus,
                         "device": device, "model": model, "tok": tok})

def shannon_search(phrases, limit=64):
    shannon_load()
    import numpy as np
    phrases = [str(x).strip()[:500] for x in phrases if str(x).strip()]
    if not phrases:
        return []
    limit = max(1, min(96, int(limit or 64)))
    torch, model, tok = _shannon["torch"], _shannon["model"], _shannon["tok"]
    with torch.no_grad():
        t = model.encode_text(tok(phrases).to(_shannon["device"])).float()
        t /= t.norm(dim=-1, keepdim=True)
        sims = t.cpu().numpy() @ _shannon["emb"].T
    out = []
    for row in sims:
        k = min(limit, len(row))
        idx = np.argpartition(-row, k - 1)[:k]
        idx = idx[np.argsort(-row[idx])]
        found = []
        for j in idx:
            sid = _shannon["ids"][int(j)]
            c = _shannon["corpus"].get(sid) or {}
            a = float(c.get("startSeconds") or 0)
            b = float(c.get("endSeconds") or a + 4)
            found.append({
                "id": sid,
                "title": c.get("sourceTitle") or c.get("title") or "Archive source",
                "source": c.get("sourceTitle") or "",
                "sourceKey": c.get("sourceSlug") or c.get("sourceTitle") or sid,
                "sourceStart": a,
                "sourceEnd": b,
                "duration": max(.4, b - a),
                "mediaIn": 0,
                "poster": c.get("thumbnailUrl") or "",
                "media": "/media/" + sid + ".mp4",
                "description": c.get("description") or c.get("transcript") or "",
                "raw": round(float(row[int(j)]), 6)
            })
        out.append(found)
    return out



def shannon_source(source_key, phrase="", limit=96):
    shannon_load()
    source_key = str(source_key or "")
    if not source_key:
        return []
    rows = []
    for idx, sid in enumerate(_shannon["ids"]):
        c = _shannon["corpus"].get(sid) or {}
        key = c.get("sourceSlug") or c.get("sourceTitle") or sid
        if key == source_key:
            rows.append((idx, sid, c))
    if not rows:
        return []
    sims = None
    phrase = str(phrase or "").strip()[:500]
    if phrase:
        torch, model, tok = _shannon["torch"], _shannon["model"], _shannon["tok"]
        with torch.no_grad():
            t = model.encode_text(tok([phrase]).to(_shannon["device"])).float()
            t /= t.norm(dim=-1, keepdim=True)
            sims = (t.cpu().numpy() @ _shannon["emb"].T)[0]
    found = []
    for idx, sid, c in rows:
        a = float(c.get("startSeconds") or 0)
        b = float(c.get("endSeconds") or a + 4)
        found.append({
            "id": sid,
            "title": c.get("sourceTitle") or c.get("title") or "Archive source",
            "source": c.get("sourceTitle") or "",
            "sourceKey": source_key,
            "sourceStart": a,
            "sourceEnd": b,
            "duration": max(.4, b - a),
            "mediaIn": 0,
            "poster": c.get("thumbnailUrl") or "",
            "media": "/media/" + sid + ".mp4",
            "description": c.get("description") or c.get("transcript") or "",
            "raw": round(float(sims[idx]), 6) if sims is not None else 0.0
        })
    found.sort(key=lambda x: (-x["raw"], x["sourceStart"]))
    return found[:max(1, min(160, int(limit or 96)))]

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
        if self.path == "/api/shannon/status":
            return self._json(200, shannon_status())
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
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return self._json(400, {"error": "bad json"})
        if self.path == "/api/shannon/source":
            try:
                return self._json(200, {"results": shannon_source(body.get("sourceKey"), body.get("phrase", ""), body.get("limit", 96))})
            except Exception as e:
                return self._json(503, {"error": "Shannon source lookup unavailable: " + str(e)})
        if self.path == "/api/shannon/search":
            phrases = body.get("phrases")
            if not isinstance(phrases, list):
                q = str(body.get("query", "")).strip()
                phrases = [q] if q else []
            try:
                return self._json(200, {"results": shannon_search(phrases, body.get("limit", 64)),
                                        "embedded": shannon_status().get("embedded", 0)})
            except Exception as e:
                return self._json(503, {"error": "Shannon search unavailable: " + str(e)})
        if self.path == "/api/search":
            q = str(body.get("query", "")).strip()[:200]
            if not q:
                return self._json(400, {"error": "empty query"})
            code, data = archive_search(q)
            return self._json(code, data)
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
