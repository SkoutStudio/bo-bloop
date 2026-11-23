"""Render the episode frames from build/timeline.json and encode with the soundtrack."""
import json, math, os, subprocess, sys
from multiprocessing import Pool
import cairosvg
from chars import *  # noqa

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



PERSIST = ("rocket", "bolt", "board", "num", "reset", "hug", "land", "go")

def state_at(t, since):
    st = dict(lesson=False, enter=None, q=None, hi=None, wave=None, title=None, phase=None,
              rocket=None, wobble=None, bolt=None, sputters=[], board=None, wrong=None, show8=None, reset=None,
              nums={}, go=None, land=None, sweeps=[], hug=None)
    for a in ACTS:
        if a["t"] > t: break
        if a["t"] < since - 1e-6 and not any(k in a for k in PERSIST):
            continue
        at = a["t"]
        if "lesson" in a: st["lesson"] = (a["lesson"], at)
        if a.get("bloop_enter"): st["enter"] = at
        if a.get("question"): st["q"] = at
        if a.get("hook_items"): st["hi"] = at
        if a.get("wave"): st["wave"] = at
        if "song_phase" in a: st["phase"] = (a["song_phase"], at)
        if a.get("title"): st["title"] = at
        if a.get("rocket"): st["rocket"] = at
        if a.get("wobble"): st["wobble"] = at
        if a.get("bolt"): st["bolt"] = at
        if a.get("sputter"): st["sputters"].append(at)
        if a.get("board"): st["board"] = at
        if isinstance(a.get("wrong"), (int, float)): st["wrong"] = (a["wrong"], at)
        if a.get("show8"): st["show8"] = at
        if a.get("reset"): st["reset"] = at; st["wrong"] = None; st["show8"] = None
        if "num" in a: st["nums"][a["num"]] = at
        if a.get("go"): st["go"] = at
        if a.get("land"): st["land"] = at
        if isinstance(a.get("sweep"), (int, float)): st["sweeps"].append((a["sweep"], a.get("n", 10), at))
        if a.get("hug"): st["hug"] = at
    return st

# ---------------- props: numbers, bolt, rocket ----------------
NUM_COL = {10: "#FF6B6B", 9: ORANGE, 8: YELLOW, 7: "#4CC28A", 6: "#4FA6DB", 5: "#8A6BE0", 4: "#FF7FA8", 3: "#FF8F7A", 2: "#7EE0C3", 1: "#FFB347"}

def num_chip(n, lit=True, s=1.0):
    col = NUM_COL[n] if lit else WHITE
    return G(C(0, 0, 38, col, LINE, 5) + T(0, 14, str(n), 40, WHITE if lit else "#9FB0C4", "bold",
                                         extra=f'stroke="{LINE}" stroke-width="4" paint-order="stroke"' if lit else ""), 0, 0, s)

def bolt_g(rot=0.0):
    hexp = " ".join(f"{16 * math.cos(k * math.pi / 3 + rot):.1f},{16 * math.sin(k * math.pi / 3 + rot):.1f}" for k in range(6))
    return f'<polygon points="{hexp}" fill="#A9B8CC" stroke="{LINE}" stroke-width="4"/>' + C(0, 0, 5, "#7D8898", LINE, 2)

def bolt_icon():
    hexp = " ".join(f"{30 * math.cos(k * math.pi / 3):.1f},{30 * math.sin(k * math.pi / 3):.1f}" for k in range(6))
    o = R(-12, 10, 24, 80, 4, "#C7CED9", LINE, 4)
    for k in range(5):
        o += P(f"M -12 {24 + k * 13} L 12 {18 + k * 13}", stroke=LINE, sw=3)
    return o + f'<polygon points="{hexp}" fill="#A9B8CC" stroke="{LINE}" stroke-width="4"/>' + C(0, 0, 9, "#7D8898", LINE, 3)

PAD_X, PAD_Y = 980, 862
HOLE = (48, -120)   # missing bolt position, relative to rocket base

