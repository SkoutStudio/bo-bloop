"""Render the episode frames from build/timeline.json and encode with the soundtrack."""
import json, math, os, subprocess, sys
from multiprocessing import Pool
import cairosvg
from chars import *  # noqa
from script import ROCKS

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

PERSIST = ("pop", "label", "bloop_enter", "move", "tumble", "square_show", "square_hide", "corner", "bins", "build", "tower_done")

def state_at(t, since):
    st = dict(b={}, big=None, lesson=False, enter=None, q=None, hb=None, wave=None, song_num=None, title=None,
              tumble=None, sq=None, sq_hide=None, corner_hl={}, corners={}, bins=None, build=None, tower=None,
              roll=None, phase=None)
    for a in ACTS:
        if a["t"] > t: break
        if a["t"] < since - 1e-6 and not any(k in a for k in PERSIST):
            continue
        at = a["t"]
        if "pop" in a: st["b"].setdefault(a["pop"], {})["spawn"] = at
        if "label" in a:
            i, n, ok = a["label"]; st["b"].setdefault(i, {})["label"] = (n, ok, at)
        if "highlight" in a: st["b"].setdefault(a["highlight"], {})["hl"] = at
        if "move" in a: st["b"].setdefault(a["move"], {})["move"] = at
        if "big" in a: st["big"] = (a["big"], at)
        if "lesson" in a: st["lesson"] = (a["lesson"], at)
        if a.get("bloop_enter"): st["enter"] = at
        if a.get("question"): st["q"] = at
        if a.get("hook_rocks"): st["hb"] = at
        if a.get("wave"): st["wave"] = at
        if "song_num" in a: st["song_num"] = (a["song_num"], at)
        if "song_phase" in a: st["phase"] = (a["song_phase"], at)
        if a.get("title"): st["title"] = at
        if a.get("tumble"): st["tumble"] = at
        if a.get("square_show"): st["sq"] = at
        if a.get("square_hide"): st["sq_hide"] = at
        if "corner_hl" in a: st["corner_hl"][a["corner_hl"]] = at
        if "corner" in a: st["corners"][a["corner"]] = at
        if a.get("bins"): st["bins"] = at
        if a.get("build"): st["build"] = at
        if a.get("tower_done"): st["tower"] = at
        if a.get("roll_fun"): st["roll"] = at
    return st

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

# ---------------- props: rocks, bins, tower ----------------
ROCK_COLS = ["#FFB347", "#7EE0C3", "#FF8F7A", "#B39DFF", "#FFD54A", "#9EC9FF", "#F7A8C8", "#8FD6E8"]
ROLL_DELAY = 3.4

def rock(shape, r, col, face=True, rot=0.0, smile=True):
    if shape == "c":
        body = C(0, 0, r, col, LINE, 6)
        spots = [(-0.4, 0.35, 0.09), (0.45, 0.4, 0.07), (0.2, -0.55, 0.06)]
    else:
        body = R(-r, -r, 2 * r, 2 * r, r * 0.16, col, LINE, 6)
        spots = [(-0.6, 0.6, 0.09), (0.62, 0.55, 0.07), (0.55, -0.6, 0.06)]
    o = [body]
    for (sx, sy, sr) in spots:
        o.append(C(sx * r, sy * r, sr * r, LINE, extra='opacity="0.18"'))
    o.append(P(f"M {-r*0.62:.1f} {-r*0.2:.1f} Q {-r*0.6:.1f} {-r*0.58:.1f} {-r*0.25:.1f} {-r*0.66:.1f}", stroke=WHITE, sw=max(3, r * 0.09), extra='opacity="0.7"'))
    if face:
        o += [E(-r * 0.24, -r * 0.05, r * 0.08, r * 0.11, NAVY), E(r * 0.24, -r * 0.05, r * 0.08, r * 0.11, NAVY),
              C(-r * 0.21, -r * 0.09, r * 0.03, WHITE), C(r * 0.27, -r * 0.09, r * 0.03, WHITE)]
        if smile:
            o.append(P(f"M {-r*0.16:.1f} {r*0.2:.1f} Q 0 {r*0.34:.1f} {r*0.16:.1f} {r*0.2:.1f}", stroke=NAVY, sw=max(2.5, r * 0.06)))
        o += [E(-r * 0.42, r * 0.16, r * 0.1, r * 0.06, PINK, extra='opacity="0.6"'), E(r * 0.42, r * 0.16, r * 0.1, r * 0.06, PINK, extra='opacity="0.6"')]
    return G("".join(o), 0, 0, 1, rot)

