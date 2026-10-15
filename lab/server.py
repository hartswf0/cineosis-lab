"""Cineosis Lab local server: static files + live archive search proxy + saving assignments.

    python3 server.py [port]      (default 8765)

The archive's search API sends no CORS headers, so the lab calls it through /api/search here.
Queries are cached in cache/live/ and spaced at least GAP seconds apart.
"""
import hashlib, json, os, re, sys, threading, time, urllib.error, urllib.request
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
    if not c and "_slop" not in _corpus:   # the Slopfeeder's archive shots (foraged, not in the corpus): their CDN urls from its atlas
        _corpus["_slop"] = {}
        try:
            _corpus["_slop"] = {x["id"]: x["media"] for x in json.load(open(os.path.join(LAB, "slopfeeder", "atlas.json")))["cards"] if x["type"] == "archive"}
        except (OSError, ValueError, KeyError):
            pass
    return (c and c.get("videoUrl")) or _corpus.get("_slop", {}).get(sid)
GAP = 2.5
_lock, _last = threading.Lock(), [0.0]
_clip, _clip_lock = {}, threading.Lock()
_vj_lock = threading.Lock()
_vj_state = {
    "seq": 1,
    "ts": time.time(),
    "beat_idx": 0,
    "beat_id": "S01-B01",
    "playing": False,
    "cinema_mode": "duet",      # "duet" (Call & Answer), "radio" (Bumblebee FM Dial), "vj" (Crossfader Split), "story" (Pure 1983 + PiP)
    "crossfader": 0.5,          # 0.0 = 100% 1983, 0.5 = Balanced Duet, 1.0 = 100% Archive
    "take_idx": 0,              # 0 = Take 1 (★ The Line), 1 = Take 2, 2 = Take 3, 3 = Multi-Speaker Cast
    "radio_mhz": 88.5,          # FM tuner frequency
    "visual_fx": "split",       # "split", "pip", "ghost", "crt"
    "audio_fx": "norm",         # "norm", "echo", "double", "tight"
    "subtitles": True,
    "story_guide": True,
    "auto_advance": True,
    "cmd": None,
    "cmd_id": 0,
}

def _get_lan_ip():
    import socket, subprocess
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass
    try:
        out = subprocess.check_output(["/sbin/ifconfig"], text=True, timeout=1.5)
        for m in re.findall(r"inet\s+(\d+\.\d+\.\d+\.\d+)", out):
            if not m.startswith("127.") and not m.startswith("169.254."):
                return m
    except Exception:
        pass
    return "127.0.0.1"


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

