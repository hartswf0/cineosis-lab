"""The periodic table of sound → lab/sound-table.json.

Columns (16 + silence): what KIND of sound, ordered from the poet's voice outwards (distance from the poet, then
tonal → noisy: the atlas's own measured line LOOP 0.008 → TEXTURE 0.74 flatness), in four families:
voice · music · field (keynote) · signal. The archive footage's own sound enters as the three "found" columns.
Rows (3): where the sound stands to the image — IN (source on screen), OFF (of the world, unseen), OUT (outside the
film-world). This is the one sound taxonomy Deamer gives (after Chion, pp.167–168). A sound is not born in a row:
it lands there when it is placed against a picture, so a cell is a kind of sound × a use of it.
Per column: counts and measured medians from the atlas (sonic.json, pack.json, codex/lines.json, samples.json) and
from lab/cache/sound-census.json (our clips), playable examples, and its mix law (priority, what it yields to).
Cell readings are the editor's, marked as inference; Deamer's own sound notes are attached where he has one.
    python3 sound/build_sound_table.py
"""
import json, os, statistics, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LAB = os.path.join(ROOT, "lab")
ATLAS = "https://hartswf0.github.io/butterfly-halfworld/wygwyl/"
CACHE = os.path.join(HERE, "atlas-cache"); os.makedirs(CACHE, exist_ok=True)

def atlas(path):
    p = os.path.join(CACHE, path.replace("/", "__"))
    if not os.path.exists(p):
        with urllib.request.urlopen(ATLAS + path, timeout=60) as r: open(p, "wb").write(r.read())
    return json.load(open(p))

def url(f): return f if f.startswith("http") else ATLAS + urllib.request.quote(f)
med = lambda xs: round(statistics.median(xs), 3) if xs else None

sonic = atlas("sonic/sonic.json")["sounds"]
pack = atlas("pack/pack.json")["segments"]
samples = atlas("samples.json")
lines = atlas("codex/lines.json")["poems"]
worlds = atlas("poemworlds.json")["worlds"]
census = json.load(open(os.path.join(LAB, "cache", "sound-census.json")))["clips"] if os.path.exists(os.path.join(LAB, "cache", "sound-census.json")) else {}
corpus = json.load(open(os.path.join(LAB, "cache", "corpus.json")))
deamer = json.load(open(os.path.join(HERE, "deamer-sound.json")))
esound = {str(e["n"]): e.get("sound") for e in deamer["element_sound"]}

sung = [dict(l, num=p["num"]) for p in lines for l in p["lines"] if l.get("sung_clip") and l.get("voice")]
def reg(f0):
    return "ABYSSAL" if f0 < 77 else "DEEP" if f0 < 110 else "LOW" if f0 < 140 else "HIGH"

