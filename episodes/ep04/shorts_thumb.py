"""Vertical Shorts cut from the episode + YouTube thumbnail."""
import os, subprocess, sys, math
import cairosvg
from chars import *  # noqa
from render import storm_cloud, face_icon, FACE_COL, board


HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
EP = os.path.join(OUT, "bo_and_bloop_ep04_when_bo_feels_grumpy.mp4")
VW, VH = 1080, 1920
VID_Y = 560          # where the episode picture sits in the vertical frame
VID_H = 738          # 1580x1080 crop scaled to 1080 wide

SHORTS = [
    dict(name="ep04_short1_grumpy_puzzle", start=21.2, end=43.5, color="#2E8FCC",
         top=["Bo's puzzle", "won't fit!"], bottom=["Have you ever", "felt grumpy?"]),
    dict(name="ep04_short2_three_breaths", start=63.3, end=92.0, color=ORANGE,
         top=["3 slow breaths", "with Bo!"], bottom=["Breathe in...", "and out!"]),
    dict(name="ep04_short3_grumpy_song", start=126.0, end=151.0, color="#8A6BE0",
         top=["The Grumpy", "Feelings Song"], bottom=["Sing along", "with Bo &amp; Bloop!"]),
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
    o.append(T(540, 1755, "Full episode: When Bo Feels Grumpy", 30, LINE, "bold"))
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
    o.append(G(bo("grumpy", t=0.6), 330, 690, 1.2))
    o.append(storm_cloud(330, 190, 1.0, 0.4))
    o.append(G(P("M -70 0 L 60 0 M 25 -38 L 66 0 L 25 38", stroke=LINE, sw=26) + P("M -70 0 L 60 0 M 25 -38 L 66 0 L 25 38", stroke=WHITE, sw=14), 640, 400))
    o.append(G(face_icon("happy", FACE_COL["happy"]), 640, 270, 1.3))
    o.append(G(bo("excited", t=0.6, wave=1.0), 930, 690, 1.2))
    o.append(G(bloop("giggle", t=0.6), 1165, 235, 0.68, 8))
    o.append(T(640, 100, "GRUMPY? TRY THIS!", 88, YELLOW, "bold", extra=f'stroke="{LINE}" stroke-width="12" paint-order="stroke"'))
    o.append(R(470, 560, 340, 70, 35, ORANGE, LINE, 5))
    o.append(T(640, 608, "Bo &amp; Bloop", 40, WHITE, "bold"))
    o.append("</svg>")
    cairosvg.svg2png(bytestring="".join(o).encode(), write_to=os.path.join(OUT, "thumbnail_ep04.png"))
    print("thumbnail done")

if __name__ == "__main__":
    what = sys.argv[1]
    if what == "thumb":
        thumbnail()
    elif what == "overlays":
        for sh in SHORTS: frame_overlay(sh)
    else:
        for sh in SHORTS: make_short(sh)
