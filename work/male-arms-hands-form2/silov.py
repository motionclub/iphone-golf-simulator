"""Overlay of plate mask vs candidate mask in the hand ROIs: pink = mesh only, green = plate only, grey = both.  py silov.py <tag...> -> proof/it/<tag>_silov.png"""
import numpy as np, sys
from pathlib import Path
from PIL import Image, ImageDraw
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import sil3, lockcam as L
from sheetlib import font
def overlay(V, T, sel, sc=5):
    tiles = []
    for v, rois in sil3.ROIS.items():
        for nm, (x0, y0, x1, y1) in rois:
            m = L.raster(V, T, v, sel=sel, roi=(x0, y0, x1, y1), ss=3); p = sil3.plate(v)[y0:y1, x0:x1]
            im = np.zeros(m.shape + (3,), np.uint8); im[...] = (24, 24, 26)
            im[m & p] = (150, 150, 150); im[m & ~p] = (235, 90, 150); im[p & ~m] = (70, 220, 150)
            I = Image.fromarray(im).resize((m.shape[1] * sc, m.shape[0] * sc), Image.NEAREST)
            d = ImageDraw.Draw(I); x = int((m ^ p).sum()); d.text((4, 2), f'{v} {nm} xor {x}', fill=(255, 230, 120), font=font(14))
            tiles.append(I)
    return tiles
if __name__ == '__main__':
    rows = []
    for nm in sys.argv[1:]:
        path = W / 'data/mesh_cur.npz' if nm == 'base' else W / f'data/cand_{nm}.npz'
        V, polys, T = sil3.mesh_from(path)
        arm = (np.abs(V[:, 0]) > 0.2) & (V[:, 2] > 0.78) & (V[:, 2] < 1.40); sel = arm[T].all(1)
        tiles = overlay(V, T, sel)
        cw = max(t.width for t in tiles); ch = max(t.height for t in tiles)
        S = Image.new('RGB', (4 * cw, 2 * ch + 24), (18, 18, 20)); ImageDraw.Draw(S).text((6, 3), nm, fill=(255, 255, 255), font=font(16))
        for i, t in enumerate(tiles): S.paste(t, ((i % 4) * cw, 24 + (i // 4) * ch))
        out = W / f'proof/it/{nm}_silov.png'; S.save(out); print(out, S.size)
