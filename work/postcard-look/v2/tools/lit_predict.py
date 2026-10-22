#!/usr/bin/env python3
"""lit_predict.py -- predict the Game-view (lit) mean colour of a ground texture for each postcard hole.

Plain python3 + Pillow (no numpy); Pillow is only needed to read PNG/JPG files (the generator imports this module and
passes pixel lists, so it also runs under Blender's python). Reads the light table straight from the Unity sources, so it
follows the Unity owner's edits:
  Unity/Assets/Scripts/Course/GolfAtmosphere.cs  (key / fill / rim / trilight ambient per hole)
  Unity/Assets/Scripts/Course/GolfLook.cs        (HoleTint; the table tint is .94 for the three grass materials)
Post-processing does NOT render in this project (RUNTIME.md section 7): no tone mapper, so the frame is
        sRGB( clip( linear lighting x albedo x tint , 1 ) ).

MODEL (URP Lit, linear colour space, flat ground, normal up -- N.L = sin(elevation), independent of the camera):
    L_c   = key_c*I_key*sin(el_key) + fill_c*I_fill*sin(el_fill) + rim_c*I_rim*sin(el_rim) + ambient_sky_c     (c = R,G,B; light colours sRGB -> linear)
    first : out_c = clip( lin(albedo_c) * lin(tint_c) * L_c )                      per texel, then sRGB-encoded, then averaged
    cal   : out_c = clip( lin(albedo_c) * lin(tint_c) * L_c * CAL_MUL_c + CAL_ADD_c )
  * clipping is per texel BEFORE averaging (the Game view clips per pixel; a clipped channel pulls the hue toward yellow);
  * the mean of the encoded texels is what the stills' 16x16 patch means are compared with.
CALIBRATION: work/postcard-look/runtime/repair/probe_1/hole0{8,9,10}_tee_probe.jpg are REAL Game-view renders (Unity batch,
HeroBaseStudioURP, real lights, real hole lights and tints) of the OLD LK_GREEN tee box (Green_C mean (116,181,73)), measured in the
box (100,1000)-(800,1500) (the lower third of the phone frame). Model vs render, per channel in linear light:
    Needle (137,204,87) vs (145,202,88)   Split (121,210,77) vs (127,209,86)   Crater (122,196,35) vs (127,192,48)
i.e. the model is within 6-13 sRGB levels; R is low by ~11 % (a warm excess: ambient/specular not modelled), G ~ -3 %, and B has an
additive +.01 (sky reflection at the grazing view). `cal` applies those constants (CAL_MUL / CAL_ADD, geometric/arithmetic mean of the
three holes). `--recalibrate` re-derives them from the probe images. Validation on a different surface: see v2/tex/TEX_V2_NOTES.
Both modes are reported; a GATE needs BOTH inside the hue band, so the verdict does not depend on which model is right.
v3 2026-10-04: a THIRD mode, `game`, fitted to REAL Game-view measurements of the INSTALLED grass textures (GolfLookSmoke GRASS_HUE_LIT,
work/postcard-look/v2/runtime/smoke_s16.txt, HeroBaseStudioURP, 10 patches on 3 holes): out_c = clip(lin(albedo_c) x lin(tint_c) x L_c x GAME_MUL_c
+ GAME_ADD[hole]_c). The fit gives MUL ~ 1 and a per-hole ADDITIVE term of .02-.06 linear (sky reflection / specular, which does not depend on
albedo x tint). It reproduces every measured patch hue within 1.6 degrees (first-principles: within 4.5) and RGB within ~8 levels. A gate needs
first, cal AND game inside the band. `--recalibrate-game` re-derives GAME_MUL / GAME_ADD from GAME_MEAS.

usage (from anywhere):
  python3 lit_predict.py [--look DIR] [--tints-json FILE] [--solve] [--json OUT] [--size 128]
      --look DIR       folder with Fairway_C.png Green_C.png Rough_C.png Scrub_C.png (default Unity/Assets/Resources/Course/Look)
      --tints-json F   {"9": {"Fairway": [r,g,b], ...}, "10": {...}}  per-hole tints to use INSTEAD of GolfLook.cs's (the recommendation)
      --solve          solve per-hole tints that land each material on the stills' colour (prints a JSON you can pass to --tints-json)
exit 1 when something is outside its hue band (with the tints actually used).
"""
import argparse
import colorsys
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
ATMO = os.path.join(ROOT, 'Unity/Assets/Scripts/Course/GolfAtmosphere.cs')
LOOKCS = os.path.join(ROOT, 'Unity/Assets/Scripts/Course/GolfLook.cs')
DEFAULT_LOOK = os.path.join(ROOT, 'Unity/Assets/Resources/Course/Look')
PROBE_DIR = os.path.join(ROOT, 'work/postcard-look/runtime/repair/probe_1')

