"""Render the episode frames from build/timeline.json and encode with the soundtrack."""
import json, math, os, subprocess, sys
from multiprocessing import Pool
import cairosvg
from chars import *  # noqa
from script import FACES

HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(HERE, "build", "timeline.json")))
FPS = TL["fps"]; DUR = TL["duration"]
W, H = 1920, 1080
ACTS = sorted(TL["acts"], key=lambda a: a["t"])
SCENES = TL["scenes"]

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")

def ease(x):
    x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3

# ---------------- timeline queries ----------------
def scene_at(t):
    cur = SCENES[0]
    for s in SCENES:
        if s["t"] <= t + 1e-6: cur = s
    return cur["name"], cur["t"]

def expr_at(who, t, default="happy"):
    e = default
    for x in TL["expr"]:
        if x["who"] == who and x["t"] <= t: e = x["e"]
    return e

def mouth_at(who, t):
    m = 0.0
    for s in TL["speak"]:
        if s["who"] != who: continue
        i = int((t - s["t"]) * FPS)
        if 0 <= i < len(s["env"]):
            m = max(m, s["env"][i])
    return m

def blink_at(t, seed):
    return ((t + seed) % 3.7) < 0.11

# ---------------- backgrounds ----------------
DEFS = ('<defs>'
        '<linearGradient id="sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#B6EBFF"/><stop offset="0.6" stop-color="#6CC3EE"/><stop offset="1" stop-color="#3FA2D8"/></linearGradient>'
        '<linearGradient id="deep" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4FB4E8"/><stop offset="1" stop-color="#1F6FA8"/></linearGradient>'
        '<linearGradient id="party" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9BE7FF"/><stop offset="0.5" stop-color="#7FD3F7"/><stop offset="1" stop-color="#B9A8FF"/></linearGradient>'
        '<radialGradient id="glow"><stop offset="0" stop-color="#FFF6B0" stop-opacity="0.9"/><stop offset="1" stop-color="#FFF6B0" stop-opacity="0"/></radialGradient>'
        '</defs>')

def bg_bubbles(t, n=14, seed=1, alpha=0.5):
    o = []
    for i in range(n):
        x = (i * 137 + seed * 61) % W + 18 * math.sin(t * 1.3 + i)
        sp = 40 + (i * 23) % 50
        y = H + 60 - ((t * sp + i * 173) % (H + 120))
        r = 5 + (i * 7) % 12
        o.append(C(x, y, r, "none", "#E8F8FF", 2.5, f'opacity="{alpha}"'))
    return "".join(o)

def seaweed(x, base, h, t, ph, col="#3FB59A"):
    s = 18 * math.sin(t * 1.4 + ph)
    d = f"M {x} {base} q {-24 + s:.1f} {-h/3:.1f} {s/2:.1f} {-h*0.55:.1f} q {24 + s:.1f} {-h/4:.1f} {s:.1f} {-h*0.45:.1f}"
    return P(d, stroke="#2E8F79", sw=26) + P(d, stroke=col, sw=16)

def background(t, kind="lab"):
    grad = {"lab": "sea", "hook": "sea", "title": "deep", "song": "party", "end": "deep", "lab_end": "sea"}[kind]
    o = [R(0, 0, W, H, 0, f"url(#{grad})")]
    for i in range(4):  # light rays
        x = 300 + i * 420 + 40 * math.sin(t * 0.3 + i)
        o.append(f'<polygon points="{x:.0f},0 {x+140:.0f},0 {x+380:.0f},{H} {x+180:.0f},{H}" fill="#FFFFFF" opacity="0.07"/>')
    o.append(P("M 0 760 Q 200 640 420 720 T 860 700 T 1300 730 T 1920 690 L 1920 900 L 0 900 Z", fill="#5DB2DD", extra='opacity="0.6"'))
    o.append(bg_bubbles(t))
    if kind in ("lab", "lab_end"):
        o.append(reef(t))
    o.append(P("M 0 880 Q 480 850 960 880 T 1920 870 L 1920 1080 L 0 1080 Z", fill="#F6E3B4"))
    o.append(P("M 0 900 Q 480 868 960 900 T 1920 890", stroke="#E9CF92", sw=6))
    for (x, y) in ((140, 980), (520, 1030), (1450, 990), (1800, 1040), (980, 1010)):
        o.append(E(x, y, 14, 6, "#EAD29C"))
    o += [seaweed(70, 890, 260, t, 0), seaweed(110, 895, 200, t, 1.1, "#4CC2A4"),
          seaweed(1830, 885, 280, t, 2.0), seaweed(1870, 890, 190, t, 0.4, "#4CC2A4")]
    o += [C(1700, 878, 30, "#FF8F7A", LINE, 4), C(1736, 888, 20, "#FFB199", LINE, 4)]
    o.append(G(starfish(0.45), 1560, 925, 1, 12))  # reef starfish friend
    return "".join(o)

def lab_hull(t):
    glow = 0.55 + 0.25 * math.sin(t * 2)
    return "".join([
        P("M 40 890 L 70 600 Q 90 540 170 520 L 520 500 Q 570 500 575 560 L 590 890 Z", fill="#3F78A8", stroke="#2A5A86", sw=6),
        P("M 62 680 L 582 650 M 52 770 L 586 745 M 66 600 L 575 578", stroke="#2E6594", sw=5),
        C(330, 615, 74, "url(#glow)", extra=f'opacity="{glow:.2f}"'),
        C(330, 615, 46, "#FFE88A", "#C98B3B", 10), C(330, 615, 46, "none", LINE, 3),
        P("M 300 600 Q 312 588 330 586", stroke=WHITE, sw=5, extra='opacity="0.7"'),
        R(384, 440, 220, 56, 12, "#C98B3B", LINE, 4), T(494, 479, "BO&#8217;S LAB", 30, WHITE, "bold"),
        P("M 420 496 L 424 515 M 566 496 L 562 512", stroke="#2A5A86", sw=6),
    ])