def ex_sonic(rows, n=8, label=lambda s: s.get("label") or s["id"]):
    rows = [s for s in rows if s.get("file")]
    step = max(1, len(rows) // n)
    return [{"label": label(s), "file": url(s["file"]), "dur": s.get("dur"), "meta": " · ".join(str(x) for x in (s.get("eco"), s.get("key") or None, f"{s['bpm']:.0f} bpm" if s.get("bpm") else None) if x)} for s in rows[::step][:n]]

def stats(rows, keys=("dur", "cent", "flat", "loud")):
    out = {"count": len(rows)}
    for k in keys:
        v = [float(r[k]) for r in rows if isinstance(r.get(k), (int, float)) and r.get(k) not in (0, -1) and abs(r[k]) < 1e5]
        if v: out[k] = med(v)
    return out

def pk(cls): return [s for s in pack if s.get("cls") == cls]
def pk_ex(cls, n=8):
    rows = pk(cls); step = max(1, len(rows) // n)
    return [{"label": s["name"], "file": url(s["file"]), "dur": round(s["e"] - s["s"], 2), "meta": " · ".join(x for x in (s.get("key"), f"{s['bpm']:.0f} bpm" if s.get("bpm") else None) if x)} for s in rows[::step][:n]]
def pk_stats(cls):
    rows = pk(cls)
    return {"count": len(rows), "dur": med([s["e"] - s["s"] for s in rows]), "cent": med([s["cent"] for s in rows if s.get("cent")]),
            "flat": med([s["flat"] for s in rows if s.get("flat") is not None]), "loud": med([s["loud"] for s in rows if s.get("loud") is not None and abs(s["loud"]) < 100])}

def found(kind, n=8, also=()):
    rows = [(i, c) for i, c in census.items() if c.get("kind") == kind or c.get("kind") in also]
    rows.sort(key=lambda x: (x[1].get("kind") != kind, -(x[1].get("p", {}).get(kind) or 0)))
    ex = []
    for i, c in rows[:n]:
        k = corpus.get(i) or {}
        ex.append({"label": k.get("sourceTitle") or i[:8], "file": k.get("videoUrl"), "thumb": k.get("thumbnailUrl"), "dur": c.get("dur"), "shot": i,
                   "meta": " · ".join(x for x in (f"{c['lufs']:.0f} LUFS" if isinstance(c.get("lufs"), (int, float)) else None,
                                                  (f"{c['music']['key']} {c['music'].get('mode', '')}".strip() if c.get("music") else None),
                                                  f"{c['music']['tempo']:.0f} bpm" if (c.get("music") or {}).get("tempo") else None) if x)})
    st = {"count": len(rows)}
    for k in ("dur", "lufs", "centroid"):
        v = [c[k] for _, c in rows if isinstance(c.get(k), (int, float))]
        if v: st[k] = med(v)
    return ex, st

# ---------------------------------------------------------------- the columns
V, M, F, S = "voice", "music", "field", "signal"
cols = []
def col(sym, name, fam, what, law, prio, examples, st, links=(), row=None):
    cols.append({"sym": sym, "name": name, "family": fam, "what": what, "law": law, "priority": prio, "examples": examples, "stats": st,
                 "links": [{"n": n, "why": why, "deamer": esound.get(n)} for n, why in links], "rows": row or {}})

read_lines = [dict(l, num=t["num"]) for t in samples["tracks"] for l in t["lines"]]
col("Po", "Poet", V, "RY reading her own lines: the spring every other voice is measured from (poet_dist 1.0, f0 111 Hz).",
    "Owns the front. Never cut, never ducked, never covered: everything else yields to her.", 1,
    [{"label": l["text"][:60], "file": url(l["file"]), "dur": round(l["e"] - l["s"], 2), "meta": f"poem {l['num']}"} for l in read_lines[::34][:8]],
    {"count": len(read_lines), "dur": med([l["e"] - l["s"] for l in read_lines]), "f0": 111.1, "poet_dist": 1.0},
    [("44", "a voice from outside the image makes the image something to read"), ("34b", "a pure sound the image no longer answers")],
    {"IN": "Her mouth seen saying it: the sound locks to a face; synchresis.",
     "OFF": "Her voice from the next room of the scene: she is somewhere, unseen.",
     "OUT": "Voice-over: she reads over the world, and the world is read."})
vox = [s for s in sonic if s.get("cls") == "VOX"]
col("Wh", "Whisper", V, "The poet's voice in fragments: 439 power-phrase chops and breaths, her words as material.",
    "Only in her silences (≥ 3.5 s gap), 18 s apart; never over a word of hers.", 2, ex_sonic(vox), stats(vox),
    [("1", "breath and voiced thought inside one body")],
    {"IN": "A whisper matched to a moving mouth: someone in frame speaks with her voice.",
     "OFF": "Her words half-heard behind the scene, as if remembered in the room.",
     "OUT": "Her voice as texture over everything: interior, inside the head."})
kin = [l for l in sung if l["voice"]["poet_dist"] < 7.5]
far = [l for l in sung if l["voice"]["poet_dist"] >= 7.5 and l.get("kind") != "combined"]
cho = [l for l in sung if l.get("kind") == "combined"]
def sung_ex(rows, n=8):
    step = max(1, len(rows) // n)
    return [{"label": l["text"][:60], "file": url(l["sung_clip"]), "dur": l.get("sung_dur"), "meta": f"{reg(l['voice']['f0'])} · {l['voice']['f0']:.0f} Hz · dist {l['voice']['poet_dist']:.1f} · {l.get('kind')}"} for l in rows[::step][:n]]
def sung_st(rows):
    return {"count": len(rows), "dur": med([l["sung_dur"] for l in rows if l.get("sung_dur")]), "f0": med([l["voice"]["f0"] for l in rows]),
            "poet_dist": med([l["voice"]["poet_dist"] for l in rows]), "registers": {r: sum(1 for l in rows if reg(l["voice"]["f0"]) == r) for r in ("ABYSSAL", "DEEP", "LOW", "HIGH")}}
col("Kn", "Kin", V, "Mouths nearest the poet (poet_dist < 7.5): narration kin singing her lines.",
    "Waits for her line to end and ≥ 2 s of quiet; then answers. Drops to 0.12 if she returns.", 3, sung_ex(kin), sung_st(kin),
    [("16", "a voice repeats another: the relation between two")],
    {"IN": "A second speaker seen answering her: dialogue.", "OFF": "An answer from beyond the frame: the scene has another person in it.",
     "OUT": "A second narrator: the text is told twice."})
col("Mo", "Mouth", V, "Other singers carrying her lines, further from the poet (dist ≥ 7.5), by register ABYSSAL / DEEP / LOW / HIGH.",
    "Same law as Kin, one step lower: never two mouths at once.", 4, sung_ex(far), sung_st(far),
    [("43", "the same words in other mouths: a story told by others")],
    {"IN": "A singer in shot mouthing her words: the musical, the number.", "OFF": "Singing from somewhere in the world of the shot.",
     "OUT": "Her poem sung over the film: the song as commentary."})
col("Co", "Chorus", V, "Many mouths at once: combined codex lines, the crowd singing the poem.",
    "Only in gaps and endings; the codas. A chorus under her is a collision.", 5, sung_ex(cho), sung_st(cho),
    [("3", "the voice dispersed, no centre of hearing")],
    {"IN": "A crowd seen singing: the collective in frame.", "OFF": "A crowd heard beyond the frame: the world is populated.",
     "OUT": "A chorus over the image: the people who are missing, speaking."})
fv_ex, fv_st = found("speech", also=("mixed",)); fv_st["speech_only"] = sum(1 for c in census.values() if c.get("kind") == "speech"); fv_st["with_music"] = sum(1 for c in census.values() if c.get("kind") == "mixed")
col("Fv", "Found voice", V, "Strangers speaking in the archive footage: narrators, instructors, voices of the films themselves.",
    "An archive voice never speaks over hers: under her words it drops to 0.12; alone it may lead.", 6, fv_ex, fv_st,
    [("28", "the educational/industrial narrator as the voice of the world's rules")],
    {"IN": "The film's own speaker, lips in sync: the found film talking.", "OFF": "The found film's narrator unseen: its world explains itself.",
     "OUT": "An archive voice cut loose from its picture: found speech as quotation."})
songs = [s for s in sonic if s.get("eco") == "song"]
col("Sg", "Song", M, "Sections of the 34 carrier songs (744 segments, 19 families): the poem's own music.",
    "One music at a time. Under her voice: mid-band carved (−7 dB at 1.4 kHz), bus to 10%.", 7, ex_sonic(songs), stats(songs, ("dur",)),
    [("2", "music covering every zone while voices hand the centre around")],
    {"IN": "A band or radio seen playing it: source music.", "OFF": "Music from a room nearby: the world has a party in it.",
     "OUT": "Score: the song over the image."})
col("Lp", "Loop", M, "Rhythm: 60 mined loops on a bar grid (median 2.56 s, flatness 0.008 — the most tonal thing in the atlas).",
    "Enters on a bar; matches tempo by playback rate; yields to any voice by carving, not stopping.", 8, pk_ex("LOOP"), pk_stats("LOOP"),
    [("15", "repetition that organises action")],
    {"IN": "A machine seen repeating: the loop is its sound.", "OFF": "A pulse from outside the frame: the world keeps time.",
     "OUT": "A beat under the film: the cut is paced by it."})
chairs = [dict(o, num=w["num"]) for w in worlds for o in w.get("orchestra", [])]
col("St", "Stem", M, "Orchestra chairs: single instruments from the songs (drums, piano, synth, vocals, bass, strings).",
    "A chair in the poem's key (root or fifth) may stay under her; other keys wait for the gap.", 9,
    [{"label": f"{o['instrument']} · {o['song']}", "file": url(o["file"]), "meta": f"{o.get('key', '')} · {o.get('tempo', 0):.0f} bpm"} for o in chairs[::max(1, len(chairs) // 8)][:8]],
    {"count": len(chairs), "instruments": {i: sum(1 for o in chairs if o["instrument"] == i) for i in sorted({o["instrument"] for o in chairs})}},
    [("6", "one instrument as a face: an affect held")],
    {"IN": "The instrument seen being played.", "OFF": "A practice through the wall.", "OUT": "Accompaniment: the chair as commentary."})
fm_ex, fm_st = found("music")
col("Fm", "Found music", M, "Music inside the archive footage: scores, radios, bands of the found films.",
    "One music at a time: two musics crossfade on a beat, or the later one sinks to texture (lowpass, −12 dB).", 10, fm_ex, fm_st,
    [("11", "the film's own score telling you what to feel")],
    {"IN": "The found film's band, seen.", "OFF": "The found film's radio, heard.", "OUT": "The found film's score lifted onto another picture."})
drone = [s for s in sonic if s.get("eco") == "keynote" and "drone" in (s.get("label") or "").lower()]
col("Dr", "Drone", F, "The unified drone: the corpus clock itself (1,440.1 s), and drone keynotes.",
    "Never leaves. Under her 0.045, in breaths 0.09, after her 0.13 (the water table's key-bed).", 11,
    [{"label": "unified drones (the clock)", "file": url("drone/unified-drones-lite.mp3"), "dur": 1440.1, "meta": "keynote · the master axis"}] + ex_sonic(drone, 7), stats(drone),
    [("34b", "a pure sound that no longer extends into action")],
    {"IN": "A hum whose source is seen: a machine, a fridge, a turbine.", "OFF": "The hum of a place: the room tone of the world.",
     "OUT": "The floor under the whole film: time itself sounding."})
col("Bd", "Bed", F, "Beds: 40 sustained segments (median 8 s, flatness 0.10).",
    "Keynote: ducks under every voice (1 − 0.9·amt, 30 ms down, 160 ms up).", 12, pk_ex("BED"), pk_stats("BED"), [],
    {"IN": "Ambience with its source in view: the sea in the shot of the sea.", "OFF": "The weather of the scene, unseen.", "OUT": "A pad under the film: mood as floor."})
col("Tx", "Texture", F, "Textures: 30 noisy segments (flatness 0.74, centroid 3.5 kHz — the noisiest element).",
    "Lowest priority of the field: first to go when two things fight.", 13, pk_ex("TEXTURE"), pk_stats("TEXTURE"),
    [("5", "matter as grain: sound particles without a figure")],
    {"IN": "Grain with a visible cause: rain on glass.", "OFF": "Static, wind, crowd murmur: the world as noise.", "OUT": "Hiss, tape, surface noise: the medium sounding."})
fn_ex, fn_st = found("noise")
col("Fn", "Found noise", F, "Noise and effects in the archive footage: machines, traffic, rooms, weather.",
    "Normalised to −24 LUFS; ducks under voices; removing it shrinks the off-screen space (Deamer p.168).", 14, fn_ex, fn_st,
    [("34b", "remove the effects and the space off-screen closes (p.168)")],
    {"IN": "The found film's effects, in sync: synchresis, the fourth dimension of the image.", "OFF": "The found film's world heard beyond its frame.",
     "OUT": "Effects laid on a picture that did not make them: the lock exposed."})
col("Rs", "Riser", S, "Risers: 20 rising segments (median 4 s).",
    "Aims at a cut: ends on the next cut or breath; never rises into her word.", 15, pk_ex("RISER"), pk_stats("RISER"),
    [("20", "tension that demands the next image")],
    {"IN": "A visible thing gathering: engine spinning up.", "OFF": "Something approaching, unseen.", "OUT": "Tension laid over the cut: the edit announced."})
col("Ht", "Hit", S, "Hits: 60 impacts (median 1.16 s, centroid 2 kHz).",
    "Snaps to the next silence ≥ 1 s within 3 s; at least 7 s apart; never on a word.", 16, pk_ex("HIT"), pk_stats("HIT"),
    [("17", "a sound as the index of an event")],
    {"IN": "An impact seen and heard at once: the index.", "OFF": "A bang off-screen: an event the frame did not catch.", "OUT": "A stinger on the cut: the edit hits."})
si_n = sum(1 for c in census.values() if c.get("kind") in ("silence", "none"))
col("Si", "Silence", "ground", "The gap: her 606 breaths and pauses, and the archive's silent shots. The zero of the table.",
    "Silence is placed, not left: the one element nothing may enter unless the law allows it.", 0, [],
    {"count": si_n, "breaths": 606, "breath_cuts": 176},
    [("34b", "Five: talk drowned by waves, then near-silence building (pp.302–304)")],
    {"IN": "A silent shot: the picture without its sound.", "OFF": "The world holds its breath.", "OUT": "The film stops speaking: the time-image's zero."})

ROWS = [{"id": "IN", "name": "In", "gloss": "the source is on screen", "deamer": "Chion's on-screen sound, via Deamer p.167"},
        {"id": "OFF", "name": "Off", "gloss": "of the world, source unseen", "deamer": "Chion's off-screen (acousmatic) sound, p.167; removing effects shrinks it, p.168"},
        {"id": "OUT", "name": "Out", "gloss": "outside the film-world", "deamer": "Chion's nondiegetic sound (score, voice-over), p.167"}]
LAWS = [
    ("One clock", "Everything sits on the 24:00 suite clock; nothing is re-timed by the mix."),
    ("Her voice untouched", "The poet is never cut, ducked or covered."),
    ("One speaker", "Voices never overlap: a lower voice waits for her line to end and ≥ 2 s of quiet, or it is held."),
    ("One music", "Two musics never play at the front together: the later crossfades in on a beat or sinks to texture."),
    ("Carve, don't bury", "Under a voice, music and field lose the mid band (−7 dB at 1.4 kHz, Q 0.7) and drop to 10%, 30 ms down, 160 ms up."),
    ("Snap to breath", "Hits and risers land in silences ≥ 1 s, at least 7 s apart."),
    ("Level", "Archive sound is normalised toward −24 LUFS; nothing jumps."),
    ("Silence is placed", "A gap is an element: leave it empty on purpose."),
]
MOVES = [  # Chion's disruptions via Deamer p.168: what pushes a mix from the movement-image to the time-image
    ("Drop the score", "remove the music: the image loses its instructions"),
    ("Drop the effects", "remove the noise: the off-screen space closes"),
    ("Unnatural voice", "theatrical, text-heavy, swamped or unsubtitled speech: the voice stops belonging to a body"),
    ("Expose the lock", "put a sound IN against a picture that did not make it: synchresis shown as a contract"),
]
out = {"title": "Periodic table of sound", "version": 1, "rows": ROWS, "columns": cols, "laws": [{"name": a, "rule": b} for a, b in LAWS],
       "moves": [{"name": a, "does": b, "page": "168"} for a, b in MOVES], "atlas": ATLAS,
       "sources": {"atlas": "WYGWYL · ATLAS (sonic.json, pack.json, codex/lines.json, samples.json, poemworlds.json)", "clips": f"lab/cache/sound-census.json ({len(census)} clips)",
                   "deamer": "sound/deamer-sound.json (Deamer pp.41–45, 138–145, 164–171, 302–304; Chion via Deamer pp.167–168)"},
       "caveat": "Rows are Deamer's (after Chion). Column order and cell readings are the editor's inference from the atlas's measurements; the picture-sign links are pointers, with Deamer's own sound note where he has one."}
json.dump(out, open(os.path.join(LAB, "sound-table.json"), "w"), ensure_ascii=False, indent=1)
print(len(cols), "columns ·", {c["sym"]: c["stats"].get("count") for c in cols})

# the per-clip sound the desk needs in CUT: kind, loudness, tempo, key, speech spans (compact)
kinds = {}
for i, c in census.items():
    k = c.get("kind")
    if not k: continue
    m = c.get("music") or {}; spans = c.get("speech_spans")
    kinds[i] = [k, round(c["lufs"], 1) if isinstance(c.get("lufs"), (int, float)) else None, round(m["tempo"]) if m.get("tempo") else None,
                (f"{m['key']} {m.get('mode', '')}".strip() if m.get("key") else None), [[round(a, 2), round(b, 2)] for a, b in (spans or [])[:12]]]
json.dump({"fields": ["kind", "lufs", "bpm", "key", "speech"], "clips": kinds}, open(os.path.join(LAB, "tools", "sound-kinds.json"), "w"), separators=(",", ":"))
print("sound-kinds:", len(kinds))