HOLE_NAMES = {8: 'Needle', 9: 'Split', 10: 'Crater'}
MATS = ('Fairway', 'Green', 'Rough')
# hue bands (degrees) the brief asks for after golf lighting; Scrub is informational (Split ridge scrub in the still: h46)
BANDS = {'Fairway': (64.0, 73.0), 'Green': (64.0, 73.0), 'Rough': (58.0, 72.0), 'Scrub': (40.0, 58.0)}
# the stills' 16x16 patch means (sRGB), measured by the lead: the solver's targets
STILL_TARGET = {
    8: {'Fairway': (172, 186, 66), 'Green': (171, 181, 64), 'Rough': (135, 134, 57)},
    9: {'Fairway': (133, 152, 52), 'Green': (154, 173, 75), 'Rough': (105, 120, 46), 'Scrub': (122, 111, 75)},
    10: {'Fairway': (136, 161, 26), 'Green': (156, 173, 28), 'Rough': (100, 122, 20)},
}
# first-principles vs the three probe renders (see docstring)
CAL_MUL = (1.029, 1.039, 1.101)      # v8 2026-10-05: --recalibrate-cal on the 10 real Game-view patches of GAME_MEAS (rms 5.5 levels per channel); v7 (probe renders of the old tee box under the OLD atmosphere): (1.108, 0.971, 1.0)
CAL_ADD = (0.0340, 0.0209, 0.0162)   # v7: (0.0, 0.0, 0.011)
# tints that were on the old probes (needed only by --recalibrate)
PROBE_TINT = {8: (.94, .94, .94), 9: (.76, .84, .72), 10: (.90, 1.15, .62)}
PROBE_OLD_GREEN_MEAN = (116, 181, 73)
# REAL Game-view means (sRGB 0..255) of the installed albedos under the tints that were in GolfLook.cs at that moment
# (smoke_s16.txt, [HeroBaseStudioURP] GRASS_HUE_LIT / INFO lines, 2026-10-04 10:18) and those tints
GAME_MEAS = {(8, 'Fairway'): (169, 186, 68), (8, 'Green'): (177, 191, 75), (8, 'Rough'): (142, 142, 58),
             (9, 'Fairway'): (148, 166, 68), (9, 'Green'): (160, 177, 76), (9, 'Rough'): (126, 134, 62), (9, 'Scrub'): (121, 114, 77),
             (10, 'Fairway'): (166, 188, 43), (10, 'Green'): (166, 184, 45), (10, 'Rough'): (114, 117, 37)}
GAME_MEAS_TINT = {(8, 'Fairway'): (.855, .87, .87), (8, 'Green'): (.865, .88, .88), (8, 'Rough'): (.94, .94, .94),
                  (9, 'Fairway'): (.69, .66, .66), (9, 'Green'): (.72, .70, .70), (9, 'Rough'): (.77, .76, .77), (9, 'Scrub'): (.82, .82, .86),
                  (10, 'Fairway'): (.95, 1.13, .62), (10, 'Green'): (.95, 1.13, .62), (10, 'Rough'): (.93, 1.09, .62)}
# v8 2026-10-05 (area T repair round 3): the two tables above are the REAL Game-view means of the installed albedos [HeroBaseStudioURP, GolfLookSmoke GRASS_HUE_LIT / INFO lines of v2/tex/v8/clone_smoke_cand3.txt] under the tints in
# GolfLook.cs at that moment.  The owner's repair round 3 moved the Crater atmosphere (a neutral ambient / fog: the equator and the ground bounce no longer add an ember red to the shaded grass) and re-tuned the three Crater tints
# (.90,1.15,.62 -> .95,1.13,.62), so the 2026-10-04 constants below predicted Crater's green 5-10 levels too bright (hue 63.2 'calibrated' against the measured 68): refitted here (derive_game_calibration + derive_cal_from_game).
# The v7 tables are in lit_predict.py.before_v8.
GAME_MUL = (1.025, 1.043, 0.902)      # v8 2026-10-05: --recalibrate-game on the table above (v7: (1.005, 0.992, 0.887) and ADD {8: (0.0581, 0.0303, 0.0203), 9: (0.0351, 0.0276, 0.0275), 10: (0.0482, 0.0254, 0.0158)})
GAME_ADD = {8: (0.0671, 0.0356, 0.0212), 9: (0.0357, 0.0245, 0.0272), 10: (0.0040, -0.0025, 0.0156)}

