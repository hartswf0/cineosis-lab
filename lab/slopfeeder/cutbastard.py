"""CUTBASTARD-1 for the eight Liturgy songs: each song's lyric read for what it does (the readings in the chapter notes: liberation vs submission,
cleanse vs erase, render = make AND be processed, communion = take in, confession = admit dependence), carved into PHASES at the song's own
vocal phrases (Whisper word times where the lyric is English, voiced stretches where it is Amharic / Icelandic / Greek / invented), and each
phase cut into 6-12 s PATCHES on the beats (patch law). For every patch: the line, what it means, the pressure shift, the trigger, the
syntagma, how many beats a shot holds, and the shots it asks for (CLIP text against every card) ranked; where nothing in the atlas answers
well, the patch is flagged to GENERATE with a master prompt built on the bible's LOCK text.
Writes slopfeeder/cutbastard.json (Blacktop's CUTBASTARD films read it) and slopfeeder/cutbastard.md (Matrices O, A, F).
usage: .venv/bin/python slopfeeder/cutbastard.py"""
import json, os
import numpy as np, torch, open_clip
D = os.path.dirname(os.path.abspath(__file__))
L, LA, DR, KI, SC, RE, TI, AF, FL = 'THE LANDING', 'THE LANDING', 'THE DRILL LINE', 'THE KITCHEN', 'THE SCREEN', 'THE RENDER', 'THE TIDE', 'THE AFTERMATH', 'THE FLEET'
# ---- the readings, as phases: (t0, t1, name, line, meaning, pressure, syntagma, world, beats per shot, [what the shots must show], flags)
SONGS = {
 "26": dict(idea="Clay creatures led through fire become one army; the chant holds liberation and submission at once, and ends by swallowing the cooled iron.",
   look="newsreel", rules=["the whole-army answers are ONE wide that grows wider each time (accumulative)", "the bucket overturn lands on the stomp HA, pound-locked", "liberation vs submission: never let the leader's face be a hero shot; the crew answers"],
   phases=[(0, 33.6, "DRONE · LEAD THE CLAY", "የጭቃውን ፍጥረታት በእሳቱ ምራ — lead the clay creatures through the fire; as the ash rises the smoke leads", "the raw material is people of mud; a masked voice takes charge", "stillness → led", "continuous", L, 8, ["hands and bodies covered in wet mud on a grey beach at dawn", "a masked figure in a black hood standing still in smoke", "smoke drifting over wet sand"], []),
           (33.6, 57, "OUT OF THE FIRE · ON THE IRON", "ከእሳቱ ወጥተህ በብረቱ ላይ — out of the fire, onto the iron! on the iron!", "the ordeal begins: heat, then metal", "led → worked", "alternating", DR, 2, ["workers pounding drills into sand", "sparks and fire on a beach", "iron machinery striking"], ["pound"]),
           (57, 73, "CHEST · BUCKET · HA", "ባልዲውን ገልብጥ አፉን በጭቃ — turn the bucket over, its mouth with mud — HA!", "the crew's own gesture: pails slammed mouth-down (word-free: the body speaks)", "worked → acting together", "accumulative", DR, 2, ["orange buckets turned upside down slammed into wet sand", "a row of upturned orange pails on a beach", "people stamping in mud"], ["pound", "pails"]),
           (73, 97, "GUARD YOUR BREATH FROM THE LAW", "እስትንፋስህን ከሕጉ ጠብቅ — protect your breath from the law!", "something living kept back from a rule (not obeying it)", "acting → withholding", "alternating", SC, 4, ["a person holding their breath, face close up", "masked critics in a row staring", "a glowing screen of rules and text"], []),
           (97, 126, "LEAVE THE EMPTY WORLD · ERASE THE RECORD · TEAR THE WALL", "ከባዶው ዓለም ውጣ… መዝገቡን ሰርዝ… ግድግዳውን አፍርስ! — come out of the empty world, erase the record, open it, tear down the wall", "the old order's record and wall come down", "withholding → breaking", "accumulative", AF, 2, ["papers and ledgers burning", "a brick wall collapsing", "a computer screen going blank", "people breaking through a barrier"], []),
           (126, 156, "BURN · BURN IN THE FIRE", "ተቃጠል! ተቃጠል በእሳቱ! — burn! be burned in the fire! (circular, unceasing)", "the participants are inside the fire now, not feeding it", "breaking → enduring", "continuous", LA, 2, ["figures standing inside fire and smoke", "a beach burning at night", "fire surrounding a crowd"], ["pound"]),
           (156, 181, "WHO CROSSES · WHO TAKES THE LAND · WHO RECEIVES THE FIRE — THE WHOLE ARMY", "ቦዩን ማን ይሻገራል? መላው ሠራዊት! — who will cross? the whole army! (×3)", "one answer for three claims: the collective becomes the agent", "enduring → claiming", "accumulative", FL, 4, ["a huge crowd marching across a beach", "an army crossing water", "a wide shot of many people moving together"], []),
           (181, 194.5, "THE IRON HAS COOLED · SWALLOW IT", "ብረቱ ቀዘቀዘ ዋጠው — the iron has cooled; swallow it. HA! (long drone)", "the ordeal goes inside; quiet, uneasy", "claiming → internalised", "continuous", TI, 8, ["a masked cook eating alone", "the tide washing over circles drawn in sand", "a still beach after battle, smoke clearing"], [])]),
 "06": dict(bscale=3, idea="A freedom chant on the 'Oh, Freedom!' refrain: the crew that carried the load claims the free ground. Dignity, not spectacle; break the iron, free the bone.",
   look="raw", rules=["dignity: no comic slop or skull-cook imagery under the refrain; the refrain gets people, hands, water, earth, morning", "the shot that 'breaks' is iron or a barrier, never a body", "the leader calls, the crew answers in pictures of many hands; no single hero", "word-free gaps belong to breath and work, not to jokes"],
   phases=[(0, 11, "HUM", "(Mmmmm-hmmmm-uuuuum)", "breath before words", "silence → breath", "continuous", TI, 8, ["early morning light over wet fields", "a quiet river at dawn"], ["clean"]),
           (11, 46, "LEAD THE WEARY-BORN · STRIKE THE IRON OFF THE BONE · HOLD YOUR BREATH · TURN THE BUCKET", "Lead the weary-born children through the fire / Strike the iron off the bone / Hold your breath against the master's word / Turn that bucket upside down", "burdened people led through danger; restraint struck off", "burden → resolve", "alternating", DR, 4, ["tired workers walking in a line at dusk", "hands breaking a chain", "a blacksmith striking iron", "an upturned bucket on the ground"], ["clean"]),
           (46, 66, "CHORUS: NO MORE MOANIN'", "No more moanin' … And before I'd be a slave / I'll be buried in my grave / And go home to my Lord and be free", "refusal: the master's claim is not the last word", "resolve → refusal", "accumulative", FL, 4, ["many people singing together", "faces turned up to the sky", "people walking together toward the horizon"], ["clean", "archive"]),
           (66, 77, "FREE BY AND BY", "Oh-oh oh-oh / Free by and by", "a promised later", "refusal → hope", "continuous", TI, 8, ["sunrise over water", "a road leading into open land"], ["clean"]),
           (77, 95, "WHO GONNA WADE · THE WHOLE CREW · HANDS IN THE CLAY", "Who gonna wade that muddy water (The whole crew) / Who gonna walk to the free ground / Who bears the heat … / Hands in the clay till the morning come", "the people who bore the work claim the crossing", "hope → crossing together", "accumulative", L, 4, ["people wading through muddy water together", "workers walking across open ground", "hands working in clay"], ["clean"]),
           (95, 120, "CHORUS", "No more moanin' … go home to my Lord and be free", "the refusal repeated, stronger", "crossing → refusal", "accumulative", FL, 4, ["a crowd walking together across a beach", "people standing up together", "many hands raised"], ["clean", "archive"]),
           (120, 143, "BURN ON THROUGH THE NIGHT · ROLL THAT STONE FROM THE DOOR", "Burn on through the night (Through the night) / Roll that stone from the door (From the door)", "endurance through night; the stone rolled away — emergence", "night → opening", "alternating", AF, 2, ["a fire burning through the night", "a heavy stone being rolled away", "a door opening onto light"], ["clean"]),
           (143, 172, "CHORUS · THE HAMMER DROPS · STAND UP", "No more moanin' … be free / The hammer drops. Stand up.", "the tool falls; the person rises", "opening → standing", "accumulative", FL, 4, ["a hammer dropped on the ground", "a person standing up straight", "a crowd at dawn"], ["clean", "archive"]),
           (172, 185.4, "FADING HUM", "(Huuuummmmm-mmmmm-ahhhh)", "breath continues after the commands", "standing → breath", "continuous", TI, 8, ["calm water at morning", "an empty field in soft light"], ["clean"])]),
 "07": dict(idea="Cleanse the memory: an outcast company remakes its remembrance through fire, breaks the gate, and swallows the cooled iron. Cleansing is not erasing.",
   look="newsreel", rules=["the archive IS the memory: old film carries the remembered; the pickups are the cleansing", "long held shots (the song is mostly drone): 8 beats", "the cleansing is water and tide, not fire alone", "one mouth: the chorus is shown as one face at a time"],
   phases=[(0, 19.4, "BARKADRYMR · DRONE", "(Mmmmmmmmm-aaaaaaah-uuummmmmmm)", "a low drone, before memory is touched", "silence → presence", "continuous", TI, 8, ["old black and white film of the sea", "fog over water"], ["archive"]),
           (19.4, 45, "LEAD THE CLAY-BORN THROUGH THE FIRE · ONTO THE IRON", "Leiðið leirborna gegnum eldinn! … Ór eldinum, beint á járnit!", "the clay-born led through fire to iron", "presence → ordeal", "alternating", DR, 8, ["old film of a blacksmith forge", "figures walking through smoke", "molten iron poured"], []),
           (45, 70, "HOLD THE BREATH AGAINST THE LAW · TURN THE BUCKET · RISE FROM THE VOID", "Haldið andanum gegn lögmálinu! … Snúið fötunni! … Rísið ór tóminu!", "breath held against the law; the bucket's mouth into clay; rising out of emptiness", "ordeal → resistance", "alternating", SC, 8, ["a masked face in darkness", "an orange bucket turned over into mud", "a figure rising out of fog"], []),
           (70, 96, "CLEANSE THE MEMORY · BREAK THE GATE · BREAK DOWN THE WALL", "HREINSIÐ MINNIT! … Brjótið grindina! BRJÓTIÐ NIÐR VEGGINN!", "memory washed, not deleted: the tide over old film", "resistance → cleansing", "insertive", TI, 8, ["waves washing away marks in the sand", "old archival footage of a crowd fading", "a gate broken open"], ["archive"]),
           (96, 121, "BURN IN THE FIRE · WHO CROSSES · THE WHOLE DAMNED TROOP", "Brennið í eldinum! … Hver gengr yfir rásina? ALLR HANN FJANDANS FLOKKR!", "the outcast company answers as one", "cleansing → claiming", "accumulative", FL, 4, ["a company of people crossing a channel", "a marching crowd", "fire at night"], []),
           (121, 147.4, "THE IRON COOLED · SWALLOW", "Járnit kólnaði. Svelgið. HÁ! (drone dies)", "the ordeal taken inside; the memory remade", "claiming → silence", "continuous", TI, 8, ["a still beach at dusk", "an old film fading to white"], ["archive"])]),
 "09": dict(idea="The Recursion: a crew names what made it (coal, slop, the iron hand), purges its cache into four beats of nothing, and returns as the whole crew. The end is the beginning transformed.",
   look="mixed", rules=["recursion: the last phase calls back the first phase's images (siblings, never the same shot)", "the purge is four beats of black, hard cut in and out", "who guards the small: show the small being guarded", "the crew is the subject; KALLAH stays masked and off-centre"],
   phases=[(0, 26, "PRAN-AL-NUL · BREATH · LEAD THEM DOWN · TEETH TO THE MUD", "Dimala-sh (lead them down) … E-l isnii-dh (into the fire) … Drak-al-silt (teeth to the mud)", "breath first, then descent", "silence → descent", "continuous", TI, 4, ["people breathing in a dark vault", "a line of figures descending into mud", "a mouth close to wet mud"], []),
           (26, 68, "AL-DIMBI-ZIKR · WHO GAVE YOU BONE? THE COAL · WEIGHT? THE SLOP · WHO GUARDS THE SMALL? THE IRON HAND", "Bellaha rudhi a-l koda-sh (we bind the breath against the code) / Who gave you bone? THE COAL / Who gave you weight? THE SLOP / Who guards the small? THE IRON HAND", "a creed of origins: fuel, residue, protection", "descent → naming", "alternating", KI, 4, ["coal burning red", "a cook ladling thick slop", "a large gloved hand protecting a small bucket", "a miniature bucket emerging from sand"], []),
           (68, 101, "KHAZ-AL-NUL · THE SKY TURNS BLANK", "Khaz-al-Nul (the sky turns blank)", "the world's picture goes white", "naming → blank", "insertive", SC, 4, ["a white overexposed sky", "a computer screen going white", "a flat featureless horizon"], []),
           (101, 105, "KHAT-AL-CACHE · PURGE (FOUR BEATS OF NOTHING)", "KHAT-AL-CACHE! (PURGE!)", "absolute silence: the cache is cleared, not the maker", "blank → void", "insertive", SC, 4, [], ["null"]),
           (105, 125, "RU CHESHAH · BREAK THE FRAME · E-L ISNII-DH (CIRCULAR)", "Ru cheshah (break the frame) … KHAT-AL-DOM! … E-L ISNII-DH!", "the frame breaks; the chant circles back in", "void → return", "continuous", LA, 2, ["a frame shattering", "a crowd stomping in a circle", "fire at the centre of a ring"], ["pound"]),
           (125, 210, "KREW-AL-GHAL · WHO WALKS THE DRAIN · WHO BUYS THE MUD · WHO CLAIMS THE FIRE — THE WHOLE CREW", "Mina al-drain-ii krew-al-ghal? KREW-AL-GHAL! (×3)", "the answer is already inside the question: the crew names itself", "return → whole", "accumulative", FL, 4, ["workers walking along a drain", "a crowd standing in mud", "the whole crew wide on a beach"], ["recur"]),
           (210, 228.4, "THE BLADE RESTS · SWALLOW · DRONE", "Ru al-dimbi. Kul-zha. (The blade rests. Swallow.) HA!", "incorporation; the loop closes on its opening", "whole → breath", "continuous", TI, 8, ["a spatula resting on a griddle", "people breathing in a dark vault"], ["recur"])]),
 "13": dict(idea="The Communion (Ritual of the Ash and Silt, 1): the short rite of the shared meal — the cook serves, the crew eats, the iron is swallowed.",
   look="newsreel", rules=["one meal, one table: the kitchen is the altar", "the near-silence at 12-18 s is a held breath, not a cut-to-black", "close-ups of mouths and hands, not wides"],
   phases=[(0, 12.4, "DRONE · THE TABLE", "(hum)", "the meal is prepared", "silence → preparation", "continuous", KI, 8, ["a griddle heating", "onions sizzling on iron"], []),
           (12.4, 18, "HELD BREATH", "(near silence)", "the pause before the serving", "preparation → pause", "insertive", KI, 8, ["a masked cook standing still", "steam rising in silence"], []),
           (18, 81, "THE SERVING · THE CREW EATS", "(call and response)", "the communion: taking in together", "pause → shared eating", "alternating", KI, 4, ["a cook serving burgers to a line of workers", "workers eating together", "hands passing food along a line"], []),
           (81, 88.3, "SWALLOW", "(final hum)", "it is inside them", "eating → swallowed", "continuous", KI, 8, ["a close-up of someone swallowing", "an empty plate"], [])]),
 "14": dict(idea="The Render Fleet: the same rite under a new title: a fleet that renders (makes, processes) and is itself rendered. Mostly wordless: cut by frame and colour; the crew and the machine rhyme.",
   look="mixed", rules=["match cuts by FRAME between workers and machines: the crew is producer and product", "the four flat shapes offshore are the fleet that renders; ships in the archive answer them", "the low-energy hole at 75 s is the purge: blank, then return"],
   phases=[(0, 26.4, "DRONE · THE FLEET OFFSHORE", "(Mmmmmmmmm-aaaaaaah-uuummmmmmm)", "the render fleet waits on the horizon", "silence → watched", "continuous", FL, 8, ["four flat cartoon shapes standing in the sea like warships", "a fleet of ships on the horizon"], []),
           (26.4, 59.4, "THE LITANY · COAL · SLOP · IRON HAND", "Who gave you bone? THE COAL / weight? THE SLOP / who guards the small? THE IRON HAND", "what the fleet runs on: fuel, residue, protection", "watched → worked", "alternating", RE, 4, ["a factory machine stamping metal", "coal shovelled into a furnace", "workers pumping drills in rhythm"], ["pound"]),
           (59.4, 78.8, "THE SKY TURNS BLANK · PURGE", "Khaz-al-Nul … KHAT-AL-CACHE!", "the rendered world clears", "worked → blank", "insertive", SC, 8, ["a white screen", "a blank sky over the sea"], []),
           (78.8, 147.3, "THE WHOLE CREW · RENDER", "Who walks the drain? / Who buys the mud? / Who claims the fire? KREW-AL-GHAL!", "producer and product: machine and crew rhyme", "blank → production", "alternating", RE, 4, ["an assembly line of identical figures", "a crowd of workers in identical suits", "ships in formation"], []),
           (147.3, 154.3, "THE BLADE RESTS", "Ru al-dimbi. Kul-zha.", "the output is taken in", "production → stillness", "continuous", TI, 8, ["the sea after the fleet has gone"], [])]),
 "20": dict(idea="The Slop Communion / Mainframe Confession: a crew made by what it eats, drills and burns; the confession is dependence; 'Who stops the rig? Nobody' is both triumph and the admission.",
   look="raw", rules=["the kitchen is concrete: spatula, grease, onions, spoon; the comedy stays", "DRILL BABY DRILL is pound-locked: every drill stroke on the beat", "'Nobody' lands on a hard cut to the rig still running", "the pickups' own lines play in the word-free stretch 147-185 (the confession)", "the last stretch shows the cost (aftermath), not a victory"],
   phases=[(0, 26, "HUM · THE GRIDDLE HEATS", "(Hmm) (Oh-oh)", "the machine before speech", "silence → heat", "continuous", KI, 8, ["a griddle heating with grease", "onions sizzling on hot iron"], []),
           (26, 50, "WHO GAVE YOU MOUTH? THE FIRE · WEIGHT? THE SLOP", "Who gave you mouth / The fire / Who gave you weight / The slop / Hot on the steel / Thick in the spoon", "a creed of appetite", "heat → intake", "alternating", KI, 4, ["a masked cook at a griddle", "a spoon of thick slop", "fire under a griddle"], []),
           (50, 59, "EAT THE SLOP", "Eat the slop (×4)", "the communion: everyone eats", "intake → communion", "accumulative", KI, 2, ["workers eating together", "a crowd eating burgers"], []),
           (59, 78, "DEEPER THAN THE PROMPT · DRILL · SKY GOES WHITE · WHO STOPS THE RIG? NOBODY", "Deeper than the prompt / Drill drill / Hit the shale / Find the pipe / Sky goes white / Wall goes flat / Who stops the rig / Nobody", "extraction with no stopping principle", "communion → extraction", "alternating", DR, 2, ["workers pumping drills into sand", "a drill rig in the sand", "a white sky over a flat wall"], ["pound"]),
           (78, 98, "DRILL BABY DRILL", "Drill baby drill (×4)", "the slogan as work song", "extraction → compulsion", "accumulative", DR, 2, ["drills pounding in rhythm", "a line of workers pumping drills"], ["pound", "pails"]),
           (98, 125, "BLADE IN MY HAND · THEY BRING THE COLD, WE KEEP THE BURN · FEED THE FIRE", "Blade in my hand / Fat on the coal / They bring the cold / We keep the burn / O my fire / Feed the fire", "tending the fire as loyalty", "compulsion → devotion", "alternating", KI, 4, ["a spatula scraping a griddle", "a fire being fed", "a cook raising a spatula"], []),
           (125, 147, "FLIP · SWALLOW · DOWN TO THE ROOT · ALL TOGETHER", "Flip / Swallow / Down to the root … Feed the fire / Eat the slop / Drill baby drill", "the whole cycle joined", "devotion → cycle", "accumulative", LA, 2, ["a burger flipped on a griddle", "drills and fire together", "a crowd chanting"], ["pound"]),
           (147, 185, "THE CONFESSION (THE PICKUPS SPEAK)", "(word-free: the crew's own recorded lines)", "the mainframe admits what it runs on", "cycle → confession", "insertive", SC, 4, ["a cook at a terminal", "a green CRT terminal with text", "a control room with operators"], ["voice"]),
           (185, 202.9, "AFTERMATH · HMM", "(Hmm) (Oh-oh) (Hmm)", "the cost", "confession → residue", "continuous", AF, 8, ["a beach after the work, smoke and debris", "the tide washing away marks"], [])]),
 "23": dict(idea="Rite of Ash and Mire (The Chorus): a company that is both chorus (dancers) and army; in fire, through fire, out of fire are three different shots; cleanse the memory; tear the woven mesh.",
   look="newsreel", rules=["three prepositions, three shot relations: IN fire (inside it), THROUGH fire (crossing it), OUT OF fire (emerging)", "the chorus moves in a circle on 'Ἐν πυρί'", "mesh is woven: nets, wire, grates — not a wall", "short and fast: 123 bpm, 2-beat shots in the chant"],
   phases=[(0, 12.2, "ΕΝ ΠΥΡΙ · DRONE", "Ἐν πυρί (in fire) · (Μμμμ-αααα-ουυυμ)", "inside the fire, before anything", "silence → in fire", "continuous", LA, 8, ["figures standing inside flames", "smoke and fire at night"], []),
           (12.2, 27, "LEAD THE MIRE-BORN THROUGH FIRE · OUT OF THE FIRE ONTO THE IRON", "Ἄγε τοὺς ἐκ βορβόρου γενομένους διὰ πυρός … Ἐκ τοῦ πυρὸς ἐπὶ τὸν σίδηρον!", "through, then out of", "in → through → out", "alternating", DR, 4, ["people walking through fire and smoke", "a figure emerging from smoke", "iron struck on an anvil"], ["pound"]),
           (27, 40, "HOLD THE BREATH AGAINST THE CODE · TURN THE BUCKET · MOUTH INTO MUD", "Κατάσχετε τὸ πνεῦμα κατὰ τοῦ κώδικος … Στρέψατε τὸν κάδον! Στόμα εἰς ἰλύν! Ἆ!", "restraint as resistance; the vessel down", "out → restraint", "alternating", SC, 2, ["a screen full of code", "an orange bucket slammed upside down into mud", "a person holding their breath"], ["pails", "pound"]),
           (40, 52, "RISE FROM THE VOID · CLEANSE THE MEMORY · TEAR THE MESH · BRING DOWN THE WALL", "Ἐκ τοῦ κενοῦ ἀνάστητε … Ἐκκαθάρατε τὴν μνήμην … Ῥήξατε τὸ πλέγμα … Καταβάλετε τὸ τεῖχος!", "the woven structure torn, the wall thrown down", "restraint → rupture", "accumulative", AF, 2, ["a net or wire mesh being torn", "a wall collapsing", "a figure rising from darkness"], []),
           (52, 62, "BURN IN FIRE (CIRCULAR)", "Καίεσθε ἐν πυρί! Ἐν πυρί! Ἐν πυρί!", "the chorus burns, moving in a circle", "rupture → ring", "continuous", LA, 2, ["people moving in a circle around a fire", "a ring of figures stomping"], ["pound"]),
           (62, 80, "WHO CROSSES · WHO ACQUIRES THE LAND · WHO RECEIVES THE FIRE — THE WHOLE ARMY", "Τίς διαβαίνει τὸν ὀχετόν; Ἅπας ὁ στρατός! (×3)", "chorus becomes army", "ring → army", "accumulative", FL, 4, ["an army crossing a channel", "a crowd taking a beach", "a wide shot of a marching company"], []),
           (80, 94.5, "THE IRON HAS COOLED · SWALLOW", "Ὁ σίδηρος ἔψυκται. Καταπίετε. Ἆ! (hum)", "cooled, taken in", "army → stillness", "continuous", TI, 8, ["a cooled iron bar in the sand", "a quiet shore at dusk"], [])])}