def reef(t):
    o = []
    for (x, h, col, ph) in ((230, 300, "#FF8F7A", 0), (330, 220, "#B39DFF", 1.2), (1330, 200, "#7EE0C3", 2.1), (1420, 250, "#FFB347", 0.6)):
        sw = 6 * math.sin(t * 1.2 + ph)
        d = f"M {x} 885 L {x} {885 - h * 0.55:.0f} M {x} {885 - h * 0.35:.0f} q -50 -20 {-60 + sw:.0f} {-h * 0.45:.0f} M {x} {885 - h * 0.45:.0f} q 50 -20 {60 + sw:.0f} {-h * 0.5:.0f}"
        o.append(P(d, stroke=LINE, sw=34) + P(d, stroke=col, sw=24))
    o.append(E(470, 875, 70, 28, "#C9A4E8", LINE, 4) + E(1250, 880, 56, 22, "#9ED8C9", LINE, 4))
    return "".join(o)

PERSIST = ("puzzle", "try", "grumpy", "drop", "bloop_enter", "chart", "chart_hide", "chart_pick", "breath_in", "breath_out",
           "breath_on", "breath_off", "step", "puzzle_back", "show_piece", "turn", "done", "hug")

def state_at(t, since):
    st = dict(lesson=False, enter=None, q=None, hf=None, wave=None, song_num=None, title=None, phase=None,
              puzzle=None, tries={}, grumpy=None, drop=None, chart=None, chart_scan=None, chart_pick=None, chart_hide=None,
              b_on=None, b_off=None, b_in={}, b_out={}, steps={}, back=None, show=None, turn=None, done=None, hug=None)
    for a in ACTS:
        if a["t"] > t: break
        if a["t"] < since - 1e-6 and not any(k in a for k in PERSIST):
            continue
        at = a["t"]
        if "lesson" in a: st["lesson"] = (a["lesson"], at)
        if a.get("bloop_enter"): st["enter"] = at
        if a.get("question"): st["q"] = at
        if a.get("hook_faces"): st["hf"] = at
        if a.get("wave"): st["wave"] = at
        if "song_num" in a: st["song_num"] = (a["song_num"], at)
        if "song_phase" in a: st["phase"] = (a["song_phase"], at)
        if a.get("title"): st["title"] = at
        if a.get("puzzle"): st["puzzle"] = at
        if "try" in a: st["tries"][a["try"]] = at
        if a.get("grumpy"): st["grumpy"] = at
        if a.get("drop"): st["drop"] = at
        if a.get("chart"): st["chart"] = at
        if a.get("chart_scan"): st["chart_scan"] = at
        if "chart_pick" in a: st["chart_pick"] = at
        if a.get("chart_hide"): st["chart_hide"] = at
        if a.get("breath_on"): st["b_on"] = at
        if a.get("breath_off"): st["b_off"] = at
        if "breath_in" in a: st["b_in"][a["breath_in"]] = at
        if "breath_out" in a: st["b_out"][a["breath_out"]] = at
        if "step" in a: st["steps"][a["step"]] = at
        if a.get("puzzle_back"): st["back"] = at
        if a.get("show_piece"): st["show"] = at
        if a.get("turn"): st["turn"] = at
        if a.get("done"): st["done"] = at
        if a.get("hug"): st["hug"] = at
    return st

# ---------------- props: feelings faces ----------------
def face_icon(kind, col):
    o = C(0, 0, 44, col, LINE, 5)
    eyes = E(-14, -8, 5, 7, NAVY) + E(14, -8, 5, 7, NAVY)
    if kind == "happy": o += eyes + P("M -16 12 Q 0 28 16 12", stroke=NAVY, sw=5)
    elif kind == "sad": o += eyes + P("M -16 22 Q 0 8 16 22", stroke=NAVY, sw=5) + E(-22, 6, 4, 6, "#5EA9E8")
    elif kind == "grumpy": o += eyes + P("M -16 20 Q -8 13 0 18 Q 8 13 16 20", stroke=NAVY, sw=5) + P("M -24 -24 L -6 -16 M 24 -24 L 6 -16", stroke=NAVY, sw=5)
    elif kind == "sleepy": o += P("M -20 -6 Q -14 0 -8 -6 M 8 -6 Q 14 0 20 -6", stroke=NAVY, sw=4) + E(0, 16, 6, 5, NAVY) + T(34, -26, "z", 26, NAVY, "bold")
    elif kind == "silly": o += eyes + P("M -16 10 Q 0 24 16 10", stroke=NAVY, sw=5) + P("M -2 16 Q 6 32 12 16 Z", fill=PINK, stroke=NAVY, sw=3)
    else: o += P("M -12 14 Q 0 20 12 14", stroke=NAVY, sw=5) + P("M -20 -10 Q -14 -4 -8 -10 M 8 -10 Q 14 -4 20 -10", stroke=NAVY, sw=4)
    return o

FACE_COL = dict(happy="#FFD54A", sad="#9EC9FF", grumpy="#FF8F7A", calm="#7EE0C3", sleepy="#C9A4E8", silly="#FFB347")

def heart(x, y, s, op=1.0, col="#FF7FA8"):
    d = "M 0 12 C -28 -6 -18 -30 0 -16 C 18 -30 28 -6 0 12 Z"
    return f'<g opacity="{op:.2f}">{G(P(d, fill=col, stroke=LINE, sw=3), x, y, s)}</g>'