def flame(t, s=1.0):
    f = 1 + 0.25 * math.sin(t * 40)
    return G(P(f"M -30 0 Q -20 {60 * f:.1f} 0 {110 * f:.1f} Q 20 {60 * f:.1f} 30 0 Z", fill=ORANGE, stroke=LINE, sw=4)
             + P(f"M -14 0 Q -8 {34 * f:.1f} 0 {60 * f:.1f} Q 8 {34 * f:.1f} 14 0 Z", fill=YELLOW), 0, 0, s)

def rocket_g(t, bolt_in=True, hole_blink=False, fire=0.0):
    o = []
    if fire > 0: o.append(G(flame(t, fire), 0, -30))
    o += [P("M -70 -130 L -132 -36 L -70 -66 Z", fill="#FF6B6B", stroke=LINE, sw=5),
          P("M 70 -130 L 132 -36 L 70 -66 Z", fill="#FF6B6B", stroke=LINE, sw=5),
          R(-38, -70, 76, 42, 10, "#5A6B85", LINE, 5),
          R(-70, -340, 140, 290, 34, "#E4EBF4", LINE, 6),
          R(-70, -200, 140, 26, 0, ORANGE), R(-70, -200, 140, 26, 0, "none", LINE, 3),
          P("M -70 -330 Q 0 -470 70 -330 Z", fill="#FF6B6B", stroke=LINE, sw=6),
          C(0, -265, 38, "#BDE7FC", LINE, 6), P("M -18 -280 Q -10 -292 4 -294", stroke=WHITE, sw=6),
          P("M -50 -300 L -50 -90", stroke=WHITE, sw=8, extra='opacity="0.7"'),
          G(bolt_g(), -48, -120), G(bolt_g(), 0, -120), G(bolt_g(), -48, -150), G(bolt_g(), 48, -150)]
    if bolt_in:
        o.append(G(bolt_g(), *HOLE))
    else:
        op = 0.5 + 0.5 * math.sin(t * 8) if hole_blink else 1.0
        o.append(C(HOLE[0], HOLE[1], 14, "#22304A") + C(HOLE[0], HOLE[1], 24, "none", "#E5484D", 5, f'stroke-dasharray="7 6" opacity="{op:.2f}"'))
    return "".join(o)

def parachute(op=1.0):
    return (f'<g opacity="{op:.2f}">' + P("M -150 -560 Q 0 -760 150 -560 Q 100 -590 50 -560 Q 0 -590 -50 -560 Q -100 -590 -150 -560 Z", fill="#FF7FA8", stroke=LINE, sw=5)
            + P("M -150 -560 L -60 -440 M -50 -560 L -30 -440 M 50 -560 L 30 -440 M 150 -560 L 60 -440", stroke=LINE, sw=3)
            + P("M -60 -440 Q 0 -420 60 -440", stroke=LINE, sw=3) + "</g>")

def launch_pad():
    return (R(PAD_X - 150, PAD_Y, 300, 24, 10, "#7D8898", LINE, 5)
            + P(f"M {PAD_X - 130} {PAD_Y + 24} L {PAD_X - 150} {PAD_Y + 50} M {PAD_X + 130} {PAD_Y + 24} L {PAD_X + 150} {PAD_Y + 50}", stroke=LINE, sw=8)
            + R(PAD_X - 200, PAD_Y - 220, 20, 240, 6, "#C98B3B", LINE, 4) + R(PAD_X - 200, PAD_Y - 150, 60, 14, 5, "#C98B3B", LINE, 3))