FALLBACK_LIGHTS = {
    8: dict(key=((1, .86, .66), 2.3, 30), fill=((.80, .88, 1), .8, 35), rim=((1, .78, .55), .5, 10), sky=(.42, .58, .86)),
    9: dict(key=((1, .95, .86), 2.3, 42), fill=((.74, .85, 1), .8, 40), rim=((1, .92, .80), .3, 14), sky=(.42, .58, .86)),
    10: dict(key=((1, .80, .58), 2.3, 32), fill=((.62, .55, .90), .55, 35), rim=((1, .8, .58), 0, 0), sky=(.34, .24, .40)),
}
FALLBACK_TINT = {(9, 'Fairway'): (.76, .84, .72), (9, 'Green'): (.76, .84, .72), (9, 'Rough'): (.80, .86, .76),
                 (10, 'Fairway'): (.90, 1.15, .62), (10, 'Green'): (.90, 1.15, .62), (10, 'Rough'): (.90, 1.10, .62)}
TABLE_TINT = (.94, .94, .94)


def s2l(x):
    return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4


def l2s(x):
    x = min(1.0, max(0.0, x))
    return x * 12.92 if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055


def hsv_deg(rgb01):
    h, s, v = colorsys.rgb_to_hsv(*[min(1.0, max(0.0, c)) for c in rgb01])
    return h * 360.0, s, v


# ----------------------------------------------------------------------------------------------- parse the C# tables
def _floats(s):
    return [float(x) for x in re.findall(r'[-+]?\d*\.?\d+', s)]


def _color(block, field):
    m = re.search(field + r'\s*=\s*new\(\s*([^)]*)\)', block)
    if not m:
        return None
    v = _floats(m.group(1))
    return tuple(v[:3]) if len(v) >= 3 else None


def _num(block, field):
    m = re.search(field + r'\s*=\s*(-?[\d.]+)f?', block)
    return float(m.group(1)) if m else None


def parse_lights():
    out = {}
    try:
        txt = open(ATMO, encoding='utf-8').read()
        for hole in (8, 9, 10):
            m = re.search(r'\[%d\]\s*=\s*new Look\s*\{(.*?)\n\s*\},' % hole, txt, re.S)
            if not m:
                raise ValueError('hole %d block' % hole)
            b = m.group(1)
            d = dict(
                key=(_color(b, 'SunColor') or (1, .9, .76), _num(b, 'SunIntensity') or 2.3, _num(b, 'SunElevation')),
                fill=(_color(b, 'FillColor') or (.84, .9, 1), _num(b, 'FillIntensity') or .8, _num(b, 'FillElevation')),
                rim=(_color(b, 'RimColor') or (1, .8, .58), _num(b, 'RimIntensity') or 0.0, _num(b, 'RimElevation') or 0.0),
                sky=_color(b, 'AmbientSky'))
            if d['key'][2] is None or d['fill'][2] is None or d['sky'] is None:
                raise ValueError('hole %d fields' % hole)
            out[hole] = d
        out['_src'] = 'GolfAtmosphere.cs'
    except Exception as ex:  # noqa
        print('WARN: could not parse %s (%s): using the hard-coded table' % (ATMO, ex), file=sys.stderr)
        out = dict(FALLBACK_LIGHTS); out['_src'] = 'fallback'
    return out


