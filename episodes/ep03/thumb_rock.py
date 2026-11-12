import math
from chars import *  # noqa
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

