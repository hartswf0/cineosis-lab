# Cutting a Republic episode (the pilot's grammar)

The model: `republic/pilot/ep01.json`. Read it first. Each cut is a JSON file `republic/pilot/epNN.json`.

## Fields
- `id`: the episode id.
- `title`: the scene title.
- `kicker`: "THE REPUBLIC · EPISODE N" (the number in words: ONE, TWO…).
- `stage`: `{"left": NAME, "right": NAME, "back": NAME (optional), "ground": "republic/planes/<id>/p0a", "places": 2}`.
  - At most three figures on stage. Put the two main speakers left and right.
  - Only characters that HAVE a figure can be on stage.
- `about`: one sentence on the cut.
- `beats`: the list below.

## Beat kinds
- `{"k":"title","mood":...}` opens the cut.
- `{"k":"end","mood":...}` closes it.
- `{"k":"narr","text":...,"see":[...],"mood":...}` is the narrator.
  - Plain, concrete, 1–2 sentences, at most 35 words.
  - It says where we are, what is at stake, and what just changed. It bridges what the dialogue leaves out.
  - It never contradicts the scene, never jokes over a line, and never names a real person or celebrity.
  - `see`: 1–3 things the pictures should show. Use concrete nouns that mid-century documentary footage would contain ("an oil refinery at night", "a crowd at a rodeo"). Never use abstractions. A see item may also be `{"place":"p1a"}` to use one of the episode's own place clips (p0/p1/p2, alternative a or b).
  - The narration must describe what the pictures show, or the pictures must show what it names: what we see and what we hear must match.
- `{"k":"intro","who":NAME}` comes immediately before a stage character's FIRST line. The film then shows that figure in its original archive clip and lifts it out onto the stage. Use exactly one per stage character.
- `{"k":"talk","who":NAME,"text":...}` is a character line.
  - Taken VERBATIM from the scene. You may trim inside a line, or join two consecutive lines by the same speaker, but you must never invent words.
  - Remove stage directions and parentheticals.
- `{"k":"chorus","ask":...,"who":"A CITIZEN"}` is a real archive person reacting at a turning point.
  - `ask` is a short plain sentence that an ordinary person in an old documentary or interview might actually say, and which lands on the moment.
  - Use 2–3 per cut, never two in a row.

## Shape
- About 2.5–3.5 minutes. That is roughly 14–22 talk lines, 4–7 narr beats and 2–3 chorus beats.
- Cut along the scene's natural joints: setup, the question, the turn, the consequence, the ending.
- The cut MUST include the scene's turn and its ending, not just its opening. Read the WHOLE scene before choosing.
- Do not crowd: one thing at a time. Let narration carry what would need too many lines.
- Do not chop through a continuous exchange. If an exchange carries pressure, keep it whole.

## Rules
- Character names exactly as given in the roster (the world.json cast keys).
- Characters without a figure may speak a few lines, but get no intro and no stage slot.
- `mood` uses words from this list: wonder and awe, quiet calm, tension and suspense, dread, sorrow, triumph, playful and comic, driving rhythm, dreamy ambient, melancholy guitar, lonely desert, a warm return home, something breaking apart, a journey in motion, ritual and ceremony, country western.
- No emoji.
- Validate with `python3 -c "import json;json.load(open(PATH))"`, then print a summary: beat counts, and estimated seconds (words / 2.6 + 4 per intro + 4 per chorus + 8).
