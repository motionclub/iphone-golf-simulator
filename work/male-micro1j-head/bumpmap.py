"""Residual (P - lowpass(P)) along the vertex normal on the neck/jaw region -> scatter heat-maps in 4 views.  python3.13 bumpmap.py <V.npy> <out.png> [zlo zhi iters]"""
import sys; sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1j-head')
from j_lib import *
sys.path.insert(0, str(I1))
from edlib import Mesh, vertex_normals
V = np.load(sys.argv[1]); out = sys.argv[2]
zlo = float(sys.argv[3]) if len(sys.argv) > 3 else 1.38; zhi = float(sys.argv[4]) if len(sys.argv) > 4 else 1.50; its = int(sys.argv[5]) if len(sys.argv) > 5 else 40
_, F, _ = load_start(); M = Mesh(V, F); N = vertex_normals(V, F)
reg = (V[:, 2] >= zlo) & (V[:, 2] <= zhi) & (np.abs(V[:, 0]) < 0.11)
# keep only the neck: exclude face/jaw verts in front above z 1.452 ... region mask for smoothing = reg ; anchors elsewhere
w = reg.astype(float)
Ps = M.taubin(V, w, iters=its, lam=0.5, mu=-0.53)
res = ((V - Ps) * N).sum(axis=1) * 1000
print('residual mm in region: min %.2f max %.2f  rms %.2f' % (res[reg].min(), res[reg].max(), np.sqrt((res[reg] ** 2).mean())))
ids = np.where(reg)[0]
top = ids[np.argsort(-res[ids])][:12]
print('top convex bumps:'); [print(f'   v{i}: res {res[i]:+.2f} mm  at x={V[i,0]*1000:+6.1f} y={V[i,1]*1000:+7.1f} z={V[i,2]*1000:7.1f}') for i in top]
bot = ids[np.argsort(res[ids])][:8]
print('top concave dents:'); [print(f'   v{i}: res {res[i]:+.2f} mm  at x={V[i,0]*1000:+6.1f} y={V[i,1]*1000:+7.1f} z={V[i,2]*1000:7.1f}') for i in bot]
S = 5.0
def panel(view):
    # view: 'back' -> look from +y (x flips), 'front' -> from -y, 'left'/'right' side views
    if view == 'front': u = V[:, 0]; vis = N[:, 1] < 0.15; flip = 1
    elif view == 'back': u = -V[:, 0]; vis = N[:, 1] > -0.15; flip = 1
    elif view == 'side': u = V[:, 1]; vis = N[:, 0] > -0.15
    else: u = -V[:, 1]; vis = N[:, 0] < 0.15
    sel = np.where(reg & vis)[0]
    umin, umax = -0.10, 0.10 if view in ('front', 'back') else (-0.16, 0.12)
    if view in ('front', 'back'): umin, umax = -0.10, 0.10
    elif view == 'side': umin, umax = -0.16, 0.12
    else: umin, umax = -0.12, 0.16
    Wd = int((umax - umin) * 1000 * S); Hd = int((zhi - zlo + 0.01) * 1000 * S)
    im = Image.new('RGB', (Wd, Hd), (24, 24, 28)); d = ImageDraw.Draw(im)
    for zz in np.arange(np.ceil(zlo * 50) / 50, zhi + 1e-6, 0.02):
        yy = (zhi + 0.005 - zz) * 1000 * S; d.line((0, yy, Wd, yy), fill=(70, 70, 80)); d.text((2, yy - 10), f'{zz:.2f}', fill=(200, 200, 100))
    for i in sel:
        px = (u[i] - umin) * 1000 * S; py = (zhi + 0.005 - V[i, 2]) * 1000 * S
        r = res[i]; t = np.clip(r / 3.0, -1, 1)
        col = (int(255 * t), int(80 * (1 - abs(t))), 40) if t > 0 else (40, int(80 * (1 - abs(t))), int(255 * -t))
        d.ellipse((px - 3, py - 3, px + 3, py + 3), fill=col)
    d.text((6, 4), view + '  (red=convex bump, blue=dent, 3 mm full)', fill=(255, 255, 255))
    return im
tiles = [panel(v) for v in ('front', 'side', 'back')]
sheet = Image.new('RGB', (sum(t.width for t in tiles) + 12, max(t.height for t in tiles)), (0, 0, 0)); x = 0
for t in tiles: sheet.paste(t, (x, 0)); x += t.width + 6
sheet.save(out); print('saved', out, sheet.size)
