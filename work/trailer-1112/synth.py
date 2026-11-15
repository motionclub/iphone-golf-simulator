"""Small numpy synth + mixer for the trailer score (no samples except the game's own sound effects)."""
import os, wave, subprocess, functools
import numpy as np

SR = 48000
FF = os.path.expanduser("~/tai-films/ffmpeg")
RNG = np.random.default_rng(3)
A4 = 440.0
NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}
def hz(name):
    """'D2', 'F#3', 'Bb1' -> Hz"""
    n, o = name[:-1], int(name[-1]); n = {"Bb": "A#", "Eb": "D#", "Ab": "G#", "Db": "C#", "Gb": "F#"}.get(n, n)
    return A4 * 2 ** ((NOTE[n] - 9) / 12 + (o - 4))

def tt(dur): return np.arange(int(dur * SR)) / SR
def env(n, a=.01, d=.1, s=.7, r=.2, hold=None):
    """ADSR over n samples (seconds for a/d/r)."""
    a_, d_, r_ = int(a * SR), int(d * SR), int(r * SR); e = np.full(n, s, np.float32)
    a_ = min(a_, n); e[:a_] = np.linspace(0, 1, a_, endpoint=False)
    d_ = min(d_, n - a_); e[a_:a_ + d_] = np.linspace(1, s, d_)
    r_ = min(r_, n); e[n - r_:] *= np.linspace(1, 0, r_)
    return e
def expdecay(n, tau): return np.exp(-np.arange(n) / (tau * SR)).astype(np.float32)

def fft_filter(x, lo=0, hi=None, slope=.35):
    """Static band filter with soft edges (lo/hi in Hz)."""
    n = len(x); X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR); g = np.ones_like(f)
    if lo > 0: g *= 1 / (1 + (lo / np.maximum(f, 1e-3)) ** (2 / slope))
    if hi: g *= 1 / (1 + (f / hi) ** (2 / slope))
    return np.fft.irfft(X * g, n).astype(np.float32)
def sweep_filter(x, f0, f1, lo=0, curve=1.0, block=4096):
    """Low-pass whose cutoff moves from f0 to f1 over the sound (STFT overlap-add)."""
    hop = block // 2; win = np.hanning(block).astype(np.float32); n = len(x); pad = np.concatenate([np.zeros(hop, np.float32), x, np.zeros(block, np.float32)])
    out = np.zeros_like(pad); f = np.fft.rfftfreq(block, 1 / SR); k = 0
    while k + block <= len(pad):
        u = min(1, max(0, (k - hop) / max(1, n))) ** curve; fc = f0 * (f1 / f0) ** u
        g = 1 / (1 + (f / fc) ** 6)
        if lo > 0: g = g / (1 + (lo / np.maximum(f, 1e-3)) ** 4)
        out[k:k + block] += np.fft.irfft(np.fft.rfft(pad[k:k + block] * win) * g, block) * win; k += hop
    return (out[hop:hop + n] / 1.0).astype(np.float32)

def saw(freq, dur, detune=0.0, voices=1, phase=None):
    t = tt(dur); out = np.zeros(len(t), np.float32)
    for v in range(voices):
        d = 0 if voices == 1 else (v / (voices - 1) - .5) * 2 * detune
        f = freq * 2 ** (d / 12); p = (t * f + (RNG.random() if phase is None else phase)) % 1.0
        out += (2 * p - 1).astype(np.float32)
    return out / voices
def sine(freq, dur, phase=0): return np.sin(2 * np.pi * (freq * tt(dur) + phase)).astype(np.float32)
def chirp(f0, f1, dur, curve=1.0):
    t = tt(dur); u = (t / dur) ** curve; f = f0 * (f1 / f0) ** u
    return np.sin(2 * np.pi * np.cumsum(f) / SR).astype(np.float32)
def noise(dur): return RNG.standard_normal(int(dur * SR)).astype(np.float32)

# ---------------------------------------------------------------- instruments (mono, peak about 1)
def boom(dur=2.2, f0=95, f1=32, tone=.6):
    x = chirp(f0, f1, dur, .35) * expdecay(int(dur * SR), dur * .28)
    c = fft_filter(noise(.25), 40, 900) * expdecay(int(.25 * SR), .03)
    x[:len(c)] += c * tone; return np.tanh(x * 1.6) * .9
