"""Close-up wireframes with carved loops highlighted.  blender -b --factory-startup --python wire_loops.py -- <tag>"""
import sys, pickle
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1e')
import h1lib as H, wire
tag = sys.argv[sys.argv.index('--') + 1]
V = np.load(H.W / f'data/Vfinal_{tag}.npy'); F = pickle.load(open(H.W / f'data/Ffinal_{tag}.pkl', 'rb')); loops = pickle.load(open(H.W / f'data/loops_{tag}.pkl', 'rb'))
E = set()
for f in F:
    for i in range(len(f)):
        a, b = f[i], f[(i + 1) % len(f)]; E.add((min(a, b), max(a, b)))
E = np.array(sorted(E))
head = (V[:, 2] > 1.43) & (np.abs(V[:, 0]) < 0.14)
out = H.W / f'r/{tag}'; out.mkdir(exist_ok=True, parents=True)


def plot(name, sel, ax, bounds, size=1200):
    S = size / max(bounds[1] - bounds[0], bounds[3] - bounds[2])
    Wd = int((bounds[1] - bounds[0]) * S); Hd = int((bounds[3] - bounds[2]) * S)
    img = np.full((Hd, Wd, 3), 30, np.uint8)
    m = sel[E[:, 0]] & sel[E[:, 1]]
    e = E[m]
    a = V[e[:, 0]][:, list(ax)]; b = V[e[:, 1]][:, list(ax)]
    n = int(max(2, np.ceil(np.max(np.linalg.norm(b - a, axis=1)) * S)))
    t = np.linspace(0, 1, n)[None, :, None]
    p = a[:, None, :] * (1 - t) + b[:, None, :] * t
    x = ((p[..., 0] - bounds[0]) * S).astype(int); y = ((bounds[3] - p[..., 1]) * S).astype(int)
    ok = (x >= 0) & (x < Wd) & (y >= 0) & (y < Hd)
    img[y[ok], x[ok]] = (170, 170, 170)
    cols = {'lid': (255, 90, 90), 'nostril': (255, 200, 40), 'ala': (255, 240, 120), 'mouth': (80, 255, 120), 'helix': (80, 200, 255), 'ear_attach': (255, 120, 255), 'concha': (255, 160, 60), 'jaw': (120, 160, 255)}
    for name_, idx in loops.items():
        col = next((c for k, c in cols.items() if name_.startswith(k)), (255, 255, 255))
        for i in range(len(idx) - 1):
            pa = V[idx[i]][list(ax)]; pb = V[idx[i + 1]][list(ax)]
            nn = int(max(2, np.linalg.norm(pb - pa) * S * 2))
            tt = np.linspace(0, 1, nn)[:, None]; pp = pa * (1 - tt) + pb * tt
            xx = ((pp[:, 0] - bounds[0]) * S).astype(int); yy = ((bounds[3] - pp[:, 1]) * S).astype(int)
            okk = (xx >= 1) & (xx < Wd - 1) & (yy >= 1) & (yy < Hd - 1)
            for dx in (0, 1):
                for dy in (0, 1):
                    img[yy[okk] + dy, xx[okk] + dx] = col
    wire.write_png(str(out / f'{name}.png'), img)


front = head & (V[:, 1] < -0.05)
plot('wl_mouth', front, (0, 2), (-0.055, 0.055, 1.470, 1.540))
plot('wl_eyes', front, (0, 2), (-0.075, 0.075, 1.555, 1.615))
plot('wl_nose', front, (0, 2), (-0.040, 0.040, 1.520, 1.600))
side = head & (V[:, 0] > 0.05)
plot('wl_ear', side, (1, 2), (-0.050, 0.030, 1.500, 1.615), 1300)
plot('wl_jaw', head & (V[:, 1] < 0.0) & (V[:, 0] > 0.0), (0, 2), (0.0, 0.095, 1.44, 1.54), 1300)
print('ok')
