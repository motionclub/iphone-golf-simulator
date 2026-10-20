"""Visualise a displacement field h (mm along normals) as a coloured vertex scatter over the plate (front + q3L).  python3.13 hmap.py <tag> [vmax]"""
import sys; sys.path.insert(0, '.')
from pmo import *
tag = sys.argv[1]; vmax = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
h = np.load(f'data/h_{tag}.npy'); V0, F, loops = load('e1')
sel = np.where(np.abs(h) > 0)[0] if (np.abs(h) > 0).any() else np.array([], int)
Nb = None
tiles = []
for view, crop, z5 in (('front', (140, 90, 330, 300), 3), ('q3L', (5 + 90, 390 + 40, 5 + 330, 390 + 270), 3)):
    im = PLATE.crop(crop).resize(((crop[2] - crop[0]) * z5, (crop[3] - crop[1]) * z5), Image.LANCZOS)
    im = Image.blend(im, Image.new('RGB', im.size, (128, 128, 128)), 0.35)
    d = ImageDraw.Draw(im)
    if view == 'front': col, row = colx(V0[:, 0]), rowz(V0[:, 2]); vis = V0[:, 1] < -0.04
    else: col, row, dep = q3_project(V0, 'q3L'); vis = (V0[:, 1] < -0.02) & (V0[:, 0] > -0.01)
    for i in sel:
        if not vis[i]: continue
        X = (col[i] - crop[0]) * z5; Y = (row[i] - crop[1]) * z5
        t = np.clip(h[i] / vmax, -1, 1)
        c = (int(255 * (1 if t > 0 else 1 + t)), int(255 * (1 - abs(t))), int(255 * (1 if t < 0 else 1 - t)))
        d.ellipse((X - 2, Y - 2, X + 2, Y + 2), fill=c)
    tiles.append(im)
W = sum(t.width for t in tiles) + 10
sheet = Image.new('RGB', (W, max(t.height for t in tiles)), (0, 0, 0)); x = 0
for t in tiles: sheet.paste(t, (x, 0)); x += t.width + 10
sheet.save(f'r/hmap_{tag}.png'); print(sheet.size, 'h range', h.min(), h.max())
