"""Section plots of mesh variants: python3.13 secplot.py <out.png> <axis x|y|z> <val_mm,val_mm,...> <tag:V.npy> ...   (right half only, mm)
axis x: plane x=val  -> plot (y horizontal, z vertical) ; axis y: plane y=val -> (x, z) ; axis z: plane z=val -> (x, y)"""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from j_edit import *
from PIL import Image, ImageDraw
out = sys.argv[1]; axis = {'x': 0, 'y': 1, 'z': 2}[sys.argv[2]]; vals = [float(v) for v in sys.argv[3].split(',')]
items = [a.split(':', 1) for a in sys.argv[4:]]
F = pickle.load(open(W / 'data/F_start.pkl', 'rb')); E = edges_of(F)
PAL = [(255, 255, 255), (255, 120, 60), (90, 220, 120), (90, 160, 255), (255, 230, 60), (220, 110, 255)]
R = dict(x=((-170, 40), (1420, 1570)), y=((0, 100), (1420, 1580)), z=((0, 90), (-150, 30)))[sys.argv[2]]   # (horizontal range mm, vertical range mm)
import os
if os.environ.get('SEC_R'):
    a, b, c, d = [float(v) for v in os.environ['SEC_R'].split(',')]; R = ((a, b), (c, d))
if axis == 0: H_, V_ = 1, 2
elif axis == 1: H_, V_ = 0, 2
else: H_, V_ = 0, 1
S = float(__import__('os').environ.get('SEC_S', 5.0)); Wd = int((R[0][1] - R[0][0]) * S); Hd = int((R[1][1] - R[1][0]) * S)
pan = []
for v in vals:
    im = Image.new('RGB', (Wd, Hd), (22, 22, 26)); d = ImageDraw.Draw(im)
    X = lambda a: (a * 1000 - R[0][0]) * S; Y = lambda b: Hd - (b * 1000 - R[1][0]) * S
    for g in range(int(R[0][0] // 10 * 10), int(R[0][1]) + 1, 10): d.line((X(g / 1000), 0, X(g / 1000), Hd), fill=(48, 48, 56) if g % 50 else (90, 90, 100))
    for g in range(int(R[1][0] // 10 * 10), int(R[1][1]) + 1, 10): d.line((0, Y(g / 1000), Wd, Y(g / 1000)), fill=(48, 48, 56) if g % 50 else (90, 90, 100))
    for i, (tag, path) in enumerate(items):
        V = np.load(path)
        sel = (V[:, 0] > -0.003) if axis != 0 else (np.ones(len(V), bool))
        P = plane_section(V, E, axis, v / 1000.0, None)
        if axis == 1: P = P[P[:, 0] > -0.002]
        if axis == 2: P = P[P[:, 0] > -0.002]
        col = PAL[i % len(PAL)]
        for p in P: d.ellipse((X(p[H_]) - 1.3, Y(p[V_]) - 1.3, X(p[H_]) + 1.3, Y(p[V_]) + 1.3), fill=col)
        d.text((6, 6 + 12 * i), tag, fill=col)
    d.text((Wd - 90, 6), f'{sys.argv[2]}={v:g} mm', fill=(255, 255, 0)); pan.append(im)
cols = min(3, len(pan)); rows = (len(pan) + cols - 1) // cols
sheet = Image.new('RGB', (Wd * cols + 4 * (cols - 1), Hd * rows + 4 * (rows - 1)), (0, 0, 0))
for i, im in enumerate(pan): sheet.paste(im, ((i % cols) * (Wd + 4), (i // cols) * (Hd + 4)))
sheet.save(out); print(out, sheet.size)