def rock_item(x, y, r, t, i, label=None, hl=0.0, scale=1.0):
    o = []
    if hl > 0:
        o.append(C(x, y, r + 34, "url(#glow)", extra=f'opacity="{min(1, hl):.2f}"'))
        o.append(C(x, y, r + 20, "none", YELLOW, 7, f'opacity="{min(1, hl):.2f}"'))
    g = rock(ROCKS[i], r, ROCK_COLS[i % 8], rot=4 * math.sin(t * 2 + i) if ROCKS[i] == "s" else 0)
    if label:
        txt, ls = label
        col = ORANGE if ROCKS[i] == "c" else "#2E8FCC"
        w = len(txt) * 22 + 40
        g += G(R(-w / 2, -30, w, 60, 30, WHITE, col, 5) + T(0, 13, txt, 38, col, "bold"), 0, -r - 50, ls)
    o.append(G(g, x, y, scale))
    return "".join(o)

def grid_pos(i):
    row, col = divmod(i, 4)
    return 700 + col * 180, 290 + row * 200

BIN_X = {"c": 770, "s": 1170}; BIN_Y = 885

def bin_slot(shape, k):
    return BIN_X[shape] - 105 + k * 70, BIN_Y - 62

def sort_bin(shape, appear=1.0):
    col = ORANGE if shape == "c" else "#2E8FCC"
    name = "CIRCLES" if shape == "c" else "SQUARES"
    icon = C(0, 0, 16, ORANGE_L, LINE, 4) if shape == "c" else R(-15, -15, 30, 30, 4, "#9ED8F5", LINE, 4)
    g = (P("M -160 -20 Q -165 30 -120 40 L 120 40 Q 165 30 160 -20 Z", fill="#D9B07A", stroke=LINE, sw=6)
         + P("M -150 0 L 150 0 M -140 22 L 140 22", stroke="#B8894F", sw=5)
         + R(-170, -34, 340, 22, 11, "#E8C690", LINE, 5)
         + R(-110, 52, 220, 48, 24, col, LINE, 4) + G(icon, -78, 76) + T(14, 87, name, 26, WHITE, "bold"))
    return G(g, BIN_X[shape], BIN_Y, appear)

TOWER_X = 555

def tower_slot(k):
    return TOWER_X, 878 - 50 - k * 100

def big_badge(n, age):
    if age < 0 or age > 1.9: return ""
    s = ease(age / 0.25) * (1 + 0.15 * math.sin(min(age, 0.6) * 10) * max(0, 1 - age / 0.6))
    op = 1 if age < 1.5 else max(0, 1 - (age - 1.5) / 0.4)
    g = (C(0, 0, 88, YELLOW, LINE, 6) + C(0, 0, 70, "none", WHITE, 4, 'opacity="0.6"')
         + T(0, 42, str(n), 120, LINE, "bold"))
    return f'<g opacity="{op:.2f}">{G(g, 960, 120, s)}</g>'

def lesson_banner(age):
    s = ease(age / 0.35)
    g = (R(-560, -56, 1120, 112, 56, WHITE, ORANGE, 6)
         + G(rock("c", 30, ORANGE_L, face=False), -490, 0) + G(rock("s", 28, "#9ED8F5", face=False), 490, 0)
         + T(0, 16, "Circles roll! Squares have 4 corners!", 46, LINE, "bold"))
    return G(g, 960, 112, s)

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
def place_bo(t, x, ground, s, wave=0.0, dance=0.0):
    m = mouth_at("bo", t)
    bob = 4 * math.sin(t * 2.4) + (6 * m) + dance * abs(math.sin(t * math.pi * 100 / 60)) * -22
    shadow = E(x, ground + 4, 120 * s, 16 * s, LINE, extra='opacity="0.12"')
    return shadow + G(bo(expr_at("bo", t), m, blink_at(t, 0.3) and m < 0.06, t, wave=wave), x, ground - bob * s, s)

def place_bloop(t, x, y, s, energy=1.0, dance=0.0):
    m = mouth_at("bloop", t)
    fy = 12 * math.sin(t * 1.6) + dance * abs(math.sin(t * math.pi * 100 / 60 + 0.5)) * -26
    return G(bloop(expr_at("bloop", t), m, blink_at(t, 1.9) and m < 0.06, t, energy), x, y + fy, s, 4 * math.sin(t * 1.1))

