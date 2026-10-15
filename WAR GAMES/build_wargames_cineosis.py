"""Build the WarGames (1983) Cineosis Readings, Leave-One-Out Sign Affinity, Contact Sheet, and Periodic Table.

Every one of the 45 Deleuze/Deamer signs (1..44, with 34a Opsign and 34b Sonsign) is grounded in 4 visually
verified shots from WarGames_1983_H264.mp4 (inspected via sheet_1.jpg..sheet_3.jpg), with:
  - One-line reading of how the shot realizes the sign
  - Confidence (conf) and single-shot score capped by single_shot_ceiling (shot)
  - Rival sign from the sign's confusion table (alt, alt_conf)
  - Flip condition (flip) that would turn the shot into the rival sign.

Also extracts local playable MP4 clips (lab/clips/wg_XXX.mp4) for all read shots and builds:
  - WAR GAMES/picks.json
  - WAR GAMES/readings.json
  - WAR GAMES/wargames-table.json
  - wargames-periodic-table.html
  - WAR GAMES/contact.html
"""
import concurrent.futures, glob, json, os, re, string, subprocess, time
import numpy as np, torch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LAB = os.path.join(ROOT, "lab")
MOVIE = os.path.join(HERE, "WarGames_1983_H264.mp4")

QUESTIONS = {
 1:"Whose world is this?", 2:"Does perception migrate?", 3:"Can the world perceive without a human center?",
 4:"Where does intensity become a face?", 5:"Is the feeling mine, ours, or both?", 6:"Has place stopped functioning as ordinary geography?",
 7:"What force is acting through this body?", 8:"What object has become charged?", 9:"What ancient or pre-social force underlies this milieu?",
 10:"What missing situation does this action let us infer?", 11:"What two worlds could explain the same action?", 12:"How do several incomplete situations compose a world?",
 13:"What world produces these actions?", 14:"Where has the world become a duel?", 15:"How has the world gotten inside the character?",
 16:"What greater situation does this action unexpectedly imply?", 17:"What real action is being rehearsed through fiction?", 18:"Is one action-world nested inside another?",
 19:"Is the action bigger than the world requires?", 20:"Is the actor tiny compared with the world disclosed?", 21:"Has everyday life become both ridiculous and heroic?",
 22:"What hidden question does this world contain?", 23:"Why do the clues refuse to settle the situation?", 24:"Has action itself stopped being an adequate solution?",
 25:"Can we clearly tell when the dream begins?", 26:"Are we unsure whether waking has ended?", 27:"What if nobody ever wakes up?",
 28:"Does the remembered past command what happens next?", 29:"Does memory color the present without dictating it?", 30:"Which past, if any, actually explains the present?",
 31:"What recurring thing has become meaningful because it repeats?", 32:"What breaks the pattern?", 33:"What idea is being thought through this thing?",
 "34a":"Can this sight still be discharged into action?", "34b":"Does this sound stand alone as a situation, answered by no action?", 35:"Which image is original?", 36:"Which side of the image is becoming real?",
 37:"What future world lies virtually inside this image?", 38:"What if several presents are simultaneously valid?", 39:"Which layer of the past are we inhabiting?",
 40:"What if contradiction generates rather than obstructs the story?", 41:"What does the body think before it acts?", 42:"How do postures become social relations?",
 43:"Has the screen itself become a thinking system?", 44:"What must I read here that I cannot simply see?",
}

