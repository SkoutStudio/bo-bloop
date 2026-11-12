"""Turn the script into a timed timeline + a mixed soundtrack."""
import json, os, subprocess
import numpy as np
import audio as A
from script import BEATS, SONG, N, ROCKS, SORT_WHO, SONG_CHANT, SONG_BEATS, TITLE

FPS = 24
OUT = os.path.join(A.HERE, "build")

def clip(who, text, ls=None):
    p = A.speak(who, text, ls)
    return A.read_wav(p)

def build():
    t = 0.0
    tl = dict(fps=FPS, scenes=[], speak=[], expr=[], acts=[], subs=[])
    voices, sfx, music = [], [], []  # (start, samples, gain)

    def say(who, text, at, expr=None, sub=None, listener=None, sub_style="line", ls=None):
        whos = ["bo", "bloop"] if who == "both" else [who]
        dur = 0
        for w in whos:
            x = clip(w, text, ls)
            voices.append((at, x, 0.85 if who == "both" else 1.0))
            tl["speak"].append(dict(who=w, t=round(at, 3), env=A.envelope(x, FPS)))
            dur = max(dur, len(x) / A.SR)
            if expr:
                tl["expr"].append(dict(who=w, t=round(at, 3), e=expr))
        if listener:
            other = "bloop" if who == "bo" else "bo"
            tl["expr"].append(dict(who=other, t=round(at, 3), e=listener))
        tl["subs"].append(dict(t0=round(at, 3), t1=round(at + dur + 0.25, 3), text=sub or text, who=who, style=sub_style))
        return dur

    def act(at, d):
        if d:
            tl["acts"].append(dict(t=round(at, 3), **d))
            if "spawn" in d:
                for k, i in enumerate(d["spawn"]):
                    sfx.append((at + k * 0.18, A.sfx_pop(1 + 0.08 * k), 0.8))
                    tl["acts"].append(dict(t=round(at + k * 0.18, 3), pop=i))
            if "label" in d:
                sfx.append((at, A.sfx_sparkle() if d["label"][2] else A.sfx_pop(0.6), 0.5))
            if d.get("clear_labels") or "clear_labels_from" in d:
                sfx.append((at, A.sfx_boing(), 0.6))
            if d.get("bloop_enter"):
                sfx.append((at, A.sfx_whoosh(), 0.5)); sfx.append((at + 0.9, A.sfx_bloop(), 0.7))
            if d.get("tumble"):
                for k in range(3):
                    sfx.append((at + k * 0.6, A.sfx_pop(0.7 + 0.15 * k), 0.8))
                sfx.append((at + 3.4, A.sfx_boing(), 0.7)); sfx.append((at + 3.7, A.sfx_boing(), 0.5))
            if d.get("square_show") or d.get("bins"):
                sfx.append((at, A.sfx_sparkle(), 0.6))
            if d.get("build"):
                for k in range(4):
                    sfx.append((at + 0.4 + k * 0.5, A.sfx_pop(0.6 + 0.1 * k), 0.8))
            if d.get("tower_done"):
                sfx.append((at, A.sfx_tada(), 0.6))
            if d.get("roll_fun"):
                sfx.append((at + 0.3, A.sfx_whoosh(), 0.5)); sfx.append((at + 1.0, A.sfx_boing(), 0.4))
            if "big" in d or d.get("to_jar"):
                sfx.append((at, A.sfx_tada(), 0.6))

    bed_ranges = []
    scene_start = None

    for b in BEATS:
        k = b["t"]
        if k == "scene":
            tl["scenes"].append(dict(t=round(t, 3), name=b["name"]))
            if b["name"] in ("hook", "lab", "lab_end"):
                scene_start = t
            if b["name"] in ("title", "song") and scene_start is not None:
                bed_ranges.append((scene_start, t)); scene_start = None
        elif k == "pause":
            act(t, b.get("act")); t += b["dur"]
        elif k == "say":
            act(t, b.get("act"))
            d = say(b["who"], b["text"], t, b.get("expr"), b.get("sub"), b.get("listener_expr"))
            t += d + b.get("gap", 0.5)
        elif k == "count":
            n = b["n"]
            act(t, dict(highlight=n - 1)); sfx.append((t, A.sfx_ding(n), 0.7))
            t += 1.0  # time for kids at home to say it
            act(t, dict(label=[n - 1, n, True]))
            if b.get("move"):
                act(t + 0.55, dict(move=n - 1)); sfx.append((t + 0.55, A.sfx_pop(0.8), 0.6))
            d = say(b["who"], N[n], t, "excited", sub_style="number")
            t += d + 0.45
        elif k == "corner":
            n = b["n"]
            act(t, dict(corner_hl=n)); sfx.append((t, A.sfx_ding(n), 0.7))
            t += 1.0
            act(t, dict(corner=n))
            d = say(b["who"], N[n], t, "excited", sub_style="number")
            t += d + 0.45
        elif k == "sort":
            i = b["i"]; shape = "Circle!" if ROCKS[i] == "c" else "Square!"
            act(t, dict(highlight=i)); sfx.append((t, A.sfx_ding(i + 1), 0.6))
            t += 1.2  # kids say it
            act(t, dict(label=[i, shape, True]))
            act(t + 0.6, dict(move=i)); sfx.append((t + 0.6, A.sfx_pop(0.8 if ROCKS[i] == "c" else 0.6), 0.6))
            d = say(SORT_WHO[i], shape, t, "excited", sub_style="number")
            t += max(d, 1.0) + 0.45
        elif k == "jingle":
            music.append((t, A.jingle(), 0.9))
            act(t, dict(title=True))
            say("bo", "Bo", t + 0.8, "happy", sub="Bo...")
            say("bloop", "and Bloop!", t + 1.7, "giggle", sub="...and Bloop!")
            tl["subs"].append(dict(t0=round(t + 4.0, 3), t1=round(t + 7.6, 3), text=TITLE, who="none", style="title"))
            t += 8.0
        elif k == "song":
            bpm = 100; beat = 60 / bpm; start = t
            music.append((start, A.music_bed(SONG_BEATS * beat + 1.0, bpm, 1.25, drums=True), 1.0))
            act(start, dict(song=True))
            for bt, who, line, ac in SONG:
                at = start + bt * beat
                act(at, ac)
                say(who, line, at, "excited", sub_style="song", ls=1.0)
            tl["subs"].append(dict(t0=round(start + SONG_CHANT * beat - 0.1, 3), t1=round(start + (SONG_CHANT + 5) * beat, 3),
                                   text="One, two, three, four!", who="both", style="song"))
            for j in range(4):
                at = start + (SONG_CHANT + j) * beat
                act(at, dict(song_num=j + 1)); sfx.append((at, A.sfx_ding(j + 1), 0.35))
                for w, g in (("bloop", 0.8), ("bo", 0.6)):
                    x = clip(w, N[j + 1].strip("!"), 1.0)
                    voices.append((at, x, g))
                    tl["speak"].append(dict(who=w, t=round(at, 3), env=A.envelope(x, FPS)))
            t = start + SONG_BEATS * beat
            scene_start = t
        else:
            raise ValueError(k)

    if scene_start is not None:
        bed_ranges.append((scene_start, t))
    tl["duration"] = round(t, 3)

    # ---- mix ----
    n = int(A.SR * (t + 1))
    mix = np.zeros(n, dtype=np.float32)
    for at, x, g in voices:
        A.add(mix, x, at, g)
    voice_level = mix.copy()
    for at, x, g in sfx:
        A.add(mix, x, at, g)
    for at, x, g in music:
        A.add(mix, x, at, g)
    for s, e in bed_ranges:
        bed = A.music_bed(e - s, 100, 0.55)
        fade = np.ones_like(bed)
        f = int(A.SR * 1.0)
        fade[:f] = np.linspace(0, 1, f); fade[-f:] = np.linspace(1, 0, f)
        # duck the bed under dialogue
        seg = voice_level[int(s * A.SR): int(s * A.SR) + len(bed)]
        env = np.convolve(np.abs(seg), np.ones(4410) / 4410, mode="same")
        duck = 1 - 0.55 * np.clip(env / 0.05, 0, 1)
        A.add(mix, bed * fade * duck[: len(bed)], s)
    mix = mix[: int(A.SR * t)]
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.95
    raw = os.path.join(OUT, "mix_raw.wav")
    A.write_wav(raw, mix)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "loudnorm=I=-15:TP=-1.5:LRA=11", "-ar", "48000",
                    os.path.join(OUT, "mix.wav")], check=True)
    with open(os.path.join(OUT, "timeline.json"), "w") as f:
        json.dump(tl, f)
    print("duration", round(t, 1), "s | lines", len(tl["subs"]), "| scenes", [s["name"] for s in tl["scenes"]])

if __name__ == "__main__":
    build()