def taiko(dur=.9, f0=120, f1=58, hard=.8):
    n = int(dur * SR); x = chirp(f0, f1, dur, .3) * expdecay(n, dur * .22)
    c = fft_filter(noise(.12), 200, 3500) * expdecay(int(.12 * SR), .012)
    x[:len(c)] += c * hard; return np.tanh(x * 1.8) * .9
def clack(dur=.14, f=2200):
    n = int(dur * SR); return (fft_filter(noise(dur), f * .6, f * 2.2) * expdecay(n, .018)).astype(np.float32)
def hat(dur=.07): n = int(dur * SR); return fft_filter(noise(dur), 6000, 15000) * expdecay(n, .014)
def clap(dur=.35):
    n = int(dur * SR); x = fft_filter(noise(dur), 700, 5000); e = np.zeros(n, np.float32)
    for off in (0, .011, .023, .034): k = int(off * SR); e[k:] += expdecay(n - k, .045 if off > .03 else .008)
    return x * e * .6
def braam(freq, dur=4.0, bright=1600):
    n = int(dur * SR); x = saw(freq, dur, .18, 7) + .8 * saw(freq * 2, dur, .14, 5) + .5 * saw(freq * 1.4983, dur, .1, 3) + .9 * sine(freq / 2, dur)
    x = sweep_filter(x, bright, 220, 30, curve=.5) * env(n, .03, .5, .75, dur * .45)
    return np.tanh(x * 1.5) * .8
def pad(freqs, dur, bright=1400, attack=.8, release=1.2):
    n = int(dur * SR); x = np.zeros(n, np.float32)
    for f in freqs: x += saw(f, dur, .12, 5) + .35 * saw(f * 2, dur, .1, 3)
    x = fft_filter(x / len(freqs), 60, bright) * env(n, attack, .3, .9, release); return x * .9
def strings(freqs, dur, bright=2600, attack=.25, release=.5, trem=5.2):
    n = int(dur * SR); x = pad(freqs, dur, bright, attack, release); t = tt(dur)
    return x * (1 + .12 * np.sin(2 * np.pi * trem * t)).astype(np.float32)
def piano(freq, dur=3.0, vel=1.0):
    n = int(dur * SR); t = tt(dur); x = np.zeros(n, np.float32)
    for h in range(1, 13):
        fh = freq * h * (1 + .00035 * h * h)
        if fh > SR / 2.2: break
        x += (np.sin(2 * np.pi * fh * t) * np.exp(-t * (1.1 + .55 * h)) / (h ** 1.15)).astype(np.float32)
    knock = fft_filter(noise(.03), 800, 5000) * expdecay(int(.03 * SR), .006)
    x[:len(knock)] += knock * .12; x[:int(.004 * SR)] *= np.linspace(0, 1, int(.004 * SR)); return x * vel * .75
def pluck(freq, dur=.5, bright=3000):
    n = int(dur * SR); x = saw(freq, dur, .06, 3) + .5 * saw(freq * 2, dur, 0, 1)
    return sweep_filter(x, bright, 300, 40, curve=.4, block=1024) * expdecay(n, dur * .3) * .8
def bass(freq, dur=.25, bright=700):
    n = int(dur * SR); x = saw(freq, dur, .04, 2) + sine(freq, dur) * .8
    return np.tanh(sweep_filter(x, bright, 160, 25, curve=.5, block=1024) * env(n, .004, .06, .6, .04) * 1.6) * .8
def lead(freq, dur, bright=3200, vib=5.5):
    n = int(dur * SR); t = tt(dur); f = freq * (1 + .004 * np.sin(2 * np.pi * vib * t) * np.clip(t / .35, 0, 1)); ph = np.cumsum(f) / SR; x = np.zeros(n, np.float32)
    for d in (-.07, 0, .07): x += (2 * ((ph * 2 ** (d / 12)) % 1) - 1).astype(np.float32)
    x = x / 3 + .4 * np.sin(2 * np.pi * ph).astype(np.float32)
    return fft_filter(x, 120, bright) * env(n, .06, .2, .85, min(.35, dur * .4)) * .8
def riser(dur=3.0, f0=200, f1=6000):
    n = int(dur * SR); x = sweep_filter(noise(dur), f0, f1, 100, curve=1.6) * (np.linspace(0, 1, n) ** 2.2).astype(np.float32)
    tone = chirp(110, 880, dur, 1.8) * (np.linspace(0, 1, n) ** 3).astype(np.float32) * .25
    return (x * .7 + tone) * .9
def whoosh(dur=.6, f=1800):
    n = int(dur * SR); e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2.5; return fft_filter(noise(dur), f * .4, f * 2.5) * e.astype(np.float32) * .8
