"""Announcer lines and crowd voices for golf + tennis, generated offline with Kokoro-82M
(Apache-2.0 weights, via kokoro-onnx, MIT). Nothing is ripped or recorded.

    ESPEAK_DATA_PATH=~/.cache/espk <venv>/bin/python make_voices.py <kokoro dir> <Unity/Assets/Resources/Audio>

Writes 24 kHz mono 16-bit WAVs:
  Announcer/Golf/<key>.wav     golf calls (numbered takes: key_2, key_3 ...)
  Announcer/Tennis/<key>.wav   the TennisAnnouncer script (umpire = bm_george, commentator = af_heart)
  Crowd/<name>.wav             crowd reactions (ooh, aww, cheer, roar) built by layering ~28 different
                               voices with random offsets, pitch and distance; murmur beds (loops)
"""
import os, sys, random
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly

sys.path.insert(0, sys.argv[1])
from tts_common import kokoro  # noqa: E402

OUT = sys.argv[2]
SR = 24000
k = kokoro()

HOST = 'af_heart'      # the standard announcer: bright, friendly, party-sports
UMPIRE = 'bm_george'   # tennis umpire: calm British male

GOLF = [
    ('welcome', "Welcome to the course, everyone! Let's play some golf!"),
    ('turn', "You're up!"), ('turn_2', "Your shot!"),
    ('turn_p1', "Player one, you're up!"), ('turn_p2', "Player two, you're up!"),
    ('turn_p3', "Player three, you're up!"), ('turn_p4', "Player four, you're up!"),
    ('great_shot', "Great shot!"), ('great_shot_2', "What a strike!"), ('great_shot_3', "Pure! Absolutely pure!"),
    ('nice_shot', "Nice shot!"), ('nice_shot_2', "Lovely!"),
    ('fairway', "Right down the middle!"),
    ('on_green', "On the green!"), ('close', "Oh, so close!"), ('close_2', "Ooh, just missed!"), ('tap_in', "Tap-in range!"),
    ('lip_out', "Lipped out!"), ('lip_out_2', "Oh no, it lipped out!"),
    ('in_hole', "In the hole!"), ('in_hole_2', "It's in!"),
    ('hole_in_one', "Hole in one! Unbelievable!"),
    ('albatross', "Albatross! Incredible!"), ('eagle', "Eagle!"), ('birdie', "Birdie!"), ('par', "That's par."), ('bogey', "Bogey."),
    ('water', "Splash! Into the water."), ('lava', "Ooh, into the lava!"), ('bunker', "In the sand."), ('out_of_bounds', "Out of bounds!"),
    ('round_over', "That's the round!"),
]

TENNIS_UMPIRE = {'fifteen_love', 'thirty_love', 'forty_love', 'love_fifteen', 'love_thirty', 'love_forty', 'fifteen_all',
                 'thirty_all', 'thirty_fifteen', 'fifteen_thirty', 'forty_fifteen', 'fifteen_forty', 'forty_thirty',
                 'thirty_forty', 'deuce', 'advantage_server', 'advantage_receiver', 'game', 'game_point', 'break_point',
                 'match_point', 'game_set_match', 'fault', 'double_fault', 'out', 'quiet_please', 'play'}
# (same text as TennisAnnouncer.Script; parsed from the C# so the two never drift)
def tennis_script():
    import re
    src = open(os.path.join(os.path.dirname(__file__), '../../../Unity/Assets/Scripts/Tennis/TennisAnnouncer.cs')).read()
    return re.findall(r'\("([a-z0-9_]+)", "([^"]+)"\)', src)


def hp(x, hz, sr=SR):
    return sosfilt(butter(2, hz, 'highpass', fs=sr, output='sos'), x)


def lp(x, hz, sr=SR):
    return sosfilt(butter(2, hz, 'lowpass', fs=sr, output='sos'), x)


