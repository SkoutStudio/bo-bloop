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

PERSIST = ("tank", "show", "drop", "result", "fill", "hug")

def state_at(t, since):
    st = dict(lesson=False, enter=None, q=None, hi=None, wave=None, song_num=None, title=None, phase=None,
              tank=None, rule=None, rule_x=None, rule_hide=None, shows={}, drops={}, results={}, guess=None,
              pick=None, scan=None, fill=None, air={}, hug=None)
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
        if "song_num" in a: st["song_num"] = (a["song_num"], at)
        if "song_phase" in a: st["phase"] = (a["song_phase"], at)
        if a.get("title"): st["title"] = at
        if a.get("tank"): st["tank"] = at
        if a.get("rule"): st["rule"] = at
        if a.get("rule_x"): st["rule_x"] = at
        if a.get("rule_hide"): st["rule_hide"] = at
        if "show" in a: st["shows"][a["show"]] = at
        if "drop" in a: st["drops"][a["drop"]] = at
        if "result" in a: st["results"][a["result"]] = at
        if "guess" in a: st["guess"] = (a["guess"], at); st["pick"] = a.get("pick"); st["scan"] = None
        if a.get("scan"): st["scan"] = at
        if a.get("fill"): st["fill"] = at
        if "air" in a: st["air"][a["air"]] = at
        if a.get("hug"): st["hug"] = at
    return st

# ---------------- props: the things we test ----------------
def pebble_g():
    return (E(0, 0, 36, 25, "#9AA5B4", LINE, 5) + E(-12, -9, 12, 5, WHITE, extra='opacity="0.45"')
            + C(10, 6, 4, "#7D8898") + C(-4, 10, 3, "#7D8898") + C(18, -6, 3, "#7D8898"))

BALL_R = 62

def ball_g(spin=0.0):
    r = BALL_R
    cols = ["#FF6B6B", WHITE, YELLOW, WHITE, "#4FA6DB", WHITE]
    o = []
    for k in range(6):
        a1 = spin + k * math.pi / 3; a2 = a1 + math.pi / 3
        o.append(P(f"M 0 0 L {r*math.cos(a1):.1f} {r*math.sin(a1):.1f} A {r} {r} 0 0 1 {r*math.cos(a2):.1f} {r*math.sin(a2):.1f} Z",
                   fill=cols[k]))
    o.append(C(0, 0, r, "none", LINE, 5) + C(0, 0, 13, WHITE, LINE, 3)
             + P(f"M {-r*0.62:.0f} {-r*0.3:.0f} Q {-r*0.5:.0f} {-r*0.66:.0f} {-r*0.18:.0f} {-r*0.76:.0f}", stroke=WHITE, sw=7, extra='opacity="0.7"'))
    return "".join(o)

def key_g():
    m = "#C7CED9"
    return (C(-44, 0, 24, m, LINE, 5) + C(-44, 0, 10, "#9FB0C4", LINE, 4)
            + R(-22, -8, 82, 16, 5, m, LINE, 4) + R(34, 6, 10, 16, 2, m, LINE, 4) + R(50, 6, 10, 12, 2, m, LINE, 4)
            + P("M -60 -10 Q -52 -20 -40 -20", stroke=WHITE, sw=4, extra='opacity="0.7"'))

def duck_g():
    return (E(0, 12, 54, 32, YELLOW, LINE, 5) + P("M -54 6 Q -72 -6 -62 -20 Q -50 -2 -40 0 Z", fill=YELLOW, stroke=LINE, sw=4)
            + C(26, -26, 26, YELLOW, LINE, 5) + E(28, 10, 12, 0.1, YELLOW)
            + P("M 48 -24 Q 70 -22 66 -14 Q 58 -8 46 -14 Z", fill=ORANGE, stroke=LINE, sw=4)
            + C(32, -32, 5, NAVY) + C(34, -34, 1.8, WHITE)
            + P("M -16 6 Q 0 26 18 8", stroke="#E8B830", sw=5) + E(18, -18, 7, 4, PINK, extra='opacity="0.8"'))

