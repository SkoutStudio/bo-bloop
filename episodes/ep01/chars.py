"""Bo & Bloop drawing functions with animation controls (talk, blink, wave, sway).
Matches the official character sheets (same shapes, palette and proportions)."""
import math

NAVY = "#24324F"; LINE = "#22304A"; WHITE = "#FFFFFF"; ORANGE = "#FF8A3D"; ORANGE_L = "#FFC08A"
CYAN = "#5EE6FF"; STEEL = "#A9B8CC"; PANEL = "#E4EBF4"; YELLOW = "#FFD54A"
B_BLUE = "#7DCBF5"; B_DARK = "#4FA6DB"; B_LIGHT = "#BDE7FC"; PINK = "#FF9EB5"
FONT = "DejaVu Sans"

def E(cx, cy, rx, ry, fill, stroke="none", sw=0, extra=""):
    return f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'
def C(cx, cy, r, fill, stroke="none", sw=0, extra=""):
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'
def R(x, y, w, h, rx, fill, stroke="none", sw=0, extra=""):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'
def P(d, fill="none", stroke="none", sw=0, extra=""):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" {extra}/>'
def T(x, y, s, size, fill=LINE, weight="normal", anchor="middle", extra=""):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {extra}>{s}</text>'
def G(inner, x=0, y=0, s=1, rot=0):
    r = f" rotate({rot:.2f})" if rot else ""
    return f'<g transform="translate({x:.1f},{y:.1f}) scale({s:.3f}){r}">{inner}</g>'
def tube(d, w=15):
    return P(d, stroke=LINE, sw=w + 11) + P(d, stroke=ORANGE, sw=w)

# ---------------- BO ----------------
def bo_face(expr, mouth=0.0, blink=False):
    o = []
    lx, rx_, ey = -30, 30, -8
    def eye(x, y, a=13, b=17):
        if blink:
            return R(x - a, y - 2.5, 2 * a, 5, 2.5, CYAN)
        return E(x, y, a, b, CYAN) + C(x + 4, y - 6, 4, WHITE)
    talking = mouth > 0.06
    def open_mouth():
        return E(0, 28, 9 + 8 * mouth, 3 + 13 * mouth, CYAN)
    if expr == "happy":
        o += [eye(lx, ey), eye(rx_, ey), open_mouth() if talking else P("M -22 22 Q 0 42 22 22", stroke=CYAN, sw=6)]
    elif expr == "excited":
        o += [eye(lx, ey - 2, 15, 19), eye(rx_, ey - 2, 15, 19),
              open_mouth() if talking else P("M -24 18 Q 0 52 24 18 Z", fill=CYAN),
              E(-52, 20, 10, 6, PINK, extra='opacity="0.7"'), E(52, 20, 10, 6, PINK, extra='opacity="0.7"')]
    elif expr == "surprised":
        if blink:
            o += [eye(lx, ey), eye(rx_, ey)]
        else:
            o += [C(lx, ey - 2, 17, CYAN) + C(lx + 5, ey - 8, 5, WHITE), C(rx_, ey - 2, 17, CYAN) + C(rx_ + 5, ey - 8, 5, WHITE)]
        o += [open_mouth() if talking else E(0, 30, 9, 12, "none", CYAN, 5)]
    elif expr == "sad":
        o += [eye(lx, ey + 2, 12, 14), eye(rx_, ey + 2, 12, 14),
              P(f"M {lx-22} {ey-2} L {lx+22} {ey-16} L {lx+22} {ey-40} L {lx-22} {ey-40} Z", fill=NAVY),
              P(f"M {rx_+22} {ey-2} L {rx_-22} {ey-16} L {rx_-22} {ey-40} L {rx_+22} {ey-40} Z", fill=NAVY),
              open_mouth() if talking else P("M -18 34 Q 0 20 18 34", stroke=CYAN, sw=6)]
    elif expr == "thinking":
        o += [eye(lx + 5, ey - 6, 11, 14), eye(rx_ + 5, ey - 6, 11, 14),
              open_mouth() if talking else P("M -6 28 L 18 24", stroke=CYAN, sw=6)]
    elif expr == "confused":
        o += [eye(lx, ey - 2, 14, 18), E(rx_, ey + 2, 12, 5, CYAN),
              open_mouth() if talking else P("M -22 28 q 7 -8 14 0 t 14 0 t 14 0", stroke=CYAN, sw=5)]
    return "".join(o)

