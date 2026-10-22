"""glow_classes.py <still> <shot name> <out.png> : colour the integrator's glow classes (vertical = red, rung = blue, blob = green, other = yellow) over a darkened still"""
import sys, json, os
import numpy as np
from PIL import Image
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/proof')
import measure as M
meta = {s["name"]: s for s in json.load(open(M.P + "/masks/9/masks_meta.json"))["shots"]}
still, n, out = sys.argv[1:4]
sh = M.Shot(n, still, M.P + "/masks/9", meta[n]); sh.full = None; sh.px = sh.still
p = sh.px; m = sh.idmask("basalt"); hh, ss, vv = M.rgb2hsv(p)
glow = m & (hh >= 5) & (hh <= 35) & (ss >= 0.55) & (vv >= 0.40)
comps = M.components(glow, 6)
img = (p * 0.35).astype(np.uint8)
cnt = dict(v=0, r=0, b=0, o=0); big = []
for k, ys, xs in comps:
    el, ang, bh, bw = M.comp_shape(ys, xs)
    if el >= 2.5 and ang <= 35: c = (255, 40, 40); cnt['v'] += k
    elif el >= 2.5 and ang >= 55: c = (60, 120, 255); cnt['r'] += k
    elif el < 2.0: c = (40, 230, 80); cnt['b'] += k
    else: c = (250, 230, 40); cnt['o'] += k
    img[ys, xs] = c
    if k >= 80: big.append((k, round(el, 1), round(ang), bh, bw))
tot = sum(cnt.values()); print({a: round(v / tot, 2) for a, v in cnt.items()}, 'n comps', len(comps)); print('largest', sorted(big, reverse=True)[:12])
Image.fromarray(img).save(out)