def trim(a, floor=0.01, pad=0.03):
    idx = np.where(np.abs(a) > floor)[0]
    if len(idx) == 0:
        return a
    s, e = max(0, idx[0] - int(pad * SR)), min(len(a), idx[-1] + int(pad * SR * 2))
    return a[s:e]


def finish(a, peak=0.89):
    a = np.asarray(a, dtype=np.float64)
    a = a / (np.abs(a).max() + 1e-9)
    a = np.tanh(1.6 * a) / np.tanh(1.6)            # gentle squash: a voice that cuts through a crowd
    a = a / (np.abs(a).max() + 1e-9) * peak
    f = min(len(a), int(0.006 * SR))
    a[:f] *= np.linspace(0, 1, f); a[-f:] *= np.linspace(1, 0, f)
    return a.astype(np.float32)


def say(text, voice, speed=1.08):
    lang = 'en-gb' if voice.startswith('b') else 'en-us'
    a, sr = k.create(text, voice=voice, speed=speed, lang=lang)
    assert sr == SR
    return trim(a)


def write(rel, a):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    sf.write(p, a, SR, subtype='PCM_16')


def announcer():
    for key, text in GOLF:
        write(f'Announcer/Golf/{key}.wav', finish(hp(say(text, HOST), 90)))
    for key, text in tennis_script():
        voice = UMPIRE if key in TENNIS_UMPIRE else HOST
        write(f'Announcer/Tennis/{key}.wav', finish(hp(say(text, voice, 1.0 if voice == UMPIRE else 1.08), 90)))


# ---- crowd -------------------------------------------------------------------------------
EN_VOICES = [v for v in k.get_voices() if v[:2] in ('af', 'am', 'bf', 'bm') and v != 'am_santa']


def room(x, wet=0.35, seconds=0.9, seed=1):
    """Open-air stands: early taps + a short decaying diffuse tail."""
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (0.18 * SR))
    ir = lp(ir, 3500)
    ir /= np.sqrt((ir ** 2).sum())
    for d, g in ((0.021, .5), (0.037, .35), (0.055, .25)):
        ir[int(d * SR)] += g
    tail = np.convolve(x, ir)[:len(x) + n]
    out = np.zeros(len(tail)); out[:len(x)] += x * (1 - wet)
    return out + tail * wet


def crowd(name, takes, seconds, voices=None, spread=0.22, pitch=(0.9, 1.12), speeds=(0.85, 1.1), seed=0,
          env=None, bright=4200):
    """Many people at once: each voice says one of `takes` (text or ('/phonemes/',)), offset, re-pitched, at a distance."""
    rng = random.Random(seed)
    voices = voices or EN_VOICES
    n = int(seconds * SR)
    mix = np.zeros(n + SR)
    for i, v in enumerate(voices * 2):            # every voice twice, different takes: ~56 people
        t = rng.choice(takes)
        lang = 'en-gb' if v.startswith('b') else 'en-us'
        if isinstance(t, tuple):
            a, _ = k.create(t[0], voice=v, speed=rng.uniform(*speeds), lang=lang, is_phonemes=True)
        else:
            a, _ = k.create(t, voice=v, speed=rng.uniform(*speeds), lang=lang)
        a = trim(a)
        p = rng.uniform(*pitch)                    # resample = pitch + length change, like different people
        up, down = int(round(100 / p)), 100
        a = resample_poly(a, up, down)
        a = lp(a, rng.uniform(bright * .55, bright))   # near and far seats
        a = a / (np.abs(a).max() + 1e-9) * rng.uniform(.35, 1.0)
        at = int(abs(rng.gauss(0, spread)) * SR)
        e = min(len(mix), at + len(a))
        mix[at:e] += a[:e - at]
    mix = hp(mix[:n], 120)
    if env is not None:
        mix *= env(np.arange(n) / SR)
    out = room(mix, seed=seed)[:n]
    f = int(0.25 * SR); out[-f:] *= np.linspace(1, 0, f) ** 2
    return finish(out, 0.85)


