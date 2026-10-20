"""silhouette overlay (pink = mesh only, green = plate only, grey = both) in the left/right plate cameras around the arm+hand.
py.sh profsil.py out.png tag1 [tag2...]"""
import sys, numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import sil3, lockcam as L
from sheetlib import font
out = sys.argv[1]; tags = sys.argv[2:]
BOX = {'left': (700, 60, 880, 250), 'right': (1000, 60, 1180, 250)}
tiles = []
for t in tags:
    path = W / 'data/mesh_cur.npz' if t == 'base' else W / f'data/cand_{t}.npz'
    V, polys, T = sil3.mesh_from(path)
    for v, (x0, y0, x1, y1) in BOX.items():
        m = L.raster(V, T, v, roi=(x0, y0, x1, y1), ss=3); p = sil3.plate(v)[y0:y1, x0:x1]
        im = np.zeros(m.shape + (3,), np.uint8); im[...] = (24, 24, 26)
        im[m & p] = (150, 150, 150); im[m & ~p] = (235, 90, 150); im[p & ~m] = (70, 220, 150)
        I = Image.fromarray(im).resize((m.shape[1] * 4, m.shape[0] * 4), Image.NEAREST)
        ImageDraw.Draw(I).text((4, 2), f'{t} {v} xor {int((m ^ p).sum())}', fill=(255, 230, 120), font=font(16)); tiles.append(I)
w, h = tiles[0].size
S = Image.new('RGB', (w * 2, h * len(tags)))
for i, I in enumerate(tiles): S.paste(I, ((i % 2) * w, (i // 2) * h))
S.save(out); print(out, S.size)
