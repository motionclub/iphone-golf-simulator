#!/usr/bin/env python3
"""The trailer's music and sound, generated in code and laid against timeline.json (written by edit.py --timeline).
No voice. Music follows the `marks` in edit.json; game sounds follow each shot's `snd` list.  -> stage/score.wav"""
import os, json, sys
import numpy as np
from synth import *

W = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(os.path.join(W, "timeline.json"))); M = T["marks"]; TOTAL = T["total"]
mix = Mix(TOTAL)
def has(*k): return all(x in M for x in k)
BEAT = .5                                  # 120 beats a minute: every beat is 12 pictures
PROG = [("D2", ["D3", "F3", "A3"]), ("Bb1", ["D3", "F3", "Bb3"]), ("F2", ["C3", "F3", "A3"]), ("C2", ["C3", "E3", "G3"])]
THEME = [  # (beat in the 16-beat phrase, note, beats long)
    (0, "D5", 2), (2, "F5", 1), (3, "E5", 1), (4, "D5", 2), (6, "Bb4", 2),
    (8, "C5", 2), (10, "F5", 1), (11, "A5", 1), (12, "G5", 3), (15, "E5", 1)]

def groove(t0, t1, level=1.0, drums=True, bassline=True, strs=True, hats=True, big=False, claps=False, octave=0, start_bar=0):
    """Bars of four beats from t0 to t1: bass eighths, drums, sustained strings. Chords change every bar."""
    bar = 0; t = t0
    while t < t1 - .05:
        root, chord = PROG[(bar + start_bar) % 4]; dur = min(4 * BEAT, t1 - t)
        if strs: mix.add(strings([hz(n) * 2 ** octave for n in chord], dur + .3, 2400 if big else 1700), t, .30 * level, 0, .45)
        for e in range(8):
            te = t + e * BEAT / 2
            if te >= t1 - .02: break
            if bassline: mix.add(bass(hz(root) * (2 if e % 4 == 3 else 1), .24), te, .42 * level, 0, .05)
            if hats and drums: mix.add(hat(), te, (.10 if e % 2 else .05) * level, .3, .1)
        for b in range(4):
            tb = t + b * BEAT
            if tb >= t1 - .02 or not drums: break
            if b in (0, 2): mix.add(taiko(.8, 110, 52), tb, (.75 if big else .6) * level, 0, .2)
            if b in (1, 3): mix.add(clap() if claps else clack(.16, 1900), tb, (.5 if claps else .32) * level, -.2, .3)
            if big and b == 3: mix.add(taiko(.5, 150, 80, .9), tb + BEAT / 2, .45 * level, .4, .25)
        t += 4 * BEAT; bar += 1
    return bar

def theme(t0, t1, level=1.0, octave=0, voice="lead", start_beat=0):
    k = 0
    while True:
        for b, n, l in THEME:
            tb = t0 + (k * 16 + b - start_beat) * BEAT
            if tb < t0 - 1e-3: continue
            if tb >= t1 - .05: return
            d = min(l * BEAT, t1 - tb) + .12
            if voice == "lead": mix.add(lead(hz(n) * 2 ** octave, d), tb, .34 * level, .1, .5); mix.add(lead(hz(n) * 2 ** (octave - 1), d, 1800), tb, .18 * level, -.2, .5)
            else: mix.add(piano(hz(n) * 2 ** octave, max(2.2, d + 1.5)), tb, .5 * level, .1, .6)
        k += 1

# ---------------------------------------------------------------- game sounds on the cuts (each shot's `snd` in edit.json)
INSTR = {"boom": lambda: boom(), "taiko": lambda: taiko(), "whoosh": lambda: whoosh(), "whooshlong": lambda: whoosh(1.1, 1200), "heartbeat": heartbeat, "thump": lambda: boom(1.1, 70, 36, .2),
         "subdrop": lambda: boom(3.0, 120, 26, .1), "clack": lambda: clack(), "revcym": lambda: revcym()}
for e in T["snd"]:
    t, name = e[0], e[1]; gain = e[2] if len(e) > 2 else 1.0; pan = e[3] if len(e) > 3 else 0.0
    if name in INSTR: mix.add(INSTR[name](), t, gain, pan, .3)
    elif name.startswith("riser:"): d = float(name.split(":")[1]); mix.add(riser(d), t - d, gain, 0, .35)
    elif name.startswith("revcym:"): d = float(name.split(":")[1]); mix.add(revcym(d), t - d, gain, 0, .35)
    else:
        rate = 1.0
        if "@" in name: name, r = name.split("@"); rate = float(r)
        mix.add(sfx(name), t, gain, pan, .25, rate=rate)

