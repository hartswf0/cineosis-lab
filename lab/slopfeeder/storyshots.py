"""THE STORY SHOTS: what the archive cannot carry. For every film six shots that tell its story with its protagonist in frame (cold open,
setup, inciting, turn, climax, end), plus the two shots that open and close the megafilm. Each: a complete generation prompt (the bible's
LOCK text for whoever is in it, the action, the camera, the duration, the negatives) and three reference stills from our own footage, chosen
by CLIP, so the generation keeps the cook, the crew, the four and the pails consistent. Writes storyshots.json (slopfeeder-storyshots.html).
usage: .venv/bin/python slopfeeder/storyshots.py"""
import json, os
import numpy as np, torch, open_clip
D = os.path.dirname(os.path.abspath(__file__))
B = json.load(open(os.path.join(D, "bible.json"))); LOCK, NEG = B["locks"], B["neg"]
CB = json.load(open(os.path.join(D, "cutbastard.json")))["songs"]
# (beat, who: keys into LOCK, action, camera, seconds)
SHOTS = {
 "MEGA": [("OPEN", ["cook", "four"], "the developer sits at a dark terminal in a bunker on the beach; on the screen the login page with the four flat characters; he turns from the screen and stares straight into the lens, not moving, breathing in his headset", "locked close-up at eye height, slow push-in over the whole shot, the screen's light on the mask", 10),
          ("CLOSE", ["cook", "four", "world"], "the same terminal at night; on the screen the beach from the films, the crew small and still; the developer reaches out and presses one key; the four flat characters on the screen look up at him", "over-the-shoulder, then a cut-free drift round to his masked face", 10)],
 "26": [("COLD OPEN", ["cook", "pails"], "extreme close-up: steam rolls off the cook's skull mask; he lifts one orange pail and slams it mouth-down into the wet sand; a thud; sand jumps", "macro then a hard tilt down to the pail, handheld, eye-level", 6),
        ("SETUP", ["crew", "pails", "world"], "dawn: a long line of mud-covered workers rises out of the wet sand like clay figures, each beside an upturned pail; the cook walks the line inspecting them", "slow lateral tracking shot at sand level", 10),
        ("INCITING", ["cook", "crew", "pails"], "the cook raises his spatula like a baton; the first worker drives the pail-drill into the sand; sparks; fire breaks out on the horizon", "low angle from the sand, the cook above frame-left", 8),
        ("TURN", ["crew", "world"], "workers drag ledgers and paper records out of the brick fort and throw them on a fire; ropes pull down a section of the fort's wall", "witness drone drifting low behind them, smoke crossing the lens", 10),
        ("CLIMAX", ["crew", "pails", "world"], "the whole crew crosses the tidal channel toward the fire, hundreds of figures; the frame keeps widening", "extreme wide, slow pull-back and rise", 10),
        ("END", ["cook", "crew"], "the cook hands a worker a cooled iron bar on the griddle like a burger; the worker looks at it, then bites; behind them the tide washes over circles in the sand", "close two-shot, then hold on the worker's face", 8)],
 "14": [("COLD OPEN", ["four", "world"], "the four flat characters rise out of the sea on the horizon at dawn, enormous, still flat, their eyes turning toward the beach", "locked extreme wide from the sand, very slow", 8),
        ("SETUP", ["crew", "pails", "four"], "the crew at their drills look up; a giant white cursor descends from the sky and clicks; a flat white change-request rectangle appears over the sea", "low angle behind the crew, the sky filling the frame", 8),
        ("INCITING", ["crew", "pails", "world"], "the crew pump their drills in unison; with every stroke the fort behind them changes a little, as if re-rendered", "locked medium wide, the fort centred", 10),
        ("TURN", ["world"], "the sky turns flat featureless white; every figure stops mid-motion; nothing moves except the sea", "static wide", 6),
        ("CLIMAX", ["crew", "four"], "the crew and a row of identical machine arms move in the same rhythm, figure and machine matching stroke for stroke", "side-on tracking along the line", 10),
        ("END", ["pails", "world"], "the sea empty, the four gone; a single orange pail floats mouth-down in the surf", "locked wide at the waterline", 8)],
 "13": [("COLD OPEN", ["cook"], "macro: grease hits the hot white-blue-red griddle; onions sizzle; steam", "macro, shallow focus", 5),
        ("SETUP", ["cook", "crew"], "the cook stands in the surf with the griddle on his forearm; a long line of crew waits with tin plates", "wide from the sea looking up the beach", 10),
        ("INCITING", ["cook"], "the cook stops with the spatula raised and does not move, staring; the crew holds its breath", "locked medium close-up", 6),
        ("TURN", ["cook", "crew"], "he serves: burgers passed hand to hand down the whole line", "tracking along the hands", 10),
        ("CLIMAX", ["crew"], "the whole crew eats in silence, close on mouths and hands", "a slow pan across faces at eye level", 10),
        ("END", ["crew"], "one recruit swallows and looks straight into the lens", "locked close-up", 6)],
 "23": [("COLD OPEN", ["world"], "clay figures stand inside a ring of fire at night, unmoving", "locked wide, low", 6),
        ("SETUP", ["crew", "world"], "figures rise out of the mire, mud running off them, one after another", "low angle at mud level", 10),
        ("INCITING", ["crew"], "they walk in a line through the fire and come out the other side", "side-on tracking through smoke", 8),
        ("TURN", ["crew", "world"], "they tear a wire-mesh fence apart with their hands; beyond it a wall falls", "medium, handheld, the mesh in the foreground", 8),
        ("CLIMAX", ["crew"], "they circle the fire stamping in rhythm (a chorus), then break into ranks and cross the channel (an army)", "overhead drift, then a wide from the far bank", 10),
        ("END", ["world"], "a cooled iron bar lies on the sand in a circle of ash; the tide comes in", "locked close-up then hold", 8)],
 "20": [("COLD OPEN", ["cook"], "the cook flips a burger on the griddle; behind him a drill rig pounds the sand on every beat", "medium, the rig soft in the background", 6),
        ("SETUP", ["cook", "crew"], "the cook ladles thick slop into spoons held out by the crew", "close on the spoons, the cook above", 8),
        ("INCITING", ["crew", "pails"], "the crew drill down through shale until a pipe appears in the hole", "top-down into the hole", 8),
        ("TURN", ["cook", "crew"], "the cook raises a hand to stop the rig; it keeps pounding; nobody stops it", "locked wide, the rig centred", 8),
        ("CLIMAX", ["cook", "crew"], "in one shot: drilling, eating and feeding the fire with burgers and paper, all at once", "slow push through the scene", 10),
        ("END", ["cook"], "the cook alone at a green terminal in the bunker types a confession; the text glows on his mask", "over the shoulder to the screen, then his face", 10)],
 "09": [("COLD OPEN", ["crew"], "darkness; a line of people breathing in unison; a mouth lowered to wet mud", "macro in near-darkness", 6),
        ("SETUP", ["crew", "cook"], "in a brick vault the crew name their makers: coal glowing red, slop in a pot, a large iron-gloved hand covering a tiny pail", "slow pan across the three objects", 10),
        ("INCITING", ["world"], "the sky over the beach turns blank white", "static wide", 6),
        ("TURN", ["cook"], "the cook's hand presses a switch; everything goes black", "insert, then black", 4),
        ("CLIMAX", ["crew", "pails"], "the crew stands again in exactly the positions of the opening, but changed: the orange shoulder panels lit", "the opening's framing repeated", 10),
        ("END", ["cook"], "the cook rests the spatula on the griddle; the opening shot returns with one difference", "locked medium", 8)],
 "06": [("COLD OPEN", ["crew"], "dawn over a muddy river; a line of bare feet steps into the water", "low, at the waterline", 6),
        ("SETUP", ["crew"], "workers carry heavy loads at dusk, hands raw, still walking together", "lateral tracking at shoulder height", 10),
        ("INCITING", ["crew"], "a chain falls from a worker's ankle into the mud and lies there", "macro on the mud", 6),
        ("TURN", ["world"], "a heavy stone is rolled from a doorway; morning light floods in", "locked from inside, facing the door", 8),
        ("CLIMAX", ["crew"], "the whole crew wades the muddy water together, arms linked, toward open ground", "wide from the far bank, slow", 10),
        ("END", ["crew"], "a hammer lies dropped in the mud; a worker stands up straight in morning light", "close, then tilt up to the face", 8)],
 "07": [("COLD OPEN", ["world"], "a projector beam through fog on the beach; old film flickers on the mist", "locked wide", 6),
        ("SETUP", ["crew"], "a lone hooded figure walks past the company; they turn away from him", "medium tracking", 8),
        ("INCITING", ["crew"], "he walks through fire to a forge; molten iron is poured", "low, through flames", 8),
        ("TURN", ["world"], "the tide washes over old photographs laid on the sand, washing them blank", "top-down, slow", 10),
        ("CLIMAX", ["crew"], "the company breaks a gate and walks through as one, the outcast among them", "wide, slow push", 10),
        ("END", ["crew"], "he drinks from a cooled pail; the frame fades to white", "close-up, hold", 8)]}
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
A = json.load(open(os.path.join(D, "atlas.json"))); C = A["cards"]
E = np.fromfile(os.path.join(D, "atlas-emb.bin"), np.int8).reshape(-1, 512).astype(np.float32); E /= np.linalg.norm(E, axis=1, keepdims=True)
ai = np.array([c["type"] == "ai" for c in C]); pois = np.array([c.get("poison", 0) or 0 for c in C]); fam = [c.get("twin") or c["id"] for c in C]
def refs(text):
    with torch.no_grad(): t = m.encode_text(tok([text[:300]])).float(); t = (t / t.norm(dim=-1, keepdim=True)).numpy()[0]
    s = np.where(ai & (pois < .5), E @ t, -9); out, seen = [], set()
    for i in np.argsort(-s):
        if fam[i] in seen: continue
        seen.add(fam[i]); out.append({"id": C[i]["id"], "title": C[i]["title"], "thumb": C[i]["thumb"]})
        if len(out) == 3: break
    return out
out = {}
for key, shots in SHOTS.items():
    st = CB[key]["story"] if key in CB else {"title": "The Slopfeeder (megafilm)", "logline": "What has this developer been up to?"}
    lst = []
    for k, (beat, who, act, cam, sec) in enumerate(shots):
        lock = " ".join(LOCK[w] for w in dict.fromkeys(who + ["world"]) if w in LOCK)
        prompt = f"{act[0].upper() + act[1:]}. {lock} Camera: {cam}. One continuous {sec}-second shot, natural light, film grain, no music, diegetic sound only. Avoid: {'; '.join(NEG)}."
        lst.append({"id": f"{key}-S{k + 1}", "beat": beat, "who": who, "action": act, "camera": cam, "seconds": sec, "prompt": prompt, "refs": refs(act)})
    out[key] = {"title": st["title"], "logline": st["logline"], "shots": lst}
json.dump({"films": out}, open(os.path.join(D, "storyshots.json"), "w"), ensure_ascii=False, indent=1)
print(sum(len(v["shots"]) for v in out.values()), "story shots with prompts and references")