def bottle_g(sand=0.0):
    o = [R(-32, -50, 64, 110, 18, "#E8F8FF", LINE, 5, 'fill-opacity="0.75"')]
    if sand > 0:
        h = 100 * sand
        o.append(R(-26, 55 - h, 52, h, 12, "#E9CF92"))
        for k in range(int(sand * 8)):
            o.append(C(-16 + (k * 13) % 34, 50 - (k * 17) % max(8, int(h - 6)), 2.5, "#C9A86A"))
    o.append(R(-32, -50, 64, 110, 18, "none", LINE, 5))
    o.append(R(-15, -74, 30, 26, 6, "#E8F8FF", LINE, 5) + R(-19, -90, 38, 18, 6, "#FF7FA8", LINE, 4))
    o.append(P("M -20 -36 L -20 30", stroke=WHITE, sw=6, extra='opacity="0.8"'))
    return "".join(o)

def item_g(name, t=0.0, sand=0.0):
    if name == "pebble": return pebble_g()
    if name == "ball": return ball_g(0.3 * math.sin(t * 1.5))
    if name == "key": return key_g()
    if name == "duck": return duck_g()
    return bottle_g(sand)

# x slot, half height (bottom extent), floats?, resting centre offset from the surface when floating
ITEMS = dict(pebble=(720, 25, False, 0), ball=(850, BALL_R, True, -30), key=(995, 24, False, 0),
             duck=(1110, 44, True, -14), bottle=(1215, 60, True, -38))
SINKS = ("pebble", "key", "sand")
TX0, TX1, RIM, SURF, BOT = 640, 1290, 380, 470, 846
HOVER = 288

def splash(x, a):
    if a < 0 or a > 0.9: return ""
    k = a / 0.9
    o = [E(x, SURF, 40 + 90 * k, 8 + 10 * k, "none", WHITE, 6 * (1 - k) + 1, f'opacity="{1 - k:.2f}"')]
    for j in range(5):
        dx = (j - 2) * 22
        o.append(C(x + dx * (1 + 2 * k), SURF - 70 * math.sin(k * math.pi) * (1 - abs(j - 2) * 0.25), 8, "#E8F8FF", LINE, 2, f'opacity="{1 - k:.2f}"'))
    return "".join(o)

def item_pos(name, t, st):
    """-> (x, y, scale, rot, extra_svg) or None."""
    if name not in st["shows"] or t < st["shows"][name]: return None
    x, half, floats, off = ITEMS[name]
    ts = st["shows"][name]
    s = ease((t - ts) / 0.3) * (1 + 0.2 * max(0, 1 - (t - ts) / 0.5))
    y = HOVER + 8 * math.sin(t * 2.2); rot = 6 * math.sin(t * 1.7); fx = ""
    if (t - ts) < 0.6:
        fx += "".join(sparkle(x + 80 * math.cos(k * 1.57 + 0.5), HOVER + 60 * math.sin(k * 1.57 + 0.5), 1.2, YELLOW, 1 - (t - ts) / 0.6) for k in range(4))
    td = st["drops"].get(name)
    if td is not None and t >= td:
        s = 1.0
        a = t - td
        if a < 0.5:
            k = a / 0.5; y = HOVER + (SURF - HOVER) * k * k; rot = 0
        else:
            b = a - 0.5
            fx += splash(x, b)
            if floats:
                y = SURF + off + 60 * math.sin(b * 5) * math.exp(-b * 2.2) + 4 * math.sin(t * 2.0); rot = 5 * math.sin(t * 1.6)
            else:
                y = SURF + (BOT - half - SURF) * ease(b / 1.8) + 0.0; rot = 10 * math.sin(b * 4) * max(0, 1 - b / 1.8)
                if b < 2.4:
                    for j in range(5):
                        q = (b * 1.2 + j * 0.2) % 1
                        if b < 1.8 or q > (b - 1.8) / 0.6:
                            fx += C(x - 20 + j * 10 + 8 * math.sin(j + b * 6), y - 30 - q * (y - SURF - 30), 5 + j % 3 * 2, "none", WHITE, 3, f'opacity="{0.9 * (1 - q):.2f}"')
    # the magic bottle: lifted out, filled with sand, dropped again
    if name == "bottle" and st["fill"] is not None and t >= st["fill"]:
        a = t - st["fill"]
        y0 = SURF + off
        k = ease(a / 0.7)
        y = y0 + (HOVER - y0) * k + 8 * math.sin(t * 2.2) * k; rot = 0; fx = ""
        td2 = st["drops"].get("sand")
        if td2 is not None and t >= td2:
            b = t - td2
            if b < 0.5:
                y = HOVER + (SURF - HOVER) * (b / 0.5) ** 2
            else:
                c = b - 0.5
                fx += splash(x, c)
                y = SURF + (BOT - half - SURF) * ease(c / 1.6); rot = 8 * math.sin(c * 4) * max(0, 1 - c / 1.6)
                if c < 2.2:
                    for j in range(5):
                        q = (c * 1.2 + j * 0.2) % 1
                        fx += C(x - 20 + j * 10, y - 40 - q * max(0, y - SURF - 40), 5 + j % 3 * 2, "none", WHITE, 3, f'opacity="{0.9 * (1 - q) * max(0, 1 - c / 2.2):.2f}"')
    return x, y, s, rot, fx

