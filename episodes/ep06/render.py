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


from script import DAYS, START_ORDER, DAY_NAME

PERSIST = ("train", "swap", "go", "seven", "hug")

def state_at(t, since):
    st = dict(lesson=False, enter=None, q=None, hi=None, h7=None, wave=None, title=None, phase=None,
              train=None, swaps=[], lits=[], sweeps=[], asks=[], scan=None, bumps=[], go=None, seven=None,
              lit_end=None, hug=None)
    for a in ACTS:
        if a["t"] > t: break
        if a["t"] < since - 1e-6 and not any(k in a for k in PERSIST):
            continue
        at = a["t"]
        if "lesson" in a: st["lesson"] = (a["lesson"], at)
        if a.get("bloop_enter"): st["enter"] = at
        if a.get("question"): st["q"] = at
        if a.get("hook_items"): st["hi"] = at
        if a.get("hook_seven"): st["h7"] = at
        if a.get("wave"): st["wave"] = at
        if "song_phase" in a: st["phase"] = (a["song_phase"], at)
        if a.get("title"): st["title"] = at
        if a.get("train"): st["train"] = at
        if "swap" in a: st["swaps"].append((a["swap"][0], a["swap"][1], a.get("ans"), at))
        if "lit" in a: st["lits"].append((a["lit"], at))
        if isinstance(a.get("sweep"), (int, float)): st["sweeps"].append((a["sweep"], a.get("n", 7), at))
        if "ask" in a: st["asks"].append((a["ask"], at)); st["scan"] = None
        if a.get("scan"): st["scan"] = at
        if a.get("bump"): st["bumps"].append(at)
        if a.get("go"): st["go"] = at
        if a.get("seven"): st["seven"] = at
        if a.get("lit_end"): st["lit_end"] = at
        if a.get("hug"): st["hug"] = at
    return st

# ---------------- props: the Week Train ----------------
DAY_COL = dict(MON="#FF6B6B", TUE=ORANGE, WED=YELLOW, THU="#4CC28A", FRI="#4FA6DB", SAT="#8A6BE0", SUN="#FF7FA8")
SLOT_X = [700 + i * 118 for i in range(7)]
RAIL = 872
ENGINE_X = 578
SWAP_DUR = 1.0

def day_chip(d, s=1.0, lit=True):
    col = DAY_COL[d] if lit else WHITE
    return G(C(0, 0, 46, col, LINE, 5) + T(0, 11, d[0] if s < 0.8 else d, 28 if s >= 0.8 else 40, WHITE if lit else "#9FB0C4", "bold",
                                          extra=f'stroke="{LINE}" stroke-width="5" paint-order="stroke"' if lit else ""), 0, 0, s)

def wheel(x, y, r, ang):
    sp = "".join(P(f"M {x + r * 0.75 * math.cos(ang + k * math.pi / 3):.1f} {y + r * 0.75 * math.sin(ang + k * math.pi / 3):.1f} "
                   f"L {x - r * 0.75 * math.cos(ang + k * math.pi / 3):.1f} {y - r * 0.75 * math.sin(ang + k * math.pi / 3):.1f}", stroke=LINE, sw=3)
                 for k in range(3))
    return C(x, y, r, "#5A6B85", LINE, 4) + sp + C(x, y, 4, LINE)

def carriage(d, glow=0.0, ang=0.0, num=None):
    col = DAY_COL[d]
    o = ""
    if glow > 0.01:
        o += C(0, -50, 100, "url(#glow)", extra=f'opacity="{min(1, glow):.2f}"')
        o += R(-62, -138, 124, 122, 20, "none", YELLOW, 8, f'opacity="{min(1, glow):.2f}"')
    o += (R(-54, -132, 108, 108, 14, col, LINE, 5) + R(-54, -132, 108, 20, 9, WHITE, extra='opacity="0.35"')
          + T(0, -62, d, 40, WHITE, "bold", extra=f'stroke="{LINE}" stroke-width="6" paint-order="stroke"')
          + wheel(-30, -14, 15, ang) + wheel(30, -14, 15, ang))
    if num is not None:
        o += G(C(0, 0, 22, WHITE, LINE, 4) + T(0, 9, str(num), 26, LINE, "bold"), 0, -160)
    return o

