"""Fingertip silhouettes (side = n-w plane, plan = a-w plane) of candidates, finger k (default 1), R hand.
py.sh tipplot.py out.png name1 '<params json>' name2 '<params json>' ...   (optional env K=finger, WIN=window mm)"""
import sys, os, json, numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import asm3
from hlib import *
out = sys.argv[1]; specs = [(sys.argv[i], json.loads(sys.argv[i + 1])) for i in range(2, len(sys.argv), 2)]
K = int(os.environ.get('K', '1')); WIN = float(os.environ.get('WIN', '36')); SC = 11.0
def verts_of(params, k=K):
    Vn, polys, si = asm3.assemble(params, verbose=False)
    m = si[+1]['mapping']; info = si[+1]['info']; rows, C = info['fin_rows'][k]
    Lp = lambda vid: to_local(Vn[[m[vid]]], +1)[0] * 1000
    pts = np.array([Lp(v) for r in rows for v in r] + [Lp(C)]); pole = Lp(C)
    return pts, pole, [np.array([Lp(v) for v in r]) for r in rows]
def outline(pts, ci, w0, w1, step=0.25):
    lo = []; hi = []
    for w in np.arange(w0, w1, step):
        m = (pts[:, 2] >= w) & (pts[:, 2] < w + step)
        if m.sum() == 0: continue
        lo.append((pts[m, ci].min(), w)); hi.append((pts[m, ci].max(), w))
    return lo, hi
PH = int(WIN * SC) + 50
tiles = []
for name, prm in specs:
    pts, pole, rows = verts_of(prm)
    w1 = pole[2] + 1.0; w0 = w1 - WIN
    im = Image.new('RGB', (860, PH), (24, 24, 28)); d = ImageDraw.Draw(im)
    for ox, ci, lab in ((220, 1, 'SIDE  n (dorsal = left)'), (640, 0, 'PLAN  a')):
        d.text((ox - 110, 6), f'{name}   {lab}', fill=(255, 230, 120))
        sel = pts[(pts[:, 2] > w0)]
        c0 = 0.5 * (np.median(sel[:, ci]))
        c0 = np.median(pts[pts[:, 2] > pole[2] - 6, ci])
        T = lambda x, w: (ox + (x - c0) * SC, 30 + (w - w0) * SC)
        # ring polylines
        for r in rows:
            if r[:, 2].mean() < w0: continue
            q = [T(p[ci], p[2]) for p in r]; q.append(q[0]); d.line(q, fill=(70, 90, 130), width=1)
        lo, hi = outline(pts, ci, w0, w1)
        for ln in (lo, hi):
            d.line([T(x, w) for x, w in ln], fill=(255, 210, 90), width=2)
        # scale bar 5 mm
        d.line([(ox - 100, PH - 14), (ox - 100 + 5 * SC, PH - 14)], fill=(200, 200, 200), width=2); d.text((ox - 100, PH - 28), '5 mm', fill=(200, 200, 200))
    tiles.append(im)
S = Image.new('RGB', (860 * len(tiles), PH))
for i, t in enumerate(tiles): S.paste(t, (860 * i, 0))
S.save(out); print(out, S.size)