def sand_level(t, st):
    if st["fill"] is None or t < st["fill"]: return 0.0
    return 0.8 * ease((t - st["fill"] - 0.6) / 1.0)

def sand_pour(t, st):
    if st["fill"] is None: return ""
    a = t - st["fill"] - 0.5
    if a < 0 or a > 1.3: return ""
    x = ITEMS["bottle"][0]
    op = min(1, a / 0.2, (1.3 - a) / 0.2)
    o = [G(P("M -50 -20 L 50 -20 L 34 30 L -34 30 Z", fill="#7EE0C3", stroke=LINE, sw=5) + R(-56, -30, 112, 14, 7, "#5CC8A8", LINE, 4),
           x + 60, HOVER - 175, 1, 40)]
    for j in range(7):
        q = (a * 2.2 + j / 7) % 1
        o.append(C(x + 6 * math.sin(j * 2), HOVER - 140 + q * 50, 5, "#E9CF92", LINE, 1.5))
    return f'<g opacity="{op:.2f}">{"".join(o)}</g>'

def tank(t, st, op=1.0):
    o = [R(TX0, RIM, TX1 - TX0, 878 - RIM, 22, "#E8F8FF", extra='fill-opacity="0.22"'),
         R(TX0 + 10, SURF, TX1 - TX0 - 20, 866 - SURF, 10, "#5BC0EB", extra='fill-opacity="0.35"'),
         P(f"M {TX0+10} 866 L {TX0+10} {BOT} Q 760 {BOT-14} 880 {BOT} T 1120 {BOT} T {TX1-10} {BOT} L {TX1-10} 866 Z", fill="#E9CF92")]
    for (x, r) in ((700, 9), (770, 6), (930, 8), (1060, 7), (1180, 9), (1250, 6)):
        o.append(C(x, BOT + 6, r, "#D6B57A"))
    o.append(P(f"M {TX0+40} 866 q -10 -60 6 -110 q 14 -40 -2 -80", stroke="#2E8F79", sw=14) + P(f"M {TX0+40} 866 q -10 -60 6 -110 q 14 -40 -2 -80", stroke="#4CC2A4", sw=8))
    return f'<g opacity="{op:.2f}">{"".join(o)}</g>'

