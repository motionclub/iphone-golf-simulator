"""Torso/leg widths through the centre line (the run of figure pixels containing the body axis), sheet 15 vs our Unity body render,
both scaled to crown..sole = 1.  Also shoulder width (widest run at 17-22 %), upper-arm and forearm thickness.  python3 tools/body_cmp2.py <dir>"""
import sys, numpy as np
from PIL import Image
SHEET = '../../ArtDir/style/alive/male-reference-pack-2026-10-17/sheets/15-body-cardinal-no-clothes.png'
A = np.asarray(Image.open(SHEET).convert('RGB')).astype(int)
REF = {'front': (40, 140, 560, 1180, 300), 'right90': (580, 140, 1000, 1180, 760), 'back': (1010, 140, 1540, 1180, 1275)}   # panel box + axis column
def fig(a, bg): return np.abs(a - bg).sum(-1) > 30
def runs_at(m, r, axis):
    row = m[r]; c = axis
    if not row[c]:
        nz = np.nonzero(row)[0]
        if not len(nz): return None
        c = nz[np.argmin(np.abs(nz - axis))]
    a = c; b = c
    while a > 0 and row[a - 1]: a -= 1
    while b < len(row) - 1 and row[b + 1]: b += 1
    return a, b
def table(m, axis, top, bot, label, fr):
    out = []
    for f in fr:
        r = int(top + f * (bot - top)); ab = runs_at(m, r, axis)
        out.append((ab[1] - ab[0]) / (bot - top) if ab else np.nan)
    return np.array(out)
d = sys.argv[1]
fr = np.array([.13, .17, .20, .24, .28, .33, .38, .43, .48, .53, .58, .65, .72, .80, .88, .94])
names = ['neck', 'trap', 'shoulder', 'chest', 'midchest', 'waist-hi', 'waist', 'hip-hi', 'hip/crotch', 'thigh-top', 'thigh', 'above knee', 'knee', 'calf', 'shin', 'ankle']
for view in ('front', 'right90'):
    x0, y0, x1, y1, ax = REF[view]; a = A[y0:y1, x0:x1]; bg = np.median(a[:15].reshape(-1, 3), 0); rm = fig(a, bg)
    rows = np.nonzero(rm[:, ax - x0 - 60: ax - x0 + 60].any(1))[0]; rt, rb = rows[0], rows[-1]
    o = np.asarray(Image.open(f'{d}/body_{view}.png').convert('RGB')).astype(int); om = fig(o, np.array([227, 227, 222]))
    orows = np.nonzero(om.any(1))[0]; ot, ob = orows[0], orows[-1]
    oax = int(np.nonzero(om[int(ot + .45 * (ob - ot))])[0].mean())
    rw = table(rm, ax - x0, rt, rb, 'ref', fr); ow = table(om, oax, ot, ob, 'ours', fr)
    print(view, f'ref height px {rb-rt}  ours {ob-ot}')
    for n, f, o_, r_ in zip(names, fr, ow, rw): print(f'  {n:11s} {f*100:4.0f}%  ours {o_:.3f}  ref {r_:.3f}  diff {100*(o_-r_)/r_:+5.0f}%')
