"""Fit yaw (+ screen shift) of the four 3/4 plate figures with whole-figure silhouette IoU (current mesh).  py.sh fit34.py"""
import sys, json, time, numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import lockcam as L
from hlib import Mesh
R = W.parents[1]
plate = np.array(Image.open(R / 'ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('L')).astype(int)
pm = plate > 62
M = Mesh.from_npz(W / 'data/mesh_cur.npz'); V = M.V.astype(np.float64); T = M.tris()
SC = 1280 / 7.452054977416992
FIG = {'34FL': (40, 330), '34FR': (350, 640), '34BL': (660, 950), '34BR': (960, 1250)}
Y0, Y1 = 376, 677
def render(theta_deg, ox, oy):
    th = np.radians(theta_deg); c, s = np.cos(th), np.sin(th)
    X = V[:, 0] * c - V[:, 1] * s; Yv = V[:, 0] * s + V[:, 1] * c
    px = ox + X * SC; py = oy - V[:, 2] * SC
    im = Image.new('L', (1280, 720), 0); d = ImageDraw.Draw(im)
    P = np.stack([px[T[:, 0]], py[T[:, 0]], px[T[:, 1]], py[T[:, 1]], px[T[:, 2]], py[T[:, 2]]], 1)
    for p in P: d.polygon([(p[0], p[1]), (p[2], p[3]), (p[4], p[5])], fill=255)
    return np.array(im) > 127
def best_shift(m, p, rng=30):
    # integer shift maximising IoU by brute-force over a window (coarse using FFT correlation)
    F = np.fft.rfft2(m.astype(float)); G = np.fft.rfft2(p.astype(float))
    cc = np.fft.irfft2(np.conj(F) * G, s=m.shape)          # cc[dy,dx] = sum m(x) p(x+d)
    best = None
    for dy in range(-rng, rng + 1):
        for dx in range(-rng, rng + 1):
            v = cc[dy % m.shape[0], dx % m.shape[1]]
            if best is None or v > best[0]: best = (v, dx, dy)
    return best
res = {}
t0 = time.time()
for name, (x0, x1) in FIG.items():
    p = np.zeros_like(pm); p[Y0:Y1, x0:x1] = pm[Y0:Y1, x0:x1]
    cx = 0.5 * (x0 + x1); cy_foot = 672
    out = []
    for sign in (+1, -1):
        for th in range(10, 81, 5):
            ox = cx; oy = cy_foot - 0 + 0
            m = render(sign * th, ox, oy)
            m2 = np.zeros_like(m); m2[Y0 - 40:Y1 + 40, x0 - 40:x1 + 40] = m[Y0 - 40:Y1 + 40, x0 - 40:x1 + 40]
            v, dx, dy = best_shift(m2, p, 25)
            ms = np.roll(np.roll(m2, dy, 0), dx, 1)
            iou = (ms & p).sum() / max((ms | p).sum(), 1)
            out.append((iou, sign * th, dx, dy))
    out.sort(reverse=True)
    # refine around the best
    iou0, th0, dx0, dy0 = out[0]
    for th in np.arange(th0 - 4, th0 + 4.01, 1.0):
        m = render(th, cx, 672); m2 = np.zeros_like(m); m2[Y0 - 40:Y1 + 40, x0 - 40:x1 + 40] = m[Y0 - 40:Y1 + 40, x0 - 40:x1 + 40]
        v, dx, dy = best_shift(m2, p, 25); ms = np.roll(np.roll(m2, dy, 0), dx, 1); iou = (ms & p).sum() / max((ms | p).sum(), 1)
        out.append((iou, float(th), dx, dy))
    out.sort(reverse=True)
    iou, th, dx, dy = out[0]
    res[name] = dict(yaw_deg=float(th), ox=float(cx + dx), oy=float(672 + dy), iou=float(iou), top3=[(round(a, 3), b) for a, b, c_, d_ in out[:3]])
    print(name, res[name], '%.0fs' % (time.time() - t0), flush=True)
json.dump(res, open(W / 'data/cam34.json', 'w'), indent=1)