def tank_front(t, op=1.0):
    w = "".join(f" Q {TX0 + 10 + 40 * (2 * k + 1):.0f} {SURF + 7 * math.sin(t * 3 + k):.1f} {TX0 + 10 + 80 * (k + 1):.0f} {SURF}" for k in range(8))
    o = [P(f"M {TX0+10} {SURF}{w} L {TX1-10} 866 L {TX0+10} 866 Z", fill="#3FA2D8", extra='fill-opacity="0.22"'),
         P(f"M {TX0+10} {SURF}{w}", stroke=WHITE, sw=6, extra='opacity="0.9"'),
         R(TX0, RIM, TX1 - TX0, 878 - RIM, 22, "none", LINE, 8),
         R(TX0 - 10, RIM - 12, TX1 - TX0 + 20, 24, 12, "#7FD3F7", LINE, 6),
         R(TX0 - 14, 866, TX1 - TX0 + 28, 26, 10, "#3F78A8", LINE, 6),
         P(f"M {TX0+26} {RIM+40} L {TX0+26} {RIM+190}", stroke=WHITE, sw=10, extra='opacity="0.5"'),
         P(f"M {TX1-28} {RIM+60} L {TX1-28} {RIM+120}", stroke=WHITE, sw=8, extra='opacity="0.4"')]
    return f'<g opacity="{op:.2f}">{"".join(o)}</g>'

def arrow_badge(up, x, y, s=1.0):
    col = "#4CC28A" if up else "#8A6BE0"
    d = "M 0 -18 L 0 18 M -14 -4 L 0 -20 L 14 -4" if up else "M 0 -18 L 0 18 M -14 4 L 0 20 L 14 4"
    return G(C(0, 0, 30, col, LINE, 5) + P(d, stroke=WHITE, sw=7), x, y, s)

def results_badges(t, st):
    o = []
    for name, at in st["results"].items():
        key = "bottle" if name == "sand" else name
        if name == "bottle" and "sand" in st["results"]: continue
        if name == "bottle" and st["fill"] is not None and t >= st["fill"]: continue
        a = t - at
        x = ITEMS[key][0]
        o.append(arrow_badge(name not in SINKS, x, RIM - 50, ease(a / 0.3) * (1 + 0.3 * max(0, 1 - a / 0.5))))
    return "".join(o)

def tank_items(t, st):
    o = []
    for name in ITEMS:
        p = item_pos(name, t, st)
        if p is None: continue
        x, y, s, rot, fx = p
        g = item_g(name, t, sand_level(t, st) if name == "bottle" else 0.0)
        o.append(G(g, x, y, s, rot) + fx)
        if name in st["air"] and 0 < t - st["air"][name] < 4.0 and not (name == "bottle" and st["fill"] is not None and t >= st["fill"]):
            a = t - st["air"][name]
            op = min(1, a / 0.3, (4.0 - a) / 0.4)
            tag = R(-110, -28, 220, 56, 28, WHITE, "#4CC28A", 5) + T(0, 12, "full of air!", 32, LINE, "bold")
            bub = "".join(C(-60 + k * 30, -54 - 8 * math.sin(t * 4 + k), 7 + k % 2 * 3, "none", "#4FA6DB", 3) for k in range(5))
            if y < SURF - 100:   # still hovering above the tank: tag to the left
                o.append(f'<g opacity="{op:.2f}">{G(tag, x - 200, y - 32)}</g>')
            else:                # floating: tag under the water, below the item
                o.append(f'<g opacity="{op:.2f}">{G(tag + bub, min(x, 1150), SURF + 150)}</g>')
    return "".join(o)

# ---------------- guess panel, Bo's rule card, lesson banner ----------------
GUESS_ICON = dict(pebble="pebble", ball="ball", key="key", duck="duck", bottle="bottle", sand="bottle")

