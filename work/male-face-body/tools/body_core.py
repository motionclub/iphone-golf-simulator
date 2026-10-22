"""Core silhouette (per row, the run of figure pixels through the body axis = torso, neck, head, legs; arms excluded where they separate),
resampled to height 1000 and centred; mismatch = XOR area / our area.  python3 tools/body_core.py <dir>"""
import sys, numpy as np
from PIL import Image
def fig(a, bg, t=35): return np.abs(a - bg).sum(-1) > t
def core(m, axis_frac=.45, legs_from=.50):
    rows = np.nonzero(m.any(1))[0]; t, b = rows[0], rows[-1]
    ax = int(np.nonzero(m[int(t + axis_frac * (b - t))])[0].mean()); H = 1000; out = np.zeros((H + 1, 800), bool)
    for k in range(H + 1):
        r = int(t + k / H * (b - t)); row = m[r]
        cols = []
        if k / H < legs_from:
            c = ax if row[ax] else (np.nonzero(row)[0][np.argmin(np.abs(np.nonzero(row)[0] - ax))] if row.any() else None)
            if c is None: continue
            a = c; e = c
            while a > 0 and row[a - 1]: a -= 1
            while e < len(row) - 1 and row[e + 1]: e += 1
            cols = [(a, e)]
        else:                                   # legs: the two runs nearest the axis
            nz = np.nonzero(np.diff(np.r_[0, row.astype(int), 0]))[0].reshape(-1, 2); nz[:, 1] -= 1
            d = np.abs((nz[:, 0] + nz[:, 1]) / 2 - ax); cols = [tuple(x) for x in nz[np.argsort(d)[:2]]]
        s = 1000 / (b - t)
        for a, e in cols: out[k, max(0, int(400 + (a - ax) * s)):min(799, int(400 + (e - ax) * s)) + 1] = True
    return out
def load(path, box, bg=None):
    a = np.asarray(Image.open(path).convert('RGB')).astype(int)
    if box: a = a[box[1]:box[3], box[0]:box[2]]
    if bg is None: bg = np.median(np.concatenate([a[:15].reshape(-1, 3), a[-15:].reshape(-1, 3)]), 0)
    return fig(a, bg)
d = sys.argv[1]
SH = '../../ArtDir/style/alive/male-reference-pack-2026-10-17/sheets/15-body-cardinal-no-clothes.png'
PL = '../../ArtDir/hero/base_lock/male_body_plain.jpg'
refs = {'front': [('sheet15', SH, (40, 140, 560, 1180)), ('plate', PL, (80, 60, 640, 700))], 'back': [('sheet15', SH, (1010, 140, 1540, 1180)), ('plate', PL, (660, 60, 1200, 700))]}
for view, rl in refs.items():
    om = core(load(f'{d}/body_{view}.png', None, np.array([227, 227, 222])))
    for name, path, box in rl:
        rm = core(load(path, box)); x = (om ^ rm).sum() / om.sum(); iou = (om & rm).sum() / (om | rm).sum()
        img = np.full((1001, 800, 3), 235, np.uint8); img[rm] = (120, 200, 120); img[om] = (230, 120, 120); img[om & rm] = (160, 160, 160)
        Image.fromarray(img).resize((320, 400)).save(f'eval/core_{view}_{name}.png')
        print(f'{view:5s} vs {name:7s}: mismatch {x*100:5.1f}% of our core area, IoU {iou:.3f}')
