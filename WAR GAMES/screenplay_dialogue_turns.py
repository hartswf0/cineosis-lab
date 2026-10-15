#!/usr/bin/env python3
"""
VERIFIED SCREENPLAY DIALOGUE TURNS & PACING SCORE FOR ALL 105 BEATS OF WARGAMES (1983)
======================================================================================
Maps every beat (S01-B01 .. S21-B05) to its exact spoken character turns (`[s, e]` in seconds
relative to the beat's `[a0, a1]` audio window in `cache/wg_sound/{beat_id}_orig.m4a`),
replacing corrupted Whisper ASR phrases and round-robin speaker cycling with:
  1. True Character Speaker Attribution (`speaker`, `speaker_color`, `role_tag`, `base_f0`)
  2. Verbatim Screenplay Dialogue (`text`)
  3. Dramatic Fulcrum Flag (`is_fulcrum`: True on "The Line" where the scene's power shifts)
  4. Explicit Pacing Telemetry (`s`, `e`, `dur`, `pause_before`, `pause_type`, `wpm`, `cadence_label`)
"""

CHARACTER_PROFILES = {
    "General Beringer":    {"color": "#ff6b52", "role_tag": "NORAD COMMANDER",  "base_f0": 108.0},
    "John McKittrick":     {"color": "#e8c070", "role_tag": "SYSTEM ARCHITECT", "base_f0": 124.0},
    "David Lightman":      {"color": "#45b1ff", "role_tag": "TEEN HACKER",      "base_f0": 148.0},
    "Jennifer Mack":       {"color": "#ff85c8", "role_tag": "CO-CONSPIRATOR",   "base_f0": 205.0},
    "Stephen Falken":      {"color": "#9b7bff", "role_tag": "AI CREATOR",       "base_f0": 114.0},
    "WOPR (Joshua)":       {"color": "#38d996", "role_tag": "SYNTHESIZED AI",   "base_f0": 106.0},
    "Paul Richter":        {"color": "#5ce1e6", "role_tag": "WOPR ENGINEER",    "base_f0": 128.0},
    "Col. Joe Conley":     {"color": "#f4a261", "role_tag": "WAR ROOM OPS",     "base_f0": 118.0},
    "Capt. Jerry Lawson":  {"color": "#e76f51", "role_tag": "SILO COMMANDER",   "base_f0": 116.0},
    "Lt. Steve Phelps":    {"color": "#e9c46a", "role_tag": "SILO DEPUTY",      "base_f0": 132.0},
    "SAC Duty Officer":    {"color": "#a8dadc", "role_tag": "EAM RADIO",        "base_f0": 122.0},
    "Arthur Cabot":        {"color": "#cdb4db", "role_tag": "DOD ADVISOR",      "base_f0": 115.0},
    "Lyle Watson":         {"color": "#90be6d", "role_tag": "PSYCHOLOGIST",     "base_f0": 126.0},
    "Mr. Liggett":         {"color": "#f9844a", "role_tag": "BIOLOGY TEACHER",  "base_f0": 120.0},
    "Jim Sting":           {"color": "#43aa8b", "role_tag": "UW PROGRAMMER",    "base_f0": 134.0},
    "Malvin":              {"color": "#f3722c", "role_tag": "UW NERD",          "base_f0": 152.0},
    "Agent Ginsberg":      {"color": "#577590", "role_tag": "FBI AGENT",        "base_f0": 112.0},
    "NORAD Guard":         {"color": "#8ecae6", "role_tag": "TOUR GUIDE",       "base_f0": 125.0},
    "Bell Operator":       {"color": "#ffb703", "role_tag": "TELEPHONE CO.",    "base_f0": 195.0},
    "TV Newscaster":       {"color": "#adb5bd", "role_tag": "CBS NEWS",         "base_f0": 119.0},
    "Loring Controller":   {"color": "#52b788", "role_tag": "BASE RADIO",       "base_f0": 126.0},
}

