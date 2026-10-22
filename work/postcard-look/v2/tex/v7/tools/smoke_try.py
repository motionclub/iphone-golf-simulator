"""smoke_try.py <outdir> [key=value ...] : v7 smoke experiments (Blender's python3.13). Overrides SMOKE_P, runs mat_smoke, prints the generator's
smoke metrics + predicted runtime band, writes a preview sheet: the card alone on the crater wall colour and a 3-card stacked-plume simulation
(two near-overlapping cards, the hole-10 smoke_group pattern) with the combined alpha 1 - prod(1 - a)."""
import sys, os, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
for kv in sys.argv[2:]:
    k, v = kv.split('=')
    g.SMOKE_P[k] = tuple(float(x) for x in v.split(',')) if ',' in v else float(v)
r = g.mat_smoke()
S = g.enc(np.concatenate([r['C'], r['A'][..., None]], -1)) if hasattr(g, 'enc') else None
S = np.concatenate([g.enc(r['C']), np.clip(np.round(r['A'] * 255), 0, 255).astype(np.uint8)[..., None]], -1)
m = g.smoke_metrics(S)
print('painted: amax %.3f border %.4f aspect %.2f grad %.4f core(>.5max) %.3f cover %.3f lstd %.3f' % (m['amax'], m['border'], m['aspect'], m['grad'], m['core'], m['cover'], m['lstd']))
sp = g.smoke_spec(); gg = g.smoke_game(S, sp)
ae = np.clip(S[..., 3].astype(np.float64) / 255 * sp['tint'][3] * sp['gain'], 0, 1)
print('share of the card with effective alpha >= .30: %.1f %%, >= .50: %.1f %%' % ((ae >= .30).mean() * 100, (ae >= .50).mean() * 100))
vis = ae > 0.10; rows = np.flatnonzero(vis.any(1)); r0, r1 = rows[0], rows[-1]
wid = np.array([vis[y].sum() for y in range(S.shape[0])]); wmax = wid.max()
low = wid[int(r1 - 0.06 * (r1 - r0)):r1 + 1]
print('foot: bottom row width %.0f%% of the widest row, mean of the lowest 6 %% of the visible height %.0f%%; vertical alpha step at the bottom edge max %.3f/texel' % (wid[r1 - 2] / wmax * 100, low.mean() / wmax * 100, np.abs(np.diff(ae, axis=0)).max()))

print('predicted:', {k: (np.round(v, 2).tolist() if hasattr(v, 'tolist') else (round(float(v), 3) if isinstance(v, (int, float, np.floating)) else v)) for k, v in gg.items()})
# stack simulation on the wall colour
N = S.shape[0]
a = S[..., 3].astype(np.float64) / 255 * sp['tint'][3] * sp['gain']
a = np.clip(a, 0, 1); col = S[..., :3].astype(np.float64) / 255
W = 1200; H = 760
bg = np.zeros((H, W, 3)); bg[:] = np.array([45, 24, 22]) / 255
yy = np.arange(H)[:, None]; bg[..., 0] += 0.0; bg *= (0.7 + 0.3 * (np.sin(np.arange(W)[None, :] * 0.25)[..., None] * 0 + 1))
def place(alpha_acc, colour_acc, dx, dy, size, mirror=False):
    # nearest-neighbour paste of the card (size px) at (dx, dy) top-left
    ys = (np.arange(size) * N / size).astype(int); xs = (np.arange(size) * N / size).astype(int)
    aa = a[ys][:, xs]; cc = col[ys][:, xs]
    if mirror: aa = aa[:, ::-1]; cc = cc[:, ::-1]
    y0, x0 = dy, dx
    sl = (slice(max(0, y0), min(H, y0 + size)), slice(max(0, x0), min(W, x0 + size)))
    sa = aa[sl[0].start - y0:sl[0].stop - y0, sl[1].start - x0:sl[1].stop - x0]; sc = cc[sl[0].start - y0:sl[0].stop - y0, sl[1].start - x0:sl[1].stop - x0]
    return sl, sa, sc
frame = bg.copy()
for (dx, dy, size, mir) in ((640, 40, 540, False), (700, 80, 480, True), (580, 120, 520, False)):
    sl, sa, sc = place(None, None, dx, dy, size, mir)
    lit = sc * np.array([0.95, 0.80, 0.78])           # crude warm light
    frame[sl] = frame[sl] * (1 - sa[..., None]) + lit * sa[..., None]
single = bg[:, :560].copy()
sl, sa, sc = place(None, None, 20, 120, 520, False)
single[sl[0], sl[1].start:sl[1].stop] = single[sl[0], sl[1].start:sl[1].stop] * (1 - sa[..., None]) + sc * np.array([0.95, 0.80, 0.78]) * sa[..., None]
frame[:, :560] = single
img = np.clip(frame, 0, 1)
g.write_png(os.path.join(out, 'smoke_sheet.png'), np.round(img * 255).astype(np.uint8))
g.write_png(os.path.join(out, 'Smoke_C_try.png'), S)
print('wrote', out)
