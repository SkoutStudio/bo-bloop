"""Turn the script into a timed timeline + a mixed soundtrack."""
import json, os, subprocess
import numpy as np
import audio as A
from script import BEATS, SONG, N

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
            d = say(b["who"], N[n], t, "excited", sub_style="number")
            t += d + 0.45
        elif k == "jingle":
            music.append((t, A.jingle(), 0.9))
            act(t, dict(title=True))
            say("bo", "Bo", t + 0.8, "happy", sub="Bo...")
            say("bloop", "and Bloop!", t + 1.7, "giggle", sub="...and Bloop!")
            tl["subs"].append(dict(t0=round(t + 4.0, 3), t1=round(t + 7.6, 3), text="Count with Bo: Bo Counts the Bubbles", who="none", style="title"))
            t += 8.0
        elif k == "fastcount":
            for n in range(1, 11):
                act(t, dict(pulse=n - 1, big=n)); sfx.append((t, A.sfx_ding(n), 0.5))
                d = say("both", N[n], t, "excited", sub_style="number")
                t += max(d, 0.55) + 0.25
            t += 0.3
        elif k == "song":
            bpm = 100; beat = 60 / bpm; start = t
            total_beats = 44
            music.append((start, A.music_bed(total_beats * beat + 1.0, bpm, 1.25, drums=True), 1.0))
            act(start, dict(song=True))
            for blk, (nums_at, phrase_at, li) in enumerate([(8, 16, 1), (24, 32, 3)]):
                nums = range(1, 6) if blk == 0 else range(6, 11)
                tl["subs"].append(dict(t0=round(start + nums_at * beat - 0.1, 3), t1=round(start + (nums_at + 7) * beat, 3),
                                       text=SONG[li - 1][1], who="both", style="song"))
                for j, n in enumerate(nums):
                    at = start + (nums_at + j) * beat
                    act(at, dict(song_num=n))
                    sfx.append((at, A.sfx_ding(n), 0.35))
                    x = clip("bloop", N[n].strip("!"), 1.0)
                    voices.append((at, x, 0.8))
                    tl["speak"].append(dict(who="bloop", t=round(at, 3), env=A.envelope(x, FPS)))
                    x2 = clip("bo", N[n].strip("!"), 1.0)
                    voices.append((at, x2, 0.6))
                    tl["speak"].append(dict(who="bo", t=round(at, 3), env=A.envelope(x2, FPS)))
                who, text = SONG[li]
                at = start + phrase_at * beat
                say(who, text, at, "excited", sub_style="song", ls=1.0)
                act(at, dict(song_phrase=li))
            t = start + total_beats * beat
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