# ---------------- props: the fish puzzle ----------------
PW, PH, PS = 450, 300, 150      # picture size, piece size
MISSING = (2, 0)

def _picture():
    o = [R(0, 0, PW, 72, 0, "#CFF3FF"), R(0, 72, PW, PH - 72, 0, "#5DB8E6"),
         P("M 0 72 Q 37 62 75 72 T 150 72 T 225 72 T 300 72 T 375 72 T 450 72", stroke="#E8F8FF", sw=6),
         C(64, 36, 22, YELLOW, LINE, 3)]
    for k in range(8):
        a = k * math.pi / 4
        o.append(P(f"M {64 + 30 * math.cos(a):.1f} {36 + 30 * math.sin(a):.1f} L {64 + 40 * math.cos(a):.1f} {36 + 40 * math.sin(a):.1f}", stroke="#F2B53A", sw=5))
    o.append(E(392, 30, 34, 14, WHITE) + C(376, 24, 14, WHITE) + C(400, 20, 16, WHITE))     # little cloud (top-right)
    o.append(P("M 0 258 Q 110 244 225 258 T 450 254 L 450 300 L 0 300 Z", fill="#F6E3B4"))
    for x, h, ph in ((36, 110, 0), (96, 80, 1)):
        o.append(P(f"M {x} 262 q -14 {-h/3:.0f} 4 {-h*0.55:.0f} q 14 {-h/4:.0f} 2 {-h*0.45:.0f}", stroke="#2E8F79", sw=13)
                 + P(f"M {x} 262 q -14 {-h/3:.0f} 4 {-h*0.55:.0f} q 14 {-h/4:.0f} 2 {-h*0.45:.0f}", stroke="#4CC2A4", sw=7))
    o.append(G(starfish(0.32), 225, 268))
    o.append(P("M 372 282 Q 392 246 412 282 Z", fill="#F7A8C8", stroke=LINE, sw=3) + P("M 392 280 L 392 256 M 382 280 L 386 260 M 402 280 L 398 260", stroke=LINE, sw=2))
    for (x, y, r) in ((180, 110, 7), (196, 92, 5), (440, 120, 6), (430, 100, 4), (140, 200, 6)):
        o.append(C(x, y, r, "none", "#E8F8FF", 2.5))
    # the big happy fish (face is on the top-right piece)
    o.append(P("M 252 120 L 200 82 L 208 120 L 200 158 Z", fill="#FF8A3D", stroke=LINE, sw=4))
    o.append(E(330, 120, 88, 56, "#FFB347", LINE, 5))
    o.append(P("M 290 72 Q 316 46 344 66", fill="#FF8A3D", stroke=LINE, sw=4))
    o.append(P("M 300 72 Q 286 120 300 168 M 330 66 Q 314 120 330 174", stroke="#FF8A3D", sw=8, extra='opacity="0.75"'))
    o.append(E(378, 104, 13, 15, WHITE, LINE, 3) + C(381, 106, 7, NAVY) + C(384, 102, 2.5, WHITE))
    o.append(P("M 384 132 Q 398 144 410 128", stroke=NAVY, sw=4) + E(366, 128, 9, 5, PINK, extra='opacity="0.8"'))
    return "".join(o)

PIC = _picture()
CLIPS = "".join(f'<clipPath id="pc{i}{j}"><rect x="{i*PS}" y="{j*PS}" width="{PS}" height="{PS}"/></clipPath>'
                for i in range(3) for j in range(2))

def piece(i, j):
    return (f'<g clip-path="url(#pc{i}{j})">{PIC}</g>'
            + R(i * PS + 2, j * PS + 2, PS - 4, PS - 4, 8, "none", LINE, 4, 'opacity="0.35"'))

BOARD_C = (960, 470); BOARD_S = 1.3

def board(cx, cy, s, missing=True, op=1.0, glow=0.0):
    o = [R(-26, -26, PW + 52, PH + 52, 22, "#D9B07A", LINE, 6), R(-12, -12, PW + 24, PH + 24, 14, "#B8894F")]
    for i in range(3):
        for j in range(2):
            if missing and (i, j) == MISSING:
                o.append(R(i * PS, j * PS, PS, PS, 8, "#2A5A86", extra='opacity="0.55"'))
                o.append(R(i * PS + 6, j * PS + 6, PS - 12, PS - 12, 8, "none", WHITE, 4, 'stroke-dasharray="14 10" opacity="0.8"'))
                o.append(T(i * PS + PS / 2, j * PS + PS / 2 + 26, "?", 76, WHITE, "bold", extra='opacity="0.8"'))
            else:
                o.append(piece(i, j))
    g = "".join(o)
    out = ""
    if glow > 0:
        out += R(cx - (PW / 2 + 50) * s, cy - (PH / 2 + 50) * s, (PW + 100) * s, (PH + 100) * s, 40, "none", YELLOW, 10, f'opacity="{glow:.2f}"')
    out += G(g, cx - PW / 2 * s, cy - PH / 2 * s, s)
    return f'<g opacity="{op:.2f}">{out}</g>' if op < 0.999 else out

def loose_piece(x, y, s, rot, hl=0.0):
    i, j = MISSING
    g = G(piece(i, j) + R(i * PS, j * PS, PS, PS, 8, "none", LINE, 6), -(i * PS + PS / 2), -(j * PS + PS / 2))
    o = ""
    if hl > 0:
        o += C(x, y, 150 * s, "url(#glow)", extra=f'opacity="{min(1, hl):.2f}"')
    return o + G(g, x, y, s, rot)

SLOT = (BOARD_C[0] - PW / 2 * BOARD_S + (MISSING[0] * PS + PS / 2) * BOARD_S,
        BOARD_C[1] - PH / 2 * BOARD_S + (MISSING[1] * PS + PS / 2) * BOARD_S)