def parse_tints():
    tint = {}
    try:
        txt = open(LOOKCS, encoding='utf-8').read()
        for m in re.finditer(r'\[\((\d+),\s*"LK_(\w+)"\)\]\s*=\s*new Color\(([^)]*)\)', txt):
            hole, name = int(m.group(1)), m.group(2).capitalize()
            v = _floats(m.group(3))
            if name in ('Fairway', 'Green', 'Rough', 'Scrub') and len(v) >= 3:
                tint[(hole, name)] = tuple(v[:3])
        for nm in ('LK_FAIRWAY', 'LK_GREEN', 'LK_ROUGH', 'LK_SCRUB'):
            line = [l for l in txt.splitlines() if '["%s"]' % nm in l]
            if line and 'Tint' in line[0]:
                print('WARN: %s has a Table Tint override; this tool assumes .94' % nm, file=sys.stderr)
        tint['_src'] = 'GolfLook.cs'
    except Exception as ex:  # noqa
        print('WARN: could not parse %s (%s): using the hard-coded tints' % (LOOKCS, ex), file=sys.stderr)
        tint = dict(FALLBACK_TINT); tint['_src'] = 'fallback'
    return tint


def hole_light_linear(d):
    L = [0.0, 0.0, 0.0]
    for name in ('key', 'fill', 'rim'):
        col, inten, el = d[name]
        if inten <= 0:
            continue
        f = inten * math.sin(math.radians(el))
        for c in range(3):
            L[c] += s2l(col[c]) * f
    for c in range(3):
        L[c] += s2l(d['sky'][c])
    return L


# ----------------------------------------------------------------------------------------------- texture sampling
def load_samples(path, size):
    """size x size nearest samples of an 8-bit RGB(A) image as a list of (r,g,b)."""
    from PIL import Image          # lazy: the generator (Blender python, no Pillow) uses predict_samples only
    im = Image.open(path).convert('RGB')
    w, h = im.size
    px = im.load()
    pts = []
    for j in range(size):
        y = int((j + .5) * h / size)
        for i in range(size):
            x = int((i + .5) * w / size)
            pts.append(px[x, y])
    return pts


_LUT = [s2l(i / 255.0) for i in range(256)]


def predict_samples(samples, L, tint, mode='first', hole=None):
    """mean sRGB-encoded colour (0..1) over the texels with a per-texel clip, and the fraction of texels with a clipped channel.
    mode 'first' | 'cal' | 'game' (needs `hole`: its additive term)."""
    t = [s2l(max(0.0, tint[c])) for c in range(3)]
    if mode == 'game':
        mul = GAME_MUL; add = GAME_ADD[hole]
    else:
        mul = CAL_MUL if mode == 'cal' else (1.0, 1.0, 1.0)
        add = CAL_ADD if mode == 'cal' else (0.0, 0.0, 0.0)
    k = [L[c] * t[c] * mul[c] for c in range(3)]
    acc = [0.0, 0.0, 0.0]
    clipped = 0
    for p in samples:
        hit = False
        for c in range(3):
            v = _LUT[int(p[c])] * k[c] + add[c]
            if v > 1.0:
                hit = True
            acc[c] += l2s(v)
        clipped += hit
    n = float(len(samples))
    return [a / n for a in acc], clipped / n


def solve_tint(samples, L, target_rgb255, start=(.8, .8, .8), hole=None):
    """per-channel tint (sRGB, not clamped above 1) that puts the MID model (mean of the first-principles, calibrated and, when `hole` is
    given, the Game-view-fitted `game` model) on `target`."""
    tgt = [t / 255.0 for t in target_rgb255]
    tint = list(start)
    for _ in range(60):
        pf, _c = predict_samples(samples, L, tint, 'first')
        pc, _c = predict_samples(samples, L, tint, 'cal')
        pg = predict_samples(samples, L, tint, 'game', hole)[0] if hole else None
        for c in range(3):
            mid = (pf[c] + pc[c] + pg[c]) / 3.0 if pg else 0.5 * (pf[c] + pc[c])
            # secant on the encoded value: out ~ tint^(1/2.4)-ish, damp the update
            if mid > 1e-4:
                tint[c] = max(0.05, min(1.6, tint[c] * (tgt[c] / mid) ** 1.6))
    return tuple(round(x, 2) for x in tint)


def derive_calibration():
    """re-derive CAL_MUL / CAL_ADD from the three tee probes (needs Pillow and the OLD Green_C mean)."""
    from PIL import Image
    lights = parse_lights()
    rows = []
    for hole in (8, 9, 10):
        im = Image.open(os.path.join(PROBE_DIR, 'hole%02d_tee_probe.jpg' % hole)).convert('RGB').crop((100, 1000, 800, 1500))
        px = list(im.getdata())
        meas = [sum(p[c] for p in px) / len(px) / 255.0 for c in range(3)]
        L = hole_light_linear(lights[hole])
        pr = [l2s(s2l(PROBE_OLD_GREEN_MEAN[c] / 255.0) * s2l(PROBE_TINT[hole][c]) * L[c]) for c in range(3)]
        rows.append((hole, meas, pr))
    mul = []
    for c in range(3):
        r = [s2l(m[c]) / max(s2l(p[c]), 1e-6) for _h, m, p in rows]
        mul.append(math.exp(sum(math.log(x) for x in r) / 3))
    add = [sum(s2l(m[c]) - s2l(p[c]) for _h, m, p in rows) / 3 for c in range(3)]
    return rows, mul, add