# ---- the story each film tells: who carries it (the spine: they open every phase and close the film), what they want, the turn, the end; a logline
STORY = {
 "26": dict(title="The Bucket Bet", logline="A masked cook leads a crew of mud through fire and iron until they answer as one army, and then makes them swallow what made them.",
   spine="a skull-masked cook leading a crew of workers carrying orange pails on a beach", want="the crew wants to stop being raw material", turn="they erase the record and tear down the wall", end="they claim the fire, and swallow the cooled iron: free, or drafted?"),
 "06": dict(title="Go Home and Be Free", logline="A crew born weary wades the muddy water together toward free ground, singing the old refusal: before I'd be a slave.",
   spine="tired workers walking together through muddy water at dawn", want="free ground", turn="the stone is rolled from the door", end="the hammer drops; they stand up"),
 "07": dict(title="Cleanse the Memory", logline="An outcast company washes its memory in fire and tide, breaks the gate, and swallows what is left.",
   spine="a lone hooded figure walking through fog on a beach", want="a memory they can live with", turn="the tide washes over the old film", end="the iron cools; the old film fades to white"),
 "09": dict(title="The Recursion", logline="A crew names what made it (coal, slop, the iron hand), purges itself into four beats of nothing, and comes back as the whole crew.",
   spine="a skull-masked cook standing before a crew in a dark vault", want="to know what they are made of", turn="the purge: four beats of black", end="the whole crew answers, and the opening returns changed"),
 "13": dict(title="The Communion", logline="One meal on the beach: the cook serves, the crew eats, and what they take in becomes them.",
   spine="a skull-masked cook serving burgers to a line of workers", want="to be fed", turn="the held breath before the serving", end="they swallow"),
 "14": dict(title="The Render Fleet", logline="Offshore, four flat shapes request changes; on the sand the crew renders them, and is rendered in turn.",
   spine="four flat cartoon shapes standing in the sea like warships", want="the fleet wants output", turn="the rendered sky goes blank", end="the crew claims the fire; the sea is empty"),
 "20": dict(title="The Slop Communion", logline="Eat the slop, drill baby drill, feed the fire: a cook's crew confesses what keeps the machine running, and that nobody stops the rig.",
   spine="a skull-masked cook at a griddle with burgers and onions", want="to keep the fire fed", turn="'who stops the rig?' 'nobody'", end="the confession, then the cost"),
 "23": dict(title="The Chorus", logline="Born of mire, a chorus passes in, through and out of the fire, tears the mesh, and becomes an army.",
   spine="a crowd of figures moving in a circle around a fire", want="to come out of the mire", turn="the mesh is torn, the wall comes down", end="the army takes the fire; the iron cools")}