HOLD = (560, 650); REST = (640, 850); SHOW = (1440, 770)

def lerp(a, b, k):
    return a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k

def piece_state(t, st):
    """-> (x, y, scale, rot, highlight) of the loose piece, or None when it is in the board."""
    if st["puzzle"] is None: return None
    x, y = HOLD; s = 1.0; rot = 180.0; hl = 0.0
    for n, at in st["tries"].items():
        a = t - at
        if 0 <= a < 0.55:
            x, y = lerp(HOLD, (SLOT[0] - 40, SLOT[1] + 10), ease(a / 0.55)); s = 1.0 + 0.3 * ease(a / 0.55)
        elif 0.55 <= a < 1.25:
            k = ease((a - 0.55) / 0.7)
            x, y = lerp((SLOT[0] - 40, SLOT[1] + 10), HOLD, k); s = 1.3 - 0.3 * k
            rot = 180 + 14 * math.sin(a * 25) * (1 - k)
    if st["drop"] is not None and t >= st["drop"] + 0.4:
        k = ease((t - st["drop"] - 0.4) / 0.45)
        x, y = lerp(HOLD, REST, k); s = 1.0 - 0.15 * k; rot = 180 + 16 * k
        y -= 60 * math.sin(k * math.pi) * 0.5
    if st["show"] is not None:
        k = ease((t - st["show"]) / 0.7)
        x, y = lerp(REST, SHOW, k); s = 0.85 + 0.45 * k; rot = 196 - 16 * k
        y -= 120 * math.sin(k * math.pi)
        hl = min(1, (t - st["show"]) / 0.3) * (0.7 + 0.3 * math.sin(t * 8))
    if st["turn"] is not None:
        a = t - st["turn"]
        rot = 180 + 180 * ease(a / 1.2)
        hl = max(0, 1 - a / 1.6)
        if a >= 1.1:
            k = ease((a - 1.1) / 0.5)
            x, y = lerp(SHOW, SLOT, k); s = 1.3
            y -= 120 * math.sin(k * math.pi)
            if a >= 1.6: return None
    return x, y, s, rot, hl

def board_op(t, st):
    if st["puzzle"] is None: return 0.0
    op = ease((t - st["puzzle"]) / 0.4)
    if st["chart"] is not None:
        op = 1 - ease((t - st["chart"]) / 0.4)
    if st["back"] is not None:
        op = ease((t - st["back"]) / 0.4)
    return op

# ---------------- props: grumpy cloud ----------------
def cloud_level(t, st):
    if st["grumpy"] is None: return 0.0
    lvl = ease((t - st["grumpy"]) / 0.4)
    for n, at in st["b_out"].items():
        k = ease((t - at - 0.4) / 1.6)
        lvl -= k / 3
    return max(0.0, lvl)

def storm_cloud(x, y, lvl, t):
    if lvl <= 0.01: return ""
    s = 0.45 + 0.55 * lvl
    o = []
    for k in range(5):  # rain drops
        ph = (t * 1.6 + k * 0.23) % 1
        dx = -70 + k * 35
        o.append(P(f"M {dx} {50 + ph * 110:.1f} l -5 16", stroke="#5EA9E8", sw=6, extra=f'opacity="{0.9 * (1 - ph):.2f}"'))
    o.append(C(-60, 10, 42, "#A8B4C6", LINE, 5) + C(0, -16, 58, "#A8B4C6", LINE, 5) + C(62, 8, 44, "#A8B4C6", LINE, 5)
             + R(-92, 4, 184, 50, 25, "#A8B4C6", LINE, 5) + R(-88, 4, 176, 40, 20, "#A8B4C6")
             + C(-60, 10, 37, "#A8B4C6") + C(0, -16, 53, "#A8B4C6") + C(62, 8, 39, "#A8B4C6"))
    o.append(E(-18, 4, 6, 8, NAVY) + E(18, 4, 6, 8, NAVY) + P("M -14 30 Q 0 20 14 30", stroke=NAVY, sw=5)
             + P("M -30 -10 L -10 -4 M 30 -10 L 10 -4", stroke=NAVY, sw=4))
    return f'<g opacity="{min(1, lvl * 2.5):.2f}">{G("".join(o), x, y + 4 * math.sin(t * 2), s)}</g>'

# ---------------- props: feelings chart, breathing bubble, steps ----------------
CHART_X = [645, 855, 1065, 1275]

def feelings_chart(t, st):
    if st["chart"] is None: return ""
    op = ease((t - st["chart"]) / 0.4)
    if st["chart_hide"] is not None:
        op = 1 - ease((t - st["chart_hide"]) / 0.4)
        if op <= 0: return ""
    o = [R(500, 300, 920, 340, 40, WHITE, "#2E8FCC", 6, 'fill-opacity="0.94"'),
         T(960, 362, "How does Bo feel?", 44, "#2E8FCC", "bold")]
    sel = None
    if st["chart_pick"] is not None: sel = 2
    elif st["chart_scan"] is not None: sel = int((t - st["chart_scan"]) / 0.6) % 4
    for i, kind in enumerate(FACES):
        x, y = CHART_X[i], 470
        if i == sel:
            pul = 0.75 + 0.25 * math.sin(t * 10)
            o.append(C(x, y, 92, "url(#glow)", extra=f'opacity="{pul:.2f}"') + C(x, y, 82, "none", YELLOW, 8))
        bump = 1.0
        if st["chart_pick"] is not None and i == 2:
            a = t - st["chart_pick"]; bump = 1 + 0.25 * max(0, 1 - a / 0.5)
        o.append(G(face_icon(kind, FACE_COL[kind]), x, y + 6 * math.sin(t * 2.5 + i), 1.5 * bump))
        o.append(T(x, 592, kind.upper(), 32, LINE, "bold"))
    if st["chart_pick"] is not None:
        a = t - st["chart_pick"]
        o.append(G(C(0, 0, 30, "#4CC28A", LINE, 5) + P("M -13 1 L -3 11 L 14 -10", stroke=WHITE, sw=7), CHART_X[2] + 62, 410, ease(a / 0.3)))
    return f'<g opacity="{op:.2f}">{"".join(o)}</g>'