# ---------------- scenes ----------------
def scene_hook(t, t0, st):
    o = [background(t, "hook")]
    if st["hb"] is not None:
        spots = [(450, 360, "c"), (1470, 330, "s"), (330, 700, "s"), (1590, 690, "c"), (1260, 170, "c"), (650, 160, "s")]
        for i, (x, y, sh) in enumerate(spots):
            age = t - st["hb"] - i * 0.25
            if age > 0:
                g = rock(sh, 66, ROCK_COLS[i], rot=(8 * math.sin(t * 2 + i) if sh == "s" else (t * 40 + i * 50)))
                o.append(G(g, x + 20 * math.sin(t + i), y + 14 * math.sin(t * 1.5 + i), ease(age / 0.4)))
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
        o.append(G(R(-160, -40, 320, 80, 40, "#2E8FCC", LINE, 5) + T(0, 16, "Shape Reef", 40, WHITE, "bold"), 960, 520, s))
    if age > 4.0:
        s = ease((age - 4.0) / 0.4)
        o.append(G(T(0, 0, "Circle Rocks &amp; Square Rocks", 60, WHITE, "bold", extra=f'stroke="{LINE}" stroke-width="7" paint-order="stroke"'), 960, 660, s))
        o.append(G(rock("c", 44, "#FFB347", rot=t * 90), 820, 780, s) + G(rock("s", 40, "#7EE0C3"), 1100, 780, s))
    for i in range(6):
        a = (t * 1.5 + i * 0.37) % 2
        o.append(sparkle(300 + i * 270, 180 + (i % 2) * 520, 1.4, YELLOW, max(0, math.sin(a * math.pi / 2))))
    return "".join(o)

def tumble_layer(t, st):
    if st["tumble"] is None: return ""
    o = []
    for k in range(3):
        at = st["tumble"] + k * 0.6
        if t < at: continue
        x, y = TOWER_X, 878 - 58 - k * 112
        a = ease((t - at) / 0.3)
        y = y - 220 * (1 - a)
        rot = 0
        rt = t - st["tumble"] - ROLL_DELAY + k * 0.05
        if rt > 0:
            if k == 0 and rt < 0.3:
                x += 30 * math.sin(rt * 20) * (1 - rt / 0.3)
            v = 230 + 140 * (2 - k)
            dx = v * rt + 60 * rt * rt
            dropy = (878 - 58) - y
            fall = min(1, rt / (0.25 + 0.15 * k))
            y = y + dropy * fall ** 2
            x = x + dx * (1 if k != 1 else 1.15)
            rot = math.degrees(dx / 58)
            if x > 2100: continue
        o.append(G(rock("c", 58, ROCK_COLS[(k * 2) % 8], rot=rot), x, y))
    return "".join(o)

def square_demo(t, st):
    if st["sq"] is None: return ""
    age = t - st["sq"]
    op = 1.0
    if st["sq_hide"] is not None:
        h = t - st["sq_hide"]
        if h > 0.4: return ""
        op = 1 - h / 0.4
    s = ease(age / 0.4)
    o = []
    # circle for comparison
    o.append(G(rock("c", 105, "#FFB347", rot=25 * math.sin(t * 1.5)) + R(-90, 128, 180, 52, 26, WHITE, ORANGE, 4)
               + T(0, 164, "CIRCLE", 30, ORANGE, "bold") + R(-110, 190, 220, 44, 22, "#FFE7D6") + T(0, 221, "no corners", 26, LINE, "bold"),
               730, 410, s))
    sq = rock("s", 150, "#7EE0C3")
    corners = [(-150, -150), (150, -150), (150, 150), (-150, 150)]
    for n, (cx, cy) in enumerate(corners, 1):
        if n in st["corner_hl"]:
            a = t - st["corner_hl"][n]
            pul = 0.75 + 0.25 * math.sin(t * 10) if n not in st["corners"] else 0.6
            sq += C(cx, cy, 46, "url(#glow)", extra=f'opacity="{min(1, a / 0.15) * pul:.2f}"')
            sq += C(cx, cy, 22, YELLOW, LINE, 5, f'opacity="{min(1, a / 0.15):.2f}"')
        if n in st["corners"]:
            a = t - st["corners"][n]
            ls = ease(a / 0.25) * (1 + 0.25 * max(0, 1 - a / 0.4))
            bx, by = cx * 1.42, cy * 1.42
            sq += G(C(0, 0, 36, WHITE, LINE, 5) + T(0, 18, str(n), 50, LINE, "bold"), bx, by, ls)
    sq += R(-90, 178, 180, 52, 26, WHITE, "#2E8FCC", 4) + T(0, 214, "SQUARE", 30, "#2E8FCC", "bold")
    o.append(G(sq, 1130, 400, s))
    return f'<g opacity="{op:.2f}">{"".join(o)}</g>'

