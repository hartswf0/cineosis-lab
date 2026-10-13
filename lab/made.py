"""How a shot is made: the lab's pipeline as stages, each with the tool it runs, the file it writes, the day it last ran
and how many of the 15,149 shots went through it. made.js draws this as an operative flow diagram for one shot.
Writes lab/made.json.   usage: python3 lab/made.py"""
import json, os, glob, time
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(H); J = lambda p: json.load(open(p))
shots = J(os.path.join(H, "lab-data.json"))["shots"]; ids = {s["id"] for s in shots}
def day(*paths):
    t = [os.path.getmtime(p) for q in paths for p in glob.glob(q)]
    return time.strftime("%Y-%m-%d", time.localtime(max(t))) if t else None
def n_in(path, key=None):
    try: d = J(path)
    except Exception: return None
    d = d[key] if key else d
    return sum(1 for k in d if k in ids)
cap = os.path.join(H, "rushes/captions.json"); snd = os.path.join(H, "sound-layer.json")
S = [  # id, band, column, verb, what it does (an instruction you could repeat), tool, files, count
 ("film", "film", "pic", "TAKE", "take a source film from the archive, with who paid for it and why", "movingimagearchive.com · archive.org metadata", [os.path.join(H, "research/purpose.json")], len({s["slug"] for s in shots})),
 ("cut", "film", "pic", "CUT", "cut the film into shots where the picture changes", "the archive's own shot pass (named in each clip's path)", [os.path.join(H, "cache/corpus.json")], len(shots)),
 ("ask", "sign", "word", "ASK", "write each of the 45 signs as one question and a test that tells it from its neighbours", "Deamer's table · grounding/g*.json, diff*.json", [os.path.join(ROOT, "grounding/*.json")], 45),
 ("search", "sign", "word", "SEARCH", "turn each question into scene phrases and run them on the archive's shot search", "search.py · archive shot search", [os.path.join(ROOT, "results/*.json")], sum(1 for s in shots if s.get("found"))),
 ("frame", "shot", "pic", "FRAME", "take the archive's thumbnail: the one frame every machine looks at", "the archive", [os.path.join(H, "thumbs")], len(shots)),
 ("embed", "shot", "pic", "EMBED · PLACE", "turn the frame into 512 numbers, then lay every shot out so close numbers sit close: the picture map", "CLIP ViT-B-32 (laion2b) + t-SNE · analyze.py", [os.path.join(H, "cache/emb.npy")], sum(1 for s in shots if s.get("xy"))),
 ("name", "shot", "pic", "NAME", "score the frame against 20 subjects and 5 shot scales", "CLIP zero-shot · analyze.py", [os.path.join(H, "cache/analysis.json")], sum(1 for s in shots if s.get("subjects"))),
 ("describe", "shot", "word", "DESCRIBE", "write one plain sentence of what the frame shows", "BLIP-large · rushes/caption.py", [cap], n_in(cap)),
 ("measure", "shot", "snd", "MEASURE", "measure loudness and whether it is speech, music or silence", "signal features · sound_census.py", [os.path.join(H, "cache/sound-census.json"), os.path.join(H, "cache/audio.json")], sum(1 for s in shots if s.get("audio"))),
 ("listen", "shot", "snd", "LISTEN · PLACE", "turn the sound into numbers, name it from 30 everyday sounds, and lay the heard shots out by sound: the sound map", "CLAP htsat-unfused + UMAP · sound-layer.py", [snd], n_in(snd, "heard") if os.path.exists(snd) else None),
 ("point", "shot", "word", "POINT", "compare the frame with each sign's words and read examples; keep the 3 closest as places to look", "CLIP · affinity.py", [os.path.join(H, "cache/affinity.json")], sum(1 for s in shots if s.get("aff_top"))),
 ("transcribe", "word", "snd", "TRANSCRIBE", "write down every word spoken, with the second it is said", "faster-whisper base.en", [os.path.join(H, "odyssey/cache/ears/words*.json")], n_in(os.path.join(H, "transcripts.json"))),
 ("vet", "read", "pic", "VET", "lay a sign's search results on a contact sheet; keep the shots that answer its question", "candidates.py · contact.html · pick.py", [os.path.join(ROOT, "picks.json")], sum(len(v) for v in J(os.path.join(ROOT, "picks.json")).values())),
 ("read", "read", "word", "READ", "write one sentence naming the sign and what in the frame answers its question", "the editor", [os.path.join(ROOT, "picks.json")], sum(1 for s in shots if s.get("signs"))),
 ("rate", "read", "word", "RATE", "score the reading: how sure in context, how sure from the shot alone, which rival sign, what would flip it", "the editor · cineosis-table.json", [os.path.join(ROOT, "cineosis-table.json")], sum(1 for s in shots if s.get("signs") and s["signs"][0].get("conf") is not None)),
 ("locate", "read", "pic", "LOCATE", "find the second in the clip where the read frame sits", "locate_thumb.py", [os.path.join(H, "cache/read_t.json")], sum(1 for s in shots if s.get("read_t") is not None)),
 ("segment", "frame", "pic", "SEGMENT", "cut out the figure the reading is about and follow it frame by frame", "SAM 2.1 + CLIP · seg_track.py", [os.path.join(H, "cache/segments.json")], sum(1 for s in shots if s.get("segments"))),
 ("use", "ours", "all", "USE", "place the shot in one of our films", "census/uses.json", [os.path.join(H, "census/uses.json")], n_in(os.path.join(H, "provenance.json"), "used")),
]

