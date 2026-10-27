#!/usr/bin/env python3
"""Frame-to-frame flicker in a captured sequence (MenuBackgroundCapture seq_<shot>_<mode>/f000.png ...).

A pixel POPS at frame t when its luminance jumps by more than T (0-255) from t-1 to t AND jumps back by more than T from
t to t+1 (a blink: up-then-down or down-then-up). Smooth motion (a camera drift, wind sway) changes pixels one way for many
frames and does not count; aliasing shimmer, z-fighting, shadow acne and sparkle do.

  flicker.py <seq dir> <out prefix> [--mask mask.png] [--T 16]
Writes <out prefix>_heat.png (frame 0 with pop counts in red), <out prefix>.csv (pops per frame) and prints a summary line.
mask.png: white = pixels that count (e.g. buildings); default every pixel.
"""
import sys, glob, os, argparse
import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("seq"); ap.add_argument("out")
ap.add_argument("--mask"); ap.add_argument("--erode", type=int, default=2, help="shrink the mask by n px (a swaying tree crossing a wall edge is not the wall flickering)"); ap.add_argument("--T", type=float, default=16)
ap.add_argument("--min-region", type=int, default=1, help="ignore pixels that pop fewer than this many times")
a = ap.parse_args()

files = sorted(glob.glob(os.path.join(a.seq, "f*.png")))
assert len(files) >= 3, "need 3+ frames"
def lum(p):
    x = np.asarray(Image.open(p).convert("RGB"), dtype=np.float32)
    return x @ np.array([.2126, .7152, .0722], np.float32)
first = np.asarray(Image.open(files[0]).convert("RGB"))
mask = None
if a.mask:
    mask = np.asarray(Image.open(a.mask).convert("L")) > 127
    for _ in range(a.erode):
        m2 = mask.copy()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): m2 &= np.roll(np.roll(mask, dy, 0), dx, 1)
        mask = m2
prev2, prev = lum(files[0]), lum(files[1])
heat = np.zeros(prev.shape, np.int32)
rows = []
for i in range(2, len(files)):
    cur = lum(files[i])
    d1, d2 = prev - prev2, cur - prev
    pop = (np.abs(d1) > a.T) & (np.abs(d2) > a.T) & (np.sign(d1) != np.sign(d2))
    if mask is not None: pop &= mask
    heat += pop
    rows.append((i - 1, int(pop.sum()), float(np.abs(d2[mask] if mask is not None else d2).mean())))
    prev2, prev = prev, cur
with open(a.out + ".csv", "w") as f:
    f.write("frame,pops,mean_abs_diff\n")
    for r in rows: f.write("%d,%d,%.4f\n" % r)
counted = heat >= a.min_region
total = int(heat[counted].sum())
pix = int(counted.sum() if a.min_region > 1 else (heat > 0).sum())
# heat overlay: frame 0 darkened, pop pixels red (brighter = more pops), dilated 1 px so single pixels show at a glance
base = (first.astype(np.float32) * .55).astype(np.uint8)
h = np.clip(heat / max(1, np.percentile(heat[heat > 0], 95) if (heat > 0).any() else 1), 0, 1)
hd = h.copy()
for dy in (-1, 0, 1):
    for dx in (-1, 0, 1):
        hd = np.maximum(hd, np.roll(np.roll(h, dy, 0), dx, 1))
over = base.copy()
sel = hd > 0
over[sel] = (np.stack([255 * np.ones_like(hd), 40 * (1 - hd), 40 * (1 - hd)], -1)[sel]).astype(np.uint8)
Image.fromarray(over).save(a.out + "_heat.png")
per = [r[1] for r in rows]
print("%s: frames %d  pops total %d  max/frame %d  mean/frame %.1f  pixels that ever popped %d" % (os.path.basename(a.seq.rstrip("/")), len(files), total, max(per), np.mean(per), pix))
