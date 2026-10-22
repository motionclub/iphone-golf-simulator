# measure glow-free u zones of the CURRENT Basalt_E (G = max channel > 0.2, the stage gate's definition) + Basalt_C slice luminance
import numpy as np, bpy, sys, os
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
L = REPO + "/Unity/Assets/Resources/Course/Look/"
def load(n):
    im = bpy.data.images.load(L + n, check_existing=False); w, h = im.size
    px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px)
    return px.reshape(h, w, 4)[:, :, :3], w, h
E, w, h = load("Basalt_E.png"); C, _, _ = load("Basalt_C.png")
G = E.max(axis=2) > 0.2
colfrac = G.mean(axis=0)                     # share of v rows glowing per u column
print("glow mean", G.mean())
# zones: maximal runs of u columns with colfrac == 0 (with 2 px margin)
free = colfrac < 1e-9
# dilate glow by 2 px both sides (a window edge must not touch glow)
bad = ~free
k = 2
bd = bad.copy()
for s in range(1, k + 1):
    bd |= np.roll(bad, s) | np.roll(bad, -s)
zones = []; s = None
# circular: rotate so we start at a bad column
start = int(np.argmax(bd))
idx = (np.arange(w) + start) % w
for j, i in enumerate(idx):
    if not bd[i] and s is None: s = j
    if bd[i] and s is not None:
        zones.append(((start + s) / w, (start + j) / w)); s = None
if s is not None: zones.append(((start + s) / w, (start + w) / w))
print("glow-free zones (u0,u1) (u1 may exceed 1 = wraps):")
Cl = C.mean(axis=2)
Z = []
for a, b in zones:
    i0, i1 = int(round(a * w)), int(round(b * w))
    cols = [(i % w) for i in range(i0, i1)]
    lum = float(Cl[:, cols].mean())
    print("  (%.3f, %.3f) width %.3f  Basalt_C mean lum %.3f" % (a, b, b - a, lum)); Z.append((a, b, lum))
print("texture Basalt_C mean lum %.3f" % float(Cl.mean()))
# glow lines: connected u-ranges where colfrac > 0 (not dilated), plus their core (colfrac >= 0.25 of max)
on = colfrac > 0
runs = []; s = None
for i in range(w):
    if on[i] and s is None: s = i
    if (not on[i]) and s is not None: runs.append((s, i - 1)); s = None
if s is not None: runs.append((s, w - 1))
print("glow u-runs (any glow):", [(round(a / w, 3), round(b / w, 3), round(float(colfrac[a:b + 1].max()), 2)) for a, b in runs])
core = colfrac > 0.12
runs = []; s = None
for i in range(w):
    if core[i] and s is None: s = i
    if (not core[i]) and s is not None: runs.append((s, i - 1)); s = None
if s is not None: runs.append((s, w - 1))
print("glow core runs (colfrac > .12):", [(round(a / w, 3), round(b / w, 3), round(float(colfrac[a:b + 1].max()), 2)) for a, b in runs])
# the same measurement for the OLD tile (v4, before this pass)
old = REPO + "/work/postcard-look/v2/tex/v5/before/Basalt_E.png"
im = bpy.data.images.load(old, check_existing=False); px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px)
Go = px.reshape(h, w, 4)[:, :, :3].max(axis=2) > 0.2
print("OLD glow mean", Go.mean(), "old colfrac>0 runs:",)
cf = Go.mean(axis=0); on = cf > 0; runs = []; s = None
for i in range(w):
    if on[i] and s is None: s = i
    if (not on[i]) and s is not None: runs.append((s, i - 1)); s = None
if s is not None: runs.append((s, w - 1))
print([(round(a / w, 3), round(b / w, 3), round(float(cf[a:b + 1].max()), 2)) for a, b in runs])