def rocks_layer(t, st):
    o = []
    moved = {"c": [], "s": []}
    for i, b in sorted(st["b"].items(), key=lambda kv: kv[1].get("move", 1e9)):
        if "move" in b: moved[ROCKS[i]].append(i)
    build = st["build"]
    for i, b in sorted(st["b"].items()):
        if "spawn" not in b: continue
        sh = ROCKS[i]
        x, y = grid_pos(i)
        x += 6 * math.sin(t * 1.1 + i); y += 8 * math.sin(t * 1.4 + i)
        sc = ease((t - b["spawn"]) / 0.35)
        hl = 0.0
        if "hl" in b and "move" not in b:
            hl = min(1, (t - b["hl"]) / 0.15) * (0.75 + 0.25 * math.sin(t * 10))
        label = None
        if "label" in b:
            a = t - b["label"][2]
            label = (b["label"][0], ease(a / 0.25) * (1 + 0.25 * max(0, 1 - a / 0.4)))
        rot = 0.0
        if "move" in b:
            k = moved[sh].index(i)
            a = ease((t - b["move"]) / 0.7)
            tx, ty = bin_slot(sh, k)
            x = x + (tx - x) * a; y = y + (ty - y) * a - 140 * math.sin(a * math.pi)
            sc *= 1 - 0.45 * a
            if a > 0.5: label = None
            if a >= 1:
                x, y = tx, ty
                # squares fly to the tower
                if sh == "s" and build is not None:
                    bt = t - build - 0.4 - k * 0.5
                    if bt > 0:
                        q = ease(bt / 0.5)
                        px, py = tower_slot(k)
                        x = tx + (px - tx) * q; y = ty + (py - ty) * q - 180 * math.sin(q * math.pi)
                        sc = 0.55 + (50 / 58 - 0.55) * q
                # circles roll away for fun
                if sh == "c" and st["roll"] is not None:
                    rt = t - st["roll"] - 0.3 - k * 0.25
                    if rt > 0:
                        hop = min(1, rt / 0.35)
                        y = ty - 90 * math.sin(hop * math.pi) + (60 * hop if hop >= 1 else 60 * hop)
                        dx = 320 * rt + 120 * rt * rt
                        x = tx + dx
                        rot = math.degrees(dx / 32)
                        if x > 2100: continue
        g = rock_item(x, y, 58, t, i, label, hl, sc)
        if rot:
            g = G(rock(sh, 58, ROCK_COLS[i % 8], rot=rot), x, y, sc)
        o.append(g)
    return "".join(o)