def breath_radius(t, st):
    r = 80.0; phase = None; n = 0
    for k in sorted(st["b_in"]):
        if t >= st["b_in"][k]:
            r = 80 + 125 * ease((t - st["b_in"][k]) / 2.8); phase = "in"; n = k
        if k in st["b_out"] and t >= st["b_out"][k]:
            r = 205 - 125 * ease((t - st["b_out"][k]) / 2.8); phase = "out"; n = k
    return r, phase, n

def breathing(t, st):
    if st["b_on"] is None: return ""
    op = ease((t - st["b_on"]) / 0.5)
    if st["b_off"] is not None:
        op = 1 - ease((t - st["b_off"]) / 0.5)
        if op <= 0: return ""
    cx, cy = 960, 450
    r, phase, n = breath_radius(t, st)
    o = [C(cx, cy, r + 30, "url(#glow)", extra='opacity="0.35"'),
         C(cx, cy, r, "#E8F8FF", WHITE, 8, 'fill-opacity="0.45"'),
         P(f"M {cx - r * 0.6:.1f} {cy - r * 0.45:.1f} Q {cx - r * 0.45:.1f} {cy - r * 0.75:.1f} {cx - r * 0.1:.1f} {cy - r * 0.8:.1f}", stroke=WHITE, sw=9, extra='opacity="0.8"')]
    label = {"in": "Breathe in", "out": "Breathe out", None: "Ready?"}[phase]
    o.append(T(cx, cy + 18, label, 52, "#1F6FA8", "bold"))
    if phase == "in":   # flower to smell
        a = t - st["b_in"][n]
        fl = "".join(C(26 * math.cos(k * 1.2566), 26 * math.sin(k * 1.2566), 20, "#FF9EB5", LINE, 3) for k in range(5)) + C(0, 0, 16, YELLOW, LINE, 3)
        o.append(G(P("M 0 20 L 0 110", stroke="#3FB59A", sw=8) + fl, 640, 430, ease(a / 0.4)))
    if phase == "out":  # blow little bubbles
        a = t - st["b_out"][n]
        for k in range(6):
            q = (a * 0.6 + k * 0.17) % 1
            o.append(C(cx + r + 30 + q * 280, cy - 40 + 60 * math.sin(k * 2 + q * 5), 10 + k % 3 * 6, "none", WHITE, 4, f'opacity="{(1 - q) * min(1, a * 2):.2f}"'))
    for k in range(1, 4):   # breath counter
        x = cx - 110 + (k - 1) * 110
        done = k in st["b_out"] and t >= st["b_out"][k] + 0.2
        cur = k == n and not done
        col = "#7EE0C3" if done else (YELLOW if cur else WHITE)
        o.append(C(x, 760, 38, col, LINE, 5) + T(x, 778, str(k), 50, LINE, "bold"))
    return f'<g opacity="{op:.2f}">{"".join(o)}</g>'

STEPS = [(1, "Name it", ORANGE), (2, "Breathe", "#2E8FCC"), (3, "Ask for help", "#8A6BE0")]

def steps_strip(t, st):
    if not st["steps"]: return ""
    if st["lesson"] and st["lesson"][0]: return ""
    o = []
    for (n, label, col), x in zip(STEPS, (540, 960, 1380)):
        if n not in st["steps"]: continue
        a = t - st["steps"][n]
        g = (R(-185, -40, 370, 80, 40, WHITE, col, 6) + C(-143, 0, 28, col) + T(-143, 14, str(n), 40, WHITE, "bold")
             + T(-100, 13, label, 36, LINE, "bold", anchor="start"))
        o.append(G(g, x, 86, ease(a / 0.3) * (1 + 0.2 * max(0, 1 - a / 0.5))))
    return "".join(o)

def lesson_banner(age):
    s = ease(age / 0.35)
    g = (R(-600, -60, 1200, 120, 60, WHITE, ORANGE, 6)
         + G(face_icon("grumpy", FACE_COL["grumpy"]), -530, 0, 0.8) + G(face_icon("happy", FACE_COL["happy"]), 530, 0, 0.8)
         + T(0, 16, "Name it &#183; Breathe &#183; Ask for help!", 48, LINE, "bold"))
    return G(g, 960, 100, s)


DEFS = DEFS.replace("</defs>", CLIPS + "</defs>")

# ---------------- subtitles ----------------
def wrap(text, maxc):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > maxc and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    return lines