def rocket_scene(t, st):
    """Rocket on its pad (or flying), with wobble / bolt / sputter / launch / landing."""
    o = [launch_pad()]
    bolt_in = st["bolt"] is not None and t >= st["bolt"] + 1.6
    blink = st["wobble"] is not None and not bolt_in
    rot = 0.0; dx = 0.0; dy = 0.0; fire = 0.0
    if st["wobble"] is not None and not bolt_in:
        rot = 4 * math.sin(t * 7)
    for sp in st["sputters"]:
        a = t - sp
        if 0 <= a < 1.4:
            dx = 6 * math.sin(a * 50) * (1 - a / 1.4); fire = max(fire, 0.35 * abs(math.sin(a * 9)))
            for k in range(3):
                q = a - k * 0.3
                if 0 < q < 1.0:
                    o.append(C(PAD_X - 40 + k * 40, PAD_Y - 10 - q * 60, 22 + q * 30, "#C9D2DE", extra=f'opacity="{0.8 * (1 - q):.2f}"'))
    chute = 0.0
    if st["go"] is not None:
        a = t - st["go"]
        fire = 1.0
        dy = -min(1400, 40 * a + 420 * a * a)
        if st["land"] is not None and t >= st["land"]:
            b = t - st["land"]
            k = ease(min(1, b / 2.6))
            dy = -1300 * (1 - k); fire = 0.0
            chute = 1.0 if b < 2.6 else max(0, 1 - (b - 2.6) / 0.6)
            dx = 30 * math.sin(b * 2) * (1 - k)
        elif st["land"] is not None and t < st["land"] and a > 3.5:
            dy = -1400
        else:
            for k in range(6):
                q = (a * 1.5 + k / 6) % 1
                o.append(C(PAD_X - 30 + 60 * math.sin(k * 2), PAD_Y + dy + 40 + q * 300, 10 + k % 3 * 5, "none", WHITE, 4, f'opacity="{0.9 * (1 - q):.2f}"'))
    if dy > -1350:
        g = ""
        if chute > 0: g += parachute(chute)
        g += rocket_g(t, bolt_in, blink, fire)
        o.append(G(g, PAD_X + dx, PAD_Y + dy, 1, rot))
    # bolt carried by Bloop, then flying into the hole
    if st["enter"] is not None and not bolt_in:
        bx, by = 1600, 600
        if st["bolt"] is not None and t >= st["bolt"]:
            a = t - st["bolt"]
            k = ease(min(1, a / 0.9))
            hx, hy = PAD_X + HOLE[0], PAD_Y + HOLE[1]
            bx = bx + (hx - bx) * k; by = by + (hy - by) * k - 160 * math.sin(k * math.pi)
            r = a * 12 if a > 0.9 else a * 4
            o.append(G(bolt_g(r), bx, by, 1.2 if a < 0.9 else 1.0))
            if a > 0.9:
                o.append(sparkle(bx + 22, by - 22, 1.2, YELLOW, 0.5 + 0.5 * math.sin(t * 12)))
        else:
            o.append(C(bx, by, 40, "url(#glow)", extra='opacity="0.7"') + G(bolt_g(t), bx, by + 6 * math.sin(t * 2), 1.4))
    return "".join(o)

# ---------------- countdown board ----------------
BOARD_X = [600 + i * 84 for i in range(10)]   # numbers 10..1, left to right
BOARD_Y = 300

def board_state(t, st):
    lit = {}
    if st["wrong"] is not None:
        step, at = st["wrong"]
        for i, n in enumerate((10, 9, 7)):
            if t >= at + i * step: lit[n] = at + i * step
    for n, at in st["nums"].items():
        if st["reset"] is None or at >= st["reset"]: lit[n] = at
    return lit

