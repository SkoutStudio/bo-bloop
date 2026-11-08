"""Voices (offline TTS + character processing), synthesized music and sound effects."""
import hashlib, os, subprocess, wave
import numpy as np

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "build", "audio")
VOICES = os.environ.get("BB_VOICES", os.path.join(os.path.dirname(os.path.dirname(HERE)), "voices"))
os.makedirs(CACHE, exist_ok=True)

_loaded = {}

def _voice(name):
    from piper import PiperVoice
    if name not in _loaded:
        _loaded[name] = PiperVoice.load(os.path.join(VOICES, name + ".onnx"))
    return _loaded[name]

def read_wav(path):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()

def write_wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())

# Character voice recipes: base TTS voice, speed, pitch factor, extra effect
RECIPES = {
    "bo": dict(voice="en-us-ryan-medium", length=1.22, pitch=1.42, fx="robot"),
    "bloop": dict(voice="en-us-lessac-medium", length=1.22, pitch=1.3, fx="bubbly"),
}

def speak(who, text, length_override=None):
    r = RECIPES[who]
    ls = length_override or r["length"]
    key = hashlib.md5(f"{who}|{text}|{ls}|v3".encode()).hexdigest()[:12]
    out = os.path.join(CACHE, f"{who}_{key}.wav")
    if os.path.exists(out):
        return out
    from piper import SynthesisConfig
    raw = os.path.join(CACHE, f"raw_{key}.wav")
    with wave.open(raw, "wb") as w:
        _voice(r["voice"]).synthesize_wav(text, w, syn_config=SynthesisConfig(length_scale=ls, noise_scale=0.6, noise_w_scale=0.7))
    shifted = os.path.join(CACHE, f"sh_{key}.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af",
                    f"aresample={SR},rubberband=pitch={r['pitch']}:formant=preserved,"
                    "highpass=f=90,acompressor=threshold=0.2:ratio=3:attack=5:release=80",
                    "-ac", "1", shifted], check=True)
    x = read_wav(shifted)
    t = np.arange(len(x)) / SR
    if r["fx"] == "robot":
        ring = x * np.sin(2 * np.pi * 55 * t)
        x = 0.78 * x + 0.32 * ring
        # tiny metallic comb
        d = int(SR * 0.004)
        x[d:] += 0.25 * x[:-d]
    else:
        d = int(SR * 0.012)
        wob = x.copy(); wob[d:] = x[:-d]
        x = 0.85 * x + 0.22 * wob
    x = x / (np.abs(x).max() + 1e-9) * 0.9
    lead = np.zeros(int(SR * 0.03), dtype=np.float32)
    x = np.concatenate([lead, x])
    # trim trailing silence
    nz = np.where(np.abs(x) > 0.02)[0]
    if len(nz):
        x = x[: min(len(x), nz[-1] + int(SR * 0.08))]
    write_wav(out, x)
    os.remove(raw); os.remove(shifted)
    return out

def envelope(x, fps=24):
    hop = SR // fps
    n = len(x) // hop + 1
    env = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    env = env / (env.max() + 1e-9)
    env = np.clip((env - 0.08) / 0.6, 0, 1)
    return [round(float(v), 3) for v in env]

# ---------------- synthesis helpers ----------------
def note_hz(n):  # midi -> hz
    return 440.0 * 2 ** ((n - 69) / 12)

def pluck(freq, dur=0.6, amp=0.3, bright=1.0):
    t = np.arange(int(SR * dur)) / SR
    x = np.zeros_like(t)
    for h in range(1, 7):
        x += (1 / h ** 1.3) * np.sin(2 * np.pi * freq * h * t) * np.exp(-t * (3.5 + 2.2 * h / bright))
    x *= np.minimum(1, t / 0.004)
    return (amp * x).astype(np.float32)

def bell(freq, dur=1.0, amp=0.25):
    t = np.arange(int(SR * dur)) / SR
    x = (np.sin(2 * np.pi * freq * t) * np.exp(-t * 3.0)
         + 0.45 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t * 6)
         + 0.25 * np.sin(2 * np.pi * freq * 5.4 * t) * np.exp(-t * 10))
    x *= np.minimum(1, t / 0.002)
    return (amp * x).astype(np.float32)

def kick(amp=0.5):
    t = np.arange(int(SR * 0.3)) / SR
    f = 50 + 90 * np.exp(-t * 30)
    return (amp * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)).astype(np.float32)

def snare(amp=0.18):
    t = np.arange(int(SR * 0.2)) / SR
    rng = np.random.default_rng(3)
    return (amp * (rng.uniform(-1, 1, len(t)) * np.exp(-t * 22) + 0.4 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 20))).astype(np.float32)