# ---------------------------------------------------------------- scene 1: the challenge (quiet)
end1 = M.get("toss", TOTAL)
mix.add(wind(end1 + 2), 0, 1.0, 0, .2, fade_in=1.5, fade_out=2)
if has("lights"): mix.add(drone(hz("D1"), end1 - M["lights"] + 1.5), M["lights"], .16, 0, .3)
if has("walk"):
    for i, n in enumerate(["D4", "A4", "F4", "D4"]): mix.add(piano(hz(n), 4), M["walk"] + i * 1.0, .42, (-.3, .3)[i % 2], .7)
    mix.add(pad([hz("D2"), hz("A2"), hz("D3")], 6.5, 900, 3.5, 1.0), M["walk"], .22, 0, .5)
if has("round1"):
    mix.add(riser(2.4), M["round1"] - 2.4, .35, 0, .4); mix.add(boom(), M["round1"], .8, 0, .4); mix.add(braam(hz("D2"), 3.2, 1100), M["round1"], .30, 0, .5)

# ---------------------------------------------------------------- scene 2: tennis
if has("toss", "serve"):
    t = M["toss"]
    while t < M["serve"] - .6: mix.add(heartbeat(), t, .55, 0, .15); t += 1.0
    mix.add(pad([hz("A4"), hz("D5")], M["serve"] - M["toss"], 2500, 1.5, .1), M["toss"], .10, 0, .7)
    mix.add(revcym(1.4), M["serve"] - 1.4, .5, 0, .4)
    mix.add(boom(), M["serve"], 1.0, 0, .4); mix.add(braam(hz("D2"), 3.5), M["serve"], .5, 0, .5); mix.add(taiko(), M["serve"], .8, 0, .3)
if has("serve", "dive"):
    g0 = M["serve"] + BEAT; groove(g0, M["dive"], 1.0, big=False)
    mix.add(boom(3.0, 120, 26, .1), M["dive"], .7, 0, .4)
if has("dive", "miss"):
    d = M["miss"] - M["dive"]; mix.add(pad([hz("D4"), hz("A4"), hz("E5")], d + .2, 2200, .3, .15), M["dive"], .22, 0, .7); mix.add(revcym(min(1.8, d)), M["miss"] - min(1.8, d), .45, 0, .5)
if has("miss"): mix.add(boom(2.6, 80, 30, .15), M["miss"] + .05, .55, 0, .5)
if has("score1"): mix.add(taiko(1.1, 100, 48), M["score1"], .9, 0, .4); mix.add(boom(), M["score1"], .7, 0, .4); mix.add(braam(hz("D2"), 2.6, 1000), M["score1"], .28, 0, .5)

# ---------------------------------------------------------------- scene 3: golf
if has("golf", "g_back"):
    t0 = M["golf"]; t1 = M["g_back"]; bar = 0; t = t0
    mix.add(drone(hz("D1"), t1 - t0 + 1, 300), t0, .14, 0, .3)
    while t < t1 - .05:
        root, chord = PROG[bar % 4]; d = min(2.0, t1 - t)
        mix.add(pad([hz(n) for n in chord], d + .6, 1500, .5, .6), t, .30, 0, .5)
        for e in range(8):
            te = t + e * .25
            if te >= t1 - .02: break
            mix.add(pluck(hz(chord[e % 3]) * (2 if e % 4 >= 2 else 1), .45, 2400), te, .16, (-.4, .4)[e % 2], .5)
        t += 2.0; bar += 1
if has("g_back", "g_hit"):
    d = M["g_hit"] - M["g_back"]; mix.add(riser(d), M["g_back"], .5, 0, .4); mix.add(pad([hz("A2"), hz("E3"), hz("A3")], d + .1, 1800, d * .7, .05), M["g_back"], .3, 0, .5)
if has("g_hit"):
    mix.add(boom(), M["g_hit"], 1.0, 0, .4); mix.add(braam(hz("D2"), 3.0), M["g_hit"], .42, 0, .5)
if has("g_hit", "g_land"):
    g0 = M["g_hit"] + BEAT; groove(g0, M["g_land"], 1.05, big=True, octave=0); theme(g0, M["g_land"], 1.0)
    mix.add(strings([hz("D4"), hz("A4"), hz("D5")], M["g_land"] - g0, 3200, 1.0, .6), g0, .16, 0, .6)