def subtitle(t):
    cur = None
    for s in TL["subs"]:
        if s["t0"] <= t < s["t1"] and s["style"] != "title":
            cur = s
    if not cur: return ""
    age = t - cur["t0"]
    style = cur["style"]
    col = {"bo": ORANGE, "bloop": "#2E8FCC", "both": "#8A6BE0", "none": LINE}[cur["who"]]
    name = {"bo": "Bo", "bloop": "Bloop", "both": "Bo &amp; Bloop", "none": ""}[cur["who"]]
    if style == "song":
        s = 1 + 0.06 * max(0, 1 - age * 4)
        g = T(0, 0, esc(cur["text"]), 66, WHITE, "bold", extra=f'stroke="{LINE}" stroke-width="7" paint-order="stroke" letter-spacing="1"')
        return G(g, 960, 1020, s)
    size = 76 if style == "number" else 46
    lines = wrap(esc(cur["text"]), 40)
    wmax = max(len(l) for l in lines) * size * 0.6 + 80
    h = len(lines) * size * 1.15 + 34
    y0 = 1058 - h
    o = [R(960 - wmax / 2, y0, wmax, h, 26, WHITE, col, 5, 'fill-opacity="0.93"')]
    if name:
        nw = len(name.replace("&amp;", "&")) * 17 + 34
        o.append(R(960 - wmax / 2 + 26, y0 - 22, nw, 40, 20, col))
        o.append(T(960 - wmax / 2 + 26 + nw / 2, y0 + 6, name, 24, WHITE, "bold"))
    for k, l in enumerate(lines):
        o.append(T(960, y0 + 17 + size * 0.95 + k * size * 1.15, l, size, col if style == "number" else LINE, "bold"))
    op = min(1, age / 0.12)
    return f'<g opacity="{op:.2f}">{"".join(o)}</g>'

# ---------------- characters placed ----------------
def place_bo(t, x, ground, s, wave=0.0, dance=0.0, point=0.0):
    m = mouth_at("bo", t)
    e = expr_at("bo", t)
    bob = 4 * math.sin(t * 2.4) + (6 * m) + dance * abs(math.sin(t * math.pi * 100 / 60)) * -22
    if e == "grumpy" and m > 0.06:
        x += 4 * math.sin(t * 38)
    shadow = E(x, ground + 4, 120 * s, 16 * s, LINE, extra='opacity="0.12"')
    return shadow + G(bo(e, m, blink_at(t, 0.3) and m < 0.06, t, wave=wave, point=point), x, ground - bob * s, s)

def place_bloop(t, x, y, s, energy=1.0, dance=0.0):
    m = mouth_at("bloop", t)
    fy = 12 * math.sin(t * 1.6) + dance * abs(math.sin(t * math.pi * 100 / 60 + 0.5)) * -26
    return G(bloop(expr_at("bloop", t), m, blink_at(t, 1.9) and m < 0.06, t, energy), x, y + fy, s, 4 * math.sin(t * 1.1))

# ---------------- scenes ----------------
def scene_hook(t, t0, st):
    o = [background(t, "hook")]
    if st["hf"] is not None:
        spots = [(450, 360, "happy"), (1470, 330, "sleepy"), (330, 690, "silly"), (1590, 680, "grumpy"), (1260, 170, "calm"), (650, 160, "sad")]
        for i, (x, y, k) in enumerate(spots):
            age = t - st["hf"] - i * 0.25
            if age > 0:
                o.append(G(face_icon(k, FACE_COL[k]), x + 20 * math.sin(t + i), y + 14 * math.sin(t * 1.5 + i), 1.7 * ease(age / 0.4), 8 * math.sin(t * 1.2 + i)))
    o.append(place_bo(t, 960, 940, 1.7))
    if st["q"] is not None and t - st["q"] < 3.2:
        age = t - st["q"]
        o.append(G(T(0, 0, "?", 190, ORANGE, "bold", extra=f'stroke="{LINE}" stroke-width="8" paint-order="stroke"'),
                   1300, 300 + 12 * math.sin(t * 4), ease(age / 0.3), 8 * math.sin(t * 3)))
    return "".join(o)

def scene_title(t, t0, st):
    age = t - t0
    o = [background(t, "title"), bg_bubbles(t * 1.6, 22, 4, 0.7)]
    words = [("Bo", 590, ORANGE), ("&amp;", 815, YELLOW), ("Bloop", 1175, "#BDE7FC")]
    for i, (wd, x, col) in enumerate(words):
        a = age - 0.2 - i * 0.25
        if a <= 0: continue
        s = ease(a / 0.3) * (1 + 0.12 * max(0, 1 - a / 0.5) * math.sin(a * 14))
        y = 360 - 18 * abs(math.sin(t * 4 + i * 0.9)) * (1 if age < 6.5 else 0.3)
        o.append(G(T(0, 0, wd, 170, col, "bold", extra=f'stroke="{LINE}" stroke-width="12" paint-order="stroke"'), x, y, s))
    if age > 0.8:
        o.append(place_bo(t, 300, 900, 1.15 * ease((age - 0.8) / 0.35)))
    if age > 1.7:
        o.append(place_bloop(t, 1630, 560, 1.15 * ease((age - 1.7) / 0.35), energy=2))
    if age > 3.5:
        s = ease((age - 3.5) / 0.4)
        o.append(G(R(-230, -40, 460, 80, 40, "#FF7FA8", LINE, 5) + T(0, 16, "Bloop&#8217;s Big Feelings", 38, WHITE, "bold"), 960, 520, s))
    if age > 4.0:
        s = ease((age - 4.0) / 0.4)
        o.append(G(T(0, 0, "When Bo Feels Grumpy", 64, WHITE, "bold", extra=f'stroke="{LINE}" stroke-width="7" paint-order="stroke"'), 960, 660, s))
        o.append(G(face_icon("grumpy", FACE_COL["grumpy"]), 830, 780, s * 1.1)
                 + G(P("M -30 0 L 30 0 M 12 -16 L 30 0 L 12 16", stroke=WHITE, sw=8), 960, 780, s)
                 + G(face_icon("happy", FACE_COL["happy"]), 1090, 780, s * 1.1))
    for i in range(6):
        a = (t * 1.5 + i * 0.37) % 2
        o.append(sparkle(300 + i * 270, 180 + (i % 2) * 520, 1.4, YELLOW, max(0, math.sin(a * math.pi / 2))))
    return "".join(o)