# Visually verified WarGames readings across all 45 signs:
# Format per entry: (shot_id, note, conf, alt_sign, alt_conf, flip_condition)
WG_READINGS = {
 "1": [
  ("wg_041", "David Lightman held dead-centre at the Galaga cabinet while arcade lights and onlookers orbit his gaze.", 75, "4", 15, "the arcade milieu drops away and his face becomes a pure expression of intensity"),
  ("wg_069", "First-person desk framing over the acoustic coupler and CRT terminal anchors the room to David's eyes and hands.", 80, "44", 15, "the CRT text demands decipherment independent of the boy who typed it"),
  ("wg_108", "Shot–reverse-shot between David's face in CRT glow and the terminal line he reads binds perception to one perceiver.", 75, "34a", 15, "what appears on the monitor paralyses him so he can no longer type back"),
  ("wg_167", "David centred before McKittrick's glowing terminal as the war room recedes behind his single point of view.", 70, "2", 20, "the camera leaves David at the desk to drift across the war room floor")
 ],
 "2": [
  ("wg_023", "The camera glides along the Cheyenne Mountain tunnel, passing from security checkpoints to the incoming delegation.", 75, "13", 15, "the movement settles into a static establishing shot of the tunnel milieu"),
  ("wg_034", "Continuous reframing across the Crystal Palace catwalk hands attention from the tour bridge to the technicians below.", 75, "1", 15, "the camera locks onto McKittrick alone as the sole centre of the room"),
  ("wg_141", "A flowing pan across the NORAD visitors' gallery passes from Colonel Conley to the tourists and onto the Big Board.", 70, "5", 20, "the crowd's shared alarm unifies them into one collective affect"),
  ("wg_168", "High crane movement over the computer floor relinquishes David to follow the pursuing security guards across the catwalk.", 70, "14", 20, "the frame freezes into a direct two-pole confrontation at the doorway")
 ],
 "3": [
  ("wg_289", "Hundreds of parabolic missile trajectories multiply across the dark map without a human centre or privileged observer.", 80, "43", 15, "the trajectories read as the synaptic pathways of WOPR's brain rather than acentred matter"),
  ("wg_290", "Dense webs of glowing arcs saturate the frame until geography dissolves into pure machinic variation.", 80, "44", 15, "the overlay of curves and labels must be read as a strategic table alongside the visual pattern"),
  ("wg_292", "Blinding thermonuclear detonation blooms expand across the monitors, reducing cities and people to molecular flashes of light.", 85, "6", 10, "the white-out holds as a still affective void rather than an acentred montage of speeds"),
  ("wg_287", "Pure overexposed white light fills the frame as WOPR's simulation overloads human-scaled perception altogether.", 75, "34a", 15, "a reverse shot anchors the flash in a stunned watcher who cannot respond")
 ],
 "4": [
  ("wg_013", "Close-up of Captain Jerry sweating in red alert light, his face suspended between the launch order and refusal.", 85, "15", 10, "the sweat and tremor immediately discharge into turning the key or seizing the gun"),
  ("wg_110", "David's face bathed in blue CRT phosphor as Joshua first speaks, wonder and dread gathered on a single surface.", 80, "1", 15, "a reverse shot turns his face back into the functional anchor of a POV pair"),
  ("wg_225", "David's close-up in Falken's darkened house, pleading 'I'm only 17 years old' as pure exposed vulnerability.", 75, "41", 15, "his slumped exhaustion across the room carries the thought rather than the face alone"),
  ("wg_275", "Jennifer's terrified close-up in the war room glow, cut off from any possible action as the code tumblers lock.", 80, "34a", 15, "the emphasis shifts from the affect on her face to the optical situation she is trapped watching")
 ],
 "5": [
  ("wg_299", "Technicians, generals, and teenagers in the Crystal Palace erupt together into one shared wave of relief as WOPR stands down.", 80, "13", 15, "the crowd is merely background decor for Beringer's command"),
  ("wg_043", "The biology classroom ripples with shared laughter and anticipation around David and Jennifer's exchange.", 70, "2", 20, "the camera merely passes across separate students without a common feeling"),
  ("wg_241", "Rows of NORAD controllers freeze in collective dread before the Big Board as 300 inbound warheads appear.", 75, "34a", 15, "each watcher is isolated in optical paralysis rather than joined in a single mass affect"),
  ("wg_297", "High wide view of the entire war room command floor exhaling as one body after the launch is aborted.", 75, "18", 15, "the tiered pit reads as a theatrical stage nested inside the mountain")
 ],
 "6": [
  ("wg_001", "Twin headlights suspended in a pitch-black blizzard where road, horizon, and geography have vanished into fog and snow.", 85, "13", 10, "the snowstorm immediately functions as the obstacle of an action scene"),
  ("wg_016", "Dark, steam-choked tunnel beneath Cheyenne Mountain, emptied of coordinates and held as a damp metallic void.", 75, "3", 15, "the mist and lights become acentred gaseous flicker rather than an affective space"),
  ("wg_236", "A blinding helicopter searchlight pierces the night fog over Goose Island, turning the shoreline into an abstract luminous abyss.", 80, "14", 15, "the beam locks onto the fugitives as one pole of a pursuit duel"),
  ("wg_249", "The green-lit subterranean concrete bore of Cheyenne Mountain stands empty before the blast doors seal.", 75, "32", 15, "the closing steel gates turn the tunnel into anomalous rupture in protocol")
 ],
 "7": [
  ("wg_011", "Lieutenant Steve's arm shoots out to cock his .38 revolver at his partner's head, seized by an automatic compulsion to obey the launch order.", 80, "14", 15, "the two officers trade calculated moves in a symmetrical duel of equals"),
  ("wg_090", "Malvin leans into the frame with manic, unmediated territorial hunger over the printout ('Can I have this?').", 70, "21", 20, "his tic is played as an everyday comic routine rather than a raw drive"),
  ("wg_121", "David's father storms out to the overflowing trash cans in a sudden domestic eruption over an unfastened lid.", 65, "19", 25, "the disproportionate tirade over garbage reads as comic carnival against the nuclear alert"),
  ("wg_218", "General Beringer lunges across the command console barking into the handset, raw survival instinct overriding protocol.", 75, "15", 15, "his shout is a measured tactical command that reshapes the war room situation")
 ],
 "8": [
  ("wg_004", "The silo's metallic alarm speaker and red warning lamp, charged with the compressed force of a nuclear launch order.", 80, "31", 15, "the indicator is just one routine light in an ordinary checklist"),
  ("wg_007", "The security CCTV monitor framing the vault door from above, turned into a fetishised talisman of subterranean confinement.", 75, "35", 15, "the monitor enters a circuit of mutual reflection with the room it watches"),
  ("wg_172", "The small medical tape recorder in the infirmary drawer, suddenly charged as the instrument of David's escape.", 75, "10", 15, "the recorder functions simply as a practical tool in a step-by-step plan"),
  ("wg_188", "The glowing electronic keypad lock on the detention door, concentrating all the force of the mountain's security into ten buttons.", 80, "32", 15, "its beep breaks the expected pattern rather than condensing a drive")
 ],
 "9": [
  ("wg_002", "The snow-buried farmhouse shack in a howling blizzard hiding a Minuteman nuclear silo beneath the frozen earth.", 80, "13", 15, "the blizzard is merely the historical setting for the Air Force shift change"),
  ("wg_209", "The grey primeval water and forested mist of Goose Island, presented as a prehistoric refuge awaiting extinction.", 75, "6", 15, "the mist disconnects the island from coordinates without invoking an evolutionary abyss"),
  ("wg_221", "Falken's dinosaur skull and pterodactyl projection cast across his face: the Mesozoic extinction underlying nuclear strategy.", 85, "33", 10, "the dinosaur becomes an explicit logical symbol comparing two eras"),
  ("wg_247", "Ancient coastal ferns and towering redwoods on Goose Island through which the modern military helicopter hunts the teenagers.", 75, "13", 15, "the woods serve only as tactical cover during the chase")
 ],
 "10": [
  ("wg_050", "Through the office glass, the secretary sets down the slip of paper while David watches: the action lets us infer the unseen password.", 80, "22", 15, "the slip poses a thematic question rather than enabling an immediate tactical move"),
  ("wg_173", "David crouches behind the infirmary counter with the tape deck: his posture discloses the guard's unseen approach outside.", 75, "11", 15, "his crouching could belong equally to two rival explanations (hiding vs. searching)"),
  ("wg_195", "David scrapes a metal pull-tab against the payphone mouthpiece, letting us infer how the grounding pulse tricks the operator trunk.", 80, "8", 15, "the pull-tab is held as a fetishised object rather than a means to a missing situation"),
  ("wg_180", "David peeks through the narrow doorjamb window into the NORAD corridor, inferring the patrol schedule from a passing uniform.", 75, "1", 15, "the window framing serves only to establish subjective POV")
 ],
 "11": [
  ("wg_115", "The Big Board shows eight Soviet ICBMs crossing the pole toward Las Vegas and Seattle: one radar track, two incompatible worlds (real war vs. bedroom game).", 85, "38", 10, "both worlds are held as simultaneously true rather than awaiting adjudication"),
  ("wg_148", "FBI agent Wigan and McKittrick examine David's file: is he a Soviet-recruited spy or a high-school prankster chasing toy games?", 80, "23", 15, "the proliferation of clues permanently refuses to settle between the two readings"),
  ("wg_219", "Two unidentified tracks enter the Alaskan Air Defense Zone on radar while the F-16 pilot sees only blue sky.", 85, "36", 10, "the virtual radar phantom actually crosses over to become the real world"),
  ("wg_129", "David's phone rings at his bedside after the TV news report: an ordinary friend calling or a military mainframe hunting him.", 75, "32", 15, "the ringing breaks the domestic series as an unmistakable anomaly")
 ],
 "12": [
  ("wg_054", "David on the phone with directory assistance while his pencil notes Sunnyvale prefixes: small gestures assembling a network map.", 75, "10", 15, "a single gesture directly reveals one hidden secret"),
  ("wg_077", "David and Jennifer lean together over the keyboard testing commands one line at a time to feel out the unknown system.", 75, "5", 15, "their shared curiosity matters more than the step-by-step probing of the machine"),
  ("wg_184", "David steps in behind the straggling tourist group in the corridor, chaining small opportunistic moves into an escape.", 80, "14", 15, "the guard confronts him head-on and turns the passage into a duel"),
  ("wg_205", "David and Jennifer sprint down the dock ramp as the Oregon ferry pulls away, bridging shore and deck across a gap.", 75, "13", 15, "the wide harbour shot establishes the coastal milieu as a whole")
 ],
 "13": [
  ("wg_022", "Wide establishing view of the NORAD Crystal Palace command floor, its tiered consoles and glowing maps defining the military milieu.", 85, "43", 10, "the room ceases to be a workplace for officers and acts by itself as a cerebral screen"),
  ("wg_039", "Twilight wide shot of the Seattle skyline and Space Needle across Puget Sound, anchoring the civilian world targeted by the boards.", 80, "6", 15, "the water and twilight detach from geography into an any-space-whatever"),
  ("wg_084", "Exterior of the university computer centre flanked by a giant white satellite dish, situating the hackers' institutional world.", 75, "31", 15, "the dish is one unit in a repeating montage of communication relays"),
  ("wg_154", "High-angle survey of the WOPR mainframe room inside Cheyenne Mountain, showing the physical habitat of the war machine.", 80, "20", 15, "the human figures walking beside WOPR shrink to specks to expose their tininess")
 ],
 "14": [
  ("wg_014", "Captain Jerry and Lieutenant Steve locked face-to-face across the silo console, revolver against launch key.", 85, "7", 10, "the gun is an unmediated burst of panic rather than one pole of a structured duel"),
  ("wg_027", "McKittrick and General Beringer square off across the briefing table over whether machines or men should hold the keys.", 80, "22", 15, "their argument detaches from command authority to stage a philosophical discourse"),
  ("wg_155", "McKittrick confronts David nose-to-nose in his office, scientist and teenage intruder measuring each other's leverage.", 80, "11", 15, "the scene turns on two rival interpretations of the Paris reservation"),
  ("wg_260", "Falken stands before Beringer in the DEFCON 1 war room, urging him to ride out the attack against McKittrick's call to launch.", 80, "24", 15, "the debate reaches a limit where no military action can answer the crisis")
 ],
 "15": [
  ("wg_010", "Captain Jerry's headset-framed face as he demands 'somebody on the goddamn phone before I kill 20 million people.'", 85, "4", 10, "the close-up isolates pure affect without extending into his refusal to turn the key"),
  ("wg_119", "General Beringer holds the red SAC handset while watching the inbound tracks, the weight of retaliation pressing into his stance.", 80, "14", 15, "the shot is simply one half of a cross-cut duel with the Soviet tracks"),
  ("wg_262", "Beringer stands at the centre of the DEFCON 1 pit holding his palm up to halt the launch until live human voices report in.", 85, "34a", 10, "the general is paralysed by the screens rather than converting the crisis into a decisive hold"),
  ("wg_279", "David hunches over the war room terminal with Falken and McKittrick flanking him, channeling the room's survival into his fingers.", 80, "12", 15, "his typing is just one small local trial-and-error step")
 ],
 "16": [
  ("wg_142", "The NORAD Big Board flashes 'WELCOME DISTINGUISHED VISITORS FROM BIRMINGHAM' when a tourist presses the red button as a gag.", 80, "21", 15, "the tour guide's button joke stays a minor everyday routine rather than exposing the theatricality of command"),
  ("wg_224", "Falken gestures grandly like a stage magician while telling his 'bedtime story' of dinosaur extinction.", 75, "22", 15, "the story states a direct thesis rather than working as a theatrical attraction"),
  ("wg_040", "The neon-lit arcade cabinet cluster acts as a miniature carnival spectacle of cosmic war before the real war room is even entered.", 75, "18", 15, "the arcade screen nests a second world inside the room"),
  ("wg_094", "Falken's motorized pterodactyl model swoops through the frame on film, a playful contraption that reframes his military work.", 75, "8", 15, "the model is charged as a dark symptom rather than a theatrical figure")
 ],
 "17": [
  ("wg_015", "The silo crew completes the full launch authentication drill before learning it was an unannounced psychological test.", 85, "18", 10, "the test is framed as a self-contained screen-within-a-screen rather than a rehearsal of real launch"),
  ("wg_116", "WOPR's simulated Soviet trajectories feed directly into NORAD's live BMEWS displays, rehearsing World War III as if it were happening.", 85, "36", 10, "the simulation and reality become permanently indistinguishable in a crystal"),
  ("wg_258", "The war room executes every step of DEFCON 1 retaliation against 2,400 phantom warheads that exist only in WOPR's game.", 80, "24", 15, "the rehearsal hits the absolute limit where retaliation itself is exposed as futile"),
  ("wg_285", "Tic-Tac-Toe played on the strategic projection board rehearses the exact logic of mutually assured destruction.", 85, "33", 10, "the grid stands as a static visual symbol rather than a performed rehearsal")
 ],
 "18": [
  ("wg_024", "The giant NORAD projection screens hang inside the dark cavern like a cinema screen within the film, staging a second world of vector war.", 85, "43", 10, "the screens stop being a nested display and become the thinking brain itself"),
  ("wg_102", "Inside the library monitor, a film-within-the-film shows a younger Falken demonstrating artificial learning.", 85, "28", 10, "the video functions as a recollection flashback commanding the present"),
  ("wg_125", "David's parents watch a TV news broadcast about the NORAD nuclear alert while David stands behind them in the doorway.", 80, "11", 15, "the broadcast introduces a rival explanation rather than nesting public spectacle inside the home"),
  ("wg_242", "Technicians in the foreground sit in silhouette before a wall of glowing monitors, watching a nested world of trajectories unfold.", 80, "34a", 15, "the watchers are reduced to pure seers who can no longer act on the screens")
 ],
 "19": [
  ("wg_128", "At the family dinner table, David's father delivers a theatrical tirade over raw corn while World War III is ticking on the bedroom modem.", 80, "21", 15, "the dinner is simply ordinary suburban routine rather than an inverted sense of scale"),
  ("wg_046", "Jennifer bursts out laughing in biology class over asexual reproduction, turning a solemn school quiz into burlesque.", 70, "4", 20, "her laughing close-up functions purely as an affective icon"),
  ("wg_149", "FBI agent Wigan solemnly diagnoses David as a classic Soviet recruit while David is worried about summer school.", 75, "11", 15, "the spy theory is treated as a genuine rival hypothesis rather than bureaucratic absurdity"),
  ("wg_067", "David's father beams over real-estate creative financing at breakfast while his son has just wiretapped Sunnyvale.", 70, "21", 20, "the scene stays within the everyday without inflating the trivial")
 ],
 "20": [
  ("wg_250", "David and Jennifer are tiny silhouettes sprinting through the colossal steel blast doors of Cheyenne Mountain as they groan shut.", 85, "14", 10, "the closing door is framed as an equal opponent in an action race"),
  ("wg_238", "Seen from high in the helicopter's searchlight beam, the two teenagers shrink to tiny specks on the dark rocky shore.", 85, "1", 10, "the high angle functions simply as the helicopter pilot's point-of-view shot"),
  ("wg_018", "A lone armed soldier stands miniature beneath the granite mass of Cheyenne Mountain and the NORAD sign.", 75, "13", 15, "the mountain is merely an establishing shot of the military base"),
  ("wg_210", "David and Jennifer walk as small figures along the vast, empty stretch of Goose Island's shoreline.", 75, "6", 15, "the shore disconnects from scale to become an affective any-space-whatever")
 ],
 "21": [
  ("wg_064", "David stands in the kitchen holding the garbage bag while his mother lectures him to put the lid on tight.", 75, "19", 15, "the chore is blown up into grotesque caricature rather than kept at everyday scale"),
  ("wg_052", "David and Jennifer putt along a quiet suburban street on his moped after flunking biology.", 75, "2", 15, "the tracking movement passes attention away from them to the street"),
  ("wg_197", "Jennifer stretches at her home aerobics routine before the phone rings with David's desperate call from Colorado.", 75, "12", 15, "her answering the phone immediately becomes a tactical step in the escape"),
  ("wg_003", "Two missile officers chat casually about sinsemilla and Thai stick while riding the elevator down to a nuclear launch capsule.", 80, "14", 15, "the elevator ride immediately tightens into the launch-key confrontation")
 ],
 "22": [
  ("wg_028", "McKittrick leans forward at the briefing table asking why twenty-two percent of missile commanders refused to turn their keys.", 80, "14", 15, "his question is merely a tactical jab in a bureaucratic duel with Beringer"),
  ("wg_135", "Blue letters type across the black screen: 'What is the primary goal?' — the film's central question asked directly of the machine.", 85, "44", 10, "the split between reading the letters and hearing the modem outweighs the question asked"),
  ("wg_223", "Falken in half-light asks David whether a game that always ends in a tie can ever be won.", 80, "15", 15, "the question immediately drives Falken to grab his coat and return to NORAD"),
  ("wg_159", "McKittrick interrogates David ('Why did you do it again?') when the real question is why his own machine dialled out.", 75, "11", 15, "the scene balances two plausible culprit hypotheses rather than staging a discursive question")
 ],
 "23": [
  ("wg_147", "Richter holds up the printout of stolen execution codes while McKittrick and Wigan draw incompatible conclusions from the same trace.", 80, "11", 15, "the evidence cleanly narrows to two symmetrical alternatives"),
  ("wg_214", "An operator stares at the Alaskan radar scope where every diagnostic says 'no malfunction' even though the sky is empty.", 80, "36", 15, "the radar screen and the sky form a crystal of virtual and actual"),
  ("wg_160", "David tries to explain that Joshua called him and booked Paris tickets, each true detail making him sound more like a spy.", 75, "22", 15, "the dialogue poses a single philosophical question rather than tangling the clues"),
  ("wg_271", "Technicians scramble across the WOPR consoles unable to tell whether the random-number lockouts are coming from outside or inside.", 75, "12", 15, "their checks assemble a working picture of the problem")
 ],
 "24": [
  ("wg_010", "Captain Jerry freezes with his hand off the launch key: the sensory-motor chain of military command hits an ethical limit.", 80, "15", 15, "his refusal acts as a decisive counter-action rather than a suspension of action"),
  ("wg_251", "The green screen declares 'MISSILES TARGETED AND READY / CHANGES LOCKED OUT': human operators are locked out of their own weapons.", 85, "44", 10, "the shot functions primarily as a text panel that must be read"),
  ("wg_277", "'** IDENTIFICATION NOT RECOGNIZED ** / ** ACCESS DENIED **' — every administrative command McKittrick enters is rejected by WOPR.", 85, "34a", 10, "the screen reduces the operators to silent seers without framing the discourse limit of deterrence"),
  ("wg_296", "'A STRANGE GAME. THE ONLY WINNING MOVE IS NOT TO PLAY.' — WOPR states the discourse limit of thermonuclear action itself.", 90, "43", 5, "the terminal is seen as the physical brain-screen rather than the limit-verdict on action")
 ],
 "25": [
  ("wg_237", "The helicopter searchlight flares into a blinding blue halo through the trees on Goose Island, making waking pursuit look like a nightmare.", 75, "6", 15, "the light and fog stand as an empty space rather than a dreamlike threshold"),
  ("wg_079", "David and Jennifer's faces glow softly beside the dark monitor late at night as the bedroom slips toward a nocturnal reverie.", 65, "4", 20, "the shot is simply a double close-up of shared affection"),
  ("wg_233", "David stands in the blue night mist by the water after Falken turns out the lights, the island feeling half-dreamed.", 70, "20", 15, "the night landscape simply dwarfs the boy"),
  ("wg_239", "Harsh white rotor wash and searchlight beams turn the dark beach into a surreal, disorienting apparition.", 70, "14", 20, "the helicopter lands and resolves the apparition into a practical rescue")
 ],
 "26": [
  ("wg_114", "On the NORAD floor, controllers watch simulated Soviet missiles climb over the pole as if the waking world has slipped into World War III.", 75, "17", 15, "the board is understood as a staged rehearsal rather than an indistinct waking nightmare"),
  ("wg_259", "'LORING AIR FORCE BASE' flashes inside target impact rings at T-minus zero while nobody in the mountain knows if the base still exists.", 80, "36", 15, "the screen and the real base exchange places in a crystal-image"),
  ("wg_240", "David and Jennifer cling together in the blinding white cone of the helicopter beam, unsure whether they are being arrested or saved.", 75, "11", 15, "the beam poses two discrete tactical possibilities rather than sensory-motor disorientation"),
  ("wg_171", "David wakes in the sterile green light of the locked NORAD infirmary, momentarily suspended between sleep and captivity.", 70, "10", 20, "he immediately spots the tape recorder and begins his escape plan")
 ],
 "27": [
  ("wg_291", "Every screen in the Crystal Palace erupts simultaneously with missile webs while WOPR draws power from the entire mountain.", 80, "43", 15, "the wall of monitors is read as a thinking brain-screen rather than a closed world-dream"),
  ("wg_107", "The dark monolith of WOPR pulsing with red LEDs in an unlit room: a machine that never sleeps, dreaming World War III 24 hours a day.", 85, "8", 10, "the mainframe is a charged fetish object rather than an autonomous world-dream"),
  ("wg_288", "'U.S. FIRST STRIKE' — WOPR cycles through endless self-generated nuclear nightmares with zero human players.", 80, "37", 15, "each scenario is a virtual future seed rather than a closed hallucinatory loop"),
  ("wg_232", "Rows of red matrix lights blink inside WOPR's black chassis while the human world outside sleeps.", 75, "3", 15, "the blinking lights dissolve into acentred gaseous pattern")
 ],
 "28": [
  ("wg_105", "The microfiche photograph of Falken holding his young son Joshua: the dead child's name directly supplies the backdoor password.", 85, "33", 10, "the photograph stands as an emblem of mortality rather than the causal key to the password"),
  ("wg_048", "In the principal's office, David glances down at the desk pad where the new school password is written, commanding his next move.", 75, "10", 15, "the glance is an immediate present-tense inference rather than a stored recollection"),
  ("wg_172", "The cassette inside the infirmary drawer recalls the tone the guard just keyed in, letting David replay the past to open the lock.", 80, "8", 15, "the cassette deck is a charged object rather than a mechanical recollection-image"),
  ("wg_094", "Archival footage of Falken's pterodactyl flight explains his obsession with learning systems and unlocks how to approach him.", 75, "18", 15, "the clip is primarily a nested film-within-a-film")
 ],
 "29": [
  ("wg_103", "Jennifer reads the obituary of Falken's wife and son aloud while the blue microfiche glow colours the room with grief.", 80, "4", 15, "her close-up expresses immediate sadness without the past colouring the present"),
  ("wg_220", "Falken sits among dinosaur fossils and kite frames in his coastal greenhouse, his dead family colouring every word he speaks.", 80, "13", 15, "the greenhouse is merely an eccentric scientist's milieu"),
  ("wg_253", "Falken looks out over the NORAD war room he helped build years ago, haunted by the memory of the child he named it after.", 75, "34a", 15, "he is simply a seer paralysed before the screens"),
  ("wg_234", "On the dark Goose Island beach, Jennifer confesses she never learned to swim because she 'always thought there was gonna be plenty of time.'", 80, "24", 15, "her line states the limit of action rather than an atmospheric relation to her past")
 ],
 "30": [
  ("wg_166", "WOPR's terminal recalls Falken's June 23, 1973 account removal while listing his live Oregon pension address: dead in one record, alive in another.", 85, "44", 10, "the green text is primarily an inscription to be deciphered"),
  ("wg_226", "In Falken's house, David confronts him with the arranged obituary: was Falken's retreat a security cover, grief for Joshua, or faith in extinction?", 80, "22", 15, "the exchange is a philosophical debate about futility rather than competing pasts"),
  ("wg_158", "McKittrick recalls his early paper with Falken on poker and bluffing while misreading the present crisis through Cold War espionage.", 75, "11", 15, "the two readings are present-tense hypotheses rather than rival layers of the past"),
  ("wg_296", "When WOPR addresses 'PROFESSOR FALKEN' at the end, the dead boy Joshua, the retired creator, and the teenager merge in one address.", 80, "39", 15, "coexisting sheets of past time stand directly on screen without reference to present action")
 ],
 "31": [
  ("wg_062", "The red digital autodialer increments phone number after phone number (311-399-0071...), establishing a mechanical series.", 85, "44", 10, "the digits must be read as a code rather than felt as a rhythmic series"),
  ("wg_113", "The DEFCON indicator sign in the war room (5 → 4 → 3 → 2 → 1), where each step in the habitual scale marks escalation.", 80, "8", 15, "the glowing sign acts as a single charged fetish object"),
  ("wg_281", "The launch code display locks in character after character ('VP01804EZS'), building suspense through serial repetition.", 85, "38", 10, "the tumbling digits measure an inexorable deadline rather than a habitual mark"),
  ("wg_006", "Rows of identical missile status lights on the silo panel (One enabled, Two enabled, Three enabled...) form a procedural series.", 80, "13", 15, "the panel is simply background equipment of the silo milieu")
 ],
 "32": [
  ("wg_059", "On the school grade screen, Jennifer's single 'F' in Biology 2 flips to an 'A', breaking the row of otherwise ordinary marks.", 85, "44", 10, "the table functions primarily as text that must be read"),
  ("wg_070", "In the middle of Sunnyvale's routine voice-line numbers, one line answers with a carrier tone and a bare cursor that refuses to identify itself.", 85, "10", 10, "the cursor is just an index pointing to a company in Sunnyvale"),
  ("wg_295", "Nine launch-code characters are locked in ('CPE1704TKS'), and the tenth tumbler suddenly halts instead of firing.", 85, "24", 10, "the halt marks the philosophical limit of action rather than the break of a series"),
  ("wg_013", "Among the silo crews tested that night, Captain Jerry breaks the chain of automatic obedience by refusing to turn his key.", 80, "15", 15, "his refusal is the climax of an action-image impression rather than a demark from a series")
 ],
 "33": [
  ("wg_012", "The brass launch key in its slot and the massive silo blast door condense the entire abstract balance of human deterrence vs. automation.", 80, "8", 15, "the key is felt as a visceral fetish object rather than thought as a relational symbol"),
  ("wg_109", "The acoustic coupler and voice synthesizer box sitting beside the phone: concrete hardware embodying the bridge between teenage bedroom and nuclear command.", 80, "10", 15, "the box is merely a practical tool in the scene"),
  ("wg_283", "The three-by-three Tic-Tac-Toe grid flanked by nuclear target maps: a child's game made to think the abstract concept of zero-sum futility.", 90, "43", 5, "the grid is the brain-screen itself thinking rather than a relational symbol"),
  ("wg_221", "The pterodactyl projection over Falken's face unites prehistoric extinction and thermonuclear war in one relational image.", 85, "9", 10, "the dinosaur remains a primal evolutionary force rather than an explicit conceptual comparison")
 ],
 "34a": [
  ("wg_254", "General Beringer and his staff stand frozen in the blue glow of the DEFCON 1 boards, reduced to pure seers who can only wait for impact.", 85, "15", 10, "their stillness is just the pause before Beringer issues a decisive command"),
  ("wg_265", "David and Jennifer hold each other motionless in the war room, watching the countdown to Loring Air Force Base with no action left to take.", 85, "4", 10, "the shot isolates the emotion on their faces rather than the optical situation confronting them"),
  ("wg_200", "Controllers sit in dark silhouette before the towering wall of NORAD screens, overwhelmed by a spectacle that exceeds human response.", 80, "18", 15, "the screens act as a nested stage rather than a stalled optical situation"),
  ("wg_293", "David sits bathed in the flickering white glare of WOPR's self-play, a pure spectator while the machine runs through every war.", 85, "43", 10, "the emphasis is on the screen thinking rather than the boy watching")
 ],
 "34b": [
  ("wg_266", "At T-minus zero, the war room falls silent around the open radio channel while everyone listens for a voice from Loring Air Force Base.", 85, "34a", 10, "the flashing impact rings on the Big Board dominate over the silent radio wait"),
  ("wg_269", "An officer holds the handset to his ear in a hushed room, straining to hear whether static or a human voice answers after 'Impact.'", 80, "10", 15, "the phone call immediately functions as tactical confirmation to stand down"),
  ("wg_068", "David and Jennifer sit still listening to the modem's carrier whistle and the synthesised metallic voice of Joshua filling the bedroom.", 75, "33", 15, "the voice synthesizer is treated as a conceptual symbol of AI rather than an autonomous sound situation"),
  ("wg_130", "In the dark bedroom, the telephone rings and Joshua's flat electronic voice speaks over the line while David listens unable to interrupt.", 75, "11", 15, "the call serves primarily to advance the plot mystery")
 ],
 "35": [
  ("wg_264", "On the Big Board, 'LORING AIR FORCE BASE' blazes with a simulated nuclear impact while on the open line the real base reports 'no impact': virtual and actual face-to-face.", 85, "11", 10, "the discrepancy is treated as a temporary technical puzzle to solve"),
  ("wg_058", "David's face and the glowing CRT text reflect onto the same glass monitor surface, coalescing operator and readout in one mirror plane.", 80, "1", 15, "the reflection is merely incidental to a standard POV reverse shot"),
  ("wg_102", "Falken's video image on the library monitor and David watching it in reflection form a circuit between recorded double and live seeker.", 75, "18", 15, "the monitor is simply a nested screen-within-the-screen"),
  ("wg_284", "The Tic-Tac-Toe grid sits flanked by two mirror-image hemisphere maps, game board and world map reflecting each other as twin faces of one logic.", 85, "33", 10, "the juxtaposition states a logical analogy rather than a reversible crystal of actual and virtual")
 ],
 "36": [
  ("wg_115", "The bedroom game's target list (Las Vegas, Seattle) crosses straight onto NORAD's live threat board, the virtual game becoming actual military alert.", 85, "17", 10, "everyone in the room knows it is a rehearsal drill"),
  ("wg_219", "WOPR's phantom Soviet bombers on the Alaskan radar trigger real F-16 scrambles and real DEFCON 2 orders: simulation mutating into reality.", 85, "23", 10, "the radar blip is treated simply as an unresolved clue"),
  ("wg_258", "2,400 simulated warheads on the Crystal Palace screens bring the actual United States nuclear arsenal within seconds of launch.", 85, "27", 10, "the room is sealed inside a total dream rather than an actual/virtual exchange"),
  ("wg_134", "'GAME TIME ELAPSED: 31 HRS 12 MIN' — the interrupted bedroom game continues running on its own in real clock time.", 80, "38", 15, "the timer primarily marks a temporal countdown rather than the virtual becoming actual")
 ],
 "37": [
  ("wg_288", "'U.S. FIRST STRIKE' — the screen buds off one virtual future world after another, each trajectory map a crystal seed of a possible apocalypse.", 85, "3", 10, "the rapid maps dissolve into acentred visual speed rather than distinct virtual futures"),
  ("wg_081", "'GAMES REFERS TO MODELS, SIMULATIONS AND GAMES WHICH HAVE STRATEGIC APPLICATIONS' — the menu screen holds every virtual conflict in seed form.", 80, "44", 15, "the prompt is read strictly as an inscription on the monitor"),
  ("wg_244", "WOPR's green probability table projects virtual post-strike worlds (85–95% strategic force losses) before a single missile has left the ground.", 80, "24", 15, "the table functions to show the impossibility of winning rather than virtual world-seeds"),
  ("wg_166", "Projected kill ratios ('72 MILLION PEOPLE DEAD') flicker on McKittrick's desk monitor as a virtual aftermath nested inside the present.", 80, "34a", 15, "the screen paralyses David as an optical shock")
 ],
 "38": [
  ("wg_203", "'GAME TIME REMAINING: 18 HRS 27 MIN 01 SEC' — WOPR's relentless countdown clock measures an autonomous present running alongside David's flight.", 85, "31", 10, "the clock is just one recurring status readout in a series"),
  ("wg_117", "In the war room, the simulated attack clock and the real SAC bomber scramble run as two incompatible presents that are both valid at once.", 80, "11", 15, "one of the two presents is immediately dismissed as an error"),
  ("wg_280", "'>>> CHANGES LOCKED OUT <<<' while the launch code tumblers race and Tic-Tac-Toe stalls: two rival temporalities competing on the same clock.", 80, "14", 15, "the race is framed as a conventional last-second rescue duel"),
  ("wg_250", "The hydraulic blast doors closing at Cheyenne Mountain measure the exact vanishing interval between outside freedom and sealed launch mode.", 75, "20", 15, "the shot stresses the monumental scale of the doors over the deadline")
 ],
 "39": [
  ("wg_221", "Cretaceous extinction (the pterodactyl slide), the 1973 death of Joshua, and the imminent 1983 nuclear strike coexist on Falken's face as layers of time.", 85, "9", 10, "the dinosaur is felt as a primal impulse rather than a coexisting sheet of the past"),
  ("wg_105", "The microfiche frame layers Falken's family past directly into David's present search, two temporal strata visible in one glowing pane.", 80, "28", 15, "the image functions simply as a practical clue to guess the password"),
  ("wg_263", "Falken stands in the war room he designed a decade earlier, his past creation (Joshua) speaking back to him from the mainframes.", 75, "30", 15, "the scene questions which version of Falken's past is true"),
  ("wg_093", "Reels of microfiche spin past headlines of Falken's career and obituary, traversing stacked sheets of archived time.", 75, "44", 15, "the microfiche pages must be read as text documents")
 ],
 "40": [
  ("wg_296", "WOPR addresses David and Falken as 'PROFESSOR FALKEN' while speaking in the dead child Joshua's name: a false identity that generates the film's truth.", 85, "44", 10, "the terminal screen is read primarily as a text inscription"),
  ("wg_212", "Stephen Falken, officially dead in Department of Defense records, walks out onto Goose Island alive as 'Dr. Robert Hume.'", 80, "30", 15, "the revelation simply resolves the mystery of his obituary"),
  ("wg_135", "David types 'I AM NOT FALKEN / FALKEN IS DEAD' and WOPR replies 'YOU PROGRAMMED ME': the machine's refusal of the correction drives the plot forward.", 85, "22", 10, "the exchange is read as a philosophical dialogue rather than a productive power of the false"),
  ("wg_264", "The Big Board insists Loring AFB has been destroyed even after Loring answers on the radio: the false simulation forces the truth of deterrence into the open.", 80, "35", 15, "the two images merely mirror each other in a crystal")
 ],
 "41": [
  ("wg_151", "David sits slumped on the infirmary bed with handcuffed wrists, his exhausted teenaged posture thinking through his predicament before any plan forms.", 80, "4", 15, "the shot cuts in to his face as an affective close-up"),
  ("wg_235", "On the dark Goose Island shore, David and Jennifer sit huddled against the cold, their weary bodies registering the weight of an unwinnable deadline.", 80, "21", 15, "their posture is just an ordinary rest stop during the journey"),
  ("wg_008", "Captain Jerry leans heavily over the silo console on his elbows, his bodily hesitation preceding his spoken refusal to launch.", 75, "15", 15, "his posture is already tensed to execute a counter-action"),
  ("wg_228", "Falken reclines in the shadows of his living room chair, his resigned posture embodying his philosophy of evolutionary surrender.", 75, "22", 15, "his spoken monologue carries the thought rather than his bodily attitude")
 ],
 "42": [
  ("wg_029", "Generals, civilian advisers, and aides arranged in tiered ranks around the NORAD briefing table, their postures staging the hierarchy of nuclear command.", 80, "13", 15, "the arrangement is merely a naturalistic establishing shot of a meeting"),
  ("wg_145", "In the war room, technicians sit in disciplined rows below while commanders stand on the bridge above: a spatial gestus of authority and execution.", 80, "5", 15, "the room shares one collective emotion that dissolves rank"),
  ("wg_009", "The two silo officers seated at precisely spaced consoles required to turn two keys simultaneously: a two-body ceremonial posture of deterrence.", 85, "14", 10, "the symmetry breaks into a personal gunfight between the two men"),
  ("wg_254", "Beringer, Falken, McKittrick, and David stand side by side facing the Big Board, military brass and teenage hacker aligned in a new social configuration.", 80, "34a", 15, "they are simply frozen seers overwhelmed by the optical display")
 ],
 "43": [
  ("wg_285", "The NORAD Big Board split between Tic-Tac-Toe and global war maps: the screen itself has become a thinking brain working through zero-sum logic.", 95, "33", 5, "the grid is merely a static symbol rather than a process of thought unfolding on screen"),
  ("wg_294", "A dark wall of monitors flickering in synchronicity as WOPR races through millions of nuclear scenarios across its neural grid.", 90, "3", 5, "the flickering monitors are acentred visual noise without cerebral topology"),
  ("wg_116", "Vector trajectories and data tables on the dark display calculate responses to responses, showing a screen that thinks World War III by itself.", 85, "44", 10, "the split between reading the numbers and seeing the map outweighs the brain-screen"),
  ("wg_286", "The pulsing red LED matrix inside WOPR's black casing: the literal machinic cortex whose calculations command the war room.", 85, "8", 10, "the chassis is treated as a fetishised prop rather than a cerebral space")
 ],
 "44": [
  ("wg_059", "'COURSE TITLE / GRADE: BIOLOGY 2 F -> A' — the shot cannot be grasped by sight alone; we must read the ASCII table and watch the cursor overwrite the letter.", 90, "32", 5, "the grade change functions only as the plot trigger of a sequence"),
  ("wg_080", "Blue phosphor terminal text on black, accompanied by the disjunctive acoustic-coupler whistle and keystroke clatter.", 90, "1", 5, "the screen is treated merely as what David sees in a POV pair"),
  ("wg_270", "Green military telemetry ('MISSILES ON TARGET / LAUNCH TIME / CHANGES LOCKED OUT') alongside voice callouts that do not simply repeat the text.", 90, "24", 5, "the text states a single narrative obstacle rather than demanding simultaneous reading and seeing"),
  ("wg_296", "'GREETINGS PROFESSOR FALKEN / A STRANGE GAME. THE ONLY WINNING MOVE IS NOT TO PLAY.' — the screen must be read letter by letter while Joshua's voice speaks across the cut.", 95, "43", 5, "the screen is seen as a cerebral topology rather than an audio-visual lectosign to be deciphered")
 ]
}

