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

def state_at(t, since):
    st = dict(b={}, big=None, lesson=False, enter=None, jar=None, q=None, hb=None, wave=None, song_num=None, title=None)
    for a in ACTS:
        if a["t"] > t: break
        if a["t"] < since - 1e-6 and not any(k in a for k in ("pop", "label", "clear_labels", "clear_labels_from", "bloop_enter", "to_jar")):
            continue
        at = a["t"]
        if "pop" in a: st["b"].setdefault(a["pop"], {})["spawn"] = at
        if "label" in a:
            i, n, ok = a["label"]; st["b"].setdefault(i, {})["label"] = (n, ok, at); st["b"][i].pop("old", None)
        if a.get("clear_labels") or "clear_labels_from" in a:
            k0 = a.get("clear_labels_from", 0)
            for i, b in st["b"].items():
                if i >= k0 and "label" in b:
                    b["old"] = (b.pop("label"), at)
        if "highlight" in a: st["b"].setdefault(a["highlight"], {})["hl"] = at
        if "pulse" in a: st["b"].setdefault(a["pulse"], {})["pulse"] = at
        if "big" in a: st["big"] = (a["big"], at)
        if "lesson" in a: st["lesson"] = (a["lesson"], at)
        if a.get("bloop_enter"): st["enter"] = at
        if a.get("to_jar"): st["jar"] = at
        if a.get("question"): st["q"] = at
        if a.get("hook_bubbles"): st["hb"] = at
        if a.get("wave"): st["wave"] = at
        if "song_num" in a: st["song_num"] = (a["song_num"], at)
        if a.get("title"): st["title"] = at
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
        o.append(lab_hull(t))
    o.append(P("M 0 880 Q 480 850 960 880 T 1920 870 L 1920 1080 L 0 1080 Z", fill="#F6E3B4"))
    o.append(P("M 0 900 Q 480 868 960 900 T 1920 890", stroke="#E9CF92", sw=6))
    for (x, y) in ((140, 980), (520, 1030), (1450, 990), (1800, 1040), (980, 1010)):
        o.append(E(x, y, 14, 6, "#EAD29C"))
    o += [seaweed(70, 890, 260, t, 0), seaweed(110, 895, 200, t, 1.1, "#4CC2A4"),
          seaweed(1830, 885, 280, t, 2.0), seaweed(1870, 890, 190, t, 0.4, "#4CC2A4")]
    o += [C(1700, 878, 30, "#FF8F7A", LINE, 4), C(1736, 888, 20, "#FFB199", LINE, 4)]
    o.append(G(starfish(0.45), 1560, 925, 1, 12))
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