def scene_lab(t, t0, st):
    o = [background(t, "lab")]
    op = board_op(t, st)
    ps = piece_state(t, st)
    if op > 0.01:
        glow = 0.0
        if st["done"] is not None:
            glow = min(1, (t - st["done"]) / 0.3) * (0.6 + 0.4 * math.sin(t * 6))
        o.append(board(BOARD_C[0], BOARD_C[1], BOARD_S, missing=ps is not None, op=op, glow=glow))
    pointing = 0.0
    for n, at in st["tries"].items():
        a = t - at
        if 0 <= a < 1.3: pointing = max(pointing, math.sin(min(1, a / 1.3) * math.pi))
    o.append(place_bo(t, 300, 900, 1.15, point=pointing))
    o.append(storm_cloud(300, 395, cloud_level(t, st), t))
    # sparkle when the cloud has gone
    if 3 in st["b_out"]:
        a = t - st["b_out"][3] - 1.8
        if 0 < a < 1.5:
            for k in range(5):
                o.append(sparkle(300 + 90 * math.cos(k * 1.256), 395 + 60 * math.sin(k * 1.256), 1.3, YELLOW, max(0, 1 - a / 1.5)))
    if st["enter"] is not None:
        a = ease((t - st["enter"]) / 1.3)
        x = 2250 + (1640 - 2250) * a
        if a < 1:
            for k in range(4):
                o.append(C(x + 140 + k * 60, 520 + 20 * math.sin(k + t * 5), 10 + k * 3, "none", "#E8F8FF", 3, 'opacity="0.8"'))
        o.append(place_bloop(t, x, 500, 1.05))
    o.append(feelings_chart(t, st))
    o.append(breathing(t, st))
    if ps is not None and (st["chart"] is None or st["back"] is not None or st["drop"] is not None):
        x, y, s, rot, hl = ps
        o.append(loose_piece(x, y, s, rot, hl))
    if st["done"] is not None:
        a = t - st["done"]
        for k in range(8):
            ang = k * math.pi / 4 + t * 0.6
            o.append(sparkle(BOARD_C[0] + 360 * math.cos(ang), BOARD_C[1] + 250 * math.sin(ang), 1.4, YELLOW,
                             max(0, math.sin((t * 1.6 + k * 0.4) % 2 * math.pi / 2)) * min(1, a / 0.3)))
    if st["hug"] is not None:
        a = t - st["hug"]
        for k in range(6):
            q = a - k * 0.35
            if 0 < q < 2.6:
                o.append(heart(520 + k * 190, 700 - q * 160, 1.6, max(0, 1 - q / 2.6)))
    o.append(steps_strip(t, st))
    if st["lesson"] and st["lesson"][0]:
        o.append(lesson_banner(t - st["lesson"][1]))
    elif st["lesson"] and not st["lesson"][0] and t - st["lesson"][1] < 0.3:
        o.append(f'<g opacity="{1 - (t - st["lesson"][1]) / 0.3:.2f}">{lesson_banner(1)}</g>')
    return "".join(o)

def scene_song(t, t0, st):
    o = [background(t, "song")]
    beat = 0.6
    ph = ((t - t0) % beat) / beat
    o.append(C(960, 520, 380 + 30 * (1 - ph), "url(#glow)", extra='opacity="0.35"'))
    kinds = ["happy", "grumpy", "calm", "silly", "sad", "happy", "sleepy", "calm", "grumpy", "happy"]
    for i in range(10):  # little feeling faces floating in an arc
        a = math.pi * (0.9 - 0.8 * i / 9)
        x, y = 960 + 820 * math.cos(a), 470 - 330 * math.sin(a)
        o.append(G(face_icon(kinds[i], FACE_COL[kinds[i]]), x, y + 8 * math.sin(t * 3 + i), 0.85, 8 * math.sin(t * 3 + i)))
    o.append(place_bo(t, 280, 900, 1.05, dance=1))
    o.append(place_bloop(t, 1650, 600, 1.05, energy=2.5, dance=1))
    phase = st["phase"][0] if st["phase"] else None
    bounce = abs(math.sin((t - t0) * math.pi / beat))
    if phase is None:
        o.append(G(face_icon("happy", FACE_COL["happy"]), 960, 540 - 20 * bounce, 3.0))
    elif phase == "name":
        o.append(G(face_icon("grumpy", FACE_COL["grumpy"]), 960, 500 - 20 * bounce, 3.0, 6 * math.sin(t * 4)))
        o.append(G(R(-200, -40, 400, 80, 40, WHITE, ORANGE, 5) + T(0, 15, "I feel GRUMPY", 40, LINE, "bold"), 960, 720))
    elif phase == "breathe":
        a = t - st["phase"][1]
        r = 110 + 70 * (0.5 - 0.5 * math.cos(a * math.pi / (4 * beat)))
        o.append(C(960, 480, r, "#E8F8FF", WHITE, 8, 'fill-opacity="0.45"'))
        o.append(T(960, 498, "Breathe", 52, "#1F6FA8", "bold"))
        cur = st["song_num"]
        for k in range(1, 4):
            x = 850 + (k - 1) * 110
            on = cur is not None and cur[1] >= st["phase"][1] and k <= cur[0]
            sc = 1.0
            if on and k == cur[0]: sc = 1 + 0.3 * max(0, 1 - (t - cur[1]) / 0.3)
            o.append(G(C(0, 0, 38, "#7EE0C3" if on else WHITE, LINE, 5) + T(0, 18, str(k), 50, LINE, "bold"), x, 740, sc))
    elif phase == "help":
        o.append(G(face_icon("happy", FACE_COL["happy"]), 860, 520 - 20 * bounce, 1.8)
                 + G(face_icon("calm", FACE_COL["calm"]), 1060, 520 - 20 * (1 - bounce), 1.8)
                 + heart(960, 380 - 10 * bounce, 2.6))
        o.append(G(R(-220, -40, 440, 80, 40, WHITE, "#8A6BE0", 5) + T(0, 15, "Ask for help!", 40, LINE, "bold"), 960, 720))
    else:
        for k, ((n, label, col), y) in enumerate(zip(STEPS, (340, 500, 660))):
            b = abs(math.sin((t - t0) * math.pi / beat + k))
            g = (R(-220, -46, 440, 92, 46, WHITE, col, 6) + C(-172, 0, 32, col) + T(-172, 16, str(n), 44, WHITE, "bold")
                 + T(-125, 16, label, 42, LINE, "bold", anchor="start"))
            o.append(G(g, 960, y - 10 * b))
    return "".join(o)