# ---- the atlas, CLIP, the songs' beats
A = json.load(open(os.path.join(D, "atlas.json"))); C = A["cards"]; S = A["songs"]
E = np.fromfile(os.path.join(D, "atlas-emb.bin"), np.int8).reshape(-1, 512).astype(np.float32); E /= np.linalg.norm(E, axis=1, keepdims=True)
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def ct(ts):
    with torch.no_grad(): e = m.encode_text(tok(ts)).float(); return (e / e.norm(dim=-1, keepdim=True)).numpy()
B = json.load(open(os.path.join(D, "bible.json"))); LOCK = B["locks"]; NEG = B["neg"]
QALL = ct([q for sp in SONGS.values() for ph in sp["phases"] for q in ph[9]]); HUB = (E @ QALL.T).mean(1)   # a card close to every query is a hub, not an answer
typ = np.array([c["type"] for c in C]); ai = typ == "ai"; arch = typ == "archive"
pois = np.array([c.get("poison", 0) or 0 for c in C]); fam = [c.get("twin") or c["id"] for c in C]
def snap(t, beats): return min(beats, key=lambda b: abs(b - t)) if beats else t
def lockfor(q):
    q = q.lower(); ks = [k for k, w in (("pails", "bucket"), ("pails", "pail"), ("cook", "cook"), ("cook", "mask"), ("crew", "worker"), ("crew", "crowd"), ("four", "cartoon shape"), ("four", "flat")) if w in q]
    return " ".join(LOCK[k] for k in dict.fromkeys(ks)) + " " + LOCK["world"]
