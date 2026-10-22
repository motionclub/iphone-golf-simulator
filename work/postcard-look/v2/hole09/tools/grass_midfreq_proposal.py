"""grass_midfreq_proposal.py - PROPOSAL ONLY (writes nothing under Unity/ and edits no library): how much mid-frequency tone variation Fairway_C / Green_C need to clear the
LOOK_FILES floor of postcard_look_verify.py (windows of 1/16 tile, luminance sd >= 0.03 in 90 % of them), what that does to the mean colour / hue the grass calibration used, and a
drop-in candidate PNG pair that passes it.

    Blender -b --factory-startup --python grass_midfreq_proposal.py -- --out DIR [--amp 0.06]

The real fix belongs to the texture owner (blender/scripts/golf_look_textures.py regenerates the PNGs) or to the lead (the 0.03 / 90 % floor is the lead's number). This script only
measures with the verifier's own window statistic (re-implemented here, same formula: stored sRGB values, Rec.709 luminance, non-overlapping win x win windows, win = side / 16),
and writes the candidates to DIR so they can be reviewed. The candidate is a multiplicative, zero-mean, band-limited (6-24 px wavelength) periodic noise on RGB (tiling is kept
because the noise is built in the frequency domain; the hue is kept because the three channels get the same factor).
"""
import json
import math
import os
import sys

import numpy as np
import bpy

A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(n, d=None):
    return A[A.index(n) + 1] if n in A and A.index(n) + 1 < len(A) else d


OUT = os.path.abspath(opt("--out"))
os.makedirs(OUT, exist_ok=True)
LOOK = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "Unity", "Assets", "Resources", "Course", "Look"))


def load(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    arr = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(arr)
    bpy.data.images.remove(img)
    return arr.reshape(h, w, 4)


def save(path, px):
    h, w = px.shape[:2]
    img = bpy.data.images.new("tmp", w, h, alpha=True, float_buffer=False)
    img.colorspace_settings.name = "sRGB"
    img.pixels.foreach_set(np.clip(px, 0, 1).astype(np.float32).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def lum709(px):
    return px[..., 0] * 0.2126 + px[..., 1] * 0.7152 + px[..., 2] * 0.0722


def window_sd(a, win):
    H, W = a.shape
    h2, w2 = H // win, W // win
    return a[:h2 * win, :w2 * win].reshape(h2, win, w2, win).std(axis=(1, 3)).ravel()


def pool(a, k):
    if k <= 1:
        return a
    H, W = a.shape[:2]
    H2, W2 = H // k, W // k
    return a[:H2 * k, :W2 * k].reshape(H2, k, W2, k).mean(axis=(1, 3))


def stats(px):
    lum = lum709(px)
    win = max(4, int(round(min(lum.shape) / 16.0)))
    k = max(1, win // 8)
    raw = window_sd(lum, win)
    blur = window_sd(pool(lum, k), max(2, win // k))
    return dict(win=win, frac_raw=float((raw >= 0.03).mean()), frac_blur=float((blur >= 0.4 * 0.03).mean()), p10=float(np.percentile(raw, 10)),
                median=float(np.median(raw)), gsd=float(lum.std()))


def hue_sat_val(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn + 1e-12
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60.0
    return h, d / (mx + 1e-12), mx


def band_noise(shape, lo_px, hi_px, seed):
    """Periodic zero-mean unit-sd noise with energy between wavelengths lo_px and hi_px (frequency-domain gaussian band)."""
    rg = np.random.default_rng(seed)
    n = rg.standard_normal(shape)
    F = np.fft.fft2(n)
    fy = np.fft.fftfreq(shape[0])[:, None]
    fx = np.fft.fftfreq(shape[1])[None, :]
    f = np.sqrt(fx * fx + fy * fy)
    f_hi, f_lo = 1.0 / lo_px, 1.0 / hi_px                      # short wavelength = high frequency
    G = np.exp(-0.5 * (f / f_hi) ** 2) * (1.0 - np.exp(-0.5 * (f / f_lo) ** 2))
    out = np.real(np.fft.ifft2(F * G))
    return (out - out.mean()) / out.std()


res = {}
for name, seed in (("Fairway_C", 11), ("Green_C", 12)):
    px = load(os.path.join(LOOK, name + ".png"))
    base = stats(px)
    h0, s0, v0 = hue_sat_val(px[..., :3])
    row = dict(base=base, mean_rgb=[float(x) for x in px[..., :3].mean((0, 1))], hue=float(h0.mean()), tries=[])
    noise = band_noise(px.shape[:2], 6.0, 24.0, seed)
    best = None
    for amp in (0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.10):
        q = px.copy()
        q[..., :3] = np.clip(px[..., :3] * (1.0 + amp * noise[..., None]), 0, 1)
        st = stats(q)
        h1, _, _ = hue_sat_val(q[..., :3])
        t = dict(amp=amp, **st, mean_rgb=[float(x) for x in q[..., :3].mean((0, 1))], hue=float(h1.mean()))
        row["tries"].append(t)
        if best is None and st["frac_raw"] >= 0.90 and st["frac_blur"] >= 0.90:
            best = (amp, q)
    if best:
        row["chosen_amp"] = best[0]
        save(os.path.join(OUT, name + "_midfreq_candidate.png"), best[1])
    res[name] = row
    print(name, json.dumps(dict(base=base, chosen=row.get("chosen_amp"), tries=[(t["amp"], round(t["frac_raw"], 2), round(t["frac_blur"], 2), round(t["p10"], 4)) for t in row["tries"]]))[:900], flush=True)
json.dump(res, open(os.path.join(OUT, "grass_midfreq_proposal.json"), "w"), indent=1)