# the actual models, what they learned from, what they put down, and what they cannot see
MODEL = {
 "film": ("Moving Image Archive + archive.org", "a person: no model", "title, year, maker; who paid for the film and why", "only what the catalogue says"),
 "cut": ("the archive's own shot cutter", "not ours; its pass is named in each clip's path", "shot boundaries: where a shot starts and ends", "a dissolve or a slow pan can be cut wrong"),
 "frame": ("the archive's thumbnail", "no model", "one still frame per shot", "every machine downstream sees only this frame, not the motion"),
 "embed": ("OpenCLIP ViT-B/32 · laion2b_s34b_b79k, then t-SNE", "LAION-2B: about two billion web images and their alt-text", "512 numbers per frame; t-SNE turns them into a place on the picture map", "it knows what the web writes under pictures, not what a film means; far apart on the map means little"),
 "name": ("the same CLIP, zero-shot", "LAION-2B", "a score for each of 20 subject words and 5 shot scales", "it can only answer with the words it is given"),
 "describe": ("BLIP-large captioning (Salesforce)", "web image-text pairs, fine-tuned on COCO captions", "one plain sentence of what is visible", "names no people, places or dates; repeats the obvious noun"),
 "measure": ("signal features: loudness, spectrum, onsets", "no model", "speech / music / silence and decibels", "run only on clips the lab downloaded"),
 "listen": ("LAION CLAP · HTS-AT audio encoder (unfused), then UMAP", "LAION-Audio-630K and other audio-text sets", "512 numbers per sound, the two closest of 30 everyday sounds, and a place on the sound map", "old optical tracks and narration over music blur together"),
 "transcribe": ("faster-whisper base.en (OpenAI Whisper base, English)", "about 680,000 hours of web audio with transcripts", "every word spoken, with the second it is said", "mishears archival narration; never knows who is speaking"),
 "ask": ("Deamer's 45 signs, written by hand", "a person: no model", "one question per sign and a test that tells it from its neighbours", "the table is a reading of Deleuze, not Deleuze"),
 "point": ("CLIP again, against each sign", "LAION-2B plus the editor's read shots as examples", "a percentage for each of the 45 signs; the top 3 are places to look", "it is a pointer, not a reading: it matches looks, not functions"),
 "search": ("the archive's shot search", "its model is the archive's, not ours", "the shots it returns for a sign's scene phrases, ranked", "it finds what the words describe, and nothing the words leave out"),
 "vet": ("the editor, at a contact sheet", "a person", "keep or drop, one shot at a time", "only shots a search returned ever reach the sheet"),
 "read": ("the editor", "a person", "the sign and one sentence on what in the frame answers its question", "253 shots so far"),
 "rate": ("the editor", "a person", "how sure, in context and from the shot alone; the rival sign; what would flip it", "a score of the editor's own certainty"),
 "locate": ("OpenCV frame matching", "no model: 64x48 greyscale at 8 fps", "the second where the read frame sits in the clip", "only for read shots"),
 "segment": ("Meta SAM 2.1 (hiera small) + CLIP", "SA-1B / SA-V masks; CLIP picks the figure the reading names", "the figure cut out and followed frame by frame", "only for read shots; picks by the reading's words"),
 "use": ("our films", "the census of what each film uses", "where the shot goes: which film, which scene, what job", "only films in the census"),
}
BANDS = [("film", "once per source film"), ("sign", "once per sign · 45 times"), ("shot", "once per shot"), ("word", "once per spoken word"),
         ("read", "once per shot the editor reads"), ("frame", "every frame of a read shot"), ("ours", "once per use in our films")]
COLS = [("pic", "picture"), ("snd", "sound"), ("word", "words")]
out = {"total": len(shots), "bands": BANDS, "cols": COLS,
       "stages": [{"id": a, "band": b, "col": c, "verb": v, "does": d, "tool": t, "day": day(*f), "n": n, "model": MODEL[a][0], "trained": MODEL[a][1], "puts": MODEL[a][2], "blind": MODEL[a][3]} for a, b, c, v, d, t, f, n in S],
       "wires": [["film", "cut"], ["cut", "frame"], ["cut", "measure"], ["cut", "transcribe"], ["frame", "embed"], ["embed", "name"],
                 ["frame", "describe"], ["measure", "listen"], ["embed", "point"], ["ask", "point"], ["ask", "search"], ["search", "vet"],
                 ["vet", "read"], ["read", "rate"], ["read", "point"], ["read", "locate"], ["locate", "segment"], ["read", "use"], ["describe", "use"], ["transcribe", "use"]]}
json.dump(out, open(os.path.join(H, "made.json"), "w"), ensure_ascii=False, indent=0)
for s in out["stages"]: print(f"{s['verb']:11} {str(s['n']):>6}  {s['day']}  {s['tool']}")
