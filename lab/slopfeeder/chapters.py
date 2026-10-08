"""SLOPFEEDER, chapter by chapter: each VOLHOLLA song is a different bet on how Cineosis makes meaning (a montage method, a set of
signs from the 45-sign table), a different chapter of the world, and a shot list of what still has to be generated with AI video.
Every AI shot carries its riverbed (what must hold), its flow (what may vary), a point of view (the embedded body or the small hovering
witness), a blend (cartoon <-> archive <-> generation), a dense prompt, and reference images chosen by CLIP from the series' frames, the
existing pickups and the world's archive. Writes slopfeeder/bible.json.   usage: .venv/bin/python slopfeeder/chapters.py"""
import json, os
import numpy as np, torch, open_clip
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D); ROOT = os.path.dirname(L)
SIGNS = {s["symbol"]: s for s in json.load(open(os.path.join(ROOT, "cineosis-table.json")))["signs"]}

# ---- the riverbed of the whole series: stated once, attached to every prompt that casts it
LOCK = {
 "pails": "Pails: orange five-gallon pails with the narrow closed factory bottom UP and the wide original mouth DOWN biting wet sand, handle bosses low, a spindle, sliding wooden crossbar and blue rope above; never right-side up, never branded.",
 "cook": "The Slopfeeder (the cook): a plain bone-white skull mask, black hood, black headset, black apron, the broad white-blue-red segmented griddle strapped to his LEFT forearm on ceramic blocks, real browned burgers and sliced onions, grease and steam; he moves little and stares long.",
 "crew": "The crew: adults in dirty ivory pressure suits with faded orange shoulder panels, closed gloves, taped knees, mud to the thigh; no insignia, no weapons aimed at anyone, no gore.",
 "four": "The Four: flat 2-D vector shapes with no outline and no shading, even inside live action, like a login-page illustration pasted onto the world: a purple #5600F5 tall slab with tiny white eyes, a black #1A1B1F slab with big white eyes, a yellow #E6C808 capsule with one dot eye and a line mouth that runs past its own edge, an orange #F25A17 half-dome with dot eyes; they stand in their huddle, lean by shearing, and their eyes follow a cursor.",
 "world": "Geography: sea on the left, a ruined red-brick fort on the right, wet tidal sand under low grey-gold light; offshore the fleet never fires at people, it requests changes."}
NEG = ["no 3-D, plush or clay versions of the four characters", "no logos or brand marks on the pails", "no recognisable game character, celebrity or real person",
       "no burned-in subtitles or captions unless the shot is a screen", "no children, no gore, no faction insignia", "no teal-and-orange grade, no glossy trailer polish", "the pails never right-side up"]
POVS = {"embedded": "Embedded first-person: the inhabitant's body is the camera (hands and tool edges enter frame, breath audible, gait shake, mud on the lens, vision blocked by the job).",
        "witness": "World-watcher: a small hovering witness drifts low, close behind and above the bodies, patient and slightly unstable in the wind, never a god's-eye or tourism aerial.",
        "wide": "A locked wide tableau at sand level, figures small against the weather; nothing moves the camera but the wind.",
        "face": "A held close-up, lens at eye height, the subject barely moving, the background soft and alive.",
        "insert": "A macro insert on material and hands, shallow focus, the gesture filling the frame.",
        "screen": "The screen as the frame: the camera is inside the interface, text and characters at monitor scale, the world reflected in the glass.",
        "optic": "Through an optic (binocular reticle, gunsight, viewfinder), its vignette and dust part of the image."}
BLENDS = {"generation→archive": "Generate it as if it were archive: 1940s newsreel 16 mm, black and white or faded Kodachrome, gate weave, hand-cranked unevenness, scratches; no modern sheen.",
          "cartoon→archive": "Make the cartoon look like an archive: the flat characters photographed on film, as a 1930s animated insert inside a newsreel, with grain and flicker but their flat shapes intact.",
          "archive→generation": "Begin from an archival still (image-to-video): let the archive move the way generations move: impossible continuity, a slow push, the world extending past its frame.",
          "generation→cartoon": "Live-action generation with the flat characters composited crisp inside it: the world photographic, the four as flat vector stickers that cast no shadow.",
          "cartoon→generation": "Begin from the cartoon key (image-to-video): the flat world becomes photographic around the characters while they stay flat.",
          "archive→cartoon": "Archival footage with its figures flattened into poster colour, as if the archive were redrawn as the login page."}