def render_film(job):
    """markov/render.py in its own process: ffmpeg composes the cut, the dissolves, the words and the voice."""
    import subprocess
    cut = job.get("cut") or []
    if not cut or len(cut) > 400:
        raise ValueError("a cut of 1-400 shots")
    key = hashlib.sha1(json.dumps({k: job.get(k) for k in ("cut", "phrases", "audio", "sound", "calm", "T0", "T1")}, sort_keys=True).encode() + (job.get("audio_b64") or "").encode()[:4096]).hexdigest()[:16]
    job["out"] = "markov/renders/" + key
    if not os.path.exists(os.path.join(LAB, job["out"] + ".mp4")):
        jf = os.path.join(LAB, "markov", "renders", key + ".job.json"); os.makedirs(os.path.dirname(jf), exist_ok=True); json.dump(job, open(jf, "w"))
        r = subprocess.run([sys.executable, os.path.join(LAB, "markov", "render.py"), jf], capture_output=True, text=True, timeout=1800)
        os.remove(jf)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or "render failed")[-400:])
    return {"video": job["out"] + ".mp4"}

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
        if self.path.startswith("/api/vj/state"):
            with _vj_lock:
                st = dict(_vj_state)
            st["lan_ip"] = _get_lan_ip()
            st["port"] = self.server.server_address[1]
            return self._json(200, st)
        if self.path == "/api/assignments":
            return self._json(200, json.load(open(ASSIGN)) if os.path.exists(ASSIGN) else [])
        if self.path == "/api/edits":
            return self._json(200, sorted((json.load(open(os.path.join(EDITS, f))) for f in os.listdir(EDITS) if f.endswith(".json")),
                                          key=lambda e: e.get("ts", "")) if os.path.isdir(EDITS) else [])
        if self.path.startswith("/api/wargames/slice"):
            return self._wargames_slice()
        if self.path.startswith("/api/wargames/splice_audio"):
            return self._wargames_splice_audio()
        if self.path.startswith("/api/wargames/clip"):
            return self._wargames_clip()
        if self.path.startswith("/api/wargames/similar"):
            return self._wargames_similar()
        if self.path.startswith("/media/"):
            return self._media(self.path[len("/media/"):].split("?")[0])
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        if rng and rng.startswith("bytes=") and os.path.isfile(path):
            return self._range(path, rng)
        return super().do_GET()

    def _ensure_wg_clip(self):
        with _clip_lock:
            if "wg_ready" not in _clip:
                import numpy as np
                wg_dir = os.path.join(ROOT, "WAR GAMES")
                wg_emb = np.load(os.path.join(wg_dir, "emb.npy")).astype(np.float32)
                wg_emb /= np.maximum(np.linalg.norm(wg_emb, axis=1, keepdims=True), 1e-8)
                wg_ids = json.load(open(os.path.join(wg_dir, "emb_ids.json")))
                arch_emb = np.load(os.path.join(LAB, "cache", "emb.npy")).astype(np.float32)
                arch_emb /= np.maximum(np.linalg.norm(arch_emb, axis=1, keepdims=True), 1e-8)
                arch_ids = json.load(open(os.path.join(LAB, "cache", "emb_ids.json")))
                corpus = json.load(open(os.path.join(LAB, "cache", "corpus.json")))
                sys.path.insert(0, wg_dir)
                from parse_watch_wargames import load_laion_clip
                _, encode_txt = load_laion_clip(dev="cpu")
                _clip.update(
                    wg_ready=True,
                    np=np,
                    wg_emb=wg_emb,
                    wg_ids=wg_ids,
                    arch_emb=arch_emb,
                    arch_ids=arch_ids,
                    corpus=corpus,
                    encode_txt=encode_txt,
                )

    def _wargames_clip(self):
        import urllib.parse
        qs = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
        q = (qs.get("q", [""])[0] or "").strip()
        if not q:
            return self._json(400, {"error": "missing q"})
        try:
            self._ensure_wg_clip()
            np = _clip["np"]
            vec = _clip["encode_txt"]([q])[0].astype(np.float32)
            vec /= max(float(np.linalg.norm(vec)), 1e-8)
            wg_sims = _clip["wg_emb"] @ vec
            wg_scores = {sid: round(float(s), 4) for sid, s in zip(_clip["wg_ids"], wg_sims)}
            arch_sims = _clip["arch_emb"] @ vec
            top_idx = np.argsort(-arch_sims)[:12]
            arch_hits = []
            for idx in top_idx:
                aid = _clip["arch_ids"][int(idx)]
                c = _clip["corpus"].get(aid) or {}
                arch_hits.append({
                    "id": aid,
                    "title": c.get("sourceTitle") or "Archival Shot",
                    "year": c.get("sourceYear"),
                    "video": c.get("videoUrl"),
                    "thumb": c.get("thumbnailUrl"),
                    "sim": round(float(arch_sims[int(idx)]), 3),
                })
            return self._json(200, {"query": q, "wg_scores": wg_scores, "archive_hits": arch_hits})
        except Exception as e:
            return self._json(500, {"error": str(e)})

    def _wargames_similar(self):
        import urllib.parse
        qs = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
        sid = (qs.get("id", [""])[0] or "").strip()
        try:
            self._ensure_wg_clip()
            np = _clip["np"]
            if sid not in _clip["wg_ids"]:
                return self._json(404, {"error": f"unknown shot {sid}"})
            s_idx = _clip["wg_ids"].index(sid)
            vec = _clip["wg_emb"][s_idx]
            wg_sims = _clip["wg_emb"] @ vec
            wg_scores = {wid: round(float(s), 4) for wid, s in zip(_clip["wg_ids"], wg_sims)}
            arch_sims = _clip["arch_emb"] @ vec
            top_idx = np.argsort(-arch_sims)[:12]
            arch_hits = []
            for idx in top_idx:
                aid = _clip["arch_ids"][int(idx)]
                c = _clip["corpus"].get(aid) or {}
                arch_hits.append({
                    "id": aid,
                    "title": c.get("sourceTitle") or "Archival Shot",
                    "year": c.get("sourceYear"),
                    "video": c.get("videoUrl"),
                    "thumb": c.get("thumbnailUrl"),
                    "sim": round(float(arch_sims[int(idx)]), 3),
                })
            return self._json(200, {"id": sid, "wg_scores": wg_scores, "archive_hits": arch_hits})
        except Exception as e:
            return self._json(500, {"error": str(e)})

    def _wargames_slice(self):
        """Lossless keyframe demuxing (-c copy) or frame-accurate slice from WarGames_1983_H264.mp4."""
        import subprocess, urllib.parse
        qs = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
        try:
            start = max(0.0, float(qs.get("start", [0])[0]))
            end = min(6764.39, float(qs.get("end", [0])[0]))
        except ValueError:
            return self._json(400, {"error": "invalid start/end"})
        if end <= start or end - start > 600:
            return self._json(400, {"error": "slice must be 0.1s to 600s"})
        master = os.path.join(ROOT, "WAR GAMES", "WarGames_1983_H264.mp4")
        if not os.path.isfile(master):
            return self._json(404, {"error": "master WarGames_1983_H264.mp4 not found"})
        mode = "exact" if qs.get("exact", ["0"])[0] == "1" else "copy"
        sdir = os.path.join(LAB, "cache", "wg_slices")
        os.makedirs(sdir, exist_ok=True)
        fname = f"wargames_{start:.2f}_{end:.2f}_{mode}.mp4"
        out = os.path.join(sdir, fname)
        if not os.path.isfile(out) or os.path.getsize(out) < 1000:
            dur = end - start
            if mode == "copy":
                cmd = ["ffmpeg", "-y", "-ss", f"{start:.3f}", "-i", master, "-t", f"{dur:.3f}", "-c", "copy", "-movflags", "+faststart", out]
            else:
                cmd = ["ffmpeg", "-y", "-ss", f"{start:.3f}", "-i", master, "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "fast", "-crf", "21", "-c:a", "aac", "-movflags", "+faststart", out]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if r.returncode != 0 or not os.path.isfile(out):
                return self._json(500, {"error": (r.stderr or "ffmpeg slice failed")[-300:]})
        if qs.get("download", ["0"])[0] == "1":
            size = os.path.getsize(out)
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
            self.send_header("Content-Length", str(size))
            self.end_headers()
            with open(out, "rb") as f:
                self.wfile.write(f.read())
            return
        rng = self.headers.get("Range")
        if rng and rng.startswith("bytes="):
            return self._range(out, rng)
        size = os.path.getsize(out)
        self.send_response(200)
        self.send_header("Content-Type", "video/mp4"); self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(size)); self.end_headers()
        with open(out, "rb") as f:
            try:
                self.wfile.write(f.read())
            except (BrokenPipeError, ConnectionResetError):
                pass

    def _wargames_splice_audio(self):
        """Serve pre-rendered or on-demand normalized audio splices for WarGames Sound Bench & Bumblebee Dilemma."""
        import urllib.parse
        qs = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
        beat = re.sub(r"[^A-Za-z0-9_-]", "", (qs.get("beat", ["S01-B01"])[0] or "S01-B01"))
        mode = (qs.get("mode", ["aligned"])[0] or "aligned").strip()
        if mode not in ("orig", "aligned", "tight"):
            mode = "aligned"
        sdir = os.path.join(LAB, "cache", "wg_sound")
        out = os.path.join(sdir, f"{beat}_{mode}.m4a")
        if not os.path.isfile(out):
            return self._json(404, {"error": f"audio {beat}_{mode}.m4a not found"})
        rng = self.headers.get("Range")
        if rng and rng.startswith("bytes="):
            return self._range(out, rng)
        size = os.path.getsize(out)
        self.send_response(200)
        self.send_header("Content-Type", "audio/mp4")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(size))
        self.end_headers()
        with open(out, "rb") as f:
            try:
                self.wfile.write(f.read())
            except (BrokenPipeError, ConnectionResetError):
                pass

    def _media(self, name):
        """/media/<shot id>.mp4 → a same-origin copy of any corpus shot, so editors can read it as a file and record
        their canvas (a cross-origin video would taint it). Local clips first; otherwise fetched once from the
        archive's CDN into cache/remote/."""
        sid = name[:-4] if name.endswith(".mp4") else name
        if not sid or any(ch not in "0123456789abcdef-_ghijklmnopqrstuvwxyz" for ch in sid):   # shot ids only; no paths
            return self._json(400, {"error": "bad shot id"})
        local = os.path.join(LAB, "clips", sid + ".mp4")
        if not os.path.isfile(local) and os.path.isfile(os.path.join(LAB, "slopfeeder", "fclips", sid + ".mp4")):
            local = os.path.join(LAB, "slopfeeder", "fclips", sid + ".mp4")
        if not os.path.isfile(local) and sid.startswith("wg_"):
            try:
                wga = json.load(open(os.path.join(ROOT, "WAR GAMES", "wargames_archive.json")))
                sh = next((s for s in wga.get("shots", []) if s["id"] == sid), None)
                master = os.path.join(ROOT, "WAR GAMES", "WarGames_1983_H264.mp4")
                if sh and os.path.isfile(master):
                    import subprocess
                    os.makedirs(os.path.join(LAB, "clips"), exist_ok=True)
                    subprocess.run(["ffmpeg", "-y", "-ss", str(sh["start"]), "-i", master, "-t", str(max(1.5, sh["end"] - sh["start"])),
                                    "-vf", "scale=640:-2", "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-c:a", "aac", local],
                                   capture_output=True, timeout=60)
            except Exception:
                pass
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
        if self.path == "/api/render":                    # a Markov Poet film as an MP4 (may carry a recorded voice, so it is allowed to be large)
            if not n or n > 60 * 1024 * 1024:
                return self._json(413, {"error": "request too large"})
            try:
                return self._json(200, render_film(json.loads(self.rfile.read(n))))
            except Exception as e:
                return self._json(500, {"error": str(e)[:400]})
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
        if self.path == "/api/vj/state":
            with _vj_lock:
                for k in ("beat_idx", "beat_id", "playing", "cinema_mode", "crossfader", "take_idx", "radio_mhz", "visual_fx", "audio_fx", "subtitles", "story_guide", "auto_advance"):
                    if k in body:
                        _vj_state[k] = body[k]
                if "cmd" in body and body["cmd"]:
                    _vj_state["cmd"] = str(body["cmd"])
                    _vj_state["cmd_id"] = int(_vj_state.get("cmd_id", 0)) + 1
                _vj_state["seq"] = int(_vj_state.get("seq", 0)) + 1
                _vj_state["ts"] = time.time()
                st = dict(_vj_state)
            st["lan_ip"] = _get_lan_ip()
            st["port"] = self.server.server_address[1]
            return self._json(200, st)
        if self.path == "/api/edits":
            if (not isinstance(body.get("clips"), list) or not body["clips"]) and not str(body.get("tool", "")).startswith("blacktop"):   # a blacktop recipe has no clips
                return self._json(400, {"error": "clips required"})
            os.makedirs(EDITS, exist_ok=True)
            body["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            name = time.strftime("%Y%m%d-%H%M%S") + "-" + str(body.get("tool", "edit"))[:12] + ".json"; body["saved_as"] = name
            json.dump(body, open(os.path.join(EDITS, name), "w"), indent=1, ensure_ascii=False)
            return self._json(200, {"saved": name, "clips": len(body.get("clips") or [])})
        return self._json(404, {"error": "unknown endpoint"})

    def log_message(self, fmt, *args):
        if "/api/" in str(args[0] if args else "") and "/api/vj/state" not in str(args[0] if args else ""):
            sys.stderr.write("%s\n" % (fmt % args))

if __name__ == "__main__":
    ThreadingHTTPServer.allow_reuse_address = True
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    srv = None
    for p in [port, 8765, 8766, 8767, 8888, 8080, 0]:
        try:
            srv = ThreadingHTTPServer(("0.0.0.0", p), Handler)
            port = srv.server_address[1]
            break
        except OSError:
            continue
    if srv is None:
        raise RuntimeError("Could not bind any local port")
    lan_ip = _get_lan_ip()
    print(f"Cineosis Lab on http://localhost:{port}/lab/found-wargames.html  ·  VJ Couch Cinema on http://{lan_ip}:{port}/lab/vj-wargames.html", flush=True)
    srv.serve_forever()