def engine(t, st, ang):
    o = [R(-70, -96, 104, 72, 12, "#3F78A8", LINE, 5),          # boiler
         R(14, -150, 62, 126, 12, "#2E6594", LINE, 5),          # cab
         R(24, -138, 42, 36, 8, "#BDE7FC", LINE, 4),            # window
         R(8, -160, 74, 16, 8, ORANGE, LINE, 4),                # roof
         R(-58, -134, 26, 40, 6, LINE),                         # chimney
         R(-64, -142, 38, 12, 6, LINE),
         P("M -70 -40 L -92 -24 L -70 -24 Z", fill=YELLOW, stroke=LINE, sw=4),
         C(-70, -70, 10, YELLOW, LINE, 3),
         wheel(-40, -16, 17, ang), wheel(40, -16, 17, ang)]
    if st["go"] is not None:
        a = t - st["go"]
        for k in range(4):
            q = (a * 0.7 + k * 0.25) % 1
            o.append(C(-45 - q * 60, -150 - q * 140, 16 + q * 26, WHITE, extra=f'opacity="{0.85 * (1 - q) * min(1, a * 2):.2f}"'))
    return "".join(o)

def order_at(t, st):
    """-> (order list, active swap or None) — order after every finished swap."""
    order = list(START_ORDER); active = None
    for a, b, ans, at in st["swaps"]:
        if t >= at + SWAP_DUR:
            i, j = order.index(a), order.index(b); order[i], order[j] = order[j], order[i]
        elif t >= at:
            active = (a, b, at)
    return order, active

def day_glow(d, t, st, order):
    g = 0.0
    for dd, at in st["lits"]:
        if dd == d and 0 <= t - at < 2.6: g = max(g, 0.7 + 0.3 * math.sin(t * 9))
    for a, b, ans, at in st["swaps"]:
        if ans == d and 0 <= t - at < 3.0: g = max(g, 0.7 + 0.3 * math.sin(t * 9))
    for step, n, at in st["sweeps"]:
        if d in order[:n]:
            i = order.index(d)
            a = t - at - i * step
            if 0 <= a < step * 1.6 + 0.3: g = max(g, 1.0)
    if st["lit_end"] is not None and d in ("FRI", "SAT", "SUN"):
        a = t - st["lit_end"] - 0.8 - ("FRI", "SAT", "SUN").index(d) * 0.45
        if 0 <= a < 2.8: g = max(g, 0.7 + 0.3 * math.sin(t * 9))
    return g

def week_sign(t):
    o = [P("M 560 300 Q 960 380 1360 300", stroke=LINE, sw=4)]
    for i, d in enumerate(DAYS):   # bunting flags
        x = 600 + i * 120; y = 300 + 80 * math.sin(math.pi * (x - 560) / 800) * 0.95
        o.append(G(P("M -26 0 L 26 0 L 0 46 Z", fill=DAY_COL[d], stroke=LINE, sw=3), x, y, 1, 4 * math.sin(t * 2 + i)))
    o.append(R(720, 420, 480, 90, 24, "#FFF6D6", LINE, 6) + R(760, 506, 14, 40, 4, "#B8894F", LINE, 3) + R(1146, 506, 14, 40, 4, "#B8894F", LINE, 3))
    o.append(T(960, 480, "Bo&#8217;s Week Train", 48, LINE, "bold"))
    return "".join(o)

def train(t, st, op=1.0):
    order, active = order_at(t, st)
    jolt = 0.0
    for b in st["bumps"]:
        a = t - b
        if 0 <= a < 0.9: jolt = 14 * math.sin(a * 40) * (1 - a / 0.9)
    moving = st["go"] is not None
    ang = (t - st["go"]) * 6 if moving else 0.0
    bounce = 3 * abs(math.sin(t * 9)) if moving else 0.0
    o = [P(f"M 470 {RAIL} L 1490 {RAIL}", stroke="#8A6A4A", sw=10)]
    for k in range(18):
        x = 480 + k * 56 - ((t - st["go"]) * 90 % 56 if moving else 0)
        o.append(R(x, RAIL - 2, 34, 12, 3, "#B8894F", LINE, 2))
    o.append(P(f"M 470 {RAIL - 4} L 1490 {RAIL - 4}", stroke="#A9B8CC", sw=6))
    o.append(G(engine(t, st, ang), ENGINE_X + jolt, RAIL - bounce, 1.15))
    for i in range(6):     # couplings
        o.append(P(f"M {SLOT_X[i] + 54 + jolt:.1f} {RAIL - 40} L {SLOT_X[i + 1] - 54 + jolt:.1f} {RAIL - 40}", stroke=LINE, sw=6))
    o.append(P(f"M {ENGINE_X + 76 + jolt:.1f} {RAIL - 40} L {SLOT_X[0] - 54 + jolt:.1f} {RAIL - 40}", stroke=LINE, sw=6))
    flying = []
    for i, d in enumerate(order):
        x, y = SLOT_X[i] + jolt, RAIL - bounce * (0.5 + 0.5 * math.sin(i))
        if active and d in active[:2]:
            a, b, at = active
            k = ease((t - at) / SWAP_DUR)
            j = order.index(b if d == a else a)
            x = SLOT_X[i] + (SLOT_X[j] - SLOT_X[i]) * k
            y = RAIL - (230 if d == a else 120) * math.sin(k * math.pi)
            flying.append(G(carriage(d, 0.8, 0), x, y))
            continue
        num = (i + 1) if st["seven"] is not None and t >= st["seven"] + i * 0.25 else None
        o.append(G(carriage(d, day_glow(d, t, st, order), ang, num), x, y))
    o += flying
    if st["bumps"]:
        a = t - st["bumps"][-1]
        if 0 <= a < 1.4:
            o.append(G(T(0, 0, "!", 120, "#E5484D", "bold", extra=f'stroke="{LINE}" stroke-width="7" paint-order="stroke"'), ENGINE_X - 10, RAIL - 230, ease(a / 0.2)))
            for k in range(4):
                o.append(sparkle(ENGINE_X - 80 + k * 50, RAIL - 180 - 30 * math.sin(k * 2 + a * 6), 1.2, YELLOW, max(0, 1 - a / 1.4)))
    return f'<g opacity="{op:.2f}">{"".join(o)}</g>' if op < 0.999 else "".join(o)

