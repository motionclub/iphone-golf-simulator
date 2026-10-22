"""Row-wise silhouette runs (mm, relative to the camera centre) of the plate target mask vs candidate renders, back/front views.
python3 silrows.py view zlo zhi step tag...   (view: bald_back|bald_front|left|right)"""
import sys, json, numpy as np
from pathlib import Path
from PIL import Image
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work'); M = R / 'male-silhouette'
CAM = {c['name']: c for c in json.load(open(M / 'reference-cameras.json'))['views']}
def mask(p):
    a = np.array(Image.open(p).convert('RGBA'))
    return (a[:, :, 3] > 127) if a[:, :, 3].min() < 250 else (a[:, :, 0] > 127)
def runs(row):
    d = np.diff(np.concatenate([[0], row.astype(int), [0]])); s = np.where(d == 1)[0]; e = np.where(d == -1)[0]; return list(zip(s, e))
def row_runs(m, view, z):
    c = CAM[view]; r = int(round(c['sole_y'] - z / c['metres_per_pixel'])); mm = c['metres_per_pixel'] * 1000
    return [((s - c['centre_x']) * mm, (e - c['centre_x']) * mm) for s, e in runs(m[r])]
if __name__ == '__main__':
    view, zlo, zhi, st = sys.argv[1], *map(float, sys.argv[2:5]); tags = sys.argv[5:]
    T = mask(M / f'{view}_target.png'); Ms = {t: mask(Path(f'r/sil_{t}/{view}.png')) for t in tags}
    for z in np.arange(zlo, zhi + 1e-9, st):
        s = f'z {z:.3f} PLATE ' + ' '.join(f'[{a:6.1f},{b:6.1f}]' for a, b in row_runs(T, view, z))
        for t in tags: s += f' | {t} ' + ' '.join(f'[{a:6.1f},{b:6.1f}]' for a, b in row_runs(Ms[t], view, z))
        print(s)
