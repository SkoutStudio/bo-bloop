# Bo & Bloop — Episode 2: "Ten Little Starfish"  (series: Count with Bo)
# Lesson: when things move around, move each one as you count it, so nothing is counted twice.
#         The last number you say tells you how many there are.

N = ["zero", "One!", "Two!", "Three!", "Four!", "Five!", "Six!", "Seven!", "Eight!", "Nine!", "Ten!"]

BEATS = [
    # 1 — HOOK
    {"t": "scene", "name": "hook"},
    {"t": "pause", "dur": 0.8, "act": {"hook_bubbles": True}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Hi friends! Look, little stars on the sand!"},
    {"t": "say", "who": "bo", "expr": "happy", "text": "They're starfish! And they're wiggling everywhere!"},
    {"t": "say", "who": "bo", "expr": "surprised", "text": "How many starfish can you see?", "sub": "How many starfish can YOU see?"},
    {"t": "pause", "dur": 2.2, "act": {"question": True}},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Let's count them together!"},
    {"t": "pause", "dur": 0.4},

    # 2 — INTRO JINGLE
    {"t": "scene", "name": "title"},
    {"t": "jingle"},

    # 3 — PROBLEM
    {"t": "scene", "name": "lab"},
    {"t": "pause", "dur": 0.6},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Beep boop! The starfish want to go home to the Starfish Bed.", "sub": "Beep-boop! The starfish want to go home to the Starfish Bed."},
    {"t": "say", "who": "bo", "expr": "happy", "text": "First I need to know how many there are.", "act": {"spawn": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "One!", "gap": 0.12, "act": {"label": [0, 1, True]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Two!", "gap": 0.12, "act": {"label": [1, 2, True]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Three!", "gap": 0.12, "act": {"label": [2, 3, True]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Four!", "gap": 0.12, "act": {"label": [2, 4, False]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Five!", "gap": 0.12, "act": {"label": [3, 5, True]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Six!", "gap": 0.12, "act": {"label": [4, 6, True]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Seven!", "gap": 0.12, "act": {"label": [4, 7, False]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Eight!", "gap": 0.12, "act": {"label": [5, 8, True]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Nine!", "gap": 0.12, "act": {"label": [6, 9, True]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Ten!", "gap": 0.12, "act": {"label": [7, 10, True]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Eleven!", "gap": 0.12, "act": {"label": [8, 11, True]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Twelve!", "gap": 0.5, "act": {"label": [9, 12, True]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Twelve starfish! Wow!"},
    {"t": "pause", "dur": 0.4, "act": {"bloop_enter": True}},
    {"t": "pause", "dur": 1.0},
    {"t": "say", "who": "bloop", "expr": "giggle", "text": "Bloop! Hi, Bo!", "listener_expr": "happy"},
    {"t": "say", "who": "bloop", "expr": "thinking", "text": "Twelve? Hmm. I think some starfish wiggled, and you counted them twice!"},
    {"t": "say", "who": "bo", "expr": "confused", "text": "Twice? Beep... boop?"},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "Here's a trick. Every time we count a starfish, we move it to the Starfish Bed.", "listener_expr": "happy"},
    {"t": "say", "who": "bloop", "expr": "excited", "text": "Then we can never count it again! Friends at home, count with us!"},

    # 4 — ATTEMPT (move each one as we count)
    {"t": "pause", "dur": 0.6, "act": {"clear_labels": True}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Ready!"},
    {"t": "count", "n": 1, "who": "bo", "move": True},
    {"t": "count", "n": 2, "who": "bloop", "move": True},
    {"t": "count", "n": 3, "who": "bo", "move": True},
    {"t": "count", "n": 4, "who": "bloop", "move": True},
    {"t": "count", "n": 5, "who": "both", "move": True},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "Five in the bed! Let's keep going.", "act": {"big": 5}},
    {"t": "count", "n": 6, "who": "both", "move": True},
    {"t": "count", "n": 7, "who": "both", "move": True},
    {"t": "count", "n": 8, "who": "both", "move": True},
    {"t": "count", "n": 9, "who": "both", "move": True},
    {"t": "count", "n": 10, "who": "both", "move": True},
    {"t": "say", "who": "bo", "expr": "surprised", "text": "No more starfish on the sand! The last number was ten.", "act": {"big": 10}},

    # 5 — SOLUTION & LESSON
    {"t": "say", "who": "bloop", "expr": "happy", "text": "That's right! The last number we say tells us how many."},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Ten little starfish! Not twelve!", "act": {"lesson": True}},
    {"t": "say", "who": "bloop", "expr": "excited", "text": "Let's count them in the bed one more time. Count with us!", "act": {"lesson": False}},
    {"t": "fastcount"},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Ten little starfish, safe at home!", "act": {"to_jar": True}},
    {"t": "pause", "dur": 1.6},

    # 6 — SONG
    {"t": "scene", "name": "song"},
    {"t": "song"},

    # 7 — OUTRO
    {"t": "scene", "name": "lab_end"},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Great counting, friends!"},
    {"t": "say", "who": "bloop", "expr": "giggle", "text": "Bloop! Remember: move it, then count it!", "listener_expr": "excited"},
    {"t": "say", "who": "both", "expr": "happy", "text": "Bye bye from Bubble Bay!", "sub": "Bye-bye from Bubble Bay!", "act": {"wave": True}},
    {"t": "pause", "dur": 0.8},
    {"t": "scene", "name": "end"},
    {"t": "pause", "dur": 6.0},
]

SONG = [
    ("bloop", "One, two, three, four, five,"),
    ("bo", "little starfish swim and dive!"),
    ("bloop", "Six, seven, eight, nine, ten,"),
    ("bo", "see you on the reef again!"),
]