def countdown_board(t, st):
    if st["board"] is None: return ""
    op = ease((t - st["board"]) / 0.4)
    lit = board_state(t, st)
    o = [R(552, BOARD_Y - 62, 816, 124, 30, "#2A5A86", LINE, 6, 'fill-opacity="0.9"')]
    for i, n in enumerate(range(10, 0, -1)):
        x = BOARD_X[i]
        s = 1.0
        if n in lit:
            a = t - lit[n]; s = 1 + 0.35 * max(0, 1 - a / 0.4)
        for step, cnt, at in st["sweeps"]:
            a = t - at - i * step
            if 0 <= a < 0.5: s = max(s, 1 + 0.3 * (1 - a / 0.5))
        o.append(G(num_chip(n, n in lit), x, BOARD_Y, s))
        if n == 8 and st["show8"] is not None:
            a = t - st["show8"]
            if a < 4.0:
                o.append(C(x, BOARD_Y, 52, "none", YELLOW, 8, f'opacity="{0.6 + 0.4 * math.sin(t * 10):.2f}"'))
                o.append(G(T(0, 0, "&#8595;", 60, YELLOW, "bold", extra=f'stroke="{LINE}" stroke-width="5" paint-order="stroke"'), x, BOARD_Y - 80 + 8 * math.sin(t * 6)))
    if st["wrong"] is not None and st["show8"] is None:
        step, at = st["wrong"]
        if t >= at + 2 * step:
            o.append(G(P("M -18 -18 L 18 18 M 18 -18 L -18 18", stroke="#E5484D", sw=9), BOARD_X[2], BOARD_Y - 58, ease((t - at - 2 * step) / 0.3)))
    return f'<g opacity="{op:.2f}">{"".join(o)}</g>'

def big_number(t, st):
    """The number being counted, big, next to the rocket."""
    if not st["nums"]: return ""
    n, at = min(st["nums"].items(), key=lambda kv: -kv[1])
    if st["reset"] is not None and at < st["reset"]: return ""
    a = t - at
    if a > 1.2 or (st["go"] is not None and t >= st["go"]): return ""
    return G(T(0, 0, str(n), 220, NUM_COL[n], "bold", extra=f'stroke="{LINE}" stroke-width="10" paint-order="stroke"'),
             1340, 640, ease(a / 0.2) * (1 + 0.2 * max(0, 1 - a / 0.3)))

def lesson_banner(age, t=0.0):
    s = ease(age / 0.35)
    g = (R(-780, -66, 1560, 132, 66, WHITE, ORANGE, 6)
         + T(-430, 16, "Count backwards: one less each time!", 42, LINE, "bold")
         + G(num_chip(10), 330, 0, 0.9) + G(P("M -40 0 L 40 0 M 20 -18 L 40 0 L 20 18", stroke=LINE, sw=7), 450, 0)
         + G(num_chip(1), 570, 0, 0.9) + G(rocket_g(t, True, False, 0), 690, 52, 0.28))
    return G(g, 960, 100, s)

def heart(x, y, s, op=1.0, col="#FF7FA8"):
    d = "M 0 12 C -28 -6 -18 -30 0 -16 C 18 -30 28 -6 0 12 Z"
    return f'<g opacity="{op:.2f}">{G(P(d, fill=col, stroke=LINE, sw=3), x, y, s)}</g>'

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
    if st["hi"] is not None:
        spots = [(420, 300), (1500, 300), (300, 560), (1620, 560), (560, 130), (1360, 130), (960, 100), (250, 790), (1680, 800), (760, 330)]
        for i, (x, y) in enumerate(spots):
            n = 10 - i
            age = t - st["hi"] - i * 0.2
            if age > 0:
                o.append(G(num_chip(n), x + 20 * math.sin(t + i), y + 14 * math.sin(t * 1.5 + i), 1.5 * ease(age / 0.4), 8 * math.sin(t * 1.2 + i)))
    o.append(place_bo(t, 960, 940, 1.7))
    if st["q"] is not None and t - st["q"] < 3.2:
        age = t - st["q"]
        o.append(G(T(0, 0, "?", 190, ORANGE, "bold", extra=f'stroke="{LINE}" stroke-width="8" paint-order="stroke"'),
                   1250, 520 + 12 * math.sin(t * 4), ease(age / 0.3), 8 * math.sin(t * 3)))
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
        o.append(G(R(-170, -40, 340, 80, 40, "#4FA6DB", LINE, 5) + T(0, 16, "Count with Bo", 38, WHITE, "bold"), 960, 520, s))
    if age > 4.0:
        s = ease((age - 4.0) / 0.4)
        o.append(G(T(0, 0, "Bo&#8217;s Missing Bolt", 64, WHITE, "bold", extra=f'stroke="{LINE}" stroke-width="7" paint-order="stroke"'), 960, 660, s))
        icons = G(num_chip(3), -210, 0, 0.9) + G(num_chip(2), -120, 0, 0.9) + G(num_chip(1), -30, 0, 0.9) + G(bolt_icon(), 90, -20, 0.8, 15 * math.sin(t * 2)) + G(rocket_g(t, True, False, 0.6), 210, 60, 0.3)
        o.append(G(icons, 960, 780, s))
    for i in range(6):
        a = (t * 1.5 + i * 0.37) % 2
        o.append(sparkle(300 + i * 270, 180 + (i % 2) * 520, 1.4, YELLOW, max(0, math.sin(a * math.pi / 2))))
    return "".join(o)