# ---------------- question panel, seven bubble, lesson banner ----------------
NEXT = {d: DAYS[(i + 1) % 7] for i, d in enumerate(DAYS)}

def ask_panel(t, st):
    if not st["asks"]: return ""
    d, g = st["asks"][-1]
    nxt = NEXT[d]
    ans = None
    for a, b, an, at in st["swaps"]:
        if an == nxt and at >= g: ans = at
    op = ease((t - g) / 0.35)
    if ans is not None and t > ans + 2.2:
        op = 1 - ease((t - ans - 2.2) / 0.4)
    if op <= 0.01: return ""
    o = [R(560, 34, 800, 170, 40, WHITE, "#2E8FCC", 6, 'fill-opacity="0.95"'),
         T(960, 92, f"What comes after {DAY_NAME[d]}?", 44, "#2E8FCC", "bold"),
         G(day_chip(d), 840, 150, 0.9),
         G(P("M -36 0 L 30 0 M 12 -16 L 30 0 L 12 16", stroke=LINE, sw=7), 960, 150)]
    if ans is None or t < ans:
        pul = 1 + (0.08 * math.sin(t * 8) if st["scan"] is not None else 0)
        o.append(G(C(0, 0, 42, WHITE, "#9FB0C4", 5, 'stroke-dasharray="10 8"') + T(0, 16, "?", 48, "#9FB0C4", "bold"), 1080, 150, 0.9 * pul))
    else:
        a = t - ans
        o.append(G(day_chip(nxt), 1080, 150, 0.9 * (1 + 0.3 * max(0, 1 - a / 0.4))))
        o.append(G(C(0, 0, 22, "#4CC28A", LINE, 4) + P("M -10 1 L -2 9 L 11 -8", stroke=WHITE, sw=6), 1140, 112, ease(a / 0.3)))
    return f'<g opacity="{op:.2f}">{"".join(o)}</g>'

def seven_bubble(t, st):
    if st["seven"] is None: return ""
    a = t - st["seven"]
    if a < 0 or a > 3.4: return ""
    op = min(1, a / 0.2, (3.4 - a) / 0.4)
    g = (R(-170, -60, 340, 120, 60, WHITE, ORANGE, 6) + T(0, 18, "7 days!", 58, ORANGE, "bold"))
    return f'<g opacity="{op:.2f}">{G(g, 1050, 600 + 6 * math.sin(t * 3), ease(a / 0.3))}</g>'

def days_row(cx, y, s, lit_fn, t):
    o = []
    for i, d in enumerate(DAYS):
        o.append(G(day_chip(d, 1.0, lit_fn(i)), cx + (i - 3) * 104 * s, y + 6 * math.sin(t * 3 + i), s * 0.9))
    return "".join(o)

def lesson_banner(age, t=0.0):
    s = ease(age / 0.35)
    g = (R(-780, -66, 1560, 132, 66, WHITE, ORANGE, 6)
         + T(-520, 16, "7 days in a week", 46, LINE, "bold")
         + days_row(170, 0, 0.82, lambda i: True, t)
         + G(P("M -40 -10 A 34 34 0 1 1 -26 22 M -40 -10 L -44 -30 M -40 -10 L -20 -14", stroke="#2E8FCC", sw=7), 715, 0))
    return G(g, 960, 100, s)