def scene_lab(t, t0, st):
    o = [background(t, "lab")]
    if st["bins"] is not None:
        ap = ease((t - st["bins"]) / 0.45)
        o.append(sort_bin("c", ap) + sort_bin("s", ap))
    o.append(place_bo(t, 300, 900, 1.15))
    o.append(tumble_layer(t, st))
    if st["enter"] is not None:
        a = ease((t - st["enter"]) / 1.3)
        x = 2250 + (1640 - 2250) * a
        if a < 1:
            for k in range(4):
                o.append(C(x + 140 + k * 60, 520 + 20 * math.sin(k + t * 5), 10 + k * 3, "none", "#E8F8FF", 3, 'opacity="0.8"'))
        o.append(place_bloop(t, x, 500, 1.05))
    o.append(square_demo(t, st))
    o.append(rocks_layer(t, st))
    if st["tower"] is not None:
        a = t - st["tower"]
        for k in range(5):
            o.append(sparkle(TOWER_X - 110 + (k % 2) * 220, 520 + k * 70, 1.2, YELLOW, max(0, math.sin((t * 1.6 + k * 0.4) % 2 * math.pi / 2)) * min(1, a / 0.3)))
    if st["big"] is not None:
        o.append(big_badge(st["big"][0], t - st["big"][1]))
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
    for i in range(10):  # little shapes floating in an arc
        a = math.pi * (0.9 - 0.8 * i / 9)
        x, y = 960 + 820 * math.cos(a), 470 - 330 * math.sin(a)
        sh = "c" if i % 2 == 0 else "s"
        o.append(G(rock(sh, 34, ROCK_COLS[i % 8], rot=(t * 60 if sh == "c" else 6 * math.sin(t * 3 + i))), x, y + 8 * math.sin(t * 3 + i)))
    o.append(place_bo(t, 280, 900, 1.05, dance=1))
    o.append(place_bloop(t, 1650, 600, 1.05, energy=2.5, dance=1))
    phase = st["phase"][0] if st["phase"] else None
    bounce = abs(math.sin((t - t0) * math.pi / beat))
    if phase in (None, "circle", "both"):
        if phase == "circle":
            x = 960 + 260 * math.sin((t - st["phase"][1]) * 1.3)
            rot = math.degrees((x - 960) / 120)
            o.append(G(rock("c", 130, "#FFB347", rot=rot), x, 560))
        else:
            o.append(G(rock("c", 110 if phase else 90, "#FFB347", rot=t * 50), 760, 560 - 20 * bounce))
    if phase in (None, "square", "both"):
        if phase == "square":
            sq = rock("s", 140, "#7EE0C3")
            cur = st["song_num"]
            corners = [(-140, -140), (140, -140), (140, 140), (-140, 140)]
            for n, (cx, cy) in enumerate(corners, 1):
                if cur and cur[1] >= st["phase"][1] and n <= cur[0]:
                    a = t - cur[1] if n == cur[0] else 1
                    sq += C(cx, cy, 24, YELLOW, LINE, 5) + G(C(0, 0, 32, WHITE, LINE, 5) + T(0, 16, str(n), 44, LINE, "bold"),
                                                          cx * 1.45, cy * 1.45, 1 + 0.3 * max(0, 1 - a / 0.3))
            o.append(G(sq, 960, 540 - 30 * bounce))
        else:
            o.append(G(rock("s", 100 if phase else 80, "#7EE0C3"), 1160, 560 - 20 * (1 - bounce)))
    return "".join(o)

def scene_lab_end(t, t0, st):
    o = [background(t, "lab_end")]
    o.append(sort_bin("c") )
    for k in range(4):
        x, y = tower_slot(k)
        o.append(G(rock("s", 50, ROCK_COLS[[1, 2, 4, 7][k]]), x + 300, y))
    for k in range(4):
        x, y = bin_slot("c", k)
        o.append(G(rock("c", 32, ROCK_COLS[[0, 3, 5, 6][k]]), x, y))
    wave = 0.0
    if st["wave"] is not None:
        wave = ease((t - st["wave"]) / 0.4)
    o.append(place_bo(t, 420, 900, 1.2, wave=wave))
    o.append(place_bloop(t, 1400, 470, 1.15, energy=1 + 2 * wave))
    return "".join(o)

def face_icon(kind, col):
    o = C(0, 0, 44, col, LINE, 5) + E(-14, -8, 5, 7, NAVY) + E(14, -8, 5, 7, NAVY)
    if kind == "happy": o += P("M -16 12 Q 0 28 16 12", stroke=NAVY, sw=5)
    elif kind == "sad": o += P("M -16 22 Q 0 8 16 22", stroke=NAVY, sw=5)
    elif kind == "grumpy": o += P("M -16 18 L 16 18", stroke=NAVY, sw=5) + P("M -24 -22 L -6 -16 M 24 -22 L 6 -16", stroke=NAVY, sw=5)
    else: o += P("M -12 14 Q 0 20 12 14", stroke=NAVY, sw=5) + P("M -20 -10 Q -14 -4 -8 -10 M 8 -10 Q 14 -4 20 -10", stroke=NAVY, sw=4)
    return o

def scene_end(t, t0, st):
    age = t - t0
    o = [background(t, "end")]
    o.append(G(T(0, 0, "Bo &amp; Bloop", 96, ORANGE, "bold", extra=f'stroke="{LINE}" stroke-width="10" paint-order="stroke"'), 960, 170, ease(age / 0.4)))
    s = ease((age - 0.4) / 0.4)
    card = (R(-520, -190, 1040, 380, 40, WHITE, LINE, 6, 'fill-opacity="0.95"')
            + T(0, -110, "NEXT TIME", 34, "#2E8FCC", "bold", extra='letter-spacing="6"')
            + T(0, -30, "When Bo Feels Grumpy", 60, LINE, "bold"))
    for i, (k, col) in enumerate([("happy", "#FFD54A"), ("grumpy", "#FF8F7A"), ("sad", "#9EC9FF"), ("calm", "#7EE0C3")]):
        card += G(face_icon(k, col), -255 + i * 170, 95 + 10 * math.sin(t * 3 + i), 1, 8 * math.sin(t * 2 + i))
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