def scene_lab_end(t, t0, st):
    o = [background(t, "lab_end")]
    o.append(board(960, 470, 1.1, missing=False))
    o.append(G(face_icon("happy", FACE_COL["happy"]), 960, 760, 1.0, 8 * math.sin(t * 2)))
    wave = 0.0
    if st["wave"] is not None:
        wave = ease((t - st["wave"]) / 0.4)
    o.append(place_bo(t, 360, 900, 1.2, wave=wave))
    o.append(place_bloop(t, 1560, 470, 1.15, energy=1 + 2 * wave))
    return "".join(o)

def float_icons(t):
    o = [R(-120, -10, 240, 90, 20, "#7FD3F7", LINE, 4)]
    o.append(P(f"M -120 -10 Q -60 {-20 + 6 * math.sin(t * 3):.1f} 0 -10 T 120 -10", stroke=WHITE, sw=5))
    o.append(G(C(0, 0, 26, "#FF8F7A", LINE, 4) + P("M -26 0 Q 0 -10 26 0", stroke=WHITE, sw=4) + P("M 0 -26 Q 8 0 0 26", stroke=YELLOW, sw=4),
               -60, -26 + 4 * math.sin(t * 3)))
    o.append(G(R(-22, -16, 44, 32, 8, "#A9B8CC", LINE, 4), 56, 52 + 3 * math.sin(t * 2)))
    o.append(T(56, 12, "&#8595;", 30, LINE, "bold") + T(-60, -66, "&#8593;", 30, LINE, "bold"))
    return o

def scene_end(t, t0, st):
    age = t - t0
    o = [background(t, "end")]
    o.append(G(T(0, 0, "Bo &amp; Bloop", 96, ORANGE, "bold", extra=f'stroke="{LINE}" stroke-width="10" paint-order="stroke"'), 960, 170, ease(age / 0.4)))
    s = ease((age - 0.4) / 0.4)
    card = (R(-520, -190, 1040, 380, 40, WHITE, LINE, 6, 'fill-opacity="0.95"')
            + T(0, -110, "NEXT TIME", 34, "#2E8FCC", "bold", extra='letter-spacing="6"')
            + T(0, -30, "Why Do Things Float?", 60, LINE, "bold"))
    card += G("".join(float_icons(t)), 0, 88, 1.25)
    card += G(T(0, 0, "?", 90, ORANGE, "bold", extra=f'stroke="{LINE}" stroke-width="6" paint-order="stroke"'), -300, 110, 1, 10 * math.sin(t * 2))
    card += G(T(0, 0, "?", 90, "#2E8FCC", "bold", extra=f'stroke="{LINE}" stroke-width="6" paint-order="stroke"'), 300, 110, 1, -10 * math.sin(t * 2))
    o.append(G(card, 960, 520, s))
    o.append(place_bo(t, 230, 940, 0.85, wave=1))
    o.append(place_bloop(t, 1700, 760, 0.85, energy=2))
    return "".join(o)

SCENE_FN = dict(hook=scene_hook, title=scene_title, lab=scene_lab, song=scene_song, lab_end=scene_lab_end, end=scene_end)

def frame_svg(t):
    name, t0 = scene_at(t)
    st = state_at(t, t0)
    body = SCENE_FN[name](t, t0, st)
    fade = ""
    if t - t0 < 0.35 and t0 > 0:
        fade = R(0, 0, W, H, 0, "#1F6FA8", extra=f'opacity="{1 - (t - t0) / 0.35:.2f}"')
    if t < 0.4:
        fade = R(0, 0, W, H, 0, "#1F6FA8", extra=f'opacity="{1 - t / 0.4:.2f}"')
    if DUR - t < 0.8:
        fade = R(0, 0, W, H, 0, "#1F6FA8", extra=f'opacity="{min(1, 1 - (DUR - t) / 0.8):.2f}"')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            + DEFS + body + subtitle(t) + fade + "</svg>")

def render_frame(i):
    return cairosvg.svg2png(bytestring=frame_svg(i / FPS).encode())

def preview(times, outdir):
    os.makedirs(outdir, exist_ok=True)
    for tt in times:
        cairosvg.svg2png(bytestring=frame_svg(tt).encode(), write_to=os.path.join(outdir, f"t{tt:07.2f}.png"))

def main(out):
    n = int(DUR * FPS)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "png", "-i", "-",
                           "-i", os.path.join(HERE, "build", "mix.wav"),
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-tune", "animation", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    with Pool(2) as pool:
        for k, png in enumerate(pool.imap(render_frame, range(n), chunksize=6)):
            ff.stdin.write(png)
            if k % 240 == 0:
                print(f"{k}/{n}", flush=True)
    ff.stdin.close(); ff.wait()
    print("done", out)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        preview([float(x) for x in sys.argv[3:]], sys.argv[2])
    else:
        main(sys.argv[2])