def guess_panel(t, st):
    if st["guess"] is None: return ""
    name, g = st["guess"]
    r = st["results"].get(name)
    if r is not None and r < g: r = None
    op = ease((t - g) / 0.35)
    if r is not None and t > r + 2.6:
        op = 1 - ease((t - r - 2.6) / 0.4)
    if op <= 0.01: return ""
    o = [R(560, 34, 800, 160, 40, WHITE, "#2E8FCC", 6, 'fill-opacity="0.95"')]
    ic = item_g(GUESS_ICON[name], t, 0.8 if name == "sand" else 0.0)
    o.append(G(ic, 650, 114, 0.62 if name != "ball" else 0.7))
    o.append(T(1000, 92, "Float or sink?", 46, "#2E8FCC", "bold"))
    sel = None
    if st["pick"] and r is None: sel = st["pick"]
    elif st["scan"] is not None and r is None: sel = ("float", "sink")[int((t - st["scan"]) / 0.55) % 2]
    answer = None if r is None else ("sink" if name in SINKS else "float")
    for which, x, up in (("float", 860, True), ("sink", 1140, False)):
        col = "#4CC28A" if up else "#8A6BE0"
        hl = which == sel or which == answer
        g = R(-120, -30, 240, 60, 30, col if hl else WHITE, col, 5) + T(16, 13, which.upper(), 36, WHITE if hl else LINE, "bold")
        g += G(P("M 0 -11 L 0 11 M -8 -2 L 0 -12 L 8 -2" if up else "M 0 -11 L 0 11 M -8 2 L 0 12 L 8 2", stroke=WHITE if hl else col, sw=5), -76, 0)
        sc = 1.0
        if which == answer: sc = 1 + 0.18 * max(0, 1 - (t - r) / 0.5)
        if hl and answer is None: sc = 1.05 + 0.04 * math.sin(t * 10)
        o.append(G(g, x, 150, sc))
        if which == answer:
            o.append(G(C(0, 0, 22, "#4CC28A", LINE, 4) + P("M -10 1 L -2 9 L 11 -8", stroke=WHITE, sw=6), x + 120, 124, ease((t - r) / 0.3)))
        if st["pick"] and which == st["pick"]:
            o.append(G(R(-30, -18, 60, 36, 18, ORANGE, LINE, 3) + T(0, 9, "Bo", 24, WHITE, "bold"), x + 122, 120))
            if answer is not None and which != answer:
                o.append(G(P("M -16 -16 L 16 16 M 16 -16 L -16 16", stroke="#E5484D", sw=9), x + 122, 120, ease((t - r) / 0.3)))
    return f'<g opacity="{op:.2f}">{"".join(o)}</g>'

def rule_card(t, st):
    if st["rule"] is None: return ""
    op = ease((t - st["rule"]) / 0.4)
    if st["rule_hide"] is not None and t >= st["rule_hide"]:
        op = 1 - ease((t - st["rule_hide"]) / 0.5)
    if op <= 0.01: return ""
    o = [R(-235, -95, 470, 190, 34, "#FFF6D6", ORANGE, 6, 'fill-opacity="0.96"'),
         T(0, -52, "Bo&#8217;s idea:", 30, ORANGE, "bold"),
         C(-188, 4, 28, "#FF8F7A", LINE, 4), T(-140, 16, "Big = sink", 36, LINE, "bold", anchor="start"), arrow_badge(False, 190, 4, 0.7),
         C(-188, 64, 13, "#FF8F7A", LINE, 4), T(-140, 76, "Small = float", 36, LINE, "bold", anchor="start"), arrow_badge(True, 190, 64, 0.7)]
    if st["rule_x"] is not None:
        k = ease((t - st["rule_x"] - 0.3) / 0.3)
        if k > 0:
            o.append(P("M -150 -70 L 150 80 M 150 -70 L -150 80", stroke="#E5484D", sw=16, extra=f'opacity="{k:.2f}"'))
    return f'<g opacity="{op:.2f}">{G("".join(o), 330, 205)}</g>'

def lesson_banner(age):
    s = ease(age / 0.35)
    g = (R(-760, -62, 1520, 124, 62, WHITE, ORANGE, 6)
         + arrow_badge(True, -700, 0, 1.0) + T(-370, 15, "Full of air = FLOAT", 46, LINE, "bold")
         + arrow_badge(False, 60, 0, 1.0) + T(400, 15, "Heavy &amp; solid = SINK", 46, LINE, "bold"))
    return G(g, 960, 100, s)

