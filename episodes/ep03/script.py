# Bo & Bloop — Episode 3: "Circle Rocks & Square Rocks"  (series: Shape Reef)
# Lesson: circles are round with no corners, so they roll.
#         Squares have 4 straight sides and 4 corners, so they stay put (good for building).
#         Sorting things by shape.

N = ["zero", "One!", "Two!", "Three!", "Four!"]

# 8 rocks to sort: c = circle, s = square
ROCKS = ["c", "s", "s", "c", "s", "c", "c", "s"]
SORT_WHO = ["bo", "bloop", "bo", "bloop", "both", "both", "both", "both"]

BEATS = [
    # 1 — HOOK
    {"t": "scene", "name": "hook"},
    {"t": "pause", "dur": 0.8, "act": {"hook_rocks": True}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Hi friends! Look at all these rocks!"},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Some rocks are round, and some rocks are pointy at the corners!"},
    {"t": "say", "who": "bo", "expr": "surprised", "text": "What shapes can you see?", "sub": "What shapes can YOU see?"},
    {"t": "pause", "dur": 2.2, "act": {"question": True}},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Let's find out together!"},
    {"t": "pause", "dur": 0.4},

    # 2 — INTRO JINGLE
    {"t": "scene", "name": "title"},
    {"t": "jingle"},

    # 3 — PROBLEM: Bo stacks round rocks and they roll away
    {"t": "scene", "name": "lab"},
    {"t": "pause", "dur": 0.6},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Beep boop! Today I am building a rock tower!", "sub": "Beep-boop! Today I'm building a rock tower!"},
    {"t": "say", "who": "bo", "expr": "happy", "text": "One rock, two rocks, three rocks. Up, up, up!", "act": {"tumble": True}},
    {"t": "pause", "dur": 1.6},
    {"t": "say", "who": "bo", "expr": "surprised", "text": "Oh no! My rocks are rolling away!"},
    {"t": "say", "who": "bo", "expr": "confused", "text": "Beep... boop? Why do they roll?"},
    {"t": "pause", "dur": 0.4, "act": {"bloop_enter": True}},
    {"t": "pause", "dur": 1.0},
    {"t": "say", "who": "bloop", "expr": "giggle", "text": "Bloop! Hi, Bo!", "listener_expr": "happy"},
    {"t": "say", "who": "bloop", "expr": "thinking", "text": "Those are circle rocks. A circle is round, and it has no corners."},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "That's why circles roll, roll, roll!", "listener_expr": "surprised"},
    {"t": "say", "who": "bloop", "expr": "excited", "text": "For a tower, we need square rocks. Look!", "act": {"square_show": True}},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "A square has four straight sides and four corners. Let's count the corners!"},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Friends at home, count with us!"},

    # 4 — ATTEMPT: count corners, then sort the rocks
    {"t": "corner", "n": 1, "who": "bo"},
    {"t": "corner", "n": 2, "who": "bloop"},
    {"t": "corner", "n": 3, "who": "bo"},
    {"t": "corner", "n": 4, "who": "both"},
    {"t": "say", "who": "bo", "expr": "surprised", "text": "Four corners! Squares have four corners!", "act": {"big": 4}},
    {"t": "say", "who": "bloop", "expr": "excited", "text": "Now let's sort the rocks. Circles go here. Squares go there!",
     "act": {"square_hide": True, "spawn": list(range(8)), "bins": True}},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Is it a circle, or a square? You tell us!"},
    {"t": "sort", "i": 0}, {"t": "sort", "i": 1}, {"t": "sort", "i": 2}, {"t": "sort", "i": 3},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "Great job! Four more rocks!"},
    {"t": "sort", "i": 4}, {"t": "sort", "i": 5}, {"t": "sort", "i": 6}, {"t": "sort", "i": 7},
    {"t": "say", "who": "bo", "expr": "excited", "text": "All sorted! Four circles and four squares!"},

    # 5 — SOLUTION & LESSON
    {"t": "say", "who": "bo", "expr": "happy", "text": "Now I'll build my tower with square rocks.", "act": {"build": True}},
    {"t": "pause", "dur": 2.4},
    {"t": "say", "who": "bo", "expr": "excited", "text": "It stays up! Squares don't roll!", "act": {"tower_done": True}},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "Circles roll. Squares have four corners.", "act": {"lesson": True}},
    {"t": "say", "who": "both", "expr": "excited", "text": "Circles roll. Squares have four corners!"},
    {"t": "say", "who": "bloop", "expr": "giggle", "text": "And circle rocks are perfect for rolling games!", "act": {"lesson": False, "roll_fun": True}},
    {"t": "pause", "dur": 2.0},

    # 6 — SONG
    {"t": "scene", "name": "song"},
    {"t": "song"},

    # 7 — OUTRO
    {"t": "scene", "name": "lab_end"},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Great sorting, friends!"},
    {"t": "say", "who": "bloop", "expr": "giggle", "text": "Bloop! Remember: circles roll, squares have four corners!", "listener_expr": "excited"},
    {"t": "say", "who": "both", "expr": "happy", "text": "Bye bye from Bubble Bay!", "sub": "Bye-bye from Bubble Bay!", "act": {"wave": True}},
    {"t": "pause", "dur": 0.8},
    {"t": "scene", "name": "end"},
    {"t": "pause", "dur": 6.0},
]

# (beat, who, line, act)
SONG = [
    (4, "bloop", "Circle, circle, round and round,", {"song_phase": "circle"}),
    (10, "bo", "rolling, rolling on the ground!", None),
    (16, "bloop", "Square, square, count with me:", {"song_phase": "square"}),
    (28, "bo", "four straight sides and corners four!", None),
    (34, "both", "Circles roll and squares stand tall!", {"song_phase": "both"}),
]
SONG_CHANT = 22  # beats 22..25: "One, two, three, four!"
SONG_BEATS = 42
TITLE = "Shape Reef: Circle Rocks & Square Rocks"