def shaker(amp=0.05):
    t = np.arange(int(SR * 0.07)) / SR
    rng = np.random.default_rng(5)
    n = rng.uniform(-1, 1, len(t))
    n = np.diff(n, prepend=0)
    return (amp * n * np.exp(-t * 60)).astype(np.float32)

def bass(freq, dur, amp=0.22):
    t = np.arange(int(SR * dur)) / SR
    x = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t)
    return (amp * x * np.exp(-t * 2.5) * np.minimum(1, t / 0.01)).astype(np.float32)

def add(buf, clip, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(clip))
    buf[i:j] += gain * clip[: j - i]

CHORDS = [  # C, Am, F, G  (midi roots + triads)
    [60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]]

def music_bed(dur, bpm=100, gain=1.0, drums=False):
    """Light ukulele-style loop: 1 chord per bar."""
    buf = np.zeros(int(SR * (dur + 2)), dtype=np.float32)
    beat = 60 / bpm
    bar = 0
    t = 0.0
    pattern = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5]
    while t < dur:
        ch = CHORDS[bar % 4]
        for k, p in enumerate(pattern):
            n = ch[k % 3] + (12 if k in (3, 6) else 0)
            add(buf, pluck(note_hz(n), 0.55, 0.07 + (0.02 if k in (0, 4) else 0)), t + p * beat)
        add(buf, bass(note_hz(ch[0] - 24), beat * 2), t, 1.0)
        add(buf, bass(note_hz(ch[0] - 24), beat * 2), t + 2 * beat, 0.8)
        for b in range(4):
            add(buf, shaker(0.035), t + b * beat + beat / 2)
            if drums:
                if b in (0, 2):
                    add(buf, kick(0.45), t + b * beat)
                else:
                    add(buf, snare(0.14), t + b * beat)
        bar += 1
        t += 4 * beat
    return buf[: int(SR * dur)] * gain

def jingle():
    """8-second intro: bell arpeggio + drums, ends on a bright chord."""
    dur = 8.0
    buf = np.zeros(int(SR * (dur + 1)), dtype=np.float32)
    bpm = 120; beat = 0.5
    mel = [72, 76, 79, 84, 79, 76, 77, 81, 84, 81, 79, 74, 79, 83, 86, 84]
    for i, m in enumerate(mel):
        add(buf, bell(note_hz(m), 0.9, 0.2), 0.3 + i * beat / 2 + (0.5 if i >= 8 else 0))
    for b in range(12):
        tb = 0.3 + b * beat
        add(buf, kick(0.45) if b % 2 == 0 else snare(0.15), tb)
        add(buf, bass(note_hz([48, 45, 41, 43][(b // 3) % 4]), beat), tb, 0.9)
    for n in [60, 64, 67, 72, 76]:
        add(buf, bell(note_hz(n), 2.2, 0.16), 6.5)
        add(buf, pluck(note_hz(n), 1.4, 0.08), 6.5)
    return buf[: int(SR * dur)]

def sfx_pop(pitch=1.0):
    t = np.arange(int(SR * 0.12)) / SR
    f = (900 + 1600 * np.exp(-t * 40)) * pitch
    return (0.35 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 35)).astype(np.float32)

def sfx_ding(n):
    return bell(note_hz(72 + [0, 2, 4, 5, 7, 9, 11, 12, 14, 16][(n - 1) % 10]), 0.8, 0.22)

def sfx_bloop():
    t = np.arange(int(SR * 0.45)) / SR
    f = 700 * np.exp(-t * 5) + 180
    return (0.35 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6) * np.minimum(1, t / 0.01)).astype(np.float32)

def sfx_boing():
    t = np.arange(int(SR * 0.5)) / SR
    f = 220 + 60 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 4)
    return (0.28 * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t * 7) * 0.6).astype(np.float32)

def sfx_sparkle():
    buf = np.zeros(int(SR * 0.9), dtype=np.float32)
    for i, n in enumerate([84, 88, 91, 96]):
        add(buf, bell(note_hz(n), 0.6, 0.1), i * 0.06)
    return buf

def sfx_whoosh():
    t = np.arange(int(SR * 0.7)) / SR
    rng = np.random.default_rng(9)
    n = rng.uniform(-1, 1, len(t)).astype(np.float32)
    # simple moving low-pass that opens and closes
    k = 25
    n = np.convolve(n, np.ones(k) / k, mode="same")
    return (0.5 * n * np.sin(np.pi * t / t[-1]) ** 2).astype(np.float32)

def sfx_tada():
    buf = np.zeros(int(SR * 1.6), dtype=np.float32)
    for i, n in enumerate([72, 76, 79]):
        add(buf, bell(note_hz(n), 1.2, 0.16), i * 0.09)
    for n in [72, 76, 79, 84]:
        add(buf, bell(note_hz(n), 1.4, 0.12), 0.32)
    return buf