def heart(x, y, s, op=1.0, col="#FF7FA8"):
    d = "M 0 12 C -28 -6 -18 -30 0 -16 C 18 -30 28 -6 0 12 Z"
    return f'<g opacity="{op:.2f}">{G(P(d, fill=col, stroke=LINE, sw=3), x, y, s)}</g>'

def float_icons(t):
    """Mini tank: ball floating, rock sinking (title + NEXT TIME teaser style)."""
    o = [R(-120, -10, 240, 90, 20, "#7FD3F7", LINE, 4)]
    o.append(P(f"M -120 -10 Q -60 {-20 + 6 * math.sin(t * 3):.1f} 0 -10 T 120 -10", stroke=WHITE, sw=5))
    o.append(G(ball_g(0.3 * math.sin(t)), -60, -26 + 4 * math.sin(t * 3), 0.42))
    o.append(G(pebble_g(), 56, 52 + 3 * math.sin(t * 2), 0.7))
    o.append(T(56, 12, "&#8595;", 30, LINE, "bold") + T(-60, -66, "&#8593;", 30, LINE, "bold"))
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
        spots = [(450, 360, "ball", 1.3), (1470, 330, "duck", 1.4), (330, 690, "pebble", 1.6), (1590, 680, "key", 1.5), (1260, 170, "bottle", 1.0), (650, 160, "pebble", 1.0)]
        for i, (x, y, k, sc) in enumerate(spots):
            age = t - st["hi"] - i * 0.25
            if age > 0:
                o.append(G(item_g(k, t), x + 20 * math.sin(t + i), y + 14 * math.sin(t * 1.5 + i), sc * ease(age / 0.4), 8 * math.sin(t * 1.2 + i)))
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
        o.append(G(R(-150, -40, 300, 80, 40, "#4CC28A", LINE, 5) + T(0, 16, "Why, Bo?", 40, WHITE, "bold"), 960, 520, s))
    if age > 4.0:
        s = ease((age - 4.0) / 0.4)
        o.append(G(T(0, 0, "Why Do Things Float?", 64, WHITE, "bold", extra=f'stroke="{LINE}" stroke-width="7" paint-order="stroke"'), 960, 660, s))
        o.append(G("".join(float_icons(t)), 960, 770, s * 1.15))
    for i in range(6):
        a = (t * 1.5 + i * 0.37) % 2
        o.append(sparkle(300 + i * 270, 180 + (i % 2) * 520, 1.4, YELLOW, max(0, math.sin(a * math.pi / 2))))
    return "".join(o)

def bo_pointing(t, st):
    p = 0.0
    for name, at in st["drops"].items():
        a = t - at
        if -0.3 <= a < 1.2: p = max(p, math.sin(min(1, (a + 0.3) / 1.5) * math.pi))
    return p

def scene_lab(t, t0, st):
    o = [background(t, "lab")]
    op = 0.0 if st["tank"] is None else ease((t - st["tank"]) / 0.4)
    if op > 0.01:
        o.append(tank(t, st, op))
        o.append(tank_items(t, st))
        o.append(tank_front(t, op))
        o.append(results_badges(t, st))
        o.append(sand_pour(t, st))
    o.append(place_bo(t, 300, 900, 1.15, point=bo_pointing(t, st)))
    if st["enter"] is not None:
        a = ease((t - st["enter"]) / 1.3)
        x = 2250 + (1640 - 2250) * a
        if a < 1:
            for k in range(4):
                o.append(C(x + 140 + k * 60, 520 + 20 * math.sin(k + t * 5), 10 + k * 3, "none", "#E8F8FF", 3, 'opacity="0.8"'))
        o.append(place_bloop(t, x, 500, 1.05))
    o.append(rule_card(t, st))
    if not (st["lesson"] and st["lesson"][0]):
        o.append(guess_panel(t, st))
    if st["hug"] is not None:
        a = t - st["hug"]
        for k in range(6):
            q = a - k * 0.35
            if 0 < q < 2.6:
                o.append(heart(520 + k * 190, 700 - q * 160, 1.6, max(0, 1 - q / 2.6)))
    if st["lesson"] and st["lesson"][0]:
        o.append(lesson_banner(t - st["lesson"][1]))
    elif st["lesson"] and not st["lesson"][0] and t - st["lesson"][1] < 0.3:
        o.append(f'<g opacity="{1 - (t - st["lesson"][1]) / 0.3:.2f}">{lesson_banner(1)}</g>')
    return "".join(o)

