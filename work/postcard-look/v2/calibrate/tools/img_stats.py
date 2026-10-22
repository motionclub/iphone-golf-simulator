#!/usr/bin/env python3
"""Pixel statistics of a Game-view PNG/JPG crop: mean RGB/HSV, share of pixels with a clipped channel (>=250, ==255), hue histogram.
usage: img_stats.py <image> <x0> <y0> <x1> <y1>   (pixel box, y down from the top)   [--json]
Pure Pillow (no numpy): HSV via Image.convert('HSV')."""
import sys, json, colorsys
from PIL import Image

def stats(path, box):
    im = Image.open(path).convert('RGB').crop(box)
    n = im.size[0] * im.size[1]
    r, g, b = im.split()
    hr, hg, hb = r.histogram(), g.histogram(), b.histogram()
    mean = tuple(sum(i * c for i, c in enumerate(h)) / n for h in (hr, hg, hb))
    px = im.getdata()
    clip250 = clip255 = 0
    for p in px:
        m = max(p)
        if m >= 250: clip250 += 1
        if m >= 255: clip255 += 1
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in mean))
    return {"file": path, "box": list(box), "n": n, "mean_rgb": [round(c, 1) for c in mean], "hue": round(h * 360, 1), "S": round(s, 3), "V": round(v, 3),
            "clip250_pct": round(100 * clip250 / n, 2), "clip255_pct": round(100 * clip255 / n, 2)}

if __name__ == '__main__':
    a = sys.argv[1:]
    out = stats(a[0], tuple(int(x) for x in a[1:5]))
    print(json.dumps(out) if '--json' in a else out)
