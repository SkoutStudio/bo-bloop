# Bo & Bloop — Episode 4: "When Bo Feels Grumpy"  (series: Bloop's Big Feelings)
# Lesson: when you feel grumpy -> 1) name the feeling, 2) take 3 slow breaths, 3) ask for help.
# Story: Bo's fish puzzle has one piece that won't fit. Bo gets grumpy (a little grey cloud over his head).
#        Bloop helps him name it, breathe it away, and ask for help — the piece was just upside down.

N = ["zero", "One!", "Two!", "Three!", "Four!"]
FACES = ["happy", "sad", "grumpy", "calm"]   # feelings chart, index 2 = grumpy

BEATS = [
    # 1 — HOOK
    {"t": "scene", "name": "hook"},
    {"t": "pause", "dur": 0.8, "act": {"hook_faces": True}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Hi friends! How do you feel today?"},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Happy? Sleepy? Silly? Or grumpy?"},
    {"t": "say", "who": "bo", "expr": "surprised", "text": "Do you ever feel grumpy?", "sub": "Do YOU ever feel grumpy?"},
    {"t": "pause", "dur": 2.2, "act": {"question": True}},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Today I learned what to do. Let's find out together!"},
    {"t": "pause", "dur": 0.4},

    # 2 — INTRO JINGLE
    {"t": "scene", "name": "title"},
    {"t": "jingle"},

    # 3 — PROBLEM: the last puzzle piece won't fit, Bo gets grumpy
    {"t": "scene", "name": "lab"},
    {"t": "pause", "dur": 0.6, "act": {"puzzle": True}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Beep boop! I am doing my fish puzzle!", "sub": "Beep-boop! I'm doing my fish puzzle!"},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Five pieces are in. Just one more piece!"},
    {"t": "say", "who": "bo", "expr": "happy", "text": "In you go!", "act": {"try": 1}},
    {"t": "pause", "dur": 1.0},
    {"t": "say", "who": "bo", "expr": "confused", "text": "Hmm. It does not fit.", "sub": "Hmm. It doesn't fit."},
    {"t": "say", "who": "bo", "expr": "thinking", "text": "Push! Push!", "act": {"try": 2}},
    {"t": "pause", "dur": 0.8},
    {"t": "say", "who": "bo", "expr": "grumpy", "text": "Hmph! It still does not fit!", "sub": "Hmph! It STILL doesn't fit!", "act": {"grumpy": True}},
    {"t": "say", "who": "bo", "expr": "grumpy", "text": "Silly puzzle! I don't want to play anymore!", "act": {"drop": True}},
    {"t": "pause", "dur": 0.4, "act": {"bloop_enter": True}},
    {"t": "pause", "dur": 1.0},
    {"t": "say", "who": "bloop", "expr": "surprised", "text": "Bloop! Oh, Bo! There is a little cloud over your head!", "listener_expr": "grumpy"},
    {"t": "say", "who": "bloop", "expr": "thinking", "text": "When we have a big feeling, the first thing we do is give it a name."},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "Friends, look at Bo's face. Which face looks like Bo?", "act": {"chart": True}},
    {"t": "pause", "dur": 2.6, "act": {"chart_scan": True}},
    {"t": "say", "who": "bloop", "expr": "excited", "text": "Grumpy! Yes! Bo feels grumpy.", "act": {"chart_pick": 2}},
    {"t": "say", "who": "bo", "expr": "grumpy", "text": "Yes. I feel grumpy.", "act": {"step": 1}},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "Great job, Bo! Saying the feeling helps a little."},

    # 4 — TRYING TOGETHER: three slow breaths with the kids
    {"t": "say", "who": "bloop", "expr": "happy", "text": "Now let's take three slow breaths.", "act": {"chart_hide": True}},
    {"t": "say", "who": "bloop", "expr": "giggle", "text": "Breathe in, like smelling a flower. Breathe out, like blowing a bubble."},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Friends at home, breathe with us!", "act": {"breath_on": True}},
    {"t": "breath", "n": 1},
    {"t": "breath", "n": 2},
    {"t": "breath", "n": 3},
    {"t": "pause", "dur": 0.6, "act": {"breath_off": True, "step": 2}},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Beep... boop. My cloud is gone. I feel calm now."},

    # 5 — SOLUTION & LESSON: ask for help
    {"t": "say", "who": "bloop", "expr": "happy", "text": "And when something is tricky, we can ask for help.", "act": {"puzzle_back": True}},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Bloop, can you help me with my puzzle, please?", "act": {"step": 3}},
    {"t": "say", "who": "bloop", "expr": "excited", "text": "Of course! Look, Bo. The piece is upside down!", "act": {"show_piece": True}},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "Let's turn it around. Turn, turn, turn!", "act": {"turn": True}},
    {"t": "pause", "dur": 1.4},
    {"t": "say", "who": "bo", "expr": "excited", "text": "It fits! A happy fish! We did it together!", "act": {"done": True}},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "When you feel grumpy: name it, breathe, and ask for help.", "act": {"lesson": True}},
    {"t": "say", "who": "both", "expr": "excited", "text": "Name it, breathe, and ask for help!"},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Thank you, Bloop! Now I feel happy!", "act": {"lesson": False, "hug": True}},
    {"t": "pause", "dur": 1.6},

    # 6 — SONG
    {"t": "scene", "name": "song"},
    {"t": "song"},

    # 7 — OUTRO
    {"t": "scene", "name": "lab_end"},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Great breathing, friends!"},
    {"t": "say", "who": "bloop", "expr": "giggle", "text": "Bloop! Remember: name it, breathe, and ask for help!", "listener_expr": "excited"},
    {"t": "say", "who": "both", "expr": "happy", "text": "Bye bye from Bubble Bay!", "sub": "Bye-bye from Bubble Bay!", "act": {"wave": True}},
    {"t": "pause", "dur": 0.8},
    {"t": "scene", "name": "end"},
    {"t": "pause", "dur": 6.0},
]

# (beat, who, line, act)
SONG = [
    (4, "bloop", "When I'm grumpy, I can say,", {"song_phase": "name"}),
    (10, "bo", "I feel grumpy, grumpy today!", None),
    (16, "bloop", "Breathe in slow, breathe out slow,", {"song_phase": "breathe"}),
    (28, "bo", "then I ask a friend for help!", {"song_phase": "help"}),
    (34, "both", "Name it, breathe, and ask for help!", {"song_phase": "all"}),
]
SONG_CHANT = 22  # beats 22..24: "One, two, three!"
CHANT_N = 3
SONG_BEATS = 42
TITLE = "Bloop's Big Feelings: When Bo Feels Grumpy"