def bo_head(expr="happy", mouth=0.0, blink=False, t=0.0, antenna_glow=None):
    glow = antenna_glow or (YELLOW if expr in ("thinking", "excited") else ORANGE)
    o = [P("M 0 -77 L 0 -118", stroke=LINE, sw=6)]
    if glow == YELLOW:
        o.append(C(0, -130, 22 + 4 * math.sin(t * 8), YELLOW, extra='opacity="0.35"'))
    o.append(C(0, -130, 13, glow, LINE, 5))
    if expr == "confused":
        o.append(T(52, -108, "?", 46, ORANGE, "bold"))
    o += [C(-104, 2, 16, ORANGE, LINE, 5), C(104, 2, 16, ORANGE, LINE, 5),
          R(-100, -77.5, 200, 155, 55, WHITE, LINE, 6),
          R(-78, -56, 156, 112, 36, NAVY),
          P("M -60 -42 Q -48 -50 -30 -50", stroke=WHITE, sw=5, extra='opacity="0.25"'),
          bo_face(expr, mouth, blink)]
    return "".join(o)

def _arm(side, hand):
    sx = 64 * side
    hx, hy = hand
    cx = (sx + hx) / 2 + 22 * side
    cy = min(-122, hy) - 6
    return tube(f"M {sx} -122 Q {cx:.1f} {cy:.1f} {hx:.1f} {hy + 10:.1f}") + C(hx, hy, 16, WHITE, LINE, 5)

def bo(expr="happy", mouth=0.0, blink=False, t=0.0, wave=0.0, point=0.0, tilt=0.0):
    """Front view. wave: 0..1 raises right arm and waves. point: 0..1 points right arm to the side."""
    lh = (-106, -74)
    rh = (106, -74)
    if wave > 0:
        ang = math.sin(t * 9) * 0.35
        rx = 106 + wave * (70 + 30 * math.sin(ang))
        ry = -74 - wave * (120 + 20 * math.cos(ang))
        rh = (rx, ry)
    elif point > 0:
        rh = (106 + 70 * point, -74 - 70 * point)
    head_rot = tilt + (2.5 * math.sin(t * 2.1) if mouth > 0.06 else 0)
    o = [E(-36, -14, 32, 16, ORANGE, LINE, 5), E(36, -14, 32, 16, ORANGE, LINE, 5),
         _arm(-1, lh), "" if wave > 0 else _arm(1, rh),
         R(-24, -168, 48, 28, 8, STEEL, LINE, 5),
         R(-70, -150, 140, 132, 50, WHITE, LINE, 6),
         C(0, -86, 30, ORANGE, LINE, 5), C(0, -86, 19, ORANGE_L),
         C(-10, -86, 5, CYAN), C(0, -86, 5, WHITE), C(10, -86, 5, NAVY),
         G(bo_head(expr, mouth, blink, t), 0, -233, 1, head_rot)]
    if wave > 0:
        o.append(_arm(1, rh))
    return "".join(o)

# ---------------- BLOOP ----------------
BELL = ("M -110 20 C -110 -126 110 -126 110 20 Q 92 40 73 20 Q 55 40 37 20 Q 18 40 0 20 "
        "Q -18 40 -37 20 Q -55 40 -73 20 Q -92 40 -110 20 Z")

def tentacle(x, sway=0):
    d = f"M {x} 24 q {-14 + sway:.1f} 24 {sway / 2:.1f} 46 t {sway / 2:.1f} 46"
    return P(d, stroke=LINE, sw=26) + P(d, stroke=B_DARK, sw=15)

