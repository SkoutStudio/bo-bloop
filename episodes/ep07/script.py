# Bo & Bloop — Episode 7: "Bo's Missing Bolt"  (series: Count with Bo)
# Lesson: counting backwards from 10 to 1 — each number is one less. Don't skip any!
# Story: Bo's Bubble Rocket is missing a bolt (Bloop finds it in the sand). Then Bo counts the wrong way
#        ("one, two, three, go!", then "ten, nine, seven...") and the rocket sputters. With the kids they count
#        down 10 -> 1 slowly, and the rocket blasts off and floats back down.

N = ["zero", "One!", "Two!", "Three!", "Four!", "Five!", "Six!", "Seven!", "Eight!", "Nine!", "Ten!"]

BEATS = [
    # 1 — HOOK
    {"t": "scene", "name": "hook"},
    {"t": "pause", "dur": 0.8, "act": {"hook_items": True}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Hi friends! Can you count backwards?"},
    {"t": "say", "who": "bo", "expr": "thinking", "text": "Ten, nine, eight... What comes next?"},
    {"t": "pause", "dur": 2.2, "act": {"question": True}},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Let's learn together!"},
    {"t": "pause", "dur": 0.4},

    # 2 — INTRO JINGLE
    {"t": "scene", "name": "title"},
    {"t": "jingle"},

    # 3 — PROBLEM: missing bolt, then counting the wrong way
    {"t": "scene", "name": "lab"},
    {"t": "pause", "dur": 0.6, "act": {"rocket": True}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Beep boop! Look at my Bubble Rocket!", "sub": "Beep-boop! Look at my Bubble Rocket!"},
    {"t": "say", "who": "bo", "expr": "happy", "text": "It can fly all the way up to the top of the sea!"},
    {"t": "say", "who": "bo", "expr": "surprised", "text": "Oh no! One bolt is missing! My rocket is wobbly!", "act": {"wobble": True}},
    {"t": "pause", "dur": 0.4, "act": {"bloop_enter": True}},
    {"t": "pause", "dur": 1.0},
    {"t": "say", "who": "bloop", "expr": "giggle", "text": "Bloop! Hi, Bo! Is this your bolt? I found it in the sand!", "listener_expr": "surprised"},
    {"t": "say", "who": "bo", "expr": "excited", "text": "My missing bolt! Thank you, Bloop!", "act": {"bolt": True}},
    {"t": "pause", "dur": 1.4},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Now, blast off! One, two, three, go!", "act": {"sputter": True}},
    {"t": "pause", "dur": 1.2},
    {"t": "say", "who": "bo", "expr": "confused", "text": "Huh? It won't go!"},
    {"t": "say", "who": "bloop", "expr": "thinking", "text": "Oh, Bo! For a rocket, we count backwards."},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "We start at ten, and count down to one. Each number is one less.", "act": {"board": True}},
    {"t": "say", "who": "bo", "expr": "thinking", "text": "Okay! Ten, nine, seven...", "act": {"wrong": "auto"}},
    {"t": "pause", "dur": 0.4, "act": {"sputter": True}},
    {"t": "pause", "dur": 1.0},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "Oops! After nine comes eight. We skipped a number!", "act": {"show8": True}},
    {"t": "say", "who": "bloop", "expr": "excited", "text": "Let's count down slowly, with our friends!", "act": {"reset": True}},

    # 4 — TRYING TOGETHER: the countdown with the kids
    {"t": "count", "from": 10, "to": 1},
    {"t": "say", "who": "both", "expr": "excited", "text": "Blast off!", "act": {"go": True}},
    {"t": "pause", "dur": 2.6},
    {"t": "say", "who": "bloop", "expr": "excited", "text": "Wow! Look at it go!"},
    {"t": "say", "who": "bo", "expr": "happy", "text": "And here it comes, back down to Bubble Bay!", "act": {"land": True}},
    {"t": "pause", "dur": 2.0},

    # 5 — SOLUTION & LESSON
    {"t": "say", "who": "bloop", "expr": "happy", "text": "Counting backwards means each number is one less.", "act": {"lesson": True}},
    {"t": "say", "who": "both", "expr": "excited", "text": "Ten, nine, eight, seven, six, five, four, three, two, one!", "act": {"sweep": "auto", "n": 10}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Thank you, Bloop! Counting down is fun!", "act": {"lesson": False, "hug": True}},
    {"t": "pause", "dur": 1.6},

    # 6 — SONG
    {"t": "scene", "name": "song"},
    {"t": "song"},

    # 7 — OUTRO
    {"t": "scene", "name": "lab_end"},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Great counting, friends!"},
    {"t": "say", "who": "bloop", "expr": "giggle", "text": "Bloop! Count down from ten at home!", "listener_expr": "excited"},
    {"t": "say", "who": "both", "expr": "happy", "text": "Bye bye from Bubble Bay!", "sub": "Bye-bye from Bubble Bay!", "act": {"wave": True}},
    {"t": "pause", "dur": 0.8},
    {"t": "scene", "name": "end"},
    {"t": "pause", "dur": 6.0},
]

# (beat, who, line, act)
SONG = [
    (4, "bloop", "Ten, nine, eight, seven, six,", {"song_phase": "top"}),
    (10, "bo", "five, four, three, two, one!", {"song_phase": "bottom"}),
    (16, "bloop", "Counting backwards, one less each time,", {"song_phase": "less"}),
    (22, "both", "Blast off! Up we go!", {"song_phase": "blast"}),
    (28, "bo", "Ten down to one, it's so much fun!", {"song_phase": "again"}),
    (34, "both", "Ten, nine, eight... blast off!", {"song_phase": "all"}),
]
SONG_CHANT = 0
CHANT_N = 0
SONG_BEATS = 42
TITLE = "Count with Bo: Bo's Missing Bolt"