def scene_lab(t, t0, st):
    o = [background(t, "lab")]
    op = 0.0 if st["rocket"] is None else ease((t - st["rocket"]) / 0.4)
    if op > 0.01:
        o.append(f'<g opacity="{op:.2f}">{rocket_scene(t, st)}</g>' if op < 0.999 else rocket_scene(t, st))
    point = 0.0
    if st["bolt"] is not None and 0 <= t - st["bolt"] < 1.6: point = math.sin(min(1, (t - st["bolt"]) / 1.6) * math.pi)
    o.append(place_bo(t, 300, 900, 1.15, point=point))
    if st["enter"] is not None:
        a = ease((t - st["enter"]) / 1.3)
        x = 2250 + (1640 - 2250) * a
        if a < 1:
            for k in range(4):
                o.append(C(x + 140 + k * 60, 470 + 20 * math.sin(k + t * 5), 10 + k * 3, "none", "#E8F8FF", 3, 'opacity="0.8"'))
        o.append(place_bloop(t, x, 460, 1.0))
    o.append(countdown_board(t, st))
    o.append(big_number(t, st))
    if st["hug"] is not None:
        a = t - st["hug"]
        for k in range(6):
            q = a - k * 0.35
            if 0 < q < 2.6:
                o.append(heart(520 + k * 190, 640 - q * 160, 1.6, max(0, 1 - q / 2.6)))
    if st["lesson"] and st["lesson"][0]:
        o.append(lesson_banner(t - st["lesson"][1], t))
    elif st["lesson"] and not st["lesson"][0] and t - st["lesson"][1] < 0.3:
        o.append(f'<g opacity="{1 - (t - st["lesson"][1]) / 0.3:.2f}">{lesson_banner(1, t)}</g>')
    return "".join(o)

