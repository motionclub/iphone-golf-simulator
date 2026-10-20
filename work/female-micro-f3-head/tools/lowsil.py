"""lower-face silhouette deviation (mm) plate vs render, per view: chamfer distance between mask boundaries inside a window.
python3 lowsil.py <render_dir> <tag> [json out]"""
import sys, json
import numpy as np
from PIL import Image
ROOT = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
sys.path.insert(0, ROOT + 'work/female-micro-f3-head/tools')
import fl
rd, tag = sys.argv[1], sys.argv[2]
UP = 3
src = Image.open(ROOT + 'ArtDir/hero/base_lock/female_head_detail.jpg').convert('RGB')
PAN = {'front': (85, 55, 430, 342), 'left': (440, 55, 800, 342), 'right': (830, 55, 1195, 342), 'q3L': (85, 385, 430, 656), 'q3R': (440, 385, 800, 656)}
# lower-face window in plate-panel rows (after UP) : rows between the lip and the collar/chin line  (fractions of panel height)
def rows_win(v, box):
    if v in ('front', 'left', 'right'):
        r0 = float(fl.rowz(1.490)) - box[1]; r1 = float(fl.rowz(1.4255 - 0.004)) - box[1] + 6
    elif v == 'q3L': r0 = 520 - box[1]; r1 = 563 + 2 - box[1]
    else: r0 = 520 - box[1]; r1 = 562 + 2 - box[1]
    return r0, r1
CWIN = {'front': (0.15, 0.85), 'left': (0.05, 0.62), 'right': (0.38, 0.95), 'q3L': (0.12, 0.88), 'q3R': (0.08, 0.88)}
def fgm(a):
    sat = a.max(axis=2) - a.min(axis=2); V = a.mean(axis=2)
    return ~((sat < 16) & (V > 150))
def boundary(m):
    m = m.astype(bool); e = np.zeros_like(m)
    e[1:-1, 1:-1] = m[1:-1, 1:-1] & ~(m[:-2, 1:-1] & m[2:, 1:-1] & m[1:-1, :-2] & m[1:-1, 2:])
    return e
res = {}
for v in ('front', 'left', 'right', 'q3L', 'q3R'):
    box = PAN[v]; pl = src.crop(box); w, h = pl.size; big = (w * UP, h * UP)
    pa = np.asarray(pl.resize(big, Image.LANCZOS)).astype(float)
    pm = fgm(pa)
    r = Image.open(f'{rd}/{tag}_{v}.png').convert('RGBA').resize(big, Image.LANCZOS)
    rm = np.asarray(r)[..., 3] > 127
    # skin-only plate mask for the neck/shoulders confusion: use plate fg but ignore the collar rows (window ends above the collar)
    rr0, rr1 = rows_win(v, box); c0, c1 = CWIN[v]; R0, R1, C0, C1 = int(rr0 * UP), int(rr1 * UP), int(c0 * big[0]), int(c1 * big[0])
    pb = boundary(pm)[R0:R1, C0:C1]; rb = boundary(rm)[R0:R1, C0:C1]
    py, px = np.nonzero(pb); ry, rx = np.nonzero(rb)
    mm_per_px = fl.K / UP * 1000.0
    if len(py) == 0 or len(ry) == 0: continue
    # nearest distances (brute force on subsampled sets)
    def nn(a, b):
        a = np.stack(a, 1).astype(float); b = np.stack(b, 1).astype(float)
        out = np.empty(len(a))
        for i in range(0, len(a), 500):
            d = np.sqrt(((a[i:i + 500, None, :] - b[None, :, :]) ** 2).sum(-1)); out[i:i + 500] = d.min(1)
        return out
    d1 = nn((py, px), (ry, rx)) * mm_per_px; d2 = nn((ry, rx), (py, px)) * mm_per_px
    res[v] = dict(plate_to_mesh_mean=float(d1.mean()), plate_to_mesh_p95=float(np.percentile(d1, 95)), plate_to_mesh_max=float(d1.max()), mesh_to_plate_mean=float(d2.mean()), mesh_to_plate_p95=float(np.percentile(d2, 95)), mesh_to_plate_max=float(d2.max()))
    print(f'{v:6s} plate->mesh mean {d1.mean():.2f} p95 {np.percentile(d1,95):.2f} max {d1.max():.2f} mm | mesh->plate mean {d2.mean():.2f} p95 {np.percentile(d2,95):.2f} max {d2.max():.2f} mm   (npix {len(py)}/{len(ry)})')
if len(sys.argv) > 3: json.dump(res, open(sys.argv[3], 'w'), indent=1)
