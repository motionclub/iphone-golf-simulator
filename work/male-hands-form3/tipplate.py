"""plate | FORM2 | FORM3 crops around the fingertips in the plate profile cameras.  py.sh tipplate.py out.png"""
import sys, numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import lockcam as L, asm3
from hlib import *
from sheetlib import font
R = W.parents[1]
pl = Image.open(R / 'ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('RGB')
def tip_center(npz, side, view):
    M = Mesh.from_npz(npz); V = M.V.astype(np.float64)
    # fingertip poles: the 4 vertices with the largest hand-local w on that side
    L_ = to_local(V, side); sel = np.nonzero((side * V[:, 0] > 0.3) & (V[:, 2] < 1.1) & (L_[:, 2] > 0.125))[0]       # distal ~5 cm of the fingers (thumb ends before w=0.125)
    P = V[sel]; px, py = L.project(P, view)
    return float(np.mean(px)), float(np.mean(py))
S0 = 14; BW, BH = 44, 34
rows = []
for nm, side, view, plate_c in (('LEFT profile (char L hand)', -1, 'left', (775, 209)), ('RIGHT profile (char R hand)', +1, 'right', (1088, 209))):
    tiles = [('PLATE', pl.crop((int(plate_c[0] - BW / 2), int(plate_c[1] - BH / 2), int(plate_c[0] + BW / 2), int(plate_c[1] + BH / 2))))]
    for tag, npz, img in (('FORM2', W / 'data/mesh_cur.npz', W / 'proof/it/base_plate' / f'{view}.png'), ('FORM3', W / 'data/cand_final.npz', W / 'proof/it/final_plate' / f'{view}.png')):
        cx, cy = tip_center(npz, side, view)
        tiles.append((tag, Image.open(img).convert('RGB').crop((int(cx - BW / 2), int(cy - BH / 2 + 2), int(cx + BW / 2), int(cy + BH / 2 + 2)))))
    tiles = [(t, i.resize((i.width * S0, i.height * S0), Image.LANCZOS)) for t, i in tiles]
    w, h = tiles[0][1].size
    row = Image.new('RGB', (w * 3 + 12, h + 28), (20, 20, 22))
    for k, (t, i) in enumerate(tiles):
        row.paste(i, (k * (w + 6), 28)); ImageDraw.Draw(row).text((k * (w + 6) + 6, 6), nm + '  -  ' + t, fill=(255, 230, 120), font=font(16))
    rows.append(row)
S = Image.new('RGB', (rows[0].width, sum(r.height for r in rows)))
y = 0
for r in rows: S.paste(r, (0, y)); y += r.height
S.save(sys.argv[1]); print(S.size)