def big_water(x0, x1, y, t):
    w = "".join(f" Q {x0 + (x1 - x0) / 12 * (2 * k + 1):.0f} {y + 9 * math.sin(t * 3 + k):.1f} {x0 + (x1 - x0) / 6 * (k + 1):.0f} {y}" for k in range(6))
    return (P(f"M {x0} {y}{w} L {x1} 860 L {x0} 860 Z", fill="#3FA2D8", extra='fill-opacity="0.45"')
            + P(f"M {x0} {y}{w}", stroke=WHITE, sw=7))

def pill(text, col, x, y, w=440, size=40):
    return G(R(-w / 2, -40, w, 80, 40, WHITE, col, 5) + T(0, 15, text, size, LINE, "bold"), x, y)

def scene_song(t, t0, st):
    o = [background(t, "song")]
    beat = 0.6
    ph = ((t - t0) % beat) / beat
    o.append(C(960, 520, 380 + 30 * (1 - ph), "url(#glow)", extra='opacity="0.35"'))
    kinds = ["ball", "pebble", "duck", "key", "bottle", "ball", "pebble", "duck", "key", "bottle"]
    for i in range(10):
        a = math.pi * (0.9 - 0.8 * i / 9)
        x, y = 960 + 820 * math.cos(a), 470 - 330 * math.sin(a)
        o.append(G(item_g(kinds[i], t), x, y + 8 * math.sin(t * 3 + i), 0.75, 8 * math.sin(t * 3 + i)))
    o.append(place_bo(t, 280, 900, 1.05, dance=1))
    o.append(place_bloop(t, 1650, 600, 1.05, energy=2.5, dance=1))
    phase = st["phase"][0] if st["phase"] else None
    bounce = abs(math.sin((t - t0) * math.pi / beat))
    if phase is None:
        o.append(G("".join(float_icons(t)), 960, 500 - 20 * bounce, 2.4))
    elif phase == "think":
        o.append(G(ball_g(0.3 * math.sin(t)), 760, 470 - 24 * bounce, 1.3) + arrow_badge(True, 760, 640, 1.2))
        o.append(G(pebble_g(), 1160, 470 - 24 * (1 - bounce), 1.8) + arrow_badge(False, 1160, 640, 1.2))
        o.append(G(T(0, 0, "?", 160, ORANGE, "bold", extra=f'stroke="{LINE}" stroke-width="8" paint-order="stroke"'), 960, 520, 1, 8 * math.sin(t * 3)))
        o.append(pill("Float or sink?", "#2E8FCC", 960, 750))
    elif phase == "float":
        o.append(big_water(620, 1300, 560, t))
        o.append(G(ball_g(0.4 * math.sin(t * 2)), 820, 530 + 10 * math.sin(t * 4), 1.4))
        o.append(G(duck_g(), 1120, 540 + 10 * math.sin(t * 4 + 1), 1.3))
        o.append(pill("Full of air = FLOAT", "#4CC28A", 960, 360, 520))
    elif phase == "sink":
        o.append(big_water(620, 1300, 400, t))
        cur = st["song_num"]
        n = cur[0] if cur is not None and cur[1] >= st["phase"][1] else 0
        a = t - st["phase"][1]
        y = 440 + min(1, a / 2.5) * 80 + n * 90
        o.append(G(pebble_g(), 960, y + 4 * math.sin(t * 3), 2.4))
        for k in range(3):
            q = (t * 0.8 + k * 0.33) % 1
            o.append(C(930 + k * 30, y - 60 - q * (y - 460), 9, "none", WHITE, 3, f'opacity="{1 - q:.2f}"'))
        for k in range(1, 4):
            on = n >= k
            sc = 1 + 0.3 * max(0, 1 - (t - cur[1]) / 0.3) if (on and n == k) else 1.0
            o.append(G(C(0, 0, 38, "#8A6BE0" if on else WHITE, LINE, 5) + T(0, 18, str(k), 50, WHITE if on else LINE, "bold"), 1380, 450 + (k - 1) * 110, sc))
        o.append(pill("Heavy &amp; solid = SINK", "#8A6BE0", 960, 300, 540))
    elif phase == "test":
        o.append(G("".join(float_icons(t)), 960, 470 - 20 * bounce, 2.0))
        o.append(G(C(0, 0, 46, "#4CC28A", LINE, 6) + P("M -20 2 L -5 17 L 22 -14", stroke=WHITE, sw=10), 1260, 380, 1 + 0.1 * bounce))
        o.append(pill("Test and see!", ORANGE, 960, 740))
    else:
        o.append(G(R(-300, -46, 600, 92, 46, WHITE, "#4CC28A", 6) + arrow_badge(True, -248, 0, 1.0) + T(30, 16, "Full of air = FLOAT", 40, LINE, "bold"), 960, 360 - 10 * bounce))
        o.append(G(R(-300, -46, 600, 92, 46, WHITE, "#8A6BE0", 6) + arrow_badge(False, -248, 0, 1.0) + T(30, 16, "Heavy &amp; solid = SINK", 40, LINE, "bold"), 960, 500 - 10 * (1 - bounce)))
        o.append(G(R(-300, -46, 600, 92, 46, ORANGE, LINE, 6) + T(0, 16, "Test and see!", 44, WHITE, "bold"), 960, 640 - 10 * bounce))
    return "".join(o)

