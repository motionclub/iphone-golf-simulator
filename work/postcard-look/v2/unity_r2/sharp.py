#!/usr/bin/env python3
"""Ground sharpness of Game-view stills (system python3, Pillow only).
usage: sharp.py <dir> [<dir2> ...]    prints, per shot and window: lap (std of a 3x3 Laplacian of luminance), gx / gy (rms of the 1-px horizontal / vertical difference), gx/gy.
Windows (900x1600 stills, y down): NEAR = x 200..700, y 1100..1500 (the ground 2-3 yd in front of the camera); MID = x 200..700, y 550..950;
LAVARIM_UL = x 0..200, y 740..830 (the review's upper-left streak window of hole10_3_lavarim).
The windows that are not ground (water, lava, walls, the ball) are excluded by a hue mask: only pixels with hue 50..90 deg, S >= .35 count (grass).
"""
import sys, os, math
from PIL import Image, ImageFilter, ImageChops

WIN = {"NEAR": (200, 1100, 700, 1500), "MID": (200, 550, 700, 950), "LAVARIM_UL": (0, 740, 200, 830)}
LAP = ImageFilter.Kernel((3, 3), [0, -1, 0, -1, 4, -1, 0, -1, 0], scale=1, offset=128)

def hsv_mask(im):
    h, s, v = im.convert("HSV").split()
    # PIL hue 0..255 = 0..360 deg: 50..90 deg -> 35..64
    hm = h.point(lambda x: 255 if 35 <= x <= 64 else 0)
    sm = s.point(lambda x: 255 if x >= 90 else 0)
    return ImageChops.multiply(hm, sm).point(lambda x: 1 if x > 0 else 0)

def stat(chan, mask, box):
    c = chan.crop(box); m = mask.crop(box)
    px = list(c.getdata()); mk = list(m.getdata())
    sel = [p for p, k in zip(px, mk) if k]
    if len(sel) < 400: return None
    mean = sum(sel) / len(sel)
    return math.sqrt(sum((p - mean) ** 2 for p in sel) / len(sel)), len(sel) / len(px)

def measure(path):
    im = Image.open(path).convert("RGB"); g = im.convert("L"); mask = hsv_mask(im)
    lap = g.filter(LAP)
    w, h = g.size
    gx = ImageChops.difference(g, ImageChops.offset(g, 1, 0))
    gy = ImageChops.difference(g, ImageChops.offset(g, 0, 1))
    out = {}
    for k, box in WIN.items():
        a = stat(lap, mask, box)
        if a is None: out[k] = None; continue
        def rms(ch):
            c = ch.crop(box); m = mask.crop(box)
            sel = [p for p, kk in zip(c.getdata(), m.getdata()) if kk]
            return math.sqrt(sum(p * p for p in sel) / len(sel))
        ex, ey = rms(gx), rms(gy)
        out[k] = (a[0], ex, ey, ex / ey if ey else 0, a[1])
    return out

if __name__ == "__main__":
    for d in sys.argv[1:]:
        print("##", d)
        for f in sorted(os.listdir(d)):
            if not f.endswith(".png") or not f.startswith("hole"): continue
            r = measure(os.path.join(d, f))
            print(f, "  ".join("%s lap %.2f gx %.2f gy %.2f gx/gy %.2f grass %.0f%%" % ((k,) + v[:4] + (v[4] * 100,)) if v else "%s -" % k for k, v in r.items()))
