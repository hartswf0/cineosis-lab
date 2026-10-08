"""The VOLHOLLA songs (THE LITURGY OF THE TWO BUTTONS) heard for the SLOPFEEDER films: for each, its tempo and beats, its energy over
time, its sections (where the music changes), and what each section sounds like to CLAP (war drums, choir, drone, throat song...).
A section's sound and energy suggest which part of the world it belongs to. Writes slopfeeder/songs.json.
usage: .venv/bin/python slopfeeder/songs.py"""
import json, os, glob
import numpy as np, librosa, torch
os.environ.setdefault("HF_HUB_OFFLINE", "1")
from transformers import ClapModel, ClapProcessor
D = os.path.dirname(os.path.abspath(__file__)); ALB = os.path.expanduser("~/moto/THE LITURGY OF THE TWO BUTTONS"); PAGES = os.path.expanduser("~/moto/VOLHOLLA")
PICK = {"26": "the best core one", "06": "", "07": "", "09": "cool starting but grating", "13": "holy sounding", "14": "best for the dune movie", "20": "good beginning, creepy voice maybe", "23": "Greek chant"}
MOODS = ["pounding war drums", "a huge choir chanting", "a low droning hum", "throat singing", "epic orchestral battle music", "tense suspense music", "a triumphant anthem",
         "a mournful lament", "a solo voice singing", "electronic synthesizer pulses", "a sacred hymn", "a marching rhythm", "silence and wind", "a creepy whispering voice"]
# which part of the slopfeeder world a sound asks for
WORLD = {"pounding war drums": "THE LANDING", "epic orchestral battle music": "THE LANDING", "a marching rhythm": "THE DRILL LINE", "a huge choir chanting": "THE FLEET",
         "a triumphant anthem": "THE FLEET", "a low droning hum": "THE TIDE", "throat singing": "THE DRILL LINE", "tense suspense music": "THE SCREEN",
         "a mournful lament": "THE AFTERMATH", "a solo voice singing": "THE KITCHEN", "electronic synthesizer pulses": "THE SCREEN", "a sacred hymn": "THE KITCHEN",
         "silence and wind": "THE TIDE", "a creepy whispering voice": "THE RENDER"}
import re, urllib.parse
cm = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval(); cp = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
with torch.no_grad(): MT = cm.get_text_features(**cp(text=MOODS, return_tensors="pt", padding=True)); MT = (MT / MT.norm(dim=-1, keepdim=True)).numpy()
songs = []
for n, note in PICK.items():
    page = open(os.path.join(PAGES, f"song-twobuttons-{n}.html")).read()
    title = re.search(r"<title>([^<·]+)", page).group(1).strip(); src = urllib.parse.unquote(re.search(r'src="\.\./THE%20LITURGY[^"]+?/([^"/]+\.ogg)"', page).group(1))
    y, sr = librosa.load(os.path.join(ALB, src), sr=22050, mono=True); dur = len(y) / sr
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr); bt = librosa.frames_to_time(beats, sr=sr)
    rms = librosa.feature.rms(y=y, hop_length=sr // 2)[0]; e = (rms - rms.min()) / (rms.max() - rms.min() + 1e-9)   # energy every half second
    on = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
    # sections: where the timbre and harmony change
    F = np.vstack([librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=2048), librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=2048)])
    k = int(np.clip(round(dur / 22), 5, 10)); bnd = librosa.segment.agglomerative(F, k); bt_s = list(librosa.frames_to_time(bnd, sr=sr, hop_length=2048)) + [dur]
    bt_s = [0.0] + [b for b in bt_s[1:-1] if b > 4] + [dur]
    # CLAP every 6 s (48 kHz), then each section's mood
    y48 = librosa.resample(y, orig_sr=sr, target_sr=48000); W = []
    for a in np.arange(0, dur - 3, 6.0):
        seg = y48[int(a * 48000): int((a + 6) * 48000)]
        with torch.no_grad(): f = cm.get_audio_features(**cp(audios=[seg], sampling_rate=48000, return_tensors="pt"))
        W.append((a, (f / f.norm(dim=-1, keepdim=True)).numpy()[0]))
    secs = []
    for a, b in zip(bt_s, bt_s[1:]):
        ws = [w for t, w in W if a - 3 <= t < b] or [min(W, key=lambda x: abs(x[0] - a))[1]]
        p = np.mean(ws, 0) @ MT.T; top = [MOODS[j] for j in np.argsort(-p)[:3]]
        rel = p - (np.mean([w for _, w in W], 0) @ MT.T)          # what this section has more of than the song as a whole
        en = float(e[int(a * 2): max(int(a * 2) + 1, int(b * 2))].mean()); ons = float(on[int(a * sr / 512): int(b * sr / 512)].mean())
        secs.append({"t0": round(a, 2), "t1": round(b, 2), "energy": round(en, 3), "attack": round(ons, 3), "sound": top, "rel": [round(float(x), 4) for x in rel], "lead": MOODS[int(np.argmax(rel))],
                     "beats": int(((bt >= a) & (bt < b)).sum())})
    # the world each section asks for: its loudest, hardest stretches are the landing; the rest by what it has more of than the song
    es = np.array([x["energy"] for x in secs]); hi = np.quantile(es, .7) if len(es) > 2 else 1
    for x in secs: x["world"] = "THE LANDING" if x["energy"] >= hi and x["energy"] > .45 else ("THE TIDE" if x["energy"] < .18 else WORLD[x["lead"]])
    songs.append({"n": n, "title": title, "note": note, "file": src, "dur": round(dur, 2), "tempo": round(float(np.atleast_1d(tempo)[0]), 1),
                  "energy": [round(float(x), 3) for x in e], "beats": [round(float(t), 2) for t in bt], "sections": secs,
                  "sound": [MOODS[j] for j in np.argsort(-(np.mean([w for _, w in W], 0) @ MT.T))[:4]]})
    print(n, title, f"{dur:.0f}s", f"{songs[-1]['tempo']} bpm", len(secs), "sections ·", " / ".join(f"{s['world']}({s['lead'][:14]},{s['energy']:.2f})" for s in secs), flush=True)
json.dump({"moods": MOODS, "songs": songs}, open(os.path.join(D, "songs.json"), "w"), ensure_ascii=False)
