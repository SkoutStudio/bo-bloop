# Bo & Bloop — Episode 6: "Days of the Week with Bo"  (series: Bubble Bay Songs)
# Lesson: there are 7 days in a week and they always come in the same order:
#         Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday — then Monday again.
# Story: Bo's Week Train has 7 day carriages, but they are mixed up and the train won't go.
#        Bloop and the kids put the days in order ("What comes after...?") and the train chugs off.

N = ["zero", "One!", "Two!", "Three!"]
DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
DAY_NAME = dict(MON="Monday", TUE="Tuesday", WED="Wednesday", THU="Thursday", FRI="Friday", SAT="Saturday", SUN="Sunday")
START_ORDER = ["MON", "FRI", "TUE", "SUN", "WED", "SAT", "THU"]   # Bo's mixed-up train

BEATS = [
    # 1 — HOOK
    {"t": "scene", "name": "hook"},
    {"t": "pause", "dur": 0.8, "act": {"hook_items": True}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Hi friends! Do you know what day it is today?"},
    {"t": "say", "who": "bo", "expr": "thinking", "text": "There are seven days in a week. Can you say them all?", "act": {"hook_seven": True}},
    {"t": "pause", "dur": 2.2, "act": {"question": True}},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Let's learn them together!"},
    {"t": "pause", "dur": 0.4},

    # 2 — INTRO JINGLE
    {"t": "scene", "name": "title"},
    {"t": "jingle"},

    # 3 — PROBLEM: the carriages are mixed up and the train won't go
    {"t": "scene", "name": "lab"},
    {"t": "pause", "dur": 0.6, "act": {"train": True}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Choo choo! This is my Week Train!", "sub": "Choo-choo! This is my Week Train!"},
    {"t": "say", "who": "bo", "expr": "happy", "text": "It has seven carriages, one for every day of the week."},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Monday, Friday, Tuesday, Sunday...", "act": {"sweep": "auto", "n": 4}},
    {"t": "say", "who": "bo", "expr": "thinking", "text": "Hmm. That sounds a little funny."},
    {"t": "say", "who": "bo", "expr": "excited", "text": "All aboard! Ready, set, go!", "act": {"bump": True}},
    {"t": "pause", "dur": 1.4},
    {"t": "say", "who": "bo", "expr": "sad", "text": "Oh no! My train won't go!", "act": {"bump": True}},
    {"t": "pause", "dur": 0.4, "act": {"bloop_enter": True}},
    {"t": "pause", "dur": 1.0},
    {"t": "say", "who": "bloop", "expr": "surprised", "text": "Bloop! Oh, Bo! Your days are all mixed up!", "listener_expr": "sad"},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "The days of the week always come in the same order."},
    {"t": "say", "who": "bloop", "expr": "excited", "text": "Let's put them in order. Friends, will you help us?"},

    # 4 — TRYING TOGETHER: what comes after...?
    {"t": "say", "who": "bloop", "expr": "happy", "text": "The week starts with Monday. Monday is first!", "act": {"lit": "MON"}},
    {"t": "say", "who": "bloop", "expr": "thinking", "text": "What comes after Monday?", "act": {"ask": "MON"}},
    {"t": "pause", "dur": 2.4, "act": {"scan": True}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Tuesday!", "act": {"swap": ["TUE", "FRI"], "ans": "TUE"}},
    {"t": "pause", "dur": 1.0},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "Yes! Monday, Tuesday. What comes next?", "act": {"ask": "TUE"}},
    {"t": "pause", "dur": 2.4, "act": {"scan": True}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Wednesday!", "act": {"swap": ["WED", "FRI"], "ans": "WED"}},
    {"t": "pause", "dur": 1.0},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "Monday, Tuesday, Wednesday. And after Wednesday?", "act": {"ask": "WED"}},
    {"t": "pause", "dur": 2.4, "act": {"scan": True}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Thursday!", "act": {"swap": ["THU", "SUN"], "ans": "THU"}},
    {"t": "pause", "dur": 1.0},
    {"t": "say", "who": "bo", "expr": "surprised", "text": "Look! Friday, Saturday and Sunday are already in the right place!", "act": {"lit_end": True}},
    {"t": "say", "who": "bloop", "expr": "excited", "text": "Seven carriages for seven days!", "act": {"seven": True}},

    # 5 — SOLUTION & LESSON
    {"t": "say", "who": "bloop", "expr": "happy", "text": "Now let's say them all, in order!"},
    {"t": "say", "who": "both", "expr": "excited", "text": "Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday!", "act": {"sweep": "auto", "n": 7}},
    {"t": "say", "who": "bo", "expr": "excited", "text": "All aboard! Choo choo!", "sub": "All aboard! Choo-choo!", "act": {"go": True}},
    {"t": "pause", "dur": 1.4},
    {"t": "say", "who": "bloop", "expr": "happy", "text": "There are seven days in a week. And after Sunday, Monday comes again!", "act": {"lesson": True}},
    {"t": "say", "who": "both", "expr": "excited", "text": "Seven days, round and round!"},
    {"t": "say", "who": "bo", "expr": "excited", "text": "Thank you, Bloop! My Week Train is going!", "act": {"lesson": False, "hug": True}},
    {"t": "pause", "dur": 1.6},

    # 6 — SONG
    {"t": "scene", "name": "song"},
    {"t": "song"},

    # 7 — OUTRO
    {"t": "scene", "name": "lab_end"},
    {"t": "say", "who": "bo", "expr": "happy", "text": "Great singing, friends!"},
    {"t": "say", "who": "bloop", "expr": "giggle", "text": "Bloop! What day is it today? Ask a grown-up!", "listener_expr": "excited"},
    {"t": "say", "who": "both", "expr": "happy", "text": "Bye bye from Bubble Bay!", "sub": "Bye-bye from Bubble Bay!", "act": {"wave": True}},
    {"t": "pause", "dur": 0.8},
    {"t": "scene", "name": "end"},
    {"t": "pause", "dur": 6.0},
]

# (beat, who, line, act)
SONG = [
    (4, "bloop", "Seven days are in a week,", {"song_phase": "seven"}),
    (10, "bo", "Monday, Tuesday, Wednesday,", {"song_phase": "days1"}),
    (16, "bloop", "Thursday, Friday, Saturday,", {"song_phase": "days2"}),
    (22, "both", "and then comes Sunday!", {"song_phase": "sun"}),
    (28, "bo", "Then Monday comes again!", {"song_phase": "again"}),
    (34, "both", "Seven days, round and round!", {"song_phase": "all"}),
]
SONG_CHANT = 0
CHANT_N = 0      # no number chant in this song
SONG_BEATS = 42
TITLE = "Bubble Bay Songs: Days of the Week with Bo"
