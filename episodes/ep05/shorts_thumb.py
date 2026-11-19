"""Vertical Shorts cut from the episode + YouTube thumbnail."""
import os, subprocess, sys, math
import cairosvg
from chars import *  # noqa
from render import ball_g, pebble_g, duck_g, arrow_badge


HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
EP = os.path.join(OUT, "bo_and_bloop_ep05_why_do_things_float.mp4")
VW, VH = 1080, 1920
VID_Y = 560          # where the episode picture sits in the vertical frame
VID_H = 738          # 1580x1080 crop scaled to 1080 wide

SHORTS = [
    dict(name="ep05_short1_big_or_small", start=21.0, end=46.8, color="#2E8FCC",
         top=["Big sinks?", "Small floats?"], bottom=["What do", "you think?"]),
    dict(name="ep05_short2_magic_bottle", start=87.3, end=116.4, color=ORANGE,
         top=["The magic", "bottle trick!"], bottom=["Float", "or sink?"]),
    dict(name="ep05_short3_float_song", start=128.6, end=153.6, color="#8A6BE0",
         top=["The Float or", "Sink Song"], bottom=["Sing along", "with Bo &amp; Bloop!"]),
]

def frame_overlay(sh):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{VW}" height="{VH}" viewBox="0 0 {VW} {VH}">',
         '<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#B6EBFF"/><stop offset="1" stop-color="#3FA2D8"/></linearGradient></defs>',
         # background everywhere except the video window
         f'<path d="M0 0 H{VW} V{VH} H0 Z M0 {VID_Y} V{VID_Y + VID_H} H{VW} V{VID_Y} Z" fill="url(#g)" fill-rule="evenodd"/>']
    for i in range(16):
        x = (i * 157) % VW; y = (i * 263) % VH
        if VID_Y - 30 < y < VID_Y + VID_H + 30: continue
        o.append(C(x, y, 8 + i % 4 * 5, "none", "#E8F8FF", 3, 'opacity="0.6"'))
    o.append(R(60, 70, 300, 64, 32, sh["color"]))
    o.append(T(210, 113, "Bo &amp; Bloop", 32, WHITE, "bold"))
    for k, line in enumerate(sh["top"]):
        o.append(T(540, 260 + k * 118, line, 104, WHITE, "bold", extra=f'stroke="{LINE}" stroke-width="9" paint-order="stroke"'))
    o.append(R(0, VID_Y - 8, VW, 8, 0, sh["color"])); o.append(R(0, VID_Y + VID_H, VW, 8, 0, sh["color"]))
    for k, line in enumerate(sh["bottom"]):
        o.append(T(540, VID_Y + VID_H + 150 + k * 92, line, 80, LINE, "bold", extra=f'stroke="{WHITE}" stroke-width="8" paint-order="stroke"'))
    o.append(R(215, 1700, 650, 90, 45, WHITE, sh["color"], 6))
    o.append(T(540, 1755, "Full episode: Why Do Things Float?", 30, LINE, "bold"))
    o.append(G(bo("excited", t=0.5), 112, 1885, 0.48))
    o.append(G(bloop("giggle", t=0.5), 970, 1790, 0.48))
    o.append("</svg>")
    path = os.path.join(HERE, "build", sh["name"] + "_overlay.png")
    cairosvg.svg2png(bytestring="".join(o).encode(), write_to=path)
    return path

def make_short(sh):
    ov = frame_overlay(sh)
    out = os.path.join(OUT, sh["name"] + ".mp4")
    dur = sh["end"] - sh["start"]
    fc = (f"[0:v]crop=1580:1080:170:0,scale={VW}:{VID_H},setsar=1[v];"
          f"color=c=#3FA2D8:s={VW}x{VH}:r=24[bg];"
          f"[bg][v]overlay=0:{VID_Y}:shortest=1[b];"
          f"[b][1:v]overlay=0:0,fade=t=in:st=0:d=0.3,fade=t=out:st={dur - 0.4:.2f}:d=0.4[o];"
          f"[0:a]afade=t=in:st=0:d=0.2,afade=t=out:st={dur - 0.4:.2f}:d=0.4[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(sh["start"]), "-t", f"{dur:.2f}", "-i", EP, "-loop", "1", "-i", ov,
                    "-filter_complex", fc, "-map", "[o]", "-map", "[a]", "-t", f"{dur:.2f}",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out], check=True)
    print("short", out, round(dur, 1), "s")

def thumbnail():
    W, H = 1280, 720
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         '<defs><radialGradient id="r" cx="0.5" cy="0.45" r="0.8"><stop offset="0" stop-color="#C9F1FF"/><stop offset="1" stop-color="#3FA2D8"/></radialGradient></defs>',
         R(0, 0, W, H, 0, "url(#r)"),
         P("M 0 610 Q 320 585 640 610 T 1280 600 L 1280 720 L 0 720 Z", fill="#F6E3B4")]
    # water window in the middle: ball floats on top, rock sinks to the bottom
    o.append(R(400, 230, 480, 370, 26, "#E8F8FF", LINE, 8, 'fill-opacity="0.35"'))
    o.append(P("M 408 330 Q 468 316 528 330 T 648 330 T 768 330 T 872 330 L 872 592 L 408 592 Z", fill="#3FA2D8", extra='fill-opacity="0.55"'))
    o.append(G(ball_g(0.3), 560, 300, 1.25) + G(duck_g(), 760, 312, 1.0))
    o.append(G(pebble_g(), 700, 540, 1.6))
    for k in range(4):
        o.append(C(690 + k * 16, 480 - k * 34, 7 + k % 2 * 3, "none", WHITE, 3))
    o.append(P("M 408 330 Q 468 316 528 330 T 648 330 T 768 330 T 872 330", stroke=WHITE, sw=7))
    o.append(R(400, 230, 480, 370, 26, "none", LINE, 8))
    o.append(arrow_badge(True, 455, 410, 1.3) + arrow_badge(False, 830, 540, 1.3))
    o.append(G(bo("surprised", t=0.6), 210, 700, 1.0))
    o.append(G(bloop("excited", t=0.6), 1085, 400, 0.85, 8))
    o.append(T(640, 150, "FLOAT OR SINK?", 104, YELLOW, "bold", extra=f'stroke="{LINE}" stroke-width="13" paint-order="stroke"'))
    o.append(R(980, 610, 280, 64, 32, ORANGE, LINE, 5))
    o.append(T(1120, 654, "Bo &amp; Bloop", 36, WHITE, "bold"))
    o.append("</svg>")
    cairosvg.svg2png(bytestring="".join(o).encode(), write_to=os.path.join(OUT, "thumbnail_ep05.png"))
    print("thumbnail done")

if __name__ == "__main__":
    what = sys.argv[1]
    if what == "thumb":
        thumbnail()
    elif what == "overlays":
        for sh in SHORTS: frame_overlay(sh)
    else:
        for sh in SHORTS: make_short(sh)