def scene_song(t, t0, st):
    o = [background(t, "song")]
    beat = 0.6
    ph = ((t - t0) % beat) / beat
    o.append(C(960, 500, 380 + 30 * (1 - ph), "url(#glow)", extra='opacity="0.35"'))
    for i in range(10):   # music notes in an arc
        a = math.pi * (0.9 - 0.8 * i / 9)
        x, y = 960 + 820 * math.cos(a), 470 - 330 * math.sin(a)
        o.append(G(T(0, 0, "&#9835;" if i % 2 else "&#9834;", 70, NUM_COL[10 - i], "bold", extra=f'stroke="{LINE}" stroke-width="4" paint-order="stroke"'),
                   x, y + 8 * math.sin(t * 3 + i), 1, 10 * math.sin(t * 3 + i)))
    o.append(place_bo(t, 280, 900, 1.05, dance=1))
    o.append(place_bloop(t, 1650, 600, 1.05, energy=2.5, dance=1))
    phase, pt = st["phase"] if st["phase"] else (None, t0)
    a = t - pt
    order = {"top": 0, "bottom": 1, "less": 2, "blast": 3, "again": 4, "all": 5}.get(phase, -1)
    def lit(i):   # i = 0 for 10 ... 9 for 1
        if order < 0: return False
        if order == 0: return i < 5 and a >= i * 0.6
        if order == 1: return i < 5 or a >= (i - 5) * 0.6
        if order == 4: return a >= i * 0.3
        return True
    if order != 3:
        for i in range(10):
            n = 10 - i
            x = 960 + (i - 4.5) * 96
            s = 1.15
            if order == 5: s *= 1 + 0.12 * abs(math.sin((t - t0) * math.pi / beat + i * 0.5))
            o.append(G(num_chip(n, lit(i)), x, 470 + 8 * math.sin(t * 3 + i), s))
            if order == 2 and i < 9:
                o.append(G(R(-26, -18, 52, 36, 18, WHITE, "#2E8FCC", 3) + T(0, 10, "&#8722;1", 24, "#2E8FCC", "bold"), x + 48, 560 + 6 * math.sin(t * 4 + i)))
    else:
        y = 760 - ((a * 260) % 900)
        o.append(G(rocket_g(t, True, False, 1.0), 960, y + 200, 0.8))
        for k in range(5):
            q = (a * 1.3 + k / 5) % 1
            o.append(C(960 + 40 * math.sin(k * 2), y + 230 + q * 220, 10 + k % 3 * 4, "none", WHITE, 4, f'opacity="{1 - q:.2f}"'))
    label = {"top": "10, 9, 8, 7, 6", "bottom": "5, 4, 3, 2, 1!", "less": "One less each time", "blast": "Blast off!",
             "again": "Ten down to one!", "all": "Count down with Bo!"}.get(phase)
    if label:
        o.append(G(R(-250, -40, 500, 80, 40, WHITE, ORANGE, 5) + T(0, 15, label, 40, LINE, "bold"), 960, 300))
    return "".join(o)

def scene_lab_end(t, t0, st):
    o = [background(t, "lab_end")]
    o.append(rocket_scene(t, st))
    o.append(countdown_board(t, st))
    wave = 0.0
    if st["wave"] is not None:
        wave = ease((t - st["wave"]) / 0.4)
    o.append(place_bo(t, 300, 900, 1.15, wave=wave))
    o.append(place_bloop(t, 1640, 460, 1.05, energy=1 + 2 * wave))
    return "".join(o)

def coral_icon(t):
    cols = ["#FF6B6B", ORANGE, YELLOW, "#4CC28A", "#4FA6DB", "#8A6BE0"]
    o = ""
    for k, c in enumerate(cols):
        a = -math.pi / 2 + (k - 2.5) * 0.28
        d = f"M 0 60 Q {40 * math.cos(a):.0f} 0 {90 * math.cos(a):.0f} {60 + 110 * math.sin(a):.0f}"
        o += P(d, stroke=LINE, sw=22) + P(d, stroke=c, sw=14)
    return o

def scene_end(t, t0, st):
    age = t - t0
    o = [background(t, "end")]
    o.append(G(T(0, 0, "Bo &amp; Bloop", 96, ORANGE, "bold", extra=f'stroke="{LINE}" stroke-width="10" paint-order="stroke"'), 960, 170, ease(age / 0.4)))
    s = ease((age - 0.4) / 0.4)
    card = (R(-520, -190, 1040, 380, 40, WHITE, LINE, 6, 'fill-opacity="0.95"')
            + T(0, -110, "NEXT TIME", 34, "#2E8FCC", "bold", extra='letter-spacing="6"')
            + T(0, -30, "The Rainbow Coral", 60, LINE, "bold"))
    card += G(coral_icon(t), -300, 70, 0.8)
    mix = (C(-130, 0, 36, "#FF6B6B", LINE, 5) + T(-65, 14, "+", 44, LINE, "bold") + C(0, 0, 36, YELLOW, LINE, 5)
           + T(65, 14, "=", 44, LINE, "bold") + C(130, 0, 36, ORANGE, LINE, 5))
    card += G(mix, 120, 100 + 6 * math.sin(t * 3))
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
    with Pool(4) as pool:
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