def heart(x, y, s, op=1.0, col="#FF7FA8"):
    d = "M 0 12 C -28 -6 -18 -30 0 -16 C 18 -30 28 -6 0 12 Z"
    return f'<g opacity="{op:.2f}">{G(P(d, fill=col, stroke=LINE, sw=3), x, y, s)}</g>'

def bolt_icon():
    hexp = " ".join(f"{30 * math.cos(k * math.pi / 3):.1f},{30 * math.sin(k * math.pi / 3):.1f}" for k in range(6))
    o = R(-12, 10, 24, 80, 4, "#C7CED9", LINE, 4)
    for k in range(5):
        o += P(f"M -12 {24 + k * 13} L 12 {18 + k * 13}", stroke=LINE, sw=3)
    o += f'<polygon points="{hexp}" fill="#A9B8CC" stroke="{LINE}" stroke-width="4" transform="translate(0 0)"/>' + C(0, 0, 9, "#7D8898", LINE, 3)
    return o

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
        spots = [(420, 330), (1500, 330), (300, 640), (1620, 650), (680, 150), (1240, 150), (960, 120)]
        for i, (x, y) in enumerate(spots):
            age = t - st["hi"] - i * 0.22
            if age > 0:
                o.append(G(day_chip(DAYS[i], 1.0), x + 20 * math.sin(t + i), y + 14 * math.sin(t * 1.5 + i), 1.6 * ease(age / 0.4), 8 * math.sin(t * 1.2 + i)))
    o.append(place_bo(t, 960, 940, 1.7))
    if st["h7"] is not None:
        a = t - st["h7"]
        o.append(G(C(0, 0, 70, ORANGE, LINE, 7) + T(0, 30, "7", 90, WHITE, "bold", extra=f'stroke="{LINE}" stroke-width="6" paint-order="stroke"'),
                   1300, 520 + 8 * math.sin(t * 3), ease(a / 0.3)))
    if st["q"] is not None and t - st["q"] < 3.2:
        age = t - st["q"]
        o.append(G(T(0, 0, "?", 190, ORANGE, "bold", extra=f'stroke="{LINE}" stroke-width="8" paint-order="stroke"'),
                   620, 560 + 12 * math.sin(t * 4), ease(age / 0.3), 8 * math.sin(t * 3)))
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
        o.append(G(R(-200, -40, 400, 80, 40, "#FF7FA8", LINE, 5) + T(0, 16, "Bubble Bay Songs", 38, WHITE, "bold"), 960, 520, s))
    if age > 4.0:
        s = ease((age - 4.0) / 0.4)
        o.append(G(T(0, 0, "Days of the Week with Bo", 64, WHITE, "bold", extra=f'stroke="{LINE}" stroke-width="7" paint-order="stroke"'), 960, 660, s))
        o.append(G(days_row(0, 0, 0.9, lambda i: True, t), 960, 780, s))
    for i in range(6):
        a = (t * 1.5 + i * 0.37) % 2
        o.append(sparkle(300 + i * 270, 180 + (i % 2) * 520, 1.4, YELLOW, max(0, math.sin(a * math.pi / 2))))
    return "".join(o)

def bo_pointing(t, st):
    p = 0.0
    for a, b, ans, at in st["swaps"]:
        x = t - at
        if -0.2 <= x < 1.3: p = max(p, math.sin(min(1, (x + 0.2) / 1.5) * math.pi))
    for step, n, at in st["sweeps"]:
        x = t - at
        if 0 <= x < step * n: p = max(p, 0.8)
    return p