def derive_game_calibration(look=DEFAULT_LOOK, size=64):
    """re-fit GAME_MUL (global, per channel) and GAME_ADD (per hole, per channel) to GAME_MEAS under GAME_MEAS_TINT. The albedos in `look` must be
    the ones that were installed when GAME_MEAS was measured (Fairway/Green/Rough/Scrub_C as of 2026-10-04 10:14)."""
    lights = parse_lights(); Ls = {h: hole_light_linear(lights[h]) for h in (8, 9, 10)}
    smp = {nm: load_samples(os.path.join(look, nm + '_C.png'), size) for nm in ('Fairway', 'Green', 'Rough', 'Scrub')}

    def pred(nm, h, mul, add):
        t = [s2l(GAME_MEAS_TINT[(h, nm)][c]) for c in range(3)]
        k = [Ls[h][c] * t[c] * mul[c] for c in range(3)]
        acc = [0.0, 0.0, 0.0]
        for p in smp[nm]:
            for c in range(3):
                acc[c] += l2s(_LUT[int(p[c])] * k[c] + add[c])
        return [a / len(smp[nm]) for a in acc]

    def err_hole(h, mul, add):
        e = 0.0
        for (hh, nm), m in GAME_MEAS.items():
            if hh == h:
                p = pred(nm, h, mul, add)
                e += sum((p[c] * 255 - m[c]) ** 2 for c in range(3))
        return e

    def golden(f, lo, hi, it=40):
        g = (math.sqrt(5) - 1) / 2; a, b = lo, hi
        c = b - g * (b - a); d = a + g * (b - a); fc = f(c); fd = f(d)
        for _ in range(it):
            if fc < fd:
                b, d, fd = d, c, fc; c = b - g * (b - a); fc = f(c)
            else:
                a, c, fc = c, d, fd; d = a + g * (b - a); fd = f(d)
        return (a + b) / 2

    mul = [1.0, 1.0, 1.0]; add = {h: [0.0, 0.0, 0.0] for h in (8, 9, 10)}
    for _ in range(6):
        for h in (8, 9, 10):
            for c in range(3):
                def f(x, h=h, c=c):
                    a = list(add[h]); a[c] = x
                    return err_hole(h, mul, a)
                add[h][c] = golden(f, -0.1, 0.4)
        for c in range(3):
            def f(x, c=c):
                m = list(mul); m[c] = x
                return sum(err_hole(h, m, add[h]) for h in (8, 9, 10))
            mul[c] = golden(f, 0.6, 1.6)
    rows = [((h, nm), m, pred(nm, h, mul, add[h])) for (h, nm), m in GAME_MEAS.items()]
    return mul, add, rows


def derive_cal_from_game(look=DEFAULT_LOOK, size=64):
    """v8: re-fit the 'calibrated' mode's GLOBAL constants (CAL_MUL per channel, CAL_ADD per channel, the same for every hole: fewer parameters than the per-hole `game` fit) to the 10 real Game-view patches of GAME_MEAS."""
    lights = parse_lights(); Ls = {h: hole_light_linear(lights[h]) for h in (8, 9, 10)}
    smp = {nm: load_samples(os.path.join(look, nm + '_C.png'), size) for nm in ('Fairway', 'Green', 'Rough', 'Scrub')}

    def err(mul, add):
        e = 0.0
        for (h, nm), m in GAME_MEAS.items():
            t = [s2l(GAME_MEAS_TINT[(h, nm)][c]) for c in range(3)]
            k = [Ls[h][c] * t[c] * mul[c] for c in range(3)]
            acc = [0.0, 0.0, 0.0]
            for p_ in smp[nm]:
                for c in range(3):
                    acc[c] += l2s(_LUT[int(p_[c])] * k[c] + add[c])
            e += sum((acc[c] / len(smp[nm]) * 255 - m[c]) ** 2 for c in range(3))
        return e

    def golden(f, lo, hi, it=30):
        g = (math.sqrt(5) - 1) / 2; a, b = lo, hi
        c = b - g * (b - a); d = a + g * (b - a); fc = f(c); fd = f(d)
        for _ in range(it):
            if fc < fd:
                b, d, fd = d, c, fc; c = b - g * (b - a); fc = f(c)
            else:
                a, c, fc = c, d, fd; d = a + g * (b - a); fd = f(d)
        return (a + b) / 2
    mul = [1.0, 1.0, 1.0]; add = [0.0, 0.0, 0.0]
    for _ in range(5):
        for c in range(3):
            add[c] = golden(lambda x, c=c: err(mul, [x if i == c else add[i] for i in range(3)]), -0.1, 0.3)
        for c in range(3):
            mul[c] = golden(lambda x, c=c: err([x if i == c else mul[i] for i in range(3)], add), 0.6, 1.6)
    return mul, add, err(mul, add)