def jar(fill_n=0, glow=0.0, t=0.0):
    o = []
    if glow > 0:
        o.append(C(0, -90, 150, "url(#glow)", extra=f'opacity="{glow:.2f}"'))
    o += [R(-80, -185, 160, 185, 34, "#FFFFFF", extra='fill-opacity="0.35"'),
          R(-62, -214, 124, 34, 10, ORANGE, LINE, 5)]
    for i in range(fill_n):
        cx = -42 + (i % 4) * 28 + (14 if (i // 4) % 2 else 0)
        cy = -26 - (i // 4) * 32 + 3 * math.sin(t * 2 + i)
        o.append(C(cx, cy, 14, "#FFFFFF", "#9FD8F7", 3, 'fill-opacity="0.6"'))
    o += [R(-80, -185, 160, 185, 34, "none", "#E8F8FF", 6), R(-80, -185, 160, 185, 34, "none", LINE, 2),
          P("M -56 -160 Q -62 -100 -56 -40", stroke=WHITE, sw=7, extra='opacity="0.6"'),
          R(-58, -172, 116, 34, 10, WHITE, LINE, 3), T(0, -148, "BUBBLES", 19, LINE, "bold")]
    if fill_n >= 10:
        o += [C(70, -200, 30, YELLOW, LINE, 4), T(70, -189, "10", 30, LINE, "bold")]
    return "".join(o)

# ---------------- props ----------------
def bubble(x, y, r, t, label=None, hl=0.0, scale=1.0, wobble_seed=0):
    o = []
    if hl > 0:
        o.append(C(x, y, r + 22, "url(#glow)", extra=f'opacity="{min(1, hl):.2f}"'))
        o.append(C(x, y, r + 10, "none", YELLOW, 7, f'opacity="{min(1, hl):.2f}"'))
    g = [C(0, 0, r, "#FFFFFF", "#E8F8FF", 5, 'fill-opacity="0.28"'), C(0, 0, r, "none", LINE, 2, 'opacity="0.35"'),
         P(f"M {-r*0.6:.1f} {-r*0.25:.1f} Q {-r*0.55:.1f} {-r*0.6:.1f} {-r*0.2:.1f} {-r*0.68:.1f}", stroke=WHITE, sw=6),
         C(r * 0.45, r * 0.45, r * 0.08, WHITE)]
    if label:
        txt, col, ls, rot = label
        g.append(G(T(0, 26, txt, 76, col, "bold", extra=f'stroke="{WHITE}" stroke-width="4" paint-order="stroke"'), 0, 0, ls, rot))
    o.append(G("".join(g), x, y, scale))
    return "".join(o)

def grid_pos(i):
    row, col = divmod(i, 5)
    return 640 + col * 160, 285 + row * 175 + 8 * math.sin(i * 1.7)

def big_badge(n, age):
    if age < 0 or age > 1.9: return ""
    s = ease(age / 0.25) * (1 + 0.15 * math.sin(min(age, 0.6) * 10) * max(0, 1 - age / 0.6))
    op = 1 if age < 1.5 else max(0, 1 - (age - 1.5) / 0.4)
    g = (C(0, 0, 88, YELLOW, LINE, 6) + C(0, 0, 70, "none", WHITE, 4, 'opacity="0.6"')
         + T(0, 42, str(n), 120, LINE, "bold"))
    return f'<g opacity="{op:.2f}">{G(g, 960, 120, s)}</g>'

def lesson_banner(age):
    s = ease(age / 0.35)
    g = (R(-430, -56, 860, 112, 56, WHITE, ORANGE, 6)
         + C(-360, 0, 34, "#FFFFFF", "#9FD8F7", 4) + T(-360, 13, "1", 38, LINE, "bold")
         + T(40, 16, "1 number = 1 bubble", 50, LINE, "bold"))
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
        spots = [(470, 330), (1460, 300), (360, 640), (1560, 620), (1250, 180)]
        for i, (x, y) in enumerate(spots):
            age = t - st["hb"] - i * 0.25
            if age > 0:
                o.append(bubble(x, y + 14 * math.sin(t * 1.5 + i), 70, t, scale=ease(age / 0.4) * (1 + 0.04 * math.sin(t * 3 + i))))
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
        o.append(place_bo(t, 320, 900, 1.15 * ease((age - 0.8) / 0.35)))
    if age > 1.7:
        o.append(place_bloop(t, 1610, 560, 1.15 * ease((age - 1.7) / 0.35), energy=2))
    if age > 3.5:
        s = ease((age - 3.5) / 0.4)
        o.append(G(R(-190, -40, 380, 80, 40, ORANGE, LINE, 5) + T(0, 16, "Count with Bo", 40, WHITE, "bold"), 960, 520, s))
    if age > 4.0:
        s = ease((age - 4.0) / 0.4)
        o.append(G(T(0, 0, "Bo Counts the Bubbles", 84, WHITE, "bold", extra=f'stroke="{LINE}" stroke-width="7" paint-order="stroke"'), 960, 680, s))
    for i in range(6):
        a = (t * 1.5 + i * 0.37) % 2
        o.append(sparkle(300 + i * 270, 180 + (i % 2) * 520, 1.4, YELLOW, max(0, math.sin(a * math.pi / 2))))
    return "".join(o)

def bubbles_layer(t, st, positions=grid_pos):
    o = []
    jt = st["jar"]
    for i, b in sorted(st["b"].items()):
        if "spawn" not in b: continue
        x, y = positions(i)
        y += 10 * math.sin(t * 1.8 + i)
        sc = ease((t - b["spawn"]) / 0.35) * (1 + 0.03 * math.sin(t * 3 + i))
        hl = 0.0
        if "hl" in b and t - b["hl"] < 2.4:
            hl = min(1, (t - b["hl"]) / 0.15) * (0.75 + 0.25 * math.sin(t * 10))
        if "pulse" in b and t - b["pulse"] < 0.6:
            sc *= 1 + 0.18 * math.sin((t - b["pulse"]) / 0.6 * math.pi)
            hl = max(hl, 1 - (t - b["pulse"]) / 0.6)
        label = None
        if "label" in b:
            n, ok, lt = b["label"]
            a = t - lt
            ls = ease(a / 0.25) * (1 + 0.25 * max(0, 1 - a / 0.4))
            rot = 0 if ok else 10 * math.sin(t * 12)
            label = (str(n), LINE if ok else "#F05A4F", ls, rot)
        elif "old" in b:
            (n, ok, _), ct = b["old"]
            a = t - ct
            if a < 0.6:
                label = (str(n), "#F05A4F", 1 - a / 0.6, 25 * math.sin(a * 30))
        if jt is not None:
            a = ease((t - jt - i * 0.08) / 1.3)
            x = x + (960 - x) * a; y = y + (800 - y) * a; sc *= 1 - 0.8 * a
            if a >= 1: continue
        o.append(bubble(x, y, 62, t, label, hl, sc))
    return "".join(o)

def scene_lab(t, t0, st):
    o = [background(t, "lab")]
    jt = st["jar"]
    filled = 0 if jt is None else min(10, int(max(0, t - jt - 0.6) / 0.09))
    o.append(G(jar(filled, 0.6 if filled >= 10 else 0, t), 960, 905))
    o.append(place_bo(t, 330, 900, 1.15))
    if st["enter"] is not None:
        a = ease((t - st["enter"]) / 1.3)
        x = 2250 + (1620 - 2250) * a
        if a < 1:
            for k in range(4):
                o.append(C(x + 140 + k * 60, 520 + 20 * math.sin(k + t * 5), 10 + k * 3, "none", "#E8F8FF", 3, 'opacity="0.8"'))
        o.append(place_bloop(t, x, 500, 1.1))
    o.append(bubbles_layer(t, st))
    if st["big"] is not None:
        o.append(big_badge(st["big"][0], t - st["big"][1]))
    if st["lesson"] and st["lesson"][0]:
        o.append(lesson_banner(t - st["lesson"][1]))
    elif st["lesson"] and not st["lesson"][0] and t - st["lesson"][1] < 0.3:
        o.append(f'<g opacity="{1 - (t - st["lesson"][1]) / 0.3:.2f}">{lesson_banner(1)}</g>')
    return "".join(o)

def song_pos(i):
    a = math.pi * (0.9 - 0.8 * i / 9)
    return 960 + 800 * math.cos(a), 480 - 320 * math.sin(a)

def scene_song(t, t0, st):
    o = [background(t, "song")]
    beat = 0.6
    ph = ((t - t0) % beat) / beat
    o.append(C(960, 560, 380 + 30 * (1 - ph), "url(#glow)", extra='opacity="0.35"'))
    o.append(place_bo(t, 300, 900, 1.1, dance=1))
    o.append(place_bloop(t, 1630, 600, 1.1, energy=2.5, dance=1))
    cur = st["song_num"]
    for i in range(10):
        x, y = song_pos(i)
        hl = 0; sc = 1.0
        if cur and cur[0] == i + 1 and t - cur[1] < 0.6:
            a = (t - cur[1]) / 0.6
            hl = 1 - a; sc = 1 + 0.3 * math.sin(a * math.pi)
        o.append(bubble(x, y + 8 * math.sin(t * 3 + i), 58, t, (str(i + 1), LINE, 1, 0), hl, sc * 0.9))
    if cur and t - cur[1] < 0.55:
        a = (t - cur[1]) / 0.55
        o.append(f'<g opacity="{1 - a**2:.2f}">' + G(T(0, 0, str(cur[0]), 300, YELLOW, "bold", extra=f'stroke="{LINE}" stroke-width="14" paint-order="stroke"'), 960, 760, 0.6 + 0.5 * ease(a / 0.4)) + "</g>")
    return "".join(o)

def scene_lab_end(t, t0, st):
    o = [background(t, "lab_end")]
    o.append(G(jar(10, 0.6 + 0.2 * math.sin(t * 3), t), 960, 905, 1.35))
    wave = 0.0
    if st["wave"] is not None:
        wave = ease((t - st["wave"]) / 0.4)
    o.append(place_bo(t, 640, 900, 1.25, wave=wave))
    o.append(place_bloop(t, 1300, 470, 1.2, energy=1 + 2 * wave))
    return "".join(o)

def scene_end(t, t0, st):
    age = t - t0
    o = [background(t, "end")]
    o.append(G(T(0, 0, "Bo &amp; Bloop", 96, ORANGE, "bold", extra=f'stroke="{LINE}" stroke-width="10" paint-order="stroke"'), 960, 170, ease(age / 0.4)))
    s = ease((age - 0.4) / 0.4)
    card = (R(-520, -190, 1040, 380, 40, WHITE, LINE, 6, 'fill-opacity="0.95"')
            + T(0, -110, "NEXT TIME", 34, "#2E8FCC", "bold", extra='letter-spacing="6"')
            + T(0, -30, "Ten Little Starfish", 78, LINE, "bold"))
    for i in range(5):
        card += G(starfish(0.62, ["#FFB347", "#FF8F7A", "#FFD54A", "#B39DFF", "#7EE0C3"][i]), -300 + i * 150, 95 + 10 * math.sin(t * 3 + i), 1, 10 * math.sin(t * 2 + i))
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
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
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