if has("g_land", "g_lip"):
    d = M["g_lip"] - M["g_land"]; mix.add(pad([hz("C3"), hz("E3"), hz("G3"), hz("D4")], d + 1.0, 1400, .2, 1.4), M["g_land"], .34, 0, .6)
if has("g_lip", "g_drop") and M["g_drop"] - M["g_lip"] > .9: mix.add(heartbeat(), M["g_lip"] + .25, .5, 0, .15)
if has("g_drop"):
    mix.add(boom(1.6, 90, 40, .2), M["g_drop"], .6, 0, .4); mix.add(strings([hz("F3"), hz("A3"), hz("C4"), hz("F4")], 3.4, 3000, .05, 1.4), M["g_drop"], .42, 0, .6)
    for i, n in enumerate(["F4", "A4", "C5", "F5"]): mix.add(piano(hz(n), 3), M["g_drop"] + i * .125, .4, 0, .6)
if has("score2"): mix.add(taiko(1.1, 100, 48), M["score2"], .9, 0, .4); mix.add(boom(), M["score2"], .7, 0, .4); mix.add(braam(hz("D2"), 2.6, 1000), M["score2"], .28, 0, .5)

# ---------------------------------------------------------------- scene 4: bowling
if has("bowl", "b_his"):
    groove(M["bowl"], M["b_his"], .95, claps=True, strs=False)
    t = M["bowl"]; k = 0
    while t < M["b_his"] - .05:
        root, chord = PROG[(k // 16) % 4]; mix.add(pluck(hz(chord[(k * 2) % 3]) * (4 if k % 8 in (3, 6) else 2), .2, 5000), t, .13, (-.5, .5)[k % 2], .45); t += BEAT / 2; k += 1
if has("b_strike"): mix.add(boom(), M["b_strike"], .9, 0, .4)
if has("b_his", "b_release"):
    mix.add(boom(3.0, 120, 26, .1), M["b_his"], .6, 0, .4); mix.add(drone(hz("D1"), M["b_release"] - M["b_his"] + 2.5, 260), M["b_his"], .2, 0, .3)
    t = M["b_his"] + .5
    while t < M["b_release"] - .3: mix.add(heartbeat(), t, .6, 0, .15); t += .9
if has("b_release", "black"):
    d = M["black"] - M["b_release"]; mix.add(riser(d, 150, 7000), M["b_release"], .7, 0, .4)
    n = 0; t = M["b_release"]
    while t < M["black"] - .08:                 # a drum roll that tightens toward the pins
        u = (t - M["b_release"]) / d; mix.add(taiko(.5, 120, 60), t, .25 + .5 * u, (-.3, .3)[n % 2], .25); t += max(.09, .5 * (1 - u) ** 1.3); n += 1
if has("title"):
    mix.add(revcym(1.2), M["title"] - 1.2, .5, 0, .5)
    mix.add(boom(3.2, 110, 28, .5), M["title"], 1.0, 0, .5); mix.add(braam(hz("D2"), 5.5, 1900), M["title"], .6, 0, .6); mix.add(taiko(1.2, 95, 45), M["title"], .9, 0, .4)
    mix.add(strings([hz("D3"), hz("F#3"), hz("A3"), hz("D4"), hz("A4")], 6.0, 3000, .05, 3.0), M["title"], .4, 0, .7)
if has("tag"):
    end = M.get("fin", TOTAL)
    mix.add(wind(end - M["tag"] + 1), M["tag"], .9, 0, .2, fade_in=1, fade_out=2)
    notes = [("D4", 0), ("F#4", .75), ("A4", 1.5), ("D5", 2.25), ("B4", 3.5), ("A4", 4.25), ("F#4", 5.0), ("A4", 6.0)]
    for n, off in notes:
        if M["tag"] + off < end - 1.5: mix.add(piano(hz(n), 4.5), M["tag"] + .4 + off, .5, 0, .7)
    mix.add(pad([hz("D3"), hz("A3"), hz("F#4")], min(8, end - M["tag"]), 1500, 2.0, 2.5), M["tag"] + .4, .22, 0, .6)
if has("end"):
    for n in ["D3", "A3", "D4", "F#4", "A4"]: mix.add(piano(hz(n), 6), M["end"], .42, 0, .8)
    mix.add(boom(2.4, 70, 32, .1), M["end"], .35, 0, .5)

os.makedirs(os.path.join(W, "stage"), exist_ok=True)
print(mix.render(os.path.join(W, "stage", "score.wav")))
