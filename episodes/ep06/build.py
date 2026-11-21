"""Turn the script into a timed timeline + a mixed soundtrack."""
import json, os, subprocess
import numpy as np
import audio as A
from script import BEATS, SONG, N, SONG_CHANT, CHANT_N, SONG_BEATS, TITLE


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
            if d.get("bloop_enter"):
                sfx.append((at, A.sfx_whoosh(), 0.5)); sfx.append((at + 0.9, A.sfx_bloop(), 0.7))
            if d.get("train") or d.get("hook_seven"):
                sfx.append((at, A.sfx_sparkle(), 0.5))
            if isinstance(d.get("sweep"), (int, float)):
                for i in range(d.get("n", 7)):
                    sfx.append((at + i * d["sweep"], A.sfx_ding(i + 1), 0.35))
            if d.get("bump"):
                sfx.append((at + 0.2, A.kick(0.5), 0.8)); sfx.append((at + 0.45, A.sfx_boing(), 0.5))
            if "swap" in d:
                sfx.append((at, A.sfx_whoosh(), 0.45)); sfx.append((at + 1.0, A.sfx_pop(1.1), 0.7))
            if "ans" in d or "lit" in d:
                sfx.append((at, A.sfx_ding(5), 0.5))
            if d.get("lit_end"):
                for i in range(3):
                    sfx.append((at + 0.8 + i * 0.45, A.sfx_ding(5 + i), 0.4))
            if d.get("go"):
                sfx.append((at, A.sfx_tada(), 0.6))
                for i in range(8):
                    sfx.append((at + 0.3 + i * 0.32, A.shaker(0.14), 1.0))
            if d.get("seven"):
                sfx.append((at, A.sfx_sparkle(), 0.6))
            if d.get("hug"):
                sfx.append((at, A.sfx_sparkle(), 0.5))
            if d.get("lesson"):
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
            a = b.get("act")
            if a and a.get("sweep") == "auto":   # light the carriages in time with the words
                d = say(b["who"], b["text"], t, b.get("expr"), b.get("sub"), b.get("listener_expr"))
                a = dict(a); a["sweep"] = round(d * 0.92 / a.get("n", 7), 3)
                act(t, a)
            else:
                act(t, a)
                d = say(b["who"], b["text"], t, b.get("expr"), b.get("sub"), b.get("listener_expr"))
            t += d + b.get("gap", 0.5)
        elif k == "breath":
            n = b["n"]
            act(t, dict(breath_in=n)); sfx.append((t, A.sfx_sparkle(), 0.3))
            say("bloop", "Breathe in...", t + 0.2, "happy", sub="Breathe in...")
            t += 3.0
            act(t, dict(breath_out=n)); sfx.append((t + 0.3, A.sfx_whoosh(), 0.35))
            d = say("bloop", "and out. " + N[n], t + 0.2, "happy", sub="...and out. " + N[n].upper())
            t += max(3.0, d + 0.9)
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
            if CHANT_N: tl["subs"].append(dict(t0=round(start + SONG_CHANT * beat - 0.1, 3), t1=round(start + (SONG_CHANT + 5) * beat, 3),
                                   text="One, two, three!", who="both", style="song"))
            for j in range(CHANT_N):
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