CHAPTERS = [
 {"n": "26", "roman": "I", "title": "THE BUCKET BET", "song": "የጭቃ ድሮን (Mud Drone)", "note": "the best core one",
  "idea": "The landing. A prompt is a bucket turned mouth-down into the sand: you speak into the ground and pump until something comes up. Every drill stroke births a new bucket. The crew lands under a sky that requests changes, and the Slopfeeder feeds the line that holds.",
  "bet": "Hybrid match-cut montage: code cartoon → archive → AI pickup → tracked segment, each cut a rhyme found by CLIP. The bet: a D-Day opening can be built entirely out of rhymes.",
  "signs": ["Mi", "Bi", "Im", "Ll"], "lie": "Generated work is weightless: it costs nothing and holds nothing.", "shatter": "The tide comes in under the wall the render approved; only the hand-pumped, fed, repaired line holds.", "principle": "Weight is made by feeding and repair, not by the picture.",
  "four": "Offshore, enormous, the huddle watches the beach like a cursor watches a field; orange smiles at every landing craft until the first shell, then frowns and does not stop.",
  "symbols": ["bucket mouth-down = a prompt spoken into the ground", "each stroke births a smaller bucket = prompts beget prompts", "the burger passed hand to hand = the only thing that crosses the line", "the cursor in the sky = the request that becomes a shell"],
  "first": "Mouth full of salt, gloved hands on a crossbar that kicks on every stroke, the pail rim biting sand by my boot, shells landing in rhythm with the pump.",
  "watcher": "A small witness skims the surf line behind the crews, pausing over each new bucket as it surfaces, rising only when the shell-smoke rises.",
  "shots": [
   {"id": "I-1", "moment": "The ramp drops: a crew in ivory suits jumps into chest-deep surf holding pails over their heads like helmets.", "world": "THE LANDING", "sign": "Mi", "pov": "embedded", "blend": "generation→archive", "cast": ["crew", "pails", "world"],
    "hold": ["the pails mouth-down even when carried", "sea left, fort right"], "vary": ["spray density", "number of crew", "light from dawn-grey to fire-gold"],
    "prompt": "From inside the landing craft, the ramp slams down onto grey surf; my gloved hands lift an orange pail overhead as I step off into chest-deep water, crew in ivory suits ahead of me wading toward a brick fort on the right, shell-spouts walking up the beach, salt on the lens, breath loud, the pail's mouth pointing down at the sea."},
   {"id": "I-2", "moment": "A drill stroke births a bucket: on the downstroke a small new pail pushes up out of the sand beside the drill like a seedling.", "world": "THE DRILL LINE", "sign": "Im", "pov": "insert", "blend": "archive→generation", "cast": ["pails", "crew"],
    "hold": ["the newborn pail is a smaller copy, mouth down", "rope and crossbar visible"], "vary": ["how many newborns", "speed of emergence"],
    "prompt": "Macro at sand level beside a pumping bucket drill: as the crossbar drives down, wet sand heaves and a small orange pail rises out of it mouth-down, shedding grains, settling with a tiny wobble; the big drill above keeps pumping, gloved hands on the bar, a line of drills receding into smoke behind."},
   {"id": "I-3", "moment": "The cursor in the sky clicks and the click lands as a shell on the beach.", "world": "THE RENDER", "sign": "Bi", "pov": "wide", "blend": "generation→cartoon", "cast": ["four", "crew", "world"],
    "hold": ["the cursor is a flat black arrow with a white edge", "the four stay flat, offshore, huddled"], "vary": ["the cloud field", "the impact plume"],
    "prompt": "Locked wide from the dunes: a flat black mouse cursor the size of a cloud drifts over the sea toward the beach, the four flat cartoon characters huddled on the horizon following it with their eyes; it clicks, squashing, and a plume of wet sand erupts among the crew a second later; nobody looks up but the crew."},
   {"id": "I-4", "moment": "The Slopfeeder at the wall feeds a recruit whose hands are both on the beam.", "world": "THE KITCHEN", "sign": "Bg", "pov": "witness", "blend": "generation→archive", "cast": ["cook", "crew", "world"],
    "hold": ["griddle on the LEFT forearm", "the recruit's hands stay on the beam"], "vary": ["smoke", "how much of the wall is visible"],
    "prompt": "A small hovering witness drifts at shoulder height behind a line of crew bracing a leaning timber against the brick wall; the skull-masked cook moves along the line, turning a burger off the griddle on his left forearm and putting it into each mouth in turn because no one can let go; grease steam crosses the frame, shells thud far off."},
   {"id": "I-5", "moment": "First light on a beach of pails: hundreds of orange pails mouth-down to the waterline, the crew asleep between them.", "world": "THE AFTERMATH", "sign": "Ll", "pov": "witness", "blend": "generation→archive", "cast": ["pails", "crew", "world"],
    "hold": ["every pail mouth-down", "nobody wounded on screen, only tired"], "vary": ["fog", "how far the rows run"],
    "prompt": "Dawn after the landing, the witness drifts low along the tideline over a field of hundreds of orange pails standing mouth-down in rows like a planted crop, crew asleep sitting against them in ivory suits, smoke thinning over the fort, the sea flat and pewter; one pail wobbles as something under it keeps working."},
   {"id": "I-6", "moment": "The stare: the Slopfeeder turns from the griddle to the lens and holds.", "world": "THE KITCHEN", "sign": "Ic", "pov": "face", "blend": "cartoon→generation", "cast": ["cook"],
    "hold": ["the turn takes a full second; then nothing moves for four"], "vary": ["the steam", "the background fire"],
    "prompt": "Close on the skull-masked cook bent over the griddle on his left forearm; he lifts his head and turns it slowly to the lens, and holds, unblinking, while steam crosses his mask and the beach burns soft behind him; the only motion is the steam and a burger hissing."}]},
 {"n": "14", "roman": "II", "title": "THE RENDER FLEET", "song": "Ritual of the Ash and Silt (2)", "note": "best for the Dune movie",
  "idea": "The SaaS sublime. The login page has grown into a fleet: four flat mascots the size of capital ships stand off the coast, watching. They are not cruel; they were drawn to make people sign in. Their gaze is the weather.",
  "bet": "The sublime by scale and parallax: the multiplane cartoon and AI wides share one horizon line so the flat four sit inside photographic weather. The bet: a flat icon becomes sublime when the world around it is real.",
  "signs": ["Su", "Ic", "As", "Mw"], "lie": "The interface is neutral: it only asks.", "shatter": "Every polite request lands on the beach as weight; the crew pays for the render's whims.", "principle": "Whoever designs the request must stand where it lands.",
  "four": "Purple leads, leaning toward the shore to see better; black hides behind purple and only its eyes show over the swell; yellow objects in one long line; orange is the fleet's mood, and the mood is the weather.",
  "symbols": ["the login page = a fleet", "eyes that follow the cursor = surveillance as cuteness", "the cursor's drag = a weather front", "a password typed wrong = a squall"],
  "first": "Standing in the surf with a pail on my shoulder, I look up and the purple slab fills a third of the sky; its eyes move when the cursor moves.",
  "watcher": "The witness hangs above the waterline between the crew and the four, small against both, turning to face whichever moved last.",
  "shots": [
   {"id": "II-1", "moment": "The four rise out of the sea at dawn behind the burning fleet.", "world": "THE FLEET", "sign": "Su", "pov": "wide", "blend": "generation→cartoon", "cast": ["four", "world"],
    "hold": ["flat, unshaded, unoutlined", "the huddle order: purple back, black peeking, yellow edge, orange front"], "vary": ["fire on the ships", "mist"],
    "prompt": "Extreme wide from the tideline at dawn: the sea bulges in one long swell and four flat cartoon shapes rise from it behind a line of burning warships, purple slab first, then the black slab, the yellow capsule and the orange half-dome, each overshooting and settling, water sheeting off their flat colour; their dot eyes open and look down at the beach."},
   {"id": "II-2", "moment": "Binocular view: a sergeant counts the four through field glasses; orange notices and smiles back.", "world": "THE FLEET", "sign": "Ve", "pov": "optic", "blend": "generation→archive", "cast": ["four"],
    "hold": ["the twin-circle reticle", "the four stay flat in the glass"], "vary": ["haze", "reticle dust"],
    "prompt": "Through a pair of old field glasses, twin circles drifting with a hand's tremor: the horizon of warships, and behind them the four flat cartoon shapes; the glasses settle on the orange half-dome, whose dot eyes turn toward the lens and whose mouth curves into a small smile; the glasses jerk away."},
   {"id": "II-3", "moment": "The cursor drags across the sky like a weather front; the four lean after it.", "world": "THE RENDER", "sign": "Mw", "pov": "witness", "blend": "generation→cartoon", "cast": ["four", "crew", "world"],
    "hold": ["they lean by shearing, feet fixed"], "vary": ["cloud speed", "rain"],
    "prompt": "The witness hovers low over the crew on the beach, looking out to sea: a giant flat cursor slides across the cloud deck dragging a shadow over the water, and the four flat shapes on the horizon all lean toward it at once, purple most, black least, their eyes tracking, while rain begins to fall from where it passed."},
   {"id": "II-4", "moment": "A wrong password: the login page on the cliff shakes no, and a squall crosses the beach.", "world": "THE RENDER", "sign": "As", "pov": "wide", "blend": "cartoon→generation", "cast": ["four", "world"],
    "hold": ["the page shakes left-right like a rejected login", "orange frowns"], "vary": ["squall density"],
    "prompt": "A login page as large as the cliff glows above the sea, its four characters standing in its left panel; the password field shakes left and right in refusal, orange's smile turns down, and a squall line marches in off the water and crosses the beach, flattening smoke and sand."},
   {"id": "II-5", "moment": "Purple bends down to the beach to look at one bucket.", "world": "THE FLEET", "sign": "Ic", "pov": "embedded", "blend": "generation→cartoon", "cast": ["four", "pails", "crew"],
    "hold": ["purple stays flat even bending", "the bucket mouth-down"], "vary": ["distance of purple"],
    "prompt": "From the drill line, my hands on the crossbar: the purple slab leans down out of the sky by shearing until its flat face, with two tiny white eyes, hangs above my pail; it looks at the pail, then at me; I keep pumping; it straightens slowly back into the sky."},
   {"id": "II-6", "moment": "Night: the four asleep on the horizon, eyes closed, the fleet's lights reflected on them.", "world": "THE FLEET", "sign": "Qu", "pov": "wide", "blend": "generation→archive", "cast": ["four", "world"],
    "hold": ["eyes closed as two short lines"], "vary": ["moonlight", "fires"],
    "prompt": "Night wide over the sea: the four flat shapes stand on the horizon with eyes shut, two short lines each, the fires of the fleet reflected as orange smears on their flat colour, waves lapping at their bases; on the beach a single griddle glows."}]},
 {"n": "13", "roman": "III", "title": "THE COMMUNION", "song": "Ritual of the Ash and Silt (1)", "note": "holy sounding",
  "idea": "Humility. The Slopfeeder is not a hero; he is a cook. Slop is food. The holiest act on the beach is turning a patty and putting it in a mouth that cannot reach for it. Ash and silt season everything.",
  "bet": "Dual-sensorium sensory ethnography: the embedded body of the eater and the small witness of the line, long takes, no plot. The bet: duration and labour make meaning before story does.",
  "signs": ["Qu", "Bg", "Ba", "Op"], "lie": "Feeding is beneath the work.", "shatter": "The line only holds while it is fed; the moment the griddle stops, the wall leans.", "principle": "Care is infrastructure.",
  "four": "They are fed too: the cook leaves a burger on the tideline for them, and orange, offshore, falls asleep.",
  "symbols": ["the griddle on the forearm = a shield used as a table", "the onion ring = a halo that floats", "steam = incense", "the queue = a procession"],
  "first": "Both hands on the beam, the cook's glove in front of my face, a burger at my mouth, grease on my chin, the beam shaking with each shell.",
  "watcher": "The witness waits above the queue that winds from the griddle to the wall, rising with the steam, dipping when a plate passes.",
  "shots": [
   {"id": "III-1", "moment": "The queue as procession: crew file past the griddle in silence, each taking one burger.", "world": "THE KITCHEN", "sign": "Qu", "pov": "witness", "blend": "generation→archive", "cast": ["cook", "crew"],
    "hold": ["one burger each, taken with both hands"], "vary": ["queue length", "weather"],
    "prompt": "The witness drifts slowly along a winding queue of crew in ivory suits filing past the skull-masked cook; each takes one burger from the griddle on his left forearm with both hands and bows slightly; steam rises like incense into ash-grey air; no one speaks; the shelling is far away."},
   {"id": "III-2", "moment": "Embedded: I eat with my hands on the beam; the cook feeds me.", "world": "THE KITCHEN", "sign": "Bg", "pov": "embedded", "blend": "generation→archive", "cast": ["cook", "crew"],
    "hold": ["my gloves stay on the beam in frame"], "vary": ["focus breathing"],
    "prompt": "My gloved hands grip a splintered beam at the bottom of frame; the skull-masked cook steps in close, a burger in his right hand, and puts it to my mouth; I bite; grease, steam, the beam shuddering with a distant impact; he waits until I chew before he moves on."},
   {"id": "III-3", "moment": "Insert: the onion ring lifts from the griddle on steam like a halo.", "world": "THE KITCHEN", "sign": "Op", "pov": "insert", "blend": "archive→generation", "cast": ["cook"],
    "hold": ["one onion ring"], "vary": ["steam speed"],
    "prompt": "Macro on the white-blue-red griddle: an onion ring loosens from the hot steel, lifts on a column of steam, and hangs there turning slowly above the patties like a small halo before drifting out of frame toward the sea."},
   {"id": "III-4", "moment": "The cook leaves a plate on the tideline for the four.", "world": "THE TIDE", "sign": "Mk", "pov": "wide", "blend": "generation→cartoon", "cast": ["cook", "four", "world"],
    "hold": ["the plate small, the four huge and flat, far"], "vary": ["tide reach"],
    "prompt": "Wide at dusk: the skull-masked cook walks to the waterline and sets a steel plate with one burger on the wet sand, facing the sea; far out, the four flat shapes watch; the tide reaches the plate and stops just short of it; orange's eyes close."},
   {"id": "III-5", "moment": "Hands washing the griddle in the sea.", "world": "THE TIDE", "sign": "Ba", "pov": "insert", "blend": "generation→archive", "cast": ["cook"],
    "hold": ["griddle still strapped to the left arm"], "vary": ["foam"],
    "prompt": "Close on the cook's arms in the shallows, the griddle still strapped to his left forearm, scrubbing it with sand and seawater, grease rainbows spreading on the foam, the mask reflected faintly in the steel."},
   {"id": "III-6", "moment": "The empty griddle at night, glowing; the line asleep around it.", "world": "THE AFTERMATH", "sign": "Qu", "pov": "witness", "blend": "generation→archive", "cast": ["crew", "pails"],
    "hold": ["the glow is the only light"], "vary": ["embers"],
    "prompt": "Night; the witness descends slowly over a ring of sleeping crew around a cooling griddle set on ceramic blocks, its last embers the only light, pails mouth-down around them like a stockade."}]},
 {"n": "23", "roman": "IV", "title": "THE CHORUS", "song": "Τελετὴ τῆς Σποδοῦ καὶ τοῦ Βορβόρου (Greek chant)", "note": "Greek chant",
  "idea": "The critics are a chorus. On the fort walls, a line of masked figures in black-and-white (the archive itself, in costume) chant against the slop. They are not wrong. The cook feeds them too.",
  "bet": "Chorus montage: archival faces and intertitles answer the song line by line, as a Greek chorus answers the protagonist. The bet: the archive can argue back.",
  "signs": ["Th", "Sn", "Pf", "Mf"], "lie": "Criticism stands outside what it criticises.", "shatter": "The chorus is fed by the same griddle; their masks steam.", "principle": "Everyone at the wall eats.",
  "four": "They listen, eyes moving from mouth to mouth along the wall; yellow, the sceptic, agrees with the chorus and says so in one long line.",
  "symbols": ["the chorus in black and white = the archive as critic", "masks on the wall = the critic's anonymity", "the plate passed up the wall = the answer"],
  "first": "Looking up the fort wall at a row of black-and-white masked faces chanting down at me, I hold a plate of burgers up toward them.",
  "watcher": "The witness travels along the top of the wall at chest height, face to face with each chanting mask, then turns to look down at the beach they are judging.",
  "shots": [
   {"id": "IV-1", "moment": "The chorus appears on the wall: a row of masked figures, desaturated, in a colour world.", "world": "THE AFTERMATH", "sign": "Th", "pov": "wide", "blend": "generation→archive", "cast": ["world"],
    "hold": ["the chorus alone is black and white"], "vary": ["wind in their robes"],
    "prompt": "Low wide from the beach: along the top of the ruined brick fort a row of figures in long robes and pale theatre masks stands against the sky, and they alone are black and white, grainy as old newsreel, while the beach below is in colour; they raise their arms together and chant."},
   {"id": "IV-2", "moment": "Face to face with each mask along the wall.", "world": "THE AFTERMATH", "sign": "Mf", "pov": "witness", "blend": "generation→archive", "cast": [],
    "hold": ["black and white, film grain"], "vary": ["mask designs"],
    "prompt": "The witness travels along the wall at face height past one chanting mask after another, each a different old theatre mask, black and white and flickering like a 1920s print, mouths open on the same syllable, breath fogging in the cold."},
   {"id": "IV-3", "moment": "The plate is passed up the wall hand to hand to the chorus.", "world": "THE KITCHEN", "sign": "Pf", "pov": "embedded", "blend": "generation→archive", "cast": ["cook", "crew"],
    "hold": ["colour at the bottom, black and white at the top"], "vary": ["how many hands"],
    "prompt": "From the foot of the wall I lift a steel plate of burgers over my head; crew hands take it and pass it up the brickwork until black-and-white hands reach down from the top and take it, the colour draining from the plate as it rises into their world."},
   {"id": "IV-4", "moment": "Yellow agrees with the chorus in one long line.", "world": "THE RENDER", "sign": "Sn", "pov": "wide", "blend": "cartoon→archive", "cast": ["four"],
    "hold": ["yellow flat; its line mouth extends and extends"], "vary": ["grain"],
    "prompt": "The four flat shapes on the horizon filmed as if on old newsreel stock, grain and flicker over their flat colour; the yellow capsule turns its one eye toward the wall of the chorus and its line mouth extends slowly sideways past its own edge, across the water, as long as a sentence."},
   {"id": "IV-5", "moment": "A masked chorus member removes the mask and eats.", "world": "THE AFTERMATH", "sign": "Pf", "pov": "face", "blend": "generation→archive", "cast": [],
    "hold": ["black and white", "no recognisable face: shadow and steam"], "vary": ["light"],
    "prompt": "Close on one chorus figure in black and white; it lowers its theatre mask halfway, its face lost in shadow and steam, and bites into a burger; then lifts the mask back and resumes the chant."},
   {"id": "IV-6", "moment": "The chorus and the crew chant the same line; colour and black and white alternate on the beat.", "world": "THE DRILL LINE", "sign": "Sn", "pov": "witness", "blend": "archive→generation", "cast": ["crew", "pails"],
    "hold": ["the chant on the drill's downstroke"], "vary": ["cutting rhythm"],
    "prompt": "The witness rises from the drill line to the wall and back on each downstroke: the crew pumping pails in colour, the chorus answering in black and white, the two images alternating on the beat until they share one frame, half colour, half archive."}]},
 {"n": "20", "roman": "V", "title": "THE MAINFRAME CONFESSION", "song": "The Slop Communion", "note": "good beginning, creepy voice maybe",
  "idea": "The hype speaks. Inside the fort, banks of green terminals type the change requests, promise everything, and whisper. The cook sits before them and listens without moving. The creepy voice is the hype's.",
  "bet": "Interface montage: screens inside screens, text as image (lectosigns), the cook's mask reflected in the glass. The bet: the interface can be filmed as a landscape.",
  "signs": ["Br", "Le", "Op", "Ma"], "lie": "Scale is the same as care.", "shatter": "The terminal asks for a happier onion; outside, the tide is at the drain.", "principle": "What is requested must be fed.",
  "four": "They live inside the monitors here, small, peering out of the glass at the cook; when the hype whispers, purple nods along.",
  "symbols": ["green text = the request", "the reflection of the mask in the glass = the developer inside the screen", "the cable to the beach = the supply line"],
  "first": "Sitting at the console, my masked reflection in the green glass, text typing itself under it: could the onions look happier?",
  "watcher": "The witness hovers behind the cook's shoulder, then drifts into the gap between two monitors and out through a cable hole into the daylight.",
  "shots": [
   {"id": "V-1", "moment": "The confession: the cook seated before a wall of terminals, text typing under his reflection.", "world": "THE SCREEN", "sign": "Le", "pov": "screen", "blend": "generation→archive", "cast": ["cook"],
    "hold": ["the text reads: could you move it slightly left?"], "vary": ["the other lines"],
    "prompt": "The camera is the monitor: green phosphor text types itself line by line, could you move it slightly left?, while the skull-masked cook's reflection sits motionless in the glass; behind him the bunker's brick vault and a small window of grey sea."},
   {"id": "V-2", "moment": "The four peer out of the monitors at the cook.", "world": "THE SCREEN", "sign": "Ma", "pov": "witness", "blend": "generation→cartoon", "cast": ["four", "cook"],
    "hold": ["each character in its own monitor, flat"], "vary": ["scanlines"],
    "prompt": "Behind the cook's shoulder, a wall of old monitors; in four of them the flat characters peer out, purple, black, yellow, orange, their eyes following his slightest movement; scanlines roll over them; he does not move."},
   {"id": "V-3", "moment": "The hype's voice: a single terminal fills with the same word repeating.", "world": "THE SCREEN", "sign": "Op", "pov": "insert", "blend": "generation→archive", "cast": [],
    "hold": ["one word repeating down the screen"], "vary": ["the word"],
    "prompt": "Macro on a curved green CRT: one word, more, repeats down the screen faster and faster until the phosphor smears into a solid glowing block, reflected in a puddle on the bunker floor."},
   {"id": "V-4", "moment": "The cable from the console runs out to the beach and into a bucket.", "world": "THE DRILL LINE", "sign": "Ve", "pov": "witness", "blend": "archive→generation", "cast": ["pails", "crew"],
    "hold": ["the cable enters the pail's raised bottom"], "vary": ["cable path"],
    "prompt": "The witness follows a thick black cable out of the bunker, across wet sand, past crew pumping drills, to a single pail mouth-down at the waterline, where the cable disappears into its raised bottom; the pail hums."},
   {"id": "V-5", "moment": "The cook pulls the plug; the monitors go dark one by one; the four close their eyes.", "world": "THE SCREEN", "sign": "Br", "pov": "wide", "blend": "generation→cartoon", "cast": ["cook", "four"],
    "hold": ["each monitor collapses to a dot"], "vary": ["order"],
    "prompt": "Wide in the bunker: the cook draws a heavy plug from the wall; one by one the monitors collapse to a bright dot and go dark, the flat characters inside each closing their eyes as their screen dies; only the griddle glows."},
   {"id": "V-6", "moment": "Archive as generation: an archival control room, its operators slowly turning to look at the lens.", "world": "THE SCREEN", "sign": "Pf", "pov": "wide", "blend": "archive→generation", "cast": [],
    "hold": ["the archive's grain and period"], "vary": ["how many turn"],
    "prompt": "Begin from an archival 1960s control room still: rows of operators at consoles; as the image begins to move, every operator slowly turns their head toward the camera at once and holds, the consoles still blinking."}]},
 {"n": "09", "roman": "VI", "title": "THE RECURSION", "song": "Krew-Al-Ghal", "note": "cool starting but grating",
  "idea": "Buckets prompting buckets. The drill line multiplies: every stroke births a pail, every pail grows a drill, until the beach is a field of prompts pumping themselves. Grating, because recursion is grating; the hype calls it scale.",
  "bet": "Rhythmic cycle montage in the line of Vertov: a 16-frame cycle repeated, each repetition one bucket more, cuts landing on the pump. The bet: repetition is a sign of its own (the dividual).",
  "signs": ["Dv", "Se", "Mk", "Dm"], "lie": "More is the same as better.", "shatter": "The field of pails reaches the sea and the tide fills them all; nothing comes up.", "principle": "A prompt needs a hand on it.",
  "four": "They count. Purple counts out loud with its eyes, flicking from bucket to bucket; orange gets dizzy and its eyes cross.",
  "symbols": ["the newborn pail = the derivative work", "the field of pails = the feed", "a pail with no one pumping = generation without labour"],
  "first": "Pumping, and every time I look down there is one more pail beside my boot, then two, then my boot is surrounded.",
  "watcher": "The witness rises slowly straight up as the field of pails multiplies below until the beach is orange to the horizon.",
  "shots": [
   {"id": "VI-1", "moment": "The field multiplies: a rising witness over pails doubling with every drill stroke.", "world": "THE DRILL LINE", "sign": "Dv", "pov": "witness", "blend": "generation→archive", "cast": ["pails", "crew"],
    "hold": ["mouth-down, all of them"], "vary": ["the pattern of growth"],
    "prompt": "The witness lifts slowly straight up from a single crew pumping a bucket drill; with each downstroke new orange pails push up out of the sand around it, mouth-down, then those pails grow their own crossbars and pump, doubling outward, until the beach is an orange field of pumping pails to the waterline."},
   {"id": "VI-2", "moment": "A pail pumping with no one at the bar.", "world": "THE DRILL LINE", "sign": "Dm", "pov": "insert", "blend": "archive→generation", "cast": ["pails"],
    "hold": ["the crossbar moves by itself"], "vary": ["speed"],
    "prompt": "Close on a bucket drill whose crossbar rises and falls on its own, no hands, rope slapping, sand spitting from under the rim, in a rhythm slightly too fast, slightly too even."},
   {"id": "VI-3", "moment": "My boot surrounded by newborn pails.", "world": "THE DRILL LINE", "sign": "Se", "pov": "embedded", "blend": "generation→archive", "cast": ["pails", "crew"],
    "hold": ["each newborn smaller than the last"], "vary": ["count"],
    "prompt": "Looking down past my gloved hands on the crossbar at my boot in wet sand: on each stroke another small pail rises beside it, mouth-down, until my boot is ringed by a dozen and I cannot step out."},
   {"id": "VI-4", "moment": "The tide fills the field: water rises into a thousand pails.", "world": "THE TIDE", "sign": "Mk", "pov": "wide", "blend": "generation→archive", "cast": ["pails", "world"],
    "hold": ["the pails stay mouth-down as water rises around them"], "vary": ["light"],
    "prompt": "Wide over the field of orange pails as the tide comes in between them, filling the furrows, lapping up their sides until only their raised bottoms show like orange stepping stones across a grey sea."},
   {"id": "VI-5", "moment": "Orange gets dizzy counting; its eyes cross.", "world": "THE RENDER", "sign": "Ic", "pov": "face", "blend": "cartoon→archive", "cast": ["four"],
    "hold": ["flat, dot eyes"], "vary": ["grain"],
    "prompt": "Close on the flat orange half-dome as a newsreel insert, film grain over its flat colour, its two dot eyes flicking left and right counting something off-screen faster and faster until they drift together and cross."},
   {"id": "VI-6", "moment": "One crew lifts one pail out of the field and carries it away.", "world": "THE AFTERMATH", "sign": "Ba", "pov": "witness", "blend": "generation→archive", "cast": ["crew", "pails"],
    "hold": ["only one is lifted"], "vary": ["path"],
    "prompt": "The witness follows a single crew member walking out of the endless field of pails carrying one pail upside down against their chest, toward the fort, the field pumping on behind them."}]},
 {"n": "06", "roman": "VII", "title": "GO HOME AND BE FREE", "song": "Go Home and Be Free", "note": "",
  "idea": "Homecoming. The crew leave the beach. The tide washes the drill circles away. The four shrink back into their login page, which closes. The cook stays to clean the griddle. Freedom is going home.",
  "bet": "Elegy by dissolve: liquid perception, everything a slow overlap, the archive's homecoming reels under the AI's beach. The bet: an ending can be a dissolve rather than a cut.",
  "signs": ["Lq", "Ga", "Sp", "Wd"], "lie": "The work is the place.", "shatter": "The tide takes every circle in one wash.", "principle": "You can leave.",
  "four": "Orange yawns; purple straightens; black is first in; one by one they step back into the page and the page closes like a laptop.",
  "symbols": ["circles in sand = the work", "the closing login page = sign out", "the empty griddle = the meal finished"],
  "first": "Walking up the beach away from the sea, my pail left behind, suit unzipped, the sound of the surf getting smaller behind me.",
  "watcher": "The witness stays at the waterline watching the crew grow small up the beach, then turns to the circles as the water reaches them.",
  "shots": [
   {"id": "VII-1", "moment": "The tide erases the drill circles one by one.", "world": "THE TIDE", "sign": "Lq", "pov": "witness", "blend": "generation→archive", "cast": ["world"],
    "hold": ["perfect circles in sand"], "vary": ["wash speed"],
    "prompt": "The witness hovers low over wet sand printed with hundreds of perfect drill circles; a thin sheet of tide slides in and smooths them away row by row, foam bubbling in the last ones, until the sand is a mirror of the grey sky."},
   {"id": "VII-2", "moment": "The four step back into the login page; it folds shut.", "world": "THE RENDER", "sign": "Wd", "pov": "wide", "blend": "cartoon→generation", "cast": ["four", "world"],
    "hold": ["order: black first, orange last"], "vary": ["light"],
    "prompt": "Over the sea a login page hangs like a cliff of light; the four flat shapes walk back into its left panel, black first, purple, yellow, orange last with a yawn, and the page folds shut like a laptop lid, leaving only weather."},
   {"id": "VII-3", "moment": "The crew walk home up the beach, suits unzipped, pails left behind.", "world": "THE AFTERMATH", "sign": "Wd", "pov": "embedded", "blend": "generation→archive", "cast": ["crew", "pails"],
    "hold": ["no one carries a pail"], "vary": ["the light warming"],
    "prompt": "Walking up the beach with my suit unzipped to the waist, other crew ahead of me in a loose line, pails left standing mouth-down behind us at the waterline, the surf sound shrinking, light warming as we reach the dunes."},
   {"id": "VII-4", "moment": "Archival homecoming: a dissolve into an old newsreel of soldiers' homecoming.", "world": "THE AFTERMATH", "sign": "Sp", "pov": "wide", "blend": "archive→generation", "cast": [],
    "hold": ["the archive's own faces, not regenerated"], "vary": ["the dissolve length"],
    "prompt": "Begin from an archival homecoming still, a station platform crowded with returning soldiers; let it breathe and move slowly, steam drifting, figures embracing, the edges dissolving into a grey beach with orange pails at the waterline."},
   {"id": "VII-5", "moment": "The cook alone, cleaning the griddle at sunset.", "world": "THE KITCHEN", "sign": "Qu", "pov": "wide", "blend": "generation→archive", "cast": ["cook"],
    "hold": ["alone"], "vary": ["sun"],
    "prompt": "Wide at sunset: the skull-masked cook alone on the emptied beach, scraping the griddle on his left forearm clean with a spatula, the fort dark behind him, pails in rows to the water, the sky going amber."},
   {"id": "VII-6", "moment": "Gaseous: the cook exhales; the mist becomes the whole beach.", "world": "THE TIDE", "sign": "Ga", "pov": "face", "blend": "generation→archive", "cast": ["cook"],
    "hold": ["the mask"], "vary": ["mist"],
    "prompt": "Close on the skull mask in cold air; the cook exhales, and the breath fog spreads and spreads until it becomes the sea mist covering the whole beach, the mask the last thing visible before it too goes white."}]},
 {"n": "07", "roman": "VIII", "title": "CLEANSE THE MEMORY", "song": "Hreinsið Minnit", "note": "",
  "idea": "Erasure. The onion ring rides the current into the drain. The archive itself degrades: frames lose grain, become smooth, become generation. Memory is cleansed and what remains looks generated. The question the lab keeps asking: when the archive is cleaned, what was it?",
  "bet": "Decay montage: archives that look like generations and generations that look like archives, cut until you cannot tell which is which. The bet: the blend is the subject.",
  "signs": ["Lo", "Mf", "Lq", "Sp"], "lie": "The clean copy is the memory.", "shatter": "The drain takes the onion; the archive frame smooths into a generation and loses its people.", "principle": "Keep the scratches.",
  "four": "They are the cleaners here: orange wipes the frame, purple straightens it, and when the image is clean they look into it and see nothing.",
  "symbols": ["the onion into the drain = the forgotten thing that found the gap", "scratches = memory", "a smooth frame = forgetting"],
  "first": "Kneeling at the brick drain, my glove reaching after the onion ring as it slips into the dark.",
  "watcher": "The witness follows the onion ring at water level down the channel and through the arch, into the dark, and does not come back.",
  "shots": [
   {"id": "VIII-1", "moment": "The onion ring rides the current into the drain.", "world": "THE TIDE", "sign": "Lq", "pov": "witness", "blend": "generation→archive", "cast": ["world"],
    "hold": ["one onion ring", "a low brick arch"], "vary": ["current speed"],
    "prompt": "Water-level witness following a single cooked onion ring floating along a finger-wide channel through wet sand toward a low brick drain arch, past the circles of drill holes; it speeds as the channel narrows and slips into the dark under the arch; the witness follows it in."},
   {"id": "VIII-2", "moment": "An archive frame cleans itself: scratches heal, grain melts, faces smooth to generation.", "world": "THE AFTERMATH", "sign": "Lo", "pov": "wide", "blend": "archive→generation", "cast": [],
    "hold": ["the composition never changes"], "vary": ["what is lost"],
    "prompt": "Begin from a scratched archival still of soldiers on a beach; slowly the scratches heal, the grain melts away, the black and white warms into smooth modern colour, and as it becomes clean the soldiers' faces smooth into the same generic face, then fade from the frame entirely, leaving the clean beach."},
   {"id": "VIII-3", "moment": "Mirrors face to face: an AI shot and its archival rhyme side by side, swapping.", "world": "THE LANDING", "sign": "Mf", "pov": "wide", "blend": "generation→archive", "cast": ["crew", "pails"],
    "hold": ["the same composition in both halves"], "vary": ["which half is which"],
    "prompt": "A split frame: on the left a generated shot of crew charging up a beach past orange pails, on the right a 1944 newsreel of soldiers charging up a beach in the same composition; slowly they exchange textures until the left is grainy black and white and the right is clean colour."},
   {"id": "VIII-4", "moment": "Orange wipes the screen; there is nothing behind.", "world": "THE RENDER", "sign": "Ic", "pov": "screen", "blend": "cartoon→generation", "cast": ["four"],
    "hold": ["flat orange"], "vary": ["what is wiped"],
    "prompt": "The frame is a dusty glass screen with the beach behind it; the flat orange half-dome slides across the inside of the glass wiping it clean in one stroke, and where it has wiped there is only flat grey, no beach; it looks at the clean grey and frowns."},
   {"id": "VIII-5", "moment": "A glove reaching into the drain after the onion.", "world": "THE TIDE", "sign": "Mk", "pov": "embedded", "blend": "generation→archive", "cast": ["crew"],
    "hold": ["the glove does not reach it"], "vary": ["light in the drain"],
    "prompt": "Kneeling at a low brick drain, my gloved hand reaches into the dark water after an onion ring that slides just out of reach and is gone; my hand stays in the water; the tide hisses behind me."},
   {"id": "VIII-6", "moment": "The last frame: the beach in perfect generated clarity, no one on it, one pail.", "world": "THE AFTERMATH", "sign": "Sp", "pov": "wide", "blend": "archive→generation", "cast": ["pails", "world"],
    "hold": ["one pail, mouth-down"], "vary": ["time of day"],
    "prompt": "A perfectly clean, sharp, silent beach under even light, no people, no smoke, the fort repaired and blank, and at the waterline a single orange pail mouth-down, the only thing in the frame that looks used."}]}]

