"""The words Whisper hears in each song (with times), as evidence for voice.py: where a word is heard, the song is not word-free.
usage: ~/.cache/mlxw-venv/bin/python slopfeeder/songwords.py   -> slopfeeder/songwords.json"""
import json, os, mlx_whisper
D = os.path.dirname(os.path.abspath(__file__)); ALB = os.path.expanduser("~/moto/THE LITURGY OF THE TWO BUTTONS"); out = {}
for s in json.load(open(os.path.join(D, "songs.json")))["songs"]:
    r = mlx_whisper.transcribe(os.path.join(ALB, s["file"]), path_or_hf_repo="mlx-community/whisper-base.en-mlx", word_timestamps=True, condition_on_previous_text=False)
    out[s["n"]] = [[round(w["start"], 2), round(w["end"], 2), w["word"].strip()] for g in r["segments"] for w in g.get("words", []) if w.get("probability", 1) > .3]
    print(s["n"], len(out[s["n"]]), "words", flush=True)
json.dump(out, open(os.path.join(D, "songwords.json"), "w"), ensure_ascii=False)
