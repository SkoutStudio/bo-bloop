# Bo & Bloop — Episode 1: "Bo Counts the Bubbles"  (series: Count with Bo)
# Lesson: when we count, we say every number, in order, one for each thing.
#
# Beat types
#   say   : a spoken line. who = bo | bloop | both. expr = expression of the speaker.
#           listener_expr optionally sets the other character's face.
#   count : bubble n lights up, a pause for the kids at home, then the number is said.
#   pause : silence (visual action can still happen)
#   scene : cut to a scene layout
#   song  : the counting chant on a fixed beat
# act = visual actions fired when the beat starts.

N = ["zero", "One!", "Two!", "Three!", "Four!", "Five!", "Six!", "Seven!", "Eight!", "Nine!", "Ten!"]

BEATS = [
    # 1 — HOOK (close-up of Bo)
    {"t": "scene", "name": "hook"},
    {"t": "pause", "dur": 0.8, "act": {"hook_bubbles": True}},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Hi friends! It's me, Bo!"},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Look at all these bubbles!"},
    {"t": "say", "who": "bo", "expr": "surprised", "text": "How many bubbles can you see?", "sub": "How many bubbles can YOU see?"},
    {"t": "pause", "dur": 2.2, "act": {"question": True}},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Let's find out together!"},
    {"t": "pause", "dur": 0.4},

    # 2 — INTRO JINGLE
    {"t": "scene", "name": "title"},
    {"t": "jingle"},

    # 3 — PROBLEM
    {"t": "scene", "name": "lab"},
    {"t": "pause", "dur": 0.6},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Beep boop! I'm making a bubble jar!", "sub": "Beep-boop! I'm making a bubble jar!"},
    {"t": "say", "who": "bo", "expr": "happy", "text": "I need to count the bubbles first.",
     "act": {"spawn": [0, 1, 2, 3, 4]}},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Easy!"},
    {"t": "say", "who": "bo", "expr": "excited", "text": "One!", "gap": 0.12, "act": {"label": [0, 1, True]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Two!", "gap": 0.12, "act": {"label": [1, 2, True]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Three!", "gap": 0.12, "act": {"label": [2, 3, True]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Five!", "gap": 0.12, "act": {"label": [3, 5, False]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Ten!", "gap": 0.5, "act": {"label": [4, 10, False]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Ten bubbles! I'm the best counter in Bubble Bay!"},
    {"t": "pause", "dur": 0.4, "act": {"bloop_enter": True}},
    {"t": "pause", "dur": 1.0},
    {"t": "say", "who": "bloop", "expr": "giggle", "text": "Bloop! Hi, Bo!", "listener_expr": "happy"},
    {"t": "say", "who": "bloop", "expr": "thinking", "text": "Hmm. Bo, I think you skipped some numbers."},
    {"t": "say", "who": "bo", "expr": "confused", "text": "Skipped? Beep... boop?"},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "Let's look again. Friends at home, can you help us count?", "listener_expr": "happy"},

    # 4 — ATTEMPT
    {"t": "pause", "dur": 0.6, "act": {"clear_labels": True}},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "We say one number for each bubble. One at a time. Ready?"},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Ready!"},
    {"t": "count", "n": 1, "who": "bo"},
    {"t": "count", "n": 2, "who": "bloop"},
    {"t": "count", "n": 3, "who": "bo"},
    {"t": "count", "n": 4, "who": "bloop"},
    {"t": "count", "n": 5, "who": "both"},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "Five bubbles!", "act": {"big": 5}},
    {"t": "say", "who": "bo", "expr": "surprised", "text": "Five? Not ten? Oh no, I went too fast!"},
    {"t": "say", "who": "bloop", "expr": "giggle", "text": "That's okay, Bo! Let's blow five more bubbles!", "listener_expr": "happy"},
    {"t": "pause", "dur": 1.6, "act": {"spawn": [5, 6, 7, 8, 9]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "My turn! Six!", "gap": 0.15, "act": {"label": [5, 6, True]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Eight!", "gap": 0.15, "act": {"label": [6, 8, False]}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Ten!", "gap": 0.4, "act": {"label": [7, 10, False]}},
    {"t": "say", "who": "bloop", "expr": "surprised", "text": "Oops! Slow down, Bo. Don't skip any!"},
    {"t": "say", "who": "bo", "expr": "sad", "text": "Beep. I skipped again.", "listener_expr": "sad"},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "Let's do it together, nice and slow.", "listener_expr": "happy",
     "act": {"clear_labels_from": 5}},
    {"t": "count", "n": 6, "who": "both"},
    {"t": "count", "n": 7, "who": "both"},
    {"t": "count", "n": 8, "who": "both"},
    {"t": "count", "n": 9, "who": "both"},
    {"t": "count", "n": 10, "who": "both"},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Ten! Now it really is ten!", "act": {"big": 10}},

    # 5 — SOLUTION & LESSON
    {"t": "say", "who": "bloop", "expr": "happy", "text": "When we count, we say every number, in order."},
    {"t": "say", "who": "bo", "expr": "happy", "text": "One number for every bubble!", "act": {"lesson": True}},
    {"t": "say", "who": "bloop", "expr": "excited", "text": "Let's count all ten bubbles again. Count with us!", "act": {"lesson": False}},
    {"t": "fastcount"},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Ten bubbles! My bubble jar is ready!", "act": {"to_jar": True}},
    {"t": "pause", "dur": 1.8},

    # 6 — SONG
    {"t": "scene", "name": "song"},
    {"t": "song"},

    # 7 — OUTRO
    {"t": "scene", "name": "lab_end"},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Great counting, friends!"},
    {"t": "say", "who": "bloop", "expr": "giggle", "text": "Bloop! You counted all the way to ten!", "listener_expr": "excited"},
    {"t": "say", "who": "both", "expr": "happy", "text": "Bye bye from Bubble Bay!", "sub": "Bye-bye from Bubble Bay!", "act": {"wave": True}},
    {"t": "pause", "dur": 0.8},
    {"t": "scene", "name": "end"},
    {"t": "pause", "dur": 6.0},
]

SONG = [  # (who, text) — one line every 2 bars at 100 BPM
    ("bloop", "One, two, three, four, five,"),
    ("bo", "little bubbles come alive!"),
    ("bloop", "Six, seven, eight, nine, ten,"),
    ("bo", "let's count them all again!"),
]