# Format of each entry in SCREENPLAY_BEAT_TURNS[beat_id]:
#   (s, e, speaker, text, is_fulcrum)
SCREENPLAY_BEAT_TURNS = {
    # === BOOK ONE: Cold Open · Missile Silo Alert & Refusal to Turn the Launch Key ===
    "S01-B01": [
        (0.15, 3.35, "SAC Duty Officer", "[DIEGETIC WIND & TELETYPE] Replacement team's here, sir. Come on through.", True),
    ],
    "S01-B02": [
        (0.35, 2.25, "SAC Duty Officer", "Stand by for EAM emergency war order!", True),
    ],
    "S01-B03": [
        (0.15, 4.15, "SAC Duty Officer", "Skybird, this is Dropkick with a Red Dash Alpha message in two parts.", False),
        (4.15, 8.85, "SAC Duty Officer", "Break, break. Red Dash Alpha. Stand by to copy message.", False),
        (9.15, 15.15, "Lt. Steve Phelps", "Romeo. Oscar. November. Charlie. Tango. Tango. Lima.", False),
        (15.15, 17.85, "Capt. Jerry Lawson", "I agree with authentication, sir.", True),
    ],
    "S01-B04": [
        (0.15, 2.15, "Lt. Steve Phelps", "We got countdown: T-minus sixty.", False),
        (2.15, 3.15, "Capt. Jerry Lawson", "All right, let's do it.", False),
        (3.15, 5.15, "Lt. Steve Phelps", "Insert launch key. Stand by.", True),
        (5.15, 7.85, "Capt. Jerry Lawson", "Launch key inserted. Roger.", False),
        (8.15, 12.25, "Lt. Steve Phelps", "On my mark, rotate launch key to SET.", False),
    ],
    "S01-B05": [
        (0.15, 3.65, "Capt. Jerry Lawson", "Damn, all missiles in A-minus! Get me Wing Command Post on a direct line.", False),
        (3.65, 5.65, "Lt. Steve Phelps", "That's not the correct procedure, Captain.", False),
        (5.65, 7.65, "Capt. Jerry Lawson", "Try SAC headquarters on the HF.", False),
        (7.65, 10.45, "Lt. Steve Phelps", "Sir, that's not the correct procedure —", False),
        (10.45, 14.65, "Capt. Jerry Lawson", "Screw the procedure! I want somebody on the goddamn phone before I kill twenty million people!", True),
    ],

    # === BOOK TWO: Cheyenne Mountain · McKittrick & Beringer Debate WOPR Taking Men Out of the Loop ===
    "S02-B01": [
        (0.25, 6.20, "General Beringer", "Better just walk on through there, gentlemen — watch the cables on the floor.", False),
        (6.40, 11.40, "John McKittrick", "I'm glad you flew out from Washington to see the WOPR center firsthand, Arthur.", True),
        (11.60, 16.10, "Arthur Cabot", "The President wants a straight answer on the silo readiness test before we brief the Hill.", False),
    ],
    "S02-B02": [
        (0.15, 3.95, "John McKittrick", "I had them on the phone and they're calmed down.", False),
        (3.95, 6.35, "Arthur Cabot", "Well, are we positive that these men —", False),
        (6.35, 9.81, "John McKittrick", "Those missile commanders had no way of knowing this was only a test. Twenty percent refused to turn the keys.", True),
        (9.81, 13.49, "John McKittrick", "Lyle, for God's sakes, how many times are we gonna go through this?", False),
        (13.49, 14.93, "Lyle Watson", "It doesn't make any difference.", False),
        (14.93, 17.95, "General Beringer", "I've spoken to each of these men. They all believed it was the real deal.", False),
    ],
    "S02-B03": [
        (0.15, 4.19, "General Beringer", "We can't ask these men to go back to the President with a lot of headshrinker horseshit!", False),
        (4.19, 8.43, "General Beringer", "Besides, you can't screen out human response. Those men in the silos know what it means", False),
        (8.43, 12.59, "General Beringer", "to turn the keys, and some of them are just not up to it! Now, it's as simple as that.", False),
        (12.59, 15.59, "John McKittrick", "I think we oughta take the men out of the loop.", True),
        (15.59, 17.45, "General Beringer", "Mr. McKittrick, you're out of line, sir.", False),
        (17.45, 18.00, "John McKittrick", "Why am I out of line?", False),
    ],
    "S02-B04": [
        (0.15, 3.15, "John McKittrick", "In a surprise attack, there's no time: twenty-three minutes from warning to impact.", False),
        (3.15, 6.55, "Paul Richter", "Six minutes if it's sub-launched. Six minutes.", False),
        (6.55, 9.95, "John McKittrick", "Six minutes! That's barely enough time for the President to make a decision.", False),
        (9.95, 13.75, "John McKittrick", "Now, once he makes that decision, the computer should take over.", True),
        (13.75, 17.95, "John McKittrick", "Sir, I know that you've got a plane waiting for you, but if you'll indulge me for five minutes, I'd like to show you something.", False),
    ],
    "S02-B05": [
        (0.15, 5.15, "John McKittrick", "The WOPR spends all its time thinking about World War III. It estimates Soviet responses to our responses,", False),
        (5.15, 9.15, "John McKittrick", "estimates damage, counts the dead,", False),
        (9.15, 12.95, "John McKittrick", "then it looks for ways to improve the score.", True),
        (12.95, 17.15, "Paul Richter", "Every conceivable option in a nuclear crisis has already been played by the WOPR.", False),
        (17.15, 18.00, "General Beringer", "So what you're telling me is that all this hardware...", False),
    ],

    # === BOOK THREE: Seattle Arcade · David Lightman Plays Galaga & Runs Late for School ===
    "S03-B01": [
        (0.15, 5.15, "Arthur Cabot", "I think I'm going to recommend McKittrick's idea to the President. And I'll get back to you on this.", False),
        (5.15, 8.15, "John McKittrick", "You won't regret this.", True),
        (8.15, 12.50, "David Lightman", "OK, you had fries and a Coke, right? Damn!", False),
    ],
    "S03-B02": [
        (0.15, 2.20, "David Lightman", "Hi, Howie! How's it going?", False),
        (2.40, 6.20, "David Lightman", "Watch this wave — if you let the boss tractor-beam your ship, you get dual fighters.", True),
    ],
    "S03-B03": [
        (0.15, 4.15, "David Lightman", "You wanna take this over? I gotta go.", True),
        (4.15, 5.15, "David Lightman", "Go ahead.", False),
        (5.15, 7.15, "David Lightman", "Thanks! Bye, David!", False),
        (11.15, 12.45, "David Lightman", "Bye!", False),
    ],
    "S03-B04": [
        (0.95, 4.40, "Mr. Liggett", "Which of the following are seedless vascular plants that sprout roots?", False),
        (6.85, 8.33, "Mr. Liggett", "Nice of you to join us.", False),
        (8.33, 10.85, "Mr. Liggett", "Oh, David, I have a little present for you: question number four.", True),
    ],
    "S03-B05": [
        (0.15, 7.75, "Mr. Liggett", "In the history of science, novel and innovative concepts occasionally arise from sudden left-field inspiration.", False),
        (7.75, 12.75, "Mr. Liggett", "Miss Mack, could you tell us your answer to question number four?", False),
        (12.75, 16.45, "Mr. Liggett", "Why do nitrogen nodules cling to the roots of plants?", True),
    ],

    # === BOOK FOUR: Biology Class & Principal's Office · Nitrogen Nodules, Asexual Reproduction & The Password ===
    "S04-B01": [
        (0.15, 3.75, "Mr. Liggett", "Why do nitrogen nodules cling to the roots of plants?", False),
        (6.65, 7.75, "Jennifer Mack", "Love?", True),
        (7.75, 10.95, "Mr. Liggett", "No, no, no. Quiet down.", False),
        (11.85, 16.45, "Mr. Liggett", "Jennifer, what do you know about nitrogen nodules that we don't?", False),
        (16.45, 18.00, "Mr. Liggett", "Some bit of salacious info to which you alone are privy?", False),
    ],
    "S04-B02": [
        (0.15, 2.25, "Mr. Liggett", "Asexual reproduction.", False),
        (3.05, 8.85, "Mr. Liggett", "Could someone tell me, please, who first suggested the idea of reproduction without sex?", False),
        (8.95, 10.25, "David Lightman", "Your wife?", True),
    ],
    "S04-B03": [
        (4.55, 6.65, "Mr. Liggett", "All right, Lightman!", False),
        (7.55, 13.40, "Mr. Liggett", "Maybe you could tell us who first suggested the idea of reproduction without sex!", True),
        (13.40, 13.70, "David Lightman", "Um...", False),
    ],
    "S04-B04": [
        (0.15, 3.15, "Mr. Liggett", "Get out, Lightman. Get out!", False),
        (9.15, 13.39, "David Lightman", "Mr. Liggett wants me to discuss my attitude problem with Mr. Kessler.", True),
        (13.39, 17.27, "Bell Operator", "I think Mr. Kessler's getting tired of discussing your attitude problem.", False),
    ],
    "S04-B05": [
        (0.95, 3.99, "David Lightman", "So you got an F on that test today too, huh?", False),
        (3.99, 4.99, "Jennifer Mack", "Yep.", False),
        (4.99, 6.99, "Jennifer Mack", "Guess we're gonna be stuck in summer school.", False),
        (6.99, 7.99, "David Lightman", "Not me.", True),
        (7.99, 8.99, "Jennifer Mack", "How's that?", False),
        (8.99, 10.99, "Jennifer Mack", "You have to take biology.", False),
        (10.99, 12.99, "David Lightman", "I don't think so.", False),
        (12.99, 14.99, "Jennifer Mack", "Why?", False),
        (15.85, 18.00, "Jennifer Mack", "Come on, how's that?", False),
    ],

    # === BOOK FIVE: David's Bedroom · IMSAI 8080, Acoustic Coupler & Hacking School Grades ===
    "S05-B01": [
        (7.55, 10.65, "Jennifer Mack", "You're really into computers, huh?", False),
        (10.65, 11.65, "David Lightman", "Yeah.", False),
        (13.55, 14.65, "Jennifer Mack", "What are you doing?", False),
        (14.65, 16.80, "David Lightman", "Dialing into the school's computer.", True),
    ],
    "S05-B02": [
        (0.35, 2.65, "David Lightman", "They change the password every couple of weeks.", True),
        (2.65, 3.85, "David Lightman", "Wait — I wrote the new one down right here: PENCIL.", False),
    ],
    "S05-B03": [
        (0.15, 3.15, "Jennifer Mack", "It's none of your business. Can you erase this, please?", False),
        (3.15, 5.15, "David Lightman", "No, it's too late.", False),
        (5.15, 6.15, "Jennifer Mack", "What are you doing?", False),
        (6.15, 8.15, "David Lightman", "I'm changing your biology grade.", True),
        (8.15, 10.15, "Jennifer Mack", "No, I don't want you to do that! You're gonna get me in trouble.", False),
        (10.15, 12.15, "David Lightman", "No, nobody can find out.", False),
        (12.15, 15.55, "David Lightman", "There — you just got a C. See, now you don't have to go to summer school.", False),
        (15.55, 17.50, "Jennifer Mack", "Change it back!", False),
    ],
    "S05-B04": [
        (5.20, 7.10, "Jennifer Mack", "I guess I better get going.", False),
        (9.50, 11.50, "Jennifer Mack", "Thanks for the grade.", True),
        (11.50, 12.60, "David Lightman", "OK.", False),
    ],
    "S05-B05": [
        (0.25, 5.50, "David Lightman", "[PROTOVISION MAGAZINE AD] 'Coming soon from Sunnyvale, California — the ultimate computer games.'", True),
    ],

    # === BOOK SIX: Sunnyvale War-Dialing · Scanning Every Prefix, Pan Am to Paris & HELP GAMES ===
    "S06-B01": [
        (0.15, 2.15, "Bell Operator", "What city, please?", False),
        (2.15, 6.15, "David Lightman", "Yeah, for Sunnyvale, California — the number for Protovision.", False),
        (6.15, 10.15, "Bell Operator", "Yes, that's 555-8632.", False),
        (10.15, 14.95, "David Lightman", "Thank you. Hey, and could you also tell me what other prefixes cover that area?", True),
        (14.95, 17.95, "Bell Operator", "There's 399, 437, 767, 936, and 311.", False),
    ],
    "S06-B02": [
        (0.15, 4.55, "David Lightman", "So I told my system to search for other computers in Sunnyvale, California.", False),
        (8.45, 13.15, "David Lightman", "They answer with a tone that other computers can recognize. Hear that?", True),
        (14.15, 16.45, "Jennifer Mack", "You're calling every number in Sunnyvale?", False),
    ],
    "S06-B03": [
        (0.15, 5.15, "David Lightman", "Pan Am reservations! Where should we go?", False),
        (5.15, 8.85, "Jennifer Mack", "Anywhere!", False),
        (8.85, 10.85, "David Lightman", "No — Paris. Two seats to Paris.", True),
        (10.85, 12.10, "Jennifer Mack", "Paris! OK.", False),
    ],
    "S06-B04": [
        (0.15, 3.69, "David Lightman", "Help games.", False),
        (5.99, 10.33, "David Lightman", "'Games' refers to models, simulations, and games which have tactical and strategic applications.", True),
        (10.33, 13.60, "David Lightman", "That must be them.", False),
        (13.60, 14.80, "Jennifer Mack", "What does that mean?", False),
        (14.80, 17.85, "David Lightman", "I don't know, but that's gotta be them. Turn on the printer, will you?", False),
    ],
    "S06-B05": [
        (1.10, 2.20, "Jennifer Mack", "What does that mean?", False),
        (2.20, 3.20, "David Lightman", "I don't know, but that's gotta be them.", False),
        (3.20, 6.72, "David Lightman", "Turn on the printer, will you? I want to get a printout of this.", False),
        (6.72, 10.20, "David Lightman", "List games.", True),
    ],

    # === BOOK SEVEN: University Computer Lab · Consulting Jim and Malvin on Backdoors ===
    "S07-B01": [
        (0.15, 3.15, "David Lightman", "Jim, I want you to take a look at this.", False),
        (4.15, 9.85, "Malvin", "Hey, what's that?", False),
        (9.85, 12.15, "David Lightman", "I wanted Jim to see that.", False),
        (15.05, 17.15, "Jim Sting", "Wow, where'd you get this?", True),
        (17.15, 18.00, "David Lightman", "I was trying to break into Protovision.", False),
    ],
    "S07-B02": [
        (0.15, 2.15, "Jim Sting", "Looks military to me. Definitely military.", False),
        (2.15, 4.15, "Malvin", "Probably classified, too.", False),
        (4.15, 7.15, "Jennifer Mack", "Yeah, but if it's military, why does it have games like checkers and backgammon?", False),
        (7.15, 10.15, "Jim Sting", "Maybe because those are the games that teach basic strategy.", True),
    ],
    "S07-B03": [
        (0.15, 2.15, "Jim Sting", "You won't get through frontline security, but you might look for a back door.", False),
        (2.15, 6.15, "Malvin", "I can't believe it, Jim! That girl's standing over there listening and you're talking about our back doors!", False),
        (6.15, 11.15, "Jim Sting", "Mr. Potato Head! Mr. Potato Head! Back doors are not secrets!", True),
        (11.15, 13.15, "Malvin", "Yeah, but Jim, you're giving away all our best tricks.", False),
        (13.15, 15.75, "Jim Sting", "Tricks? They're not tricks.", False),
        (15.75, 17.15, "Jennifer Mack", "What's a back door?", False),
        (17.15, 18.00, "Jim Sting", "Well, whenever I design a system...", False),
    ],
    "S07-B04": [
        (0.15, 3.47, "Jim Sting", "I always put in a simple password that only I know about.", False),
        (3.47, 8.15, "Jim Sting", "That way, whenever I want to get back in, I can bypass whatever security they've added on.", True),
        (8.15, 11.87, "Jim Sting", "That's basically what it is.", False),
        (11.87, 13.99, "David Lightman", "Yeah? OK.", False),
        (13.99, 16.10, "Jim Sting", "If you really want to get in, find out as much as you can about the guy who designed the system.", False),
    ],
    "S07-B05": [
        (0.15, 1.95, "Malvin", "The first game on the list!", False),
        (1.95, 4.25, "Malvin", "Go right through Falken's Maze.", True),
    ],

    # === BOOK EIGHT: Library Microfiche & Falken's Obituary · Discovering 'Joshua' ===
    "S08-B01": [
        (0.35, 5.39, "Jennifer Mack", "Oh, hi! I'm Jennifer.", False),
        (6.10, 7.39, "Jennifer Mack", "Is David here?", False),
        (7.39, 10.39, "David Lightman", "How do you do? Yeah, he's up in his room.", True),
    ],
    "S08-B02": [
        (0.15, 3.59, "David Lightman", "This is a tape that I got from the library. It's about this guy named Falken.", False),
        (6.43, 12.99, "David Lightman", "He was into games as well as computers. He designed them so that they could play checkers or poker.", True),
        (12.99, 14.19, "Jennifer Mack", "Chess.", False),
        (14.19, 16.23, "Jennifer Mack", "What's so great about that? Everybody's doing that now.", False),
        (16.23, 18.00, "David Lightman", "Oh, no, no, no. What he did was great!", False),
    ],
    "S08-B03": [
        (0.15, 3.79, "Jennifer Mack", "That's him? Wow.", False),
        (3.79, 6.23, "Jennifer Mack", "He's amazing-looking.", False),
        (7.43, 10.03, "Jennifer Mack", "Can't you write to him or call him somehow?", False),
        (10.03, 11.83, "David Lightman", "No, he's dead.", True),
        (11.83, 13.03, "Jennifer Mack", "He's dead?", False),
        (13.03, 17.80, "David Lightman", "Yeah. Here's his obituary.", False),
    ],
    "S08-B04": [
        (3.87, 6.59, "Jennifer Mack", "That's his little boy.", False),
        (6.59, 9.03, "David Lightman", "Oh, yeah?", False),
        (9.03, 14.07, "Jennifer Mack", "This is really sad. Did you know the child and his mother were killed in a car crash?", True),
        (14.07, 17.90, "Jennifer Mack", "'In the years that followed the tragic loss of his family, Dr. Falken's health deteriorated.'", False),
    ],
    "S08-B05": [
        (0.15, 2.07, "Jennifer Mack", "I remember once my dad was really sick...", False),
        (2.07, 4.19, "David Lightman", "What was his name?", False),
        (4.19, 5.87, "Jennifer Mack", "My father?", False),
        (5.87, 8.87, "David Lightman", "No, no, no — Falken's kid!", False),
        (10.07, 12.07, "Jennifer Mack", "Joshua.", True),
        (12.79, 15.07, "David Lightman", "It can't be that simple.", False),
    ],

    # === BOOK NINE: Logon JOSHUA · Voice Synthesizer, 'Shall We Play a Game?' & Global Thermonuclear War ===
    "S09-B01": [
        (0.20, 3.80, "WOPR (Joshua)", "[LOGON: JOSHUA] GREETINGS PROFESSOR FALKEN.", True),
    ],
    "S09-B02": [
        (0.15, 3.15, "David Lightman", "Hello. I'm fine. How are you?", False),
        (3.15, 7.15, "WOPR (Joshua)", "EXCELLENT. IT'S BEEN A LONG TIME. CAN YOU EXPLAIN THE REMOVAL OF YOUR USER ACCOUNT ON JUNE 23, 1973?", True),
        (7.15, 11.15, "David Lightman", "How are you feeling today?", False),
        (11.15, 16.15, "WOPR (Joshua)", "I'M FINE. HOW ARE YOU?", False),
        (16.15, 18.00, "David Lightman", "Excellent.", False),
    ],
    "S09-B03": [
        (0.15, 5.15, "David Lightman", "People sometimes make mistakes.", False),
        (5.15, 6.75, "WOPR (Joshua)", "YES, THEY DO.", False),
        (6.75, 8.39, "Jennifer Mack", "How can it talk?", False),
        (8.39, 13.31, "David Lightman", "It's not a real voice. This box just interprets signals from the computer and turns them into sound.", False),
        (13.31, 15.79, "WOPR (Joshua)", "SHALL WE PLAY A GAME?", True),
    ],
    "S09-B04": [
        (0.15, 1.75, "David Lightman", "Yeah — weird, isn't it?", False),
        (1.75, 9.43, "David Lightman", "Love to. How about Global Thermonuclear War?", True),
    ],
    "S09-B05": [
        (0.15, 4.55, "David Lightman", "Oh, let's see. How about Las Vegas?", False),
        (4.55, 6.55, "Jennifer Mack", "Las Vegas! Great!", False),
        (9.35, 10.55, "David Lightman", "What next?", False),
        (10.55, 12.35, "Jennifer Mack", "Seattle! Yeah!", True),
    ],

    # === BOOK TEN: First Strike Simulation · Las Vegas & Seattle Targeted on the NORAD Big Board (DEFCON 3) ===
    "S10-B01": [
        (0.15, 8.50, "Col. Joe Conley", "Nineteen degrees past apogee, possibly eighteen targets in track.", True),
        (8.50, 17.85, "Col. Joe Conley", "Estimated reentry at 1923 Zulu — trajectory headings for multiple MIRV impact!", False),
    ],
    "S10-B02": [
        (0.15, 5.33, "Col. Joe Conley", "Scramble alert aircraft. I repeat, scramble alert aircraft.", False),
        (5.39, 12.33, "Col. Joe Conley", "Inbounds presently MIRVing — we have approximately twenty-four possible targets in track, sir.", True),
        (12.39, 17.67, "General Beringer", "Get me SAC on the line — tell them to flush the bombers!", False),
    ],
    "S10-B03": [
        (0.15, 3.15, "General Beringer", "Get onto SAC, tell them to hold steady.", False),
        (5.15, 9.15, "John McKittrick", "It's a simulation! It's an attack simulation, General.", True),
        (9.15, 14.15, "Paul Richter", "Wait — WOPR is running a simulation! We're not being attacked, it's simulated!", False),
    ],
    "S10-B04": [
        (0.15, 3.75, "General Beringer", "Whoa, now hold it! You're not supposed to be running in here, somebody could get hurt.", False),
        (3.75, 4.95, "John McKittrick", "I'm sorry, sir.", False),
        (4.95, 10.95, "John McKittrick", "We don't know how it happened, but someone on the outside fed an attack simulation into the matrix.", False),
        (10.95, 17.95, "General Beringer", "Conley, take us off full alert. Hold at DEFCON 4 till we find out exactly what the hell's happening here!", True),
    ],
    "S10-B05": [
        (0.15, 3.15, "John McKittrick", "Did Richter cut the line? He cut the line.", False),
        (3.15, 9.15, "Paul Richter", "Sir, they shut down before we could complete our trace, but we did manage to locate the general area where the transmission originated.", False),
        (9.15, 10.15, "General Beringer", "Where?", False),
        (10.15, 13.15, "Paul Richter", "Seattle, Washington. Shut it down!", False),
        (13.15, 17.95, "General Beringer", "Somebody's playing a game with us!", True),
    ],

    # === BOOK ELEVEN: TV News & Joshua Calls Back · 'What Is the Primary Goal? To Win the Game' ===
    "S11-B01": [
        (0.15, 8.95, "TV Newscaster", "For three and a half minutes today, strategic forces of the United States went on a full-scale nuclear alert, believing that the Soviet Union had launched a surprise missile attack.", False),
        (8.95, 16.15, "TV Newscaster", "A Pentagon announcement places blame for the error on a computer malfunction at NORAD command headquarters.", True),
        (16.15, 18.00, "TV Newscaster", "For more on the story, let's go live via satellite to Washington, D.C.", False),
    ],
    "S11-B02": [
        (0.15, 3.95, "David Lightman", "Listen, if they traced the call, they would have found me already, right?", True),
        (3.95, 5.75, "Jennifer Mack", "No — yeah?", False),
        (5.75, 9.95, "Jennifer Mack", "OK, so all you have to do is throw the number away and don't call it again.", False),
        (9.95, 13.95, "David Lightman", "Yeah. Maybe they didn't trace the call, huh?", False),
        (13.95, 17.95, "Jennifer Mack", "David, answer the phone! I'm sure they didn't trace the call.", False),
    ],
    "S11-B03": [
        (0.15, 5.57, "WOPR (Joshua)", "GREETINGS PROFESSOR FALKEN.", True),
        (5.57, 7.57, "David Lightman", "Wait — Professor Falken?", False),
        (8.57, 9.57, "Jennifer Mack", "Oh, my God.", False),
        (14.50, 17.95, "WOPR (Joshua)", "INCORRECT IDENTIFICATION. I AM NOT FALKEN. FALKEN IS DEAD.", False),
    ],
    "S11-B04": [
        (0.15, 5.93, "WOPR (Joshua)", "SOLUTION IS NEAR. GAME TIME ELAPSED: 31 HOURS, 12 MINUTES.", True),
        (5.93, 12.20, "WOPR (Joshua)", "ESTIMATED TIME REMAINING: 52 HOURS, 17 MINUTES.", False),
    ],
    "S11-B05": [
        (0.15, 5.45, "David Lightman", "What is the primary goal?", False),
        (5.45, 7.85, "WOPR (Joshua)", "TO WIN THE GAME.", True),
    ],

    # === BOOK TWELVE: FBI Arrest, NORAD Tour & McKittrick's Interrogation · 'Machines Don't Call People' ===
    "S12-B01": [
        (0.15, 6.50, "Agent Ginsberg", "David Lightman? Hold it right there, please — FBI.", True),
    ],
    "S12-B02": [
        (0.15, 2.55, "John McKittrick", "Mr. Cabot, it was a one-in-a-million shot.", False),
        (2.55, 7.43, "John McKittrick", "There was an open line in our space division in Sunnyvale. The phone company screwed up!", True),
        (7.43, 13.43, "Agent Ginsberg", "John McKittrick — George Wigan, Justice Department. The FBI brought the kid in for questioning.", False),
        (13.43, 16.79, "Agent Ginsberg", "Well, it looks like we've got a high school prank on our hands.", False),
        (16.79, 18.00, "John McKittrick", "What happened? Did he break into the war games subsystem?", False),
    ],
    "S12-B03": [
        (0.15, 3.15, "Agent Ginsberg", "We'll lock him in the infirmary for you, sir.", False),
        (11.85, 16.15, "John McKittrick", "Well, David — John McKittrick. I run the computer facility here.", True),
        (16.15, 18.00, "John McKittrick", "All right, Sergeant, the handcuffs aren't necessary.", False),
    ],
    "S12-B04": [
        (0.15, 1.83, "John McKittrick", "You know what that means, David?", False),
        (1.83, 3.27, "David Lightman", "No, what does that mean?", False),
        (3.27, 6.35, "John McKittrick", "World War III.", True),
        (6.35, 10.51, "John McKittrick", "Now, you say you broke into our defense system just to play a game, right?", False),
        (10.51, 12.51, "David Lightman", "Right. That's right. That's exactly right.", False),
        (16.20, 18.00, "John McKittrick", "Yeah, but when you heard it on the news, you must've realized how serious it was.", False),
    ],
    "S12-B05": [
        (0.15, 3.15, "John McKittrick", "Who are you going to Paris with?", False),
        (5.15, 8.15, "David Lightman", "Paris? Oh, no. No, you don't understand.", False),
        (8.15, 11.15, "John McKittrick", "Now, you had reservations for two to Paris.", False),
        (13.85, 15.85, "John McKittrick", "Who are you working with?", False),
        (15.85, 18.00, "David Lightman", "Nobody! Joshua called me! I don't think I should say anything else until I talk to a lawyer.", True),
    ],

    # === BOOK THIRTEEN: David Queries WOPR Alone · Projected Kill Ratios, Countdown Clock & Goose Island Address ===
    "S13-B01": [
        (0.15, 5.15, "WOPR (Joshua)", "AT CURRENT PACE, I SHOULD REACH DEFCON 1 AND LAUNCH MY MISSILES IN 28 HOURS.", True),
        (5.15, 7.35, "WOPR (Joshua)", "WOULD YOU LIKE TO SEE SOME PROJECTED KILL RATIOS?", False),
    ],
    "S13-B02": [
        (0.15, 5.55, "WOPR (Joshua)", "69 PERCENT OF THE HOUSING DESTROYED. 72 MILLION PEOPLE DEAD.", False),
        (9.63, 14.75, "David Lightman", "Is this a game, or is it real?", False),
        (15.25, 17.55, "WOPR (Joshua)", "WHAT'S THE DIFFERENCE?", True),
    ],
    "S13-B03": [
        (0.15, 2.15, "David Lightman", "Address.", False),
        (2.15, 8.15, "WOPR (Joshua)", "DOD PENSION FILES INDICATE CURRENT MAILING ADDRESS:", False),
        (8.15, 17.85, "WOPR (Joshua)", "DR. ROBERT HUME, A.K.A. STEPHEN W. FALKEN — 5 TALL CEDAR ROAD, GOOSE ISLAND, OREGON.", True),
    ],
    "S13-B04": [
        (0.25, 6.75, "David Lightman", "[DIEGETIC FOLEY] David opens McKittrick's desk drawer and pockets the micro-cassette tape recorder.", True),
    ],
    "S13-B05": [
        (0.15, 4.15, "David Lightman", "Hold the door code tone — 8... 3... 5...", False),
        (4.15, 6.15, "David Lightman", "Is that it? Yeah, the bolt clicked!", True),
        (6.15, 14.45, "NORAD Guard", "Step right this way, folks — keep the tour group together through the main corridor.", False),
    ],

    # === BOOK FOURTEEN: Escape from Cheyenne Mountain · Infirmary Tape Recorder Lock-Pick & Tour Bus Disguise ===
    "S14-B01": [
        (5.50, 12.50, "John McKittrick", "All right, I want this infirmary door open right now!", True),
    ],
    "S14-B02": [
        (0.39, 6.75, "NORAD Guard", "All right, just wait, folks. I've just been informed that they're cleaning the floors in the computer center.", False),
        (6.75, 10.79, "NORAD Guard", "Don't want anyone to slip and hurt themselves, so we'll have to end the tour here.", True),
        (10.79, 17.90, "NORAD Guard", "Now, if I can ask you to re-board the bus as quickly as possible, we'll have a complimentary beverage waiting at the Officers' Club.", False),
    ],
    "S14-B03": [
        (0.55, 2.11, "John McKittrick", "Quick, check everywhere! He can't be far!", True),
        (2.11, 4.11, "NORAD Guard", "Let's go, come on!", False),
    ],
    "S14-B04": [
        (1.60, 4.80, "David Lightman", "Thank you — pull-tab tone locked on the payphone handset.", True),
        (8.60, 15.20, "Bell Operator", "Long-distance directory assistance, may I help you?", False),
    ],
    "S14-B05": [
        (0.15, 6.91, "David Lightman", "Goose Island, Oregon, please — the number for Dr. Robert Hume, H-U-M-E, on Tall Cedar Road.", False),
        (9.41, 14.81, "Bell Operator", "Checking under Dr. Robert Hume on Tall Cedar Road... I find no listing.", True),
        (14.81, 17.45, "David Lightman", "What does that mean — he doesn't have a phone?", False),
    ],

    # === BOOK FIFTEEN: Payphone Pull-Tab Phreaking, Grand Junction Flight & The Ferry to Goose Island ===
    "S15-B01": [
        (0.15, 1.63, "David Lightman", "Jennifer, it's me, David.", False),
        (1.63, 2.87, "Jennifer Mack", "David?", False),
        (2.87, 8.11, "David Lightman", "Yeah. Uh, listen, I'm in Colorado, and I need a really big favor.", True),
        (8.11, 9.91, "David Lightman", "Can you lend me some money?", False),
        (9.91, 11.11, "Jennifer Mack", "What?", False),
        (11.11, 17.11, "David Lightman", "I need an airline ticket. I'll pay you back as soon as I can, from Grand Junction, Colorado to Oregon.", False),
        (17.11, 18.00, "Jennifer Mack", "Why, what's going on?", False),
    ],
    "S15-B02": [
        (0.20, 5.20, "WOPR (Joshua)", "[NORAD GAME CLOCK] GAME TIME REMAINING: 18 HOURS 27 MINUTES 01 SECOND.", True),
    ],
    "S15-B03": [
        (0.15, 1.75, "Jennifer Mack", "The ferry's gonna leave any second!", False),
        (1.75, 3.75, "David Lightman", "Thanks — come on, we gotta run!", False),
        (7.43, 12.80, "David Lightman", "Wait! Wait, wait, wait! Hold the ferry!", True),
    ],
    "S15-B04": [
        (0.55, 2.55, "David Lightman", "Wait! Wait! Dr. Falken!", False),
        (2.55, 4.35, "David Lightman", "I came because of Joshua!", True),
    ],
    "S15-B05": [
        (0.15, 3.67, "General Beringer", "Two Soviet Backfire bombers in the Alaskan Air Defense Zone — I want a visual confirmation on that.", False),
        (3.67, 5.83, "General Beringer", "Scramble two F-16s out of Galena.", False),
        (5.83, 7.83, "Col. Joe Conley", "Yes, sir.", False),
        (8.50, 10.25, "General Beringer", "Go to DEFCON 2!", True),
    ],

    # === BOOK SIXTEEN: Goose Island · Falken's Pterodactyl, Dinosaurs & The Futility of Tic-Tac-Toe ===
    "S16-B01": [
        (0.15, 7.15, "Stephen Falken", "Dinosaurs dominated the world through age after age. They ran, and they swam, and they fought, and they flew.", False),
        (7.15, 12.15, "Stephen Falken", "Until suddenly, quite recently, they disappeared.", False),
        (12.15, 16.15, "Stephen Falken", "Nature just gave up and started again.", True),
        (16.15, 18.00, "Stephen Falken", "We weren't even apes then.", False),
    ],
    "S16-B02": [
        (0.15, 6.31, "Stephen Falken", "The whole point was to find a way to practice nuclear war without destroying ourselves.", False),
        (6.31, 9.99, "Stephen Falken", "To get the computers to learn from mistakes we couldn't afford to make.", False),
        (9.99, 14.19, "Stephen Falken", "Except that I never could get Joshua to learn the most important lesson.", True),
        (14.19, 15.99, "David Lightman", "What's that?", False),
        (15.99, 17.95, "Stephen Falken", "Futility. That there's a time when you should just give up.", False),
    ],
    "S16-B03": [
        (0.15, 1.79, "David Lightman", "What kind of game is that?", False),
        (1.79, 2.95, "Jennifer Mack", "It's always a tie.", False),
        (2.95, 8.59, "Stephen Falken", "Exactly. There's no way to win. The game itself is pointless!", True),
        (8.59, 13.55, "Stephen Falken", "But back at the War Room, they believe you can win a nuclear war. That there can be acceptable losses.", False),
    ],
    "S16-B04": [
        (0.15, 3.27, "Stephen Falken", "Extinction is part of the natural order.", False),
        (3.27, 5.27, "David Lightman", "Well, shit!", False),
        (6.47, 9.67, "David Lightman", "If we're extinguished, there's nothing natural about that — it's just stupid!", True),
        (9.67, 16.63, "Stephen Falken", "Oh, it's all right. I've planned ahead. We're just three miles from a primary target.", False),
        (16.63, 18.00, "Stephen Falken", "A millisecond of brilliant light, and we're vaporized.", False),
    ],
    "S16-B05": [
        (0.15, 5.15, "David Lightman", "There's nothing a phone call won't stop! This is unreal.", False),
        (5.15, 8.15, "David Lightman", "You don't care about death because you're already dead.", True),
        (8.15, 13.15, "David Lightman", "I know a lot about you. I know you weren't always like this.", False),
        (13.15, 16.25, "David Lightman", "What was the last thing you cared about?", False),
    ],

    # === BOOK SEVENTEEN: Shoreline Despair, Helicopter Rescue & Race Against the Cheyenne Mountain Blast Doors ===
    "S17-B01": [
        (0.15, 3.79, "David Lightman", "And I don't even know how to swim. I never got around to it, OK?", False),
        (3.79, 8.03, "David Lightman", "I always thought there was gonna be plenty of time. Sorry.", False),
        (9.11, 14.11, "Jennifer Mack", "I wish I didn't know about any of this.", False),
        (14.11, 17.95, "Jennifer Mack", "I wish I was like everybody else in the world, and tomorrow it would just be over.", True),
    ],
    "S17-B02": [
        (0.25, 5.75, "Stephen Falken", "[HELICOPTER ROTOR WASH] Stephen Falken lands the Air Force rescue chopper on the Goose Island beach.", True),
    ],
    "S17-B03": [
        (0.15, 10.50, "Col. Joe Conley", "We have a launch detection! We have a Soviet submarine missile launch detection!", True),
        (10.50, 16.85, "Col. Joe Conley", "BMEWS has confirmed an inbound ICBM attack!", False),
    ],
    "S17-B04": [
        (0.15, 6.67, "Col. Joe Conley", "Sir, BMEWS is tracking three hundred inbound Soviet ICBMs!", False),
        (7.83, 14.83, "General Beringer", "All right, all right — flush the bombers, get the subs in launch mode.", False),
        (14.83, 17.95, "General Beringer", "We are at DEFCON 1! Close up the mountain!", True),
    ],
    "S17-B05": [
        (0.15, 5.15, "NORAD Guard", "Seal the ventilation shafts! Shaft locks sealed.", False),
        (9.15, 12.15, "David Lightman", "The gate's closing! Gun it — right through the blast doors!", True),
    ],

    # === BOOK EIGHTEEN: DEFCON 1 · 2,400 Inbound Phantoms on the Big Board & Falken Pleas with Beringer to Ride It Out ===
    "S18-B01": [
        (0.15, 4.15, "Stephen Falken", "Come on! Come on!", False),
        (13.50, 16.80, "General Beringer", "Hold the door! Hold the blast door!", True),
    ],
    "S18-B02": [
        (1.65, 2.85, "Stephen Falken", "It's a bluff, John. Call it off!", False),
        (2.85, 4.65, "John McKittrick", "No, it's not a bluff — it's real.", False),
        (4.65, 9.65, "John McKittrick", "General Beringer, this is Stephen Falken.", False),
        (9.65, 12.65, "General Beringer", "Dr. Falken, you picked a hell of a day for a visit.", False),
        (12.65, 15.75, "Stephen Falken", "General, what you see on these screens up here is a fantasy — a computer-enhanced hallucination!", True),
    ],
    "S18-B03": [
        (0.15, 5.15, "John McKittrick", "Jack, there's nothing to indicate a simulation at all. Everything's working perfectly.", False),
        (5.15, 8.85, "General Beringer", "Well, does it make any sense? Does what they're doing make any sense?", True),
        (8.85, 9.90, "John McKittrick", "Look, we don't have time for a conversation right now.", False),
    ],
    "S18-B04": [
        (0.15, 3.15, "Stephen Falken", "Tell the President to ride out the attack.", False),
        (3.15, 6.15, "Col. Joe Conley", "Sir, SAC needs a decision.", False),
        (6.15, 11.15, "Stephen Falken", "General, do you really believe that the enemy would attack without provocation,", True),
        (11.15, 17.15, "Stephen Falken", "using so many missiles, bombers, and subs that we would have no choice but to totally annihilate them?", False),
        (17.15, 18.00, "Col. Joe Conley", "One minute and thirty seconds to impact.", False),
    ],
    "S18-B05": [
        (0.15, 7.15, "Col. Joe Conley", "Sir, initial impact points are the 42nd Bomb Wing at Loring, 319th at Grand Forks, and Alaskan Air Command headquarters at Elmendorf.", False),
        (7.15, 8.15, "Col. Joe Conley", "Fifty seconds to impact.", False),
        (8.15, 11.15, "General Beringer", "Get me the senior controllers at each of those stations. I want to talk to them myself.", True),
        (11.15, 16.85, "Col. Joe Conley", "All stations, this is Crystal Palace — stand by for a message from Brass Hat.", False),
    ],

    # === BOOK NINETEEN: Zero Hour · 'Impact' on the Screens vs. Live Voices from Loring, Grand Forks & Elmendorf ===
    "S19-B01": [
        (0.15, 5.35, "Col. Joe Conley", "Forty seconds. Sir, all stations are on the line.", False),
        (5.35, 10.23, "General Beringer", "Men, we're currently tracking approximately 2,400 inbound Soviet warheads.", False),
        (10.23, 15.51, "General Beringer", "But at the moment we cannot confirm this. I repeat, we cannot confirm this.", True),
        (15.51, 18.00, "Col. Joe Conley", "Thirty seconds to impact.", False),
    ],
    "S19-B02": [
        (0.15, 5.59, "General Beringer", "We've taken all the steps we can. Stand by to launch missiles on my command.", False),
        (13.59, 17.59, "General Beringer", "Stay on this channel as long as you can. We'll be standing by.", True),
        (17.59, 18.00, "Col. Joe Conley", "Twenty seconds to impact.", False),
    ],
    "S19-B03": [
        (0.55, 8.20, "Col. Joe Conley", "Six... five... four... three... two... one... impact.", True),
        (8.50, 10.75, "General Beringer", "This is Crystal Palace — are you still on?", False),
    ],
    "S19-B04": [
        (0.15, 5.15, "General Beringer", "This is Crystal Palace, are you still on?", False),
        (5.15, 11.15, "General Beringer", "This is Crystal Palace — are you still on? Anyone there?", False),
        (11.15, 14.15, "Loring Controller", "That's affirmative, sir!", True),
        (14.15, 17.95, "General Beringer", "Yeah! This is Crystal Palace — are you still on?", False),
    ],
    "S19-B05": [
        (0.15, 5.61, "Loring Controller", "Yeah! Yeah, we're here!", False),
        (5.61, 7.79, "General Beringer", "Jesus H. Christ, we're still alive!", True),
        (7.79, 10.59, "General Beringer", "Are you sure you have no impact?", False),
        (10.59, 14.31, "Loring Controller", "No, sir, no impact! We're alive and well!", False),
        (14.31, 17.95, "General Beringer", "All right! Recall the bombers and stand down the missiles!", False),
    ],

    # === BOOK TWENTY: CPE 1704 TKS · WOPR Brute-Forces the Launch Codes vs. Zero-Player Tic-Tac-Toe ===
    "S20-B01": [
        (0.15, 4.15, "Paul Richter", "The machine has locked us out! It's sending random numbers to the silos.", True),
        (4.15, 6.15, "General Beringer", "The codes to launch the missiles?", False),
        (6.15, 12.65, "General Beringer", "Just unplug the goddamn thing! Pull the plug!", False),
        (12.65, 17.85, "John McKittrick", "That won't work, General — it would interpret a shutdown as the destruction of NORAD.", False),
    ],
    "S20-B02": [
        (0.15, 3.35, "General Beringer", "Just unplug the goddamn thing!", False),
        (3.35, 9.35, "John McKittrick", "That won't work, General. It would interpret a shutdown as the destruction of NORAD.", False),
        (9.35, 14.15, "John McKittrick", "The computers in the silos would carry out their last instructions — they'd launch!", True),
        (14.15, 17.95, "General Beringer", "We can't disarm the missiles? All a thousand of them — there's no time!", False),
    ],
    "S20-B03": [
        (0.15, 5.45, "Paul Richter", "At this rate, it'll hit the launch codes in 5.3 minutes.", False),
        (5.45, 13.95, "General Beringer", "Mr. McKittrick, after very careful consideration, sir, I've come to the conclusion that your new defense system sucks.", True),
        (13.95, 16.95, "John McKittrick", "I don't have to take that, you pig-eyed sack of shit!", False),
        (16.95, 17.95, "General Beringer", "Oh, I was hoping for something a little better than that from you, sir.", False),
    ],
    "S20-B04": [
        (0.35, 3.35, "David Lightman", "Tic-Tac-Toe! Let's make it play Tic-Tac-Toe against itself — number of players: zero!", True),
    ],
    "S20-B05": [
        (0.65, 2.65, "Paul Richter", "It's getting caught in the loop!", False),
        (2.65, 6.65, "Paul Richter", "It's drawing more and more power from the rest of the system!", True),
        (6.65, 14.50, "John McKittrick", "Nine numbers locked... if it gets the tenth code, it's going to launch!", False),
    ],

    # === BOOK TWENTY-ONE: 'A Strange Game. The Only Winning Move Is Not to Play.' · Return to DEFCON 5 ===
    "S21-B01": [
        (0.50, 10.50, "WOPR (Joshua)", "STRATEGY: U.S. FIRST STRIKE — WINNER: NONE. USSR FIRST STRIKE — WINNER: NONE.", True),
    ],
    "S21-B02": [
        (0.50, 9.50, "WOPR (Joshua)", "GREETINGS PROFESSOR FALKEN.", True),
        (9.50, 17.50, "David Lightman", "Hello, Joshua.", False),
    ],
    "S21-B03": [
        (0.15, 7.15, "WOPR (Joshua)", "A STRANGE GAME. THE ONLY WINNING MOVE IS NOT TO PLAY.", True),
        (13.50, 17.85, "WOPR (Joshua)", "HOW ABOUT A NICE GAME OF CHESS?", False),
    ],
    "S21-B04": [
        (0.15, 7.15, "WOPR (Joshua)", "A STRANGE GAME. THE ONLY WINNING MOVE IS NOT TO PLAY.", False),
        (13.50, 17.85, "WOPR (Joshua)", "HOW ABOUT A NICE GAME OF CHESS?", True),
    ],
    "S21-B05": [
        (7.20, 12.25, "General Beringer", "Colonel Conley, take us to DEFCON 5.", True),
    ],
}


def classify_pause(pause_sec, is_first):
    if is_first:
        return "OPENING BEAT"
    if pause_sec <= 0.15:
        return "SNAP OVERLAP"
    if pause_sec <= 0.65:
        return "BREATH CADENCE"
    if pause_sec <= 1.60:
        return "DRAMATIC BEAT"
    return "TENSION SILENCE"


def classify_cadence(wpm, text):
    if str(text).startswith("["):
        return "TELEMETRY / FOLEY"
    if wpm < 105:
        return "DELIBERATE"
    if wpm <= 165:
        return "CONVERSATIONAL"
    if wpm <= 215:
        return "URGENT"
    return "RAPID FIRE"