# ----------------------------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--look', default=DEFAULT_LOOK)
    ap.add_argument('--tints-json', default=None)
    ap.add_argument('--solve', action='store_true')
    ap.add_argument('--recalibrate', action='store_true')
    ap.add_argument('--recalibrate-game', action='store_true')
    ap.add_argument('--recalibrate-cal', action='store_true')
    ap.add_argument('--size', type=int, default=128)
    ap.add_argument('--json', default=None)
    a = ap.parse_args()
    lights = parse_lights(); cs_tints = parse_tints()
    print('light table from %s, tints from %s' % (lights['_src'], cs_tints['_src']))
    Ls = {h: hole_light_linear(lights[h]) for h in (8, 9, 10)}
    for h in (8, 9, 10):
        print('  hole %d %-6s linear light on flat ground (R,G,B) = (%.3f, %.3f, %.3f)' % (h, HOLE_NAMES[h], *Ls[h]))
    if a.recalibrate:
        rows, mul, add = derive_calibration()
        for h, m, p in rows:
            print('  probe hole %d: render (%d,%d,%d) vs model (%d,%d,%d)' % (h, *[round(x * 255) for x in m], *[round(x * 255) for x in p]))
        print('  derived CAL_MUL (%.3f,%.3f,%.3f) CAL_ADD (%.3f,%.3f,%.3f); in use (%s) (%s)' % (*mul, *add, CAL_MUL, CAL_ADD))
    if getattr(a, 'recalibrate_cal', False):
        mul, add, e = derive_cal_from_game(a.look)
        print('CAL_MUL = (%.3f, %.3f, %.3f)\nCAL_ADD = (%.4f, %.4f, %.4f)   # rms %.2f levels per channel over the 10 patches' % (*mul, *add, math.sqrt(e / 30)))
        return 0
    if a.recalibrate_game:
        mul, add, rows = derive_game_calibration(a.look)
        for (h, nm), m, p in rows:
            print('  patch hole %d %-7s Game view (%d,%d,%d) hue %.1f   fit (%d,%d,%d) hue %.1f' % (h, nm, *m, hsv_deg([x / 255 for x in m])[0], *[round(x * 255) for x in p], hsv_deg(p)[0]))
        print('  derived GAME_MUL (%.3f,%.3f,%.3f)' % tuple(mul))
        for h in (8, 9, 10):
            print('  derived GAME_ADD[%d] (%.4f,%.4f,%.4f)' % (h, *add[h]))
        print('  in use: GAME_MUL %s GAME_ADD %s' % (GAME_MUL, GAME_ADD))
    tints = dict(cs_tints)
    used_src = 'GolfLook.cs'
    if a.tints_json:
        with open(a.tints_json) as f:
            rec = json.load(f)
        for hs, d in rec.items():
            for nm, v in d.items():
                tints[(int(hs), nm)] = tuple(v)
        used_src = a.tints_json
    tint_of = lambda hole, nm: tints.get((hole, nm), TABLE_TINT)
    print('tints used: %s (table .94 where no HoleTint entry)' % used_src)
    samples = {}
    for nm in MATS + ('Scrub',):
        p = os.path.join(a.look, nm + '_C.png')
        if os.path.exists(p):
            samples[nm] = load_samples(p, a.size)
    res = {}; bad = 0
    if a.solve:
        sol = {}
        for hole in (9, 10):
            sol[str(hole)] = {}
            for nm in samples:
                if nm in STILL_TARGET[hole]:
                    sol[str(hole)][nm] = list(solve_tint(samples[nm], Ls[hole], STILL_TARGET[hole][nm], hole=hole))
        # Needle is solved too, for information: the table tint (.94) is what Needle uses
        needle = {nm: list(solve_tint(samples[nm], Ls[8], STILL_TARGET[8][nm], hole=8)) for nm in samples if nm in STILL_TARGET[8]}
        print('SOLVED_TINTS_JSON ' + json.dumps(sol))
        print('(Needle, information only; the table .94 applies) ' + json.dumps(needle))
        return 0
    print()
    print('%-8s %-7s %-17s | first-principles rgb        hue    S    V clip | calibrated rgb            hue    S    V clip | game-fit rgb              hue    S    V clip | band    verdict' % ('material', 'hole', 'tint'))
    for nm, smp in samples.items():
        mean_alb = [sum(p[c] for p in smp) / len(smp) / 255.0 for c in range(3)]
        ah = hsv_deg(mean_alb)
        res[nm] = dict(albedo_mean=[round(x * 255, 1) for x in mean_alb], albedo_hsv=[round(ah[0], 1), round(ah[1], 3), round(ah[2], 3)], holes={})
        print('%s_C albedo mean (%d,%d,%d) hue %.1f S %.3f V %.3f' % (nm, *[round(x * 255) for x in mean_alb], *ah))
        for hole in (8, 9, 10):
            if nm == 'Scrub' and hole != 9:
                continue
            tn = tint_of(hole, nm)
            pf, cf = predict_samples(smp, Ls[hole], tn, 'first'); hf = hsv_deg(pf)
            pc, cc = predict_samples(smp, Ls[hole], tn, 'cal'); hc = hsv_deg(pc)
            pg, cg = predict_samples(smp, Ls[hole], tn, 'game', hole); hg = hsv_deg(pg)
            lo, hi = BANDS[nm]
            ok = lo <= hf[0] <= hi and lo <= hc[0] <= hi and lo <= hg[0] <= hi
            bad += (not ok)
            res[nm]['holes'][HOLE_NAMES[hole]] = dict(
                tint=list(tn), in_band=bool(ok),
                first=dict(rgb=[round(x * 255) for x in pf], hue=round(hf[0], 1), S=round(hf[1], 3), V=round(hf[2], 3), clip=round(cf, 3)),
                cal=dict(rgb=[round(x * 255) for x in pc], hue=round(hc[0], 1), S=round(hc[1], 3), V=round(hc[2], 3), clip=round(cc, 3)),
                game=dict(rgb=[round(x * 255) for x in pg], hue=round(hg[0], 1), S=round(hg[1], 3), V=round(hg[2], 3), clip=round(cg, 3)))
            print('%-8s %-7s (%.2f,%.2f,%.2f)  | (%3d,%3d,%3d) %5.1f %.2f %.2f %.2f | (%3d,%3d,%3d) %5.1f %.2f %.2f %.2f | (%3d,%3d,%3d) %5.1f %.2f %.2f %.2f | %2.0f..%2.0f  %s' % (
                nm, HOLE_NAMES[hole], *tn, *[round(x * 255) for x in pf], hf[0], hf[1], hf[2], cf,
                *[round(x * 255) for x in pc], hc[0], hc[1], hc[2], cc, *[round(x * 255) for x in pg], hg[0], hg[1], hg[2], cg, lo, hi, 'PASS' if ok else 'FAIL'))
    print()
    for nm, r in res.items():
        for hn, row in r['holes'].items():
            print('GATE: GRASS_HUE_PREDICTED %s_C on %s %s - hue first-principles %.1f / calibrated %.1f / game-fit %.1f, S %.2f/%.2f/%.2f, V %.2f/%.2f/%.2f, band %.0f..%.0f, tint (%.2f,%.2f,%.2f) from %s' % (
                nm, hn, 'PASS' if row['in_band'] else 'FAIL', row['first']['hue'], row['cal']['hue'], row['game']['hue'], row['first']['S'], row['cal']['S'], row['game']['S'],
                row['first']['V'], row['cal']['V'], row['game']['V'], *BANDS[nm], *row['tint'], used_src))
    if a.json:
        with open(a.json, 'w') as f:
            json.dump(res, f, indent=1)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