# ---- references for every AI shot: the nearest SLOPFEEDER frame, the nearest existing pickup, the world's nearest archive shot, and the model sheet when the four are cast
m, _, prep = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def ct(ts):
    with torch.no_grad(): e = m.encode_text(tok(ts)).float()
    return (e / e.norm(dim=-1, keepdim=True)).numpy()
def ci(ps):
    with torch.no_grad(): e = m.encode_image(torch.stack([prep(Image.open(p).convert("RGB")) for p in ps])).float()
    return (e / e.norm(dim=-1, keepdim=True)).numpy()
W = json.load(open(os.path.join(D, "world.json"))); FR = W["frames"]; FE = ci([os.path.join(D, f["src"]) for f in FR])
AI = json.load(open(os.path.join(D, "ai", "ai.json"))); AS = [(c, s) for c in AI["clips"] for s in c["shots"]]; AE = np.array([s["emb"] for _, s in AS], np.float32)
PO = json.load(open(os.path.join(D, "pools.json")))["pools"]
# archive pool thumbnails embedded by their own text "why" is not enough; use the forage/library embeddings via the ingest's records: approximate with CLIP over pool thumbnails we have locally (forage) else text
FT = os.path.join(D, "fthumbs")
SJ = json.load(open(os.path.join(D, "studio.json"))); songs = {s["n"]: s for s in SJ["songs"]}
out = []
for ch in CHAPTERS:
    s = songs.get(ch["n"], {}); ch["arc"] = [{"world": x["world"], "t0": x["t0"], "t1": x["t1"], "energy": x["energy"], "sound": x["sound"][:2], "shots": len(x["shots"])} for x in s.get("sections", [])]
    ch["file"] = s.get("file"); ch["dur"] = s.get("dur"); ch["tempo"] = s.get("tempo")
    ch["signs_full"] = [{"symbol": k, "name": SIGNS[k]["name"], "image_type": SIGNS[k].get("image_type"), "definition": SIGNS[k].get("definition", "")[:260]} for k in ch["signs"] if k in SIGNS]
    worlds = {x["world"] for x in ch["arc"]}
    ch["coverage"] = {w: {"ai": sum(1 for c, sh in AS if sh["world"] == w), "povs": sorted({sh["pov"] for c, sh in AS if sh["world"] == w})} for w in sorted(worlds)}
    for sh in ch["shots"]:
        sh["sign_name"] = SIGNS.get(sh["sign"], {}).get("name"); q = ct([sh["prompt"][:300]])[0]
        fr = FR[int(np.argmax(FE @ q))]; j = int(np.argmax(AE @ q)); c_, s_ = AS[j]
        arch = None
        for x in PO[sh["world"]][:80]:
            p = os.path.join(FT, x["id"] + ".jpg")
            if os.path.exists(p): arch = arch or []; arch.append((x, p))
        ar = None
        if arch:
            E_ = ci([p for _, p in arch[:40]]); k = int(np.argmax(E_ @ q)); ar = {kk: arch[k][0].get(kk) for kk in ("id", "title", "year", "v", "t")}
        else: ar = {kk: PO[sh["world"]][0].get(kk) for kk in ("id", "title", "year", "v", "t")}
        sh["refs"] = {"frame": {"id": fr["id"], "src": fr["src"]}, "pickup": {"clip": c_["name"], "key": s_["key"], "web": c_["web"], "t0": s_["t0"]}, "archive": ar,
                      "model_sheet": "cartoon/model-sheet.png" if "four" in sh["cast"] else None}
        locks = [LOCK[k] for k in sh["cast"] if k in LOCK]
        sh["full_prompt"] = " ".join([sh["prompt"], POVS[sh["pov"]], BLENDS[sh["blend"]], "Hold: " + "; ".join(sh["hold"]) + ".", "May vary: " + "; ".join(sh["vary"]) + ".", *locks, "Avoid: " + "; ".join(NEG) + "."])
    # the chapter's hero prompt (dense ekphrasis), built from its idea, lie, shattering, principle, symbols and both sensoria
    ch["hero"] = (f"{ch['first']} {ch['watcher']} {ch['idea']} The hidden lie on this beach: {ch['lie']} It breaks when {ch['shatter'][0].lower() + ch['shatter'][1:]} "
                  f"After it breaks: {ch['principle']} Symbols carry the load: {'; '.join(ch['symbols'])}. The four: {ch['four']} "
                  f"{LOCK['world']} {LOCK['pails']} {LOCK['cook']} {LOCK['crew']} {LOCK['four']} Render it as {ch['bet'].split(':')[0].lower()}, the image grainy where the archive speaks and clean where the generation speaks, "
                  f"violence only as consequence (sand, smoke, fatigue), never as gore; end on the image that proves the principle.")
    out.append(ch)
json.dump({"locks": LOCK, "neg": NEG, "povs": POVS, "blends": BLENDS, "chapters": out}, open(os.path.join(D, "bible.json"), "w"), ensure_ascii=False, indent=1)
print(len(out), "chapters ·", sum(len(c["shots"]) for c in out), "AI shots ·", sum(len(c["hero"]) for c in out) // len(out), "chars per hero prompt (mean)")