def bloop_face(expr, mouth=0.0, blink=False):
    o = []
    talking = mouth > 0.06
    def eye(x, y, a=14, b=19):
        if blink:
            return P(f"M {x-12} {y+2} Q {x} {y+10} {x+12} {y+2}", stroke=NAVY, sw=5)
        return E(x, y, a, b, NAVY) + C(x + 5, y - 7, 5, WHITE) + C(x - 4, y + 6, 2.5, WHITE)
    cheeks = E(-64, 10, 15, 9, PINK, extra='opacity="0.85"') + E(64, 10, 15, 9, PINK, extra='opacity="0.85"')
    def open_mouth():
        return P(f"M -15 9 Q 0 {12 + 26 * mouth:.1f} 15 9 Z", fill=NAVY) + E(0, 9 + 10 * mouth, 6 * mouth + 1, 3 * mouth + 0.5, PINK)
    if expr == "happy":
        o += [eye(-36, -12), eye(36, -12), cheeks, open_mouth() if talking else P("M -14 12 Q 0 26 14 12", stroke=NAVY, sw=5)]
    elif expr == "giggle":
        o += [P("M -50 -8 Q -36 -26 -22 -8", stroke=NAVY, sw=6), P("M 22 -8 Q 36 -26 50 -8", stroke=NAVY, sw=6), cheeks,
              open_mouth() if talking else (P("M -20 8 Q 0 40 20 8 Z", fill=NAVY) + E(0, 24, 8, 5, PINK))]
    elif expr == "surprised":
        if blink:
            o += [eye(-36, -14), eye(36, -14)]
        else:
            o += [C(-36, -14, 18, NAVY) + C(-30, -21, 6, WHITE), C(36, -14, 18, NAVY) + C(42, -21, 6, WHITE)]
        o += [cheeks, open_mouth() if talking else E(0, 22, 8, 11, NAVY)]
    elif expr == "sad":
        o += [eye(-36, -8, 13, 16), eye(36, -8, 13, 16),
              P("M -52 -30 L -26 -40", stroke=NAVY, sw=5), P("M 52 -30 L 26 -40", stroke=NAVY, sw=5),
              open_mouth() if talking else P("M -12 24 Q 0 14 12 24", stroke=NAVY, sw=5)]
    elif expr == "thinking":
        if blink:
            o += [eye(-36, -12), eye(36, -12)]
        else:
            o += [E(-36, -12, 14, 19, NAVY) + C(-31, -24, 5, WHITE), E(36, -12, 14, 19, NAVY) + C(41, -24, 5, WHITE)]
        o += [P("M 22 -44 Q 36 -54 50 -44", stroke=NAVY, sw=5), cheeks,
              open_mouth() if talking else P("M -4 18 L 14 14", stroke=NAVY, sw=5)]
    elif expr == "excited":
        o += [eye(-36, -14, 16, 21), eye(36, -14, 16, 21), cheeks, open_mouth() if talking else P("M -18 10 Q 0 36 18 10 Z", fill=NAVY)]
    return "".join(o)

def sparkle(x, y, s=1, col=YELLOW, op=1.0):
    d = (f"M {x} {y-14*s} Q {x+2*s} {y-2*s} {x+14*s} {y} Q {x+2*s} {y+2*s} {x} {y+14*s} "
         f"Q {x-2*s} {y+2*s} {x-14*s} {y} Q {x-2*s} {y-2*s} {x} {y-14*s} Z")
    return P(d, fill=col, extra=f'opacity="{op:.2f}"')

def bloop(expr="happy", mouth=0.0, blink=False, t=0.0, energy=1.0):
    sw = [10 * energy * math.sin(t * 3.1 + p) for p in (0, 1.3, 2.6, 3.9)]
    o = [tentacle(-60, -6 + sw[0]), tentacle(-20, 6 + sw[1]), tentacle(20, -6 + sw[2]), tentacle(60, 6 + sw[3]),
         P(BELL, fill=B_BLUE, stroke=LINE, sw=6),
         E(-46, -54, 26, 13, WHITE, extra='opacity="0.45" transform="rotate(-24 -46 -54)"'),
         C(56, -52, 9, B_LIGHT), C(78, -24, 6, B_LIGHT), C(-80, -12, 6, B_LIGHT),
         bloop_face(expr, mouth, blink)]
    if expr == "excited":
        o += [sparkle(-104, -86, 1.1, op=0.6 + 0.4 * math.sin(t * 6)), sparkle(108, -70, 0.8, op=0.6 + 0.4 * math.cos(t * 6))]
    if expr == "thinking":
        o += [C(96, -96, 6, WHITE, B_DARK, 3), C(114, -116, 9, WHITE, B_DARK, 3)]
    return "".join(o)

def starfish(s=1.0, col="#FFB347"):
    pts = []
    for i in range(10):
        r = 60 if i % 2 == 0 else 26
        a = -math.pi / 2 + i * math.pi / 5
        pts.append(f"{r*math.cos(a):.1f},{r*math.sin(a):.1f}")
    return (f'<polygon points="{" ".join(pts)}" fill="{col}" stroke="{LINE}" stroke-width="5" stroke-linejoin="round" transform="scale({s})"/>'
            + E(-10 * s, -4 * s, 5 * s, 7 * s, NAVY) + E(10 * s, -4 * s, 5 * s, 7 * s, NAVY)
            + P(f"M {-8*s} {10*s} Q 0 {18*s} {8*s} {10*s}", stroke=NAVY, sw=3))