def wind(dur, f=500):
    n = int(dur * SR); x = fft_filter(noise(dur), 120, f); lfo = 1 + .5 * np.sin(2 * np.pi * (.11 * tt(dur) + RNG.random())) + .3 * np.sin(2 * np.pi * .037 * tt(dur))
    return x * lfo.astype(np.float32) * .25
def drone(freq, dur, bright=420):
    n = int(dur * SR); x = saw(freq, dur, .2, 5) * .5 + sine(freq, dur) + .5 * sine(freq * 1.5, dur)
    lfo = 1 + .25 * np.sin(2 * np.pi * .09 * tt(dur)); return fft_filter(x, 25, bright) * lfo.astype(np.float32) * env(n, min(3, dur * .3), .1, 1, min(2.5, dur * .3)) * .5
def heartbeat():
    a = boom(.5, 70, 38, .15); b = boom(.5, 62, 34, .1) * .75; out = np.zeros(int(.75 * SR), np.float32); out[:len(a)] += a; k = int(.24 * SR); out[k:k + len(b)] += b[:len(out) - k]; return out * .9
def revcym(dur=1.6):
    n = int(dur * SR); return fft_filter(noise(dur), 2500, 12000) * (np.linspace(0, 1, n) ** 3).astype(np.float32) * .6

# ---------------------------------------------------------------- game sound effects
SFX_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Unity", "Assets", "Resources", "Audio", "v2", "sfx")
@functools.lru_cache(maxsize=None)
def sfx(rel):
    """A game sound effect as float32 (n,2) at 48 kHz, e.g. sfx('tennis/serve_1.wav')."""
    p = os.path.join(SFX_ROOT, rel); raw = subprocess.run([FF, "-loglevel", "error", "-i", p, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()

# ---------------------------------------------------------------- mixer
class Mix:
    def __init__(self, dur):
        self.n = int(dur * SR) + SR * 6; self.dry = np.zeros((self.n, 2), np.float32); self.wet = np.zeros((self.n, 2), np.float32)
    def add(self, x, t, gain=1.0, pan=0.0, rev=0.2, fade_in=0, fade_out=0, rate=1.0):
        """x mono or (n,2); t seconds; pan -1..1; rev = send to the hall."""
        if t < 0: return
        x = np.asarray(x, np.float32)
        if rate != 1.0:
            idx = np.arange(0, len(x) - 1, rate); i0 = idx.astype(int); fr = (idx - i0)[:, None] if x.ndim == 2 else (idx - i0)
            x = x[i0] * (1 - fr) + x[i0 + 1] * fr
        if x.ndim == 1: l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4); x = np.stack([x * l, x * r], 1) * 1.414
        x = x * gain
        if fade_in: k = min(len(x), int(fade_in * SR)); x[:k] *= np.linspace(0, 1, k)[:, None]
        if fade_out: k = min(len(x), int(fade_out * SR)); x[-k:] *= np.linspace(1, 0, k)[:, None]
        a = int(t * SR); b = min(self.n, a + len(x))
        if b <= a: return
        self.dry[a:b] += x[:b - a]; self.wet[a:b] += x[:b - a] * rev
    def render(self, path, hall=3.2, wet=.9, target=-1.0):
        n = int(hall * SR); ir = np.stack([RNG.standard_normal(n), RNG.standard_normal(n)], 1).astype(np.float32) * np.exp(-np.arange(n) / (hall * SR / 6.5))[:, None]
        for c in range(2): ir[:, c] = fft_filter(ir[:, c], 180, 5200)
        ir[: int(.012 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum(0)).max()
        m = 1 << int(np.ceil(np.log2(self.n + n))); out = self.dry.copy()
        for c in range(2):
            out[:, c] += np.fft.irfft(np.fft.rfft(self.wet[:, c], m) * np.fft.rfft(ir[:, c], m), m)[: self.n] * wet * .35
        # glue: slow gain riding, then a soft ceiling
        peak = np.abs(out).max(); out = out / max(peak, 1e-6) * 1.6; out = np.tanh(out * .9) / np.tanh(.9 * 1.6)
        out = out / np.abs(out).max() * 10 ** (target / 20)
        with wave.open(path, "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
        rms = 20 * np.log10(np.sqrt((out ** 2).mean()) + 1e-9); return dict(seconds=self.n / SR, rms_db=round(float(rms), 1), peak=round(float(np.abs(out).max()), 3))