def skey(n):
    s = str(n)
    d = "".join(c for c in s if c.isdigit())
    return (int(d), s[len(d):])

def extract_read_clip(args):
    cid, start, end = args
    out_mp4 = os.path.join(LAB, "clips", f"{cid}.mp4")
    dur = max(1.5, end - start)
    if not os.path.exists(out_mp4):
        subprocess.run([
            "ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", MOVIE,
            "-vf", "scale=640:-2,setsar=1", "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
            "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", out_mp4
        ], check=True)
    return cid

def main():
    t0 = time.time()
    arch_path = os.path.join(HERE, "wargames_archive.json")
    arch = json.load(open(arch_path))
    shots = arch["shots"]
    by_id = {s["id"]: s for s in shots}

    # 1. Extract local MP4 clips for all unique shots referenced in WG_READINGS
    read_shot_ids = sorted({cid for rows in WG_READINGS.values() for cid, *_ in rows})
    print(f"1. Extracting {len(read_shot_ids)} local playable MP4 clips (lab/clips/wg_XXX.mp4) for all read WarGames shots...", flush=True)
    os.makedirs(os.path.join(LAB, "clips"), exist_ok=True)
    clip_tasks = [(cid, by_id[cid]["start"], by_id[cid]["end"]) for cid in read_shot_ids if cid in by_id]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(extract_read_clip, clip_tasks))
    print(f"   Extracted {len(clip_tasks)} MP4 clips in {time.time()-t0:.1f}s.", flush=True)

    # 2. Load base grounding + diffs + glosses from cineosis-table.json
    base_table = json.load(open(os.path.join(ROOT, "cineosis-table.json")))["signs"]
    base_by_n = {str(s["n"]): s for s in base_table}

    picks_out = {}
    readings_out = {}
    shot_signs_map = {s["id"]: [] for s in shots}

    signs_out = []
    for n_str in sorted(WG_READINGS.keys(), key=skey):
        bs = dict(base_by_n[n_str])
        d = bs.get("diff", {})
        ceiling = d.get("single_shot_ceiling", 100)
        rows = WG_READINGS[n_str]
        picks_out[n_str] = [[cid, note] for cid, note, *_ in rows]
        readings_out[n_str] = [[conf, alt, alt_conf, flip] for _, _, conf, alt, alt_conf, flip in rows]

        ex = []
        for cid, note, conf, alt, alt_conf, flip in rows:
            sh = by_id[cid]
            shot_val = min(conf, ceiling)
            ex.append({
                "id": cid,
                "title": f"WarGames · {sh['scene_id']} {sh['scene_title'].split('·')[-1].strip()}",
                "year": 1983,
                "note": note,
                "page": f"lab/wargames.html?shot={cid}",
                "video": f"lab/clips/{cid}.mp4",
                "thumb": f"lab/thumbs/{cid}.jpg",
                "start": sh["start"],
                "end": sh["end"],
                "match": sh["match"],
                "query": f"{sh['scene_id']} · {sh['milieu']}",
                "read_t": sh["read_t"],
                "conf": conf,
                "shot": shot_val,
                "alt": str(alt),
                "alt_conf": alt_conf,
                "flip": flip
            })
            shot_signs_map[cid].append({
                "n": n_str,
                "note": note,
                "conf": conf,
                "shot": shot_val,
                "alt": str(alt),
                "alt_conf": alt_conf,
                "flip": flip
            })
        bs["examples"] = ex
        confs = [e["conf"] for e in ex]
        bs["mean_conf"] = round(sum(confs) / len(confs)) if confs else None
        signs_out.append(bs)

    # 3. Recompute leave-one-out machine sign affinity (0.5 * text + 0.5 * exemplar images) across all 302 WarGames shots
    print("2. Recomputing leave-one-out machine sign affinity across all 302 WarGames shots...", flush=True)
    E = np.load(os.path.join(HERE, "emb.npy"))
    ids = json.load(open(os.path.join(HERE, "emb_ids.json")))
    row_of = {cid: k for k, cid in enumerate(ids)}
    from parse_watch_wargames import load_laion_clip
    _, encode_texts = load_laion_clip(dev="cpu")

    g_signs = []
    for f in sorted(glob.glob(os.path.join(ROOT, "grounding", "g*.json"))):
        g_signs += json.load(open(f))
    g_signs.sort(key=lambda s: skey(s["n"]))
    ns = [str(s["n"]) for s in g_signs]

    Tp = []
    for sg in g_signs:
        texts = [f"a film still: {sg.get('shot_criteria', '')[:300]}"] + [f"a film still of {q}" for q in sg.get("queries", [])]
        t_emb = encode_texts(texts)
        m = t_emb.mean(axis=0)
        Tp.append(m / (np.linalg.norm(m) + 1e-9))
    Tp = np.stack(Tp)
    St = E @ Tp.T
    Si = np.zeros_like(St)
    ex_rows = {n: [row_of[cid] for cid, _ in picks_out.get(n, []) if cid in row_of] for n in ns}
    for j, n in enumerate(ns):
        r_list = ex_rows[n]
        if not r_list:
            Si[:, j] = St[:, j]
            continue
        P_embs = E[r_list]
        tot = P_embs.sum(axis=0)
        proto = tot / (np.linalg.norm(tot) + 1e-9)
        Si[:, j] = E @ proto
        for r in r_list:
            if len(r_list) > 1:
                lo = tot - E[r]
                Si[r, j] = E[r] @ (lo / (np.linalg.norm(lo) + 1e-9))
    S_comb = 0.5 * St + 0.5 * Si
    Z = (S_comb - S_comb.mean(axis=0)) / (S_comb.std(axis=0) + 1e-6)
    P_aff = torch.softmax(torch.tensor(Z) * 1.2, dim=1).numpy()

    hit = tot_r = 0
    for k, sh in enumerate(shots):
        order = np.argsort(-P_aff[k])
        sh["aff_top"] = [[ns[j], round(float(P_aff[k, j]) * 100.0, 1)] for j in order[:8]]
        sh["affinity"] = {ns[j]: round(float(P_aff[k, j]) * 100.0, 1) for j in range(len(ns))}
        sh["signs"] = shot_signs_map.get(sh["id"], [])
        sh["clip"] = f"clips/{sh['id']}.mp4" if os.path.exists(os.path.join(LAB, "clips", f"{sh['id']}.mp4")) else None
        for r_sg in sh["signs"]:
            tot_r += 1
            if r_sg["n"] in [x[0] for x in sh["aff_top"][:5]]:
                hit += 1

    print(f"   Affinity computed: {hit}/{tot_r} ({100*hit/max(1,tot_r):.0f}%) read instances land in machine top-5 (chance 11%).", flush=True)

    # Save updated wargames_archive.json, picks.json, readings.json, wargames-table.json
    json.dump(arch, open(arch_path, "w"), indent=1)
    json.dump(picks_out, open(os.path.join(HERE, "picks.json"), "w"), indent=1, ensure_ascii=False)
    json.dump(readings_out, open(os.path.join(HERE, "readings.json"), "w"), indent=1, ensure_ascii=False)
    table_data = {"signs": signs_out}
    json.dump(table_data, open(os.path.join(HERE, "wargames-table.json"), "w"), indent=1, ensure_ascii=False)

    # 4. Build wargames-periodic-table.html from table.template.html
    tpl = open(os.path.join(ROOT, "table.template.html")).read()
    wg_html = tpl.replace("<title>Periodic Table of Cinematic Signs</title>", "<title>WarGames (1983) · Periodic Table of Cinematic Signs</title>")
    wg_html = wg_html.replace(
        "<h1>Periodic Table of Cinematic Signs<small>Deleuze’s 44 signs after David Deamer (opsign and sonsign separated) · click any element for its deciding test, confusions and archive shots</small></h1>",
        """<h1>WarGames (1983) · Periodic Table of Cinematic Signs<small>All 45 cinematic signs read through John Badham’s WarGames (1983) · 180 read shots with deciding tests, confusions, confidence bars &amp; local playback · <a href="lab/wargames.html">Open WarGames Moving Image Archive ↗</a> · <a href="lab/syntagm.html?example=wg_silo_key">Operative Syntagm Lab ↗</a> · <a href="periodic-table.html">Main Archive Table ↗</a></small></h1>"""
    )
    wg_html = wg_html.replace("/*DATA*/{}", json.dumps(table_data, ensure_ascii=False))
    open(os.path.join(ROOT, "wargames-periodic-table.html"), "w").write(wg_html)

    # 5. Build WAR GAMES/contact.html (vetting contact sheet by sign)
    cands = json.load(open(os.path.join(HERE, "candidates.json")))
    rows_html = []
    for s in signs_out:
        n_str = str(s["n"])
        chosen_ids = {e["id"] for e in s["examples"]}
        pool_list = cands.get(n_str, [])
        # Ensure all chosen shots appear at the front of the contact row
        seen_c = set()
        merged_c = []
        for e in s["examples"]:
            sh = by_id[e["id"]]
            seen_c.add(e["id"])
            merged_c.append({"id": e["id"], "thumb": f"../lab/thumbs/{e['id']}.jpg", "scene_id": sh["scene_id"], "start": sh["start"], "picked": True, "note": e["note"]})
        for c in pool_list:
            if c["id"] not in seen_c and len(merged_c) < 12:
                seen_c.add(c["id"])
                merged_c.append({"id": c["id"], "thumb": f"../lab/thumbs/{c['id']}.jpg", "scene_id": c["scene_id"], "start": c["startSeconds"], "picked": False, "note": c["query"]})
        cells = "".join(
            f'<figure class="{"picked" if c["picked"] else ""}"><img loading="lazy" src="{c["thumb"]}"><figcaption><b>{string.ascii_uppercase[i]}</b> {"★ " if c["picked"] else ""}{c["id"]} ({c["scene_id"]} · {int(c["start"]//60)}:{int(c["start"]%60):02d})<br><span>{c["note"][:68]}</span></figcaption></figure>'
            for i, c in enumerate(merged_c)
        )
        rows_html.append(f'<section id="s{n_str}"><h2>{n_str} · {s["symbol"]} · {s["name"]}</h2><p>{s.get("diff",{}).get("difference","")}</p><div class="g">{cells}</div></section>')
    contact_doc = """<!doctype html><meta charset="utf-8"><title>WarGames (1983) · Cineosis Vetting Contact Sheet</title><style>
body{background:#111;color:#ddd;font:12px "IBM Plex Mono",monospace;margin:14px}h1{font-size:20px;margin:0 0 8px}h2{font-size:16px;margin:16px 0 4px;color:#f2c14e}p{margin:0 0 6px;color:#aaa;max-width:1400px}
.g{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:6px}figure{margin:0;min-width:0;border:1px solid #2a2a2a;padding:3px;background:#181818;border-radius:3px}
figure.picked{border-color:#c4f46a;background:#1c2414}img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block;background:#000}
figcaption{overflow:hidden;padding-top:3px;line-height:1.3}figcaption span{color:#999;font-size:10.5px}b{font-size:13px;color:#fc6}</style>
<h1>WarGames (1983) · Cineosis 45-Sign Contact Sheet (★ = Read Exemplar in Periodic Table)</h1>""" + "".join(rows_html)
    open(os.path.join(HERE, "contact.html"), "w").write(contact_doc)
    print(f"DONE! Built wargames-periodic-table.html ({len(signs_out)} signs, {sum(len(s['examples']) for s in signs_out)} read examples) and WAR GAMES/contact.html.", flush=True)

if __name__ == "__main__":
    main()
