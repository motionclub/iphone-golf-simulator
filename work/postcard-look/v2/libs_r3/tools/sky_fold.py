"""Where does the TennisSky mirror fold (panorama x = 0) fall on screen for the hole08_arch Game camera? (Unity world yards, camera pos/look from hole08/landmarks.json, fov 60, 900x1600.)
GolfAtmosphere: _Arc 180, _Heading = tee->pin heading + SkyHeadingOffset (Needle 45); TennisSky.shader: heading = atan2(d.x, d.z) - _Heading + _Arc/2, x = mod(heading, 2 Arc), u = triangle wave.
The fold (derivative discontinuity of u -> wrong mip on a 1-2 px column) is where x == 0 or x == Arc. Also: the vertical hairline columns detected in a Game still (pale 1-2 px runs in smooth sky)."""
import math, sys
import numpy as np
from PIL import Image
pos = np.array([-10.94, 13.21, 302.93]); look = np.array([-28.7, 11.81, 317.0])
f = look - pos; f /= np.linalg.norm(f)
right = np.cross(np.array([0, 1, 0.]), f); right /= np.linalg.norm(right)
up = np.cross(f, right)
if up[1] < 0: up = -up
W, H = 900, 1600
th = math.tan(math.radians(30)); tw = th * W / H
heading0 = math.degrees(math.atan2(-6 - 0, 340 - 0)); Hd = heading0 + 45; Arc = 180
def fold_x(y):
    best = None
    for x in np.arange(0, W, 0.05):
        d = f + ((x / W) * 2 - 1) * tw * right + (1 - (y / H) * 2) * th * up
        xx = (math.degrees(math.atan2(d[0], d[2])) - Hd + Arc / 2) % (2 * Arc)
        dd = min(abs(xx), abs(xx - Arc), abs(xx - 2 * Arc))
        if best is None or dd < best[0]: best = (dd, x)
    return best[1]
print("tee->pin heading %.3f deg, _Heading %.3f, fold at panorama x=0 / x=Arc" % (heading0, Hd))
for y in (170, 300, 375, 560, 600, 650, 690):
    print("screen row %4d: fold column x = %.2f" % (y, fold_x(y)))
if len(sys.argv) > 1:
    a = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(int)
    res = []
    for x in range(6, W - 6):
        c = a[:, x]; l = a[:, x - 4:x - 1].mean(1); r = a[:, x + 2:x + 5].mean(1); base = (l + r) / 2
        smooth = (np.abs(l - r).sum(1) < 6); d = np.abs(c - base).sum(1); m = smooth & (d > 10) & (d < 60)
        best = run = 0; bs = st = 0
        for y in range(H):
            if m[y]:
                if run == 0: st = y
                run += 1
                if run > best: best, bs = run, st
            else: run = 0
        if best >= 40: res.append((best, x, bs))
    res.sort(reverse=True); print("hairline runs in", sys.argv[1], "(length, x, first row):", res[:6])