def murmur(name, lines, seconds, seed, level_lp=1600):
    """Walla: a dozen people chatting at once, low-passed until no word is readable; seamless loop."""
    rng = random.Random(seed)
    n = int(seconds * SR)
    fade = int(1.5 * SR)
    mix = np.zeros(n + fade + 6 * SR)
    for v in EN_VOICES:
        t = rng.uniform(-2, 1)
        while t < seconds + 1.5:
            text = rng.choice(lines)
            lang = 'en-gb' if v.startswith('b') else 'en-us'
            a, _ = k.create(text, voice=v, speed=rng.uniform(.95, 1.15), lang=lang)
            a = trim(a)
            a = a / (np.abs(a).max() + 1e-9) * rng.uniform(.25, .8)
            at = int(max(0, t) * SR); skip = int(max(0, -t) * SR)
            seg = a[skip:]
            e = min(len(mix), at + len(seg)); mix[at:e] += seg[:e - at]
            t += len(a) / SR + rng.uniform(.4, 2.5)
    mix = lp(hp(mix, 150), level_lp)
    mix = room(mix, wet=.45, seed=seed)
    loop = mix[:n].copy()
    w = np.linspace(0, 1, fade)
    loop[:fade] = loop[:fade] * w + mix[n:n + fade] * (1 - w)   # its own continuation faded over the start
    return finish(loop, 0.8)


def crowd_set():
    swell = lambda t: np.minimum(1, t / .12) * np.exp(-np.maximum(0, t - .7) / .5)
    write('Crowd/ooh.wav', crowd('ooh', [('ˈuːːː',), ('ˈoʊːː',), ('wˈoʊːː',), "Ooooh!"], 2.2, seed=11,
                                 pitch=(.85, 1.1), speeds=(.55, .8), env=swell))
    write('Crowd/aww.wav', crowd('aww', [('ˈɔːːː',), ('ˈɑːːw',), "Awww.", "Oh no."], 2.2, seed=12,
                                 pitch=(.82, 1.05), speeds=(.55, .8), env=swell))
    write('Crowd/cheer.wav', crowd('cheer', ["Yeah!", "Yes!", "Woo!", "Nice!", "Come on!", ('wˈuːːː!',), ('jˈɛːːː!',)],
                                   2.6, seed=13, spread=.3, pitch=(.9, 1.2), speeds=(.9, 1.2), bright=5200))
    write('Crowd/roar.wav', crowd('roar', ["Yeah!", "Yes! Yes!", "Woo-hoo!", "Unbelievable!", "Come on!", ('wˈuːːːː!',),
                                           ('jˈɛːːːː!',), ('ˈoʊːː, jˈɛːː!',)], 3.6, seed=14, spread=.45, pitch=(.88, 1.22),
                                  speeds=(.8, 1.2), bright=5600))
    golf_talk = ["Where do you think it'll land?", "That was a lovely swing.", "Shall we walk to the next green?",
                 "I love this course.", "Look at the view from here.", "He always hits it long.", "Did you bring the sunscreen?",
                 "The wind's picking up a bit.", "What club is that?", "She's having a great round."]
    stand_talk = ["What a match this is.", "Can you see the ball from here?", "Pass me the water, please.",
                  "That serve was so fast.", "Who do you think will win?", "I love watching tennis by the sea.",
                  "Great seats, aren't they?", "Did you see that last rally?", "It's so sunny today.", "Let's get ice cream after."]
    write('Crowd/gallery_murmur.wav', murmur('gallery', golf_talk, 20, 21, 1400))
    write('Crowd/stands_murmur.wav', murmur('stands', stand_talk, 20, 22, 1700))


if __name__ == '__main__':
    what = sys.argv[3] if len(sys.argv) > 3 else 'all'
    if what in ('all', 'announcer'):
        announcer()
    if what in ('all', 'crowd'):
        crowd_set()
    print('done', what)
