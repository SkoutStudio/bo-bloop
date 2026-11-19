# Bo & Bloop — Episode 5: "Why Do Things Float?"  (series: Why, Bo?)
# Lesson: light things and things full of air float; heavy, solid things sink. Not sure? Test and see!
# Story: Bo thinks "big things sink, small things float". His small pebble sinks and his big beach ball floats.
#        Bloop shows him how to test and see (key sinks, duck floats), then the magic bottle: empty = floats,
#        filled with sand = sinks.

N = ["zero", "One!", "Two!", "Three!"]

BEATS = [
    # 1 — HOOK
    {"t": "scene", "name": "hook"},
    {"t": "pause", "dur": 0.8, "act": {"hook_items": True}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Hi friends! I have a question for you."},
    {"t": "say", "who": "bo", "expr": "thinking", "text": "If I put a ball in the water, will it float on top?", "sub": "If I put a ball in the water, will it FLOAT on top..."},
    {"t": "say", "who": "bo", "expr": "surprised", "text": "Or will it sink to the bottom?", "sub": "...or SINK to the bottom?"},
    {"t": "pause", "dur": 2.2, "act": {"question": True}},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Let's find out together!"},
    {"t": "pause", "dur": 0.4},

    # 2 — INTRO JINGLE
    {"t": "scene", "name": "title"},
    {"t": "jingle"},

    # 3 — PROBLEM: Bo's rule "big sinks, small floats" is wrong
    {"t": "scene", "name": "lab"},
    {"t": "pause", "dur": 0.6, "act": {"tank": True}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Beep boop! Welcome to my float or sink tank!", "sub": "Beep-boop! Welcome to my Float-or-Sink tank!"},
    {"t": "say", "who": "bo", "expr": "happy", "text": "I already know the answer. Big things sink, and small things float!", "act": {"rule": True}},
    {"t": "say", "who": "bo", "expr": "happy", "text": "This pebble is small. So it will float!", "act": {"show": "pebble", "guess": "pebble", "pick": "float"}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "In you go!", "act": {"drop": "pebble"}},
    {"t": "pause", "dur": 1.8},
    {"t": "say", "who": "bo", "expr": "surprised", "text": "Oh! It sank!", "sub": "Oh! It SANK!", "act": {"result": "pebble"}},
    {"t": "say", "who": "bo", "expr": "thinking", "text": "Hmm. My beach ball is big. So it will sink!", "act": {"show": "ball", "guess": "ball", "pick": "sink"}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Down you go!", "act": {"drop": "ball"}},
    {"t": "pause", "dur": 1.8},
    {"t": "say", "who": "bo", "expr": "confused", "text": "What? It is floating! My guesses are all wrong!", "sub": "What? It's FLOATING! My guesses are all wrong!", "act": {"result": "ball", "rule_x": True}},
    {"t": "pause", "dur": 0.4, "act": {"bloop_enter": True}},
    {"t": "pause", "dur": 1.0},
    {"t": "say", "who": "bloop", "expr": "giggle", "text": "Bloop! Hello, Bo! What a fun tank!", "listener_expr": "confused"},
    {"t": "say", "who": "bloop", "expr": "thinking", "text": "Big or small does not tell us if something floats.", "act": {"rule_hide": True}},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "But we can test and see! Friends, will you guess with us?"},

    # 4 — TRYING TOGETHER: kids guess, then we test
    {"t": "say", "who": "bloop", "expr": "happy", "text": "Here is a metal key. Float or sink? What do you think?", "act": {"show": "key", "guess": "key"}},
    {"t": "pause", "dur": 2.6, "act": {"scan": True}},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Let's test and see!", "act": {"drop": "key"}},
    {"t": "pause", "dur": 1.8},
    {"t": "say", "who": "bloop", "expr": "excited", "text": "It sinks! The key is heavy and solid, so it sinks.", "act": {"result": "key"}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Next, my rubber duck! Float or sink?", "act": {"show": "duck", "guess": "duck"}},
    {"t": "pause", "dur": 2.6, "act": {"scan": True}},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "Let's test and see!", "act": {"drop": "duck"}},
    {"t": "pause", "dur": 1.8},
    {"t": "say", "who": "bo", "expr": "excited", "text": "It floats! Quack quack!", "act": {"result": "duck"}},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "The duck is light, and it is full of air inside. So it floats!", "act": {"air": "duck"}},

    # 5 — SOLUTION & LESSON: the magic bottle
    {"t": "say", "who": "bloop", "expr": "thinking", "text": "Now, a magic trick! Here is an empty bottle. It is full of air.", "act": {"show": "bottle", "guess": "bottle", "air": "bottle"}},
    {"t": "pause", "dur": 2.4, "act": {"scan": True}},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Test and see!", "act": {"drop": "bottle"}},
    {"t": "pause", "dur": 1.8},
    {"t": "say", "who": "bo", "expr": "excited", "text": "It floats!", "act": {"result": "bottle"}},
    {"t": "say", "who": "bloop", "expr": "excited", "text": "Now let's fill the bottle with sand.", "act": {"fill": True}},
    {"t": "pause", "dur": 1.6},
    {"t": "say", "who": "bo", "expr": "surprised", "text": "The same bottle, but now it is heavy! Float or sink?", "act": {"guess": "sand"}},
    {"t": "pause", "dur": 2.4, "act": {"scan": True}},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "Test and see!", "act": {"drop": "sand"}},
    {"t": "pause", "dur": 2.0},
    {"t": "say", "who": "bo", "expr": "excited", "text": "It sinks! Now it is heavy, so it sinks!", "act": {"result": "sand"}},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "Light things, and things full of air, float. Heavy, solid things sink.", "act": {"lesson": True}},
    {"t": "say", "who": "both", "expr": "excited", "text": "Float or sink? Test and see!"},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Thank you, Bloop! Testing is fun!", "act": {"lesson": False, "hug": True}},
    {"t": "pause", "dur": 1.6},

    # 6 — SONG
    {"t": "scene", "name": "song"},
    {"t": "song"},

    # 7 — OUTRO
    {"t": "scene", "name": "lab_end"},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Great guessing, friends!"},
    {"t": "say", "who": "bloop", "expr": "giggle", "text": "Bloop! Remember: float or sink? Test and see!", "listener_expr": "excited"},
    {"t": "say", "who": "both", "expr": "happy", "text": "Bye bye from Bubble Bay!", "sub": "Bye-bye from Bubble Bay!", "act": {"wave": True}},
    {"t": "pause", "dur": 0.8},
    {"t": "scene", "name": "end"},
    {"t": "pause", "dur": 6.0},
]

# (beat, who, line, act)
SONG = [
    (4, "bloop", "Float or sink, what do you think?", {"song_phase": "think"}),
    (10, "bo", "Full of air, it floats up there!", {"song_phase": "float"}),
    (16, "bloop", "Heavy and solid goes down, down, down!", {"song_phase": "sink"}),
    (28, "bo", "Test and see, just like me!", {"song_phase": "test"}),
    (34, "both", "Float or sink? Test and see!", {"song_phase": "all"}),
]
SONG_CHANT = 22  # beats 22..24: "One, two, three!" (the rock sinks one step per count)
CHANT_N = 3
SONG_BEATS = 42
TITLE = "Why, Bo?: Why Do Things Float?"