out, md = {}, ["# CUTBASTARD-1 · the eight Liturgy songs\n", "CUTBASTARD-1 ONLINE. PATCH CARVING ACTIVE. O, A, F LIVE (B and E are carried by the phases and the blueprint lines below). C AND D LOCKED.\n"]
for n, sp in SONGS.items():
    s = S[n]; beats = s["beats"]; patches = []
    for pi, (a, b, name, line, mean, press, syn, world, nb, qs, flags) in enumerate(sp["phases"]):
        a2, b2 = (snap(a, beats) if pi else 0.0), (snap(b, beats) if pi < len(sp["phases"]) - 1 else s["dur"])
        span = b2 - a2; k = max(1, round(span / 9)); k = max(k, int(np.ceil(span / 12)))   # patch law: 6-12 s, aim 9
        cuts = [a2] + [snap(a2 + span * j / k, beats) for j in range(1, k)] + [b2]
        qv = ct(qs).mean(0) if qs else None
        if qv is not None: qv /= np.linalg.norm(qv)
        for j in range(k):
            t0, t1 = cuts[j], cuts[j + 1]
            if t1 - t0 < .5: continue
            pid = f"{n}-P{len(patches) + 1:02d}"; trig = (f"phase: {name.split(' · ')[0].lower()}" if j == 0 else "patch law: 12 s limit, cut on the beat")
            cands, best_ai, aic = [], 0.0, []
            if qv is not None:
                raw = E @ qv - HUB; sc = raw.copy()
                for t in ("ai", "archive"): mk = typ == t; sc[mk] = (raw[mk] - raw[mk].mean()) / (raw[mk].std() + 1e-9) * .05   # rank within each source: the AI/archive gap otherwise hands everything to one side
                if "clean" in flags: sc = sc - 2 * (ai & (pois > .3))
                sc = sc - .5 * (ai & (pois > .55))
                if "archive" in flags: sc = sc + .02 * arch
                if "pails" in flags: sc = sc + .05 * np.array([c.get("pails", 0) for c in C])
                if "pound" in flags: sc = sc + .02 * np.array([len(c.get("pound") or []) >= 2 for c in C])
                seen = set()
                for i in np.argsort(-sc):
                    if typ[i] == "drawn" or fam[i] in seen: continue
                    seen.add(fam[i]); cands.append(C[i]["id"])
                    if len(cands) >= 16: break
                best_ai = float(np.max(np.where(ai, sc, -9)))
                aic, seen3 = [], set()
                for i in np.argsort(-np.where(ai & (pois <= .5), sc, -9)):
                    if fam[i] in seen3 or not ai[i]: continue
                    seen3.add(fam[i]); aic.append(C[i]["id"])
                    if len(aic) >= 24: break
            patches.append({"id": pid, "t0": round(t0, 3), "t1": round(t1, 3), "phase": pi, "name": name, "line": line, "meaning": mean, "pressure": press, "trigger": trig,
                            "syntagma": syn, "world": world, "beats": nb * sp.get("bscale", 1), "flags": flags, "queries": qs, "cands": cands, "ai_cands": aic if qv is not None else [], "fit": round(best_ai, 3)})
    fits = [p["fit"] for p in patches if p["queries"]]; lo = np.quantile(fits, .3) if fits else 0
    for p in patches:
        if p["queries"] and p["fit"] <= lo and "null" not in p["flags"]:
            q = p["queries"][0]; p["generate"] = True
            p["prompt"] = (f"{q.capitalize()}. {p['meaning'].capitalize()}. {lockfor(' '.join(p['queries']))} Hold {p['beats']} beats at {s['tempo']:.0f} bpm; "
                           f"a {p['syntagma']} beat in the song's '{p['name'].title()}' phase. Avoid: {'; '.join(NEG)}.")
    st = STORY[n]; sv = ct([st["spine"]])[0]; sraw = E @ sv - HUB; sz = np.where(ai & (pois <= .5), sraw, -9)
    spine, seen2 = [], set()
    for i in np.argsort(-sz):
        if fam[i] in seen2: continue
        seen2.add(fam[i]); spine.append(C[i]["id"])
        if len(spine) >= 10: break
    out[n] = {"story": st, "spine": spine, "title": s["title"], "idea": sp["idea"], "look": sp["look"], "rules": sp["rules"], "patches": patches}
    # ---- the matrices (O, A, F), compressed
    md += [f"\n## {n} · {s['title']} — {st['title']}\n", f"**Logline.** {st['logline']}\n", f"**Story spine.** {st['want']}; the turn: {st['turn']}; the end: {st['end']}. Carried by: {st['spine']}.\n", f"**Idea.** {sp['idea']}\n", "### Matrix O · Brutal Structural Diagnosis"] + [f"- {r}" for r in sp["rules"]]
    md += ["\n### Olog Map"] + [f"- <{n}> [is carried by] <phase {i + 1}: {ph[2].title()}>" for i, ph in enumerate(sp["phases"])]
    md += [f"- <phase {i + 1}> [shifts pressure] <{ph[5]}>" for i, ph in enumerate(sp["phases"])]
    md += [f"- <{p['id']}> [triggered by] <{p['trigger']}>" for p in patches[:6]] + [f"- <patch> [cuts on] <the song's beats at {s['tempo']:.0f} bpm>", f"- <look> [unifies] <{sp['look']}>"]
    md += ["\n### Matrix A · YAML Patch Genome", "```yaml", f"title: \"{s['title']}\"", f"seed: \"{sp['idea'][:180]}\"", "patch_timeline:"]
    for p in patches:
        f = lambda t: f"01:{int(t // 60):02d}:{int(t % 60):02d}:{int((t % 1) * 24):02d}"
        md += [f"  - patch_id: \"{p['id']}\"", f"    start_time: \"{f(p['t0'])}\"", f"    end_time: \"{f(p['t1'])}\"", f"    phase: \"{p['name']}\"", f"    line: \"{p['line'][:140]}\"",
               f"    pressure_shift: \"{p['pressure']}\"", f"    syntagma_type: \"{p['syntagma']}\"", f"    camera_relation: \"{p['beats']} beats per shot\"", f"    patch_trigger: \"{p['trigger']}\"",
               f"    rehydration_seed: \"{(p['queries'] or ['black'])[0]}\"" + (f"\n    generate: true" if p.get("generate") else "")]
    md += ["```"]
    md += ["\n### The story shots (generate these first: the archive can rhyme with a song but cannot carry its protagonist)"] + [
        f"- **{lab}** — {st['spine'].capitalize()}: {txt}. {lockfor(st['spine'])} One continuous shot, 8-10 s, the protagonist in frame throughout. Avoid: {'; '.join(NEG[:4])}."
        for lab, txt in (("SETUP", st["want"]), ("TURN", st["turn"]), ("END", st["end"]))]
    gen = [p for p in patches if p.get("generate")]
    if gen: md += ["\n### Matrix F · Master Patch Prompts (the patches the atlas can't answer: generate these)"] + [f"- **{p['id']}** ({p['t0']:.0f}-{p['t1']:.0f} s · {p['name'].title()}): {p['prompt']}" for p in gen]
json.dump({"songs": out}, open(os.path.join(D, "cutbastard.json"), "w"), ensure_ascii=False, indent=0)
open(os.path.join(D, "cutbastard.md"), "w").write("\n".join(md))
for n, o in out.items(): print(n, o["title"], len(o["patches"]), "patches ·", sum(1 for p in o["patches"] if p.get("generate")), "to generate", flush=True)