def scene_lab_end(t, t0, st):
    o = [background(t, "lab_end")]
    o.append(tank(t, st)); o.append(tank_items(t, st)); o.append(tank_front(t)); o.append(results_badges(t, st))
    wave = 0.0
    if st["wave"] is not None:
        wave = ease((t - st["wave"]) / 0.4)
    o.append(place_bo(t, 300, 900, 1.15, wave=wave))
    o.append(place_bloop(t, 1600, 470, 1.1, energy=1 + 2 * wave))
    return "".join(o)

DAYS = [("M", "#FF6B6B"), ("T", ORANGE), ("W", YELLOW), ("T", "#4CC28A"), ("F", "#4FA6DB"), ("S", "#8A6BE0"), ("S", "#FF7FA8")]

def scene_end(t, t0, st):
    age = t - t0
    o = [background(t, "end")]
    o.append(G(T(0, 0, "Bo &amp; Bloop", 96, ORANGE, "bold", extra=f'stroke="{LINE}" stroke-width="10" paint-order="stroke"'), 960, 170, ease(age / 0.4)))
    s = ease((age - 0.4) / 0.4)
    card = (R(-520, -190, 1040, 380, 40, WHITE, LINE, 6, 'fill-opacity="0.95"')
            + T(0, -110, "NEXT TIME", 34, "#2E8FCC", "bold", extra='letter-spacing="6"')
            + T(0, -30, "Days of the Week with Bo", 58, LINE, "bold"))
    for k, (d, col) in enumerate(DAYS):
        x = -360 + k * 120
        b = 8 * math.sin(t * 4 + k * 0.8)
        card += G(C(0, 0, 46, col, LINE, 5) + T(0, 17, d, 48, WHITE, "bold", extra=f'stroke="{LINE}" stroke-width="4" paint-order="stroke"'), x, 90 + b)
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