def scene_lab(t, t0, st):
    o = [background(t, "lab")]
    op = 0.0 if st["train"] is None else ease((t - st["train"]) / 0.4)
    if op > 0.01:
        o.append(f'<g opacity="{op:.2f}">{week_sign(t)}</g>')
        o.append(train(t, st, op))
    o.append(place_bo(t, 300, 900, 1.15, point=bo_pointing(t, st)))
    if st["enter"] is not None:
        a = ease((t - st["enter"]) / 1.3)
        x = 2250 + (1660 - 2250) * a
        if a < 1:
            for k in range(4):
                o.append(C(x + 140 + k * 60, 470 + 20 * math.sin(k + t * 5), 10 + k * 3, "none", "#E8F8FF", 3, 'opacity="0.8"'))
        o.append(place_bloop(t, x, 450, 1.0))
    o.append(seven_bubble(t, st))
    if not (st["lesson"] and st["lesson"][0]):
        o.append(ask_panel(t, st))
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
        o.append(G(T(0, 0, "&#9835;" if i % 2 else "&#9834;", 70, DAY_COL[DAYS[i % 7]], "bold", extra=f'stroke="{LINE}" stroke-width="4" paint-order="stroke"'),
                   x, y + 8 * math.sin(t * 3 + i), 1, 10 * math.sin(t * 3 + i)))
    o.append(place_bo(t, 280, 900, 1.05, dance=1))
    o.append(place_bloop(t, 1650, 600, 1.05, energy=2.5, dance=1))
    phase, pt = st["phase"] if st["phase"] else (None, t0)
    a = t - pt
    order = {"seven": 0, "days1": 1, "days2": 2, "sun": 3, "again": 4, "all": 5}.get(phase, -1)
    def lit(i):
        if order < 0: return False
        if order == 0: return a >= i * 0.35
        if order == 1: return i < 3 and a >= i * 0.7
        if order == 2: return i < 3 or (i < 6 and a >= (i - 3) * 0.7)
        if order == 3: return i < 6 or a >= 0.2
        return True
    for i, d in enumerate(DAYS):
        x = 960 + (i - 3) * 150
        on = lit(i)
        s = 1.25
        if order == 5: s *= 1 + 0.12 * abs(math.sin((t - t0) * math.pi / beat + i * 0.6))
        if order == 3 and i == 6: s *= 1 + 0.35 * max(0, 1 - a / 0.6)
        if order == 4 and i == 0: s *= 1 + 0.2 * abs(math.sin(t * 8))
        o.append(G(day_chip(d, 1.0, on), x, 470 + 10 * math.sin(t * 3 + i), s))
        if order == 0 and on:
            o.append(G(C(0, 0, 20, WHITE, LINE, 4) + T(0, 8, str(i + 1), 24, LINE, "bold"), x, 560))
    if order >= 4:   # loop arrow: after Sunday comes Monday again
        k = min(1, a / 0.8) if order == 4 else 1
        o.append(P("M 1410 540 C 1380 720, 540 720, 510 545", stroke="#2E8FCC", sw=10, extra=f'opacity="{k:.2f}"'))
        o.append(G(P("M -20 -6 L 0 -30 L 20 -6", stroke="#2E8FCC", sw=10), 510, 545, k))
    label = {"seven": "7 days in a week", "days1": "Mon, Tue, Wed", "days2": "Thu, Fri, Sat", "sun": "...and Sunday!",
             "again": "Then Monday again!", "all": "Round and round!"}.get(phase)
    if label:
        o.append(G(R(-250, -40, 500, 80, 40, WHITE, ORANGE, 5) + T(0, 15, label, 40, LINE, "bold"), 960, 300))
    return "".join(o)

def scene_lab_end(t, t0, st):
    o = [background(t, "lab_end")]
    o.append(week_sign(t)); o.append(train(t, st))
    wave = 0.0
    if st["wave"] is not None:
        wave = ease((t - st["wave"]) / 0.4)
    o.append(place_bo(t, 300, 900, 1.15, wave=wave))
    o.append(place_bloop(t, 1640, 430, 1.05, energy=1 + 2 * wave))
    return "".join(o)

def scene_end(t, t0, st):
    age = t - t0
    o = [background(t, "end")]
    o.append(G(T(0, 0, "Bo &amp; Bloop", 96, ORANGE, "bold", extra=f'stroke="{LINE}" stroke-width="10" paint-order="stroke"'), 960, 170, ease(age / 0.4)))
    s = ease((age - 0.4) / 0.4)
    card = (R(-520, -190, 1040, 380, 40, WHITE, LINE, 6, 'fill-opacity="0.95"')
            + T(0, -110, "NEXT TIME", 34, "#2E8FCC", "bold", extra='letter-spacing="6"')
            + T(0, -30, "Bo&#8217;s Missing Bolt", 60, LINE, "bold"))
    for k, n in enumerate((10, 9, 8, 3, 2, 1)):
        x = -330 + k * 110 + (80 if k >= 3 else 0)
        card += G(C(0, 0, 36, WHITE, "#2E8FCC", 5) + T(0, 14, str(n), 38, LINE, "bold"), x, 95 + 6 * math.sin(t * 4 + k))
    card += T(-5, 105, "...", 40, LINE, "bold")
    card += G(bolt_icon(), 430, 40, 0.9, 20 * math.sin(t * 2))
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
