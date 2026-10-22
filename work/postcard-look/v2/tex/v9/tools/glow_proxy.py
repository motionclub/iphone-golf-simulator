"""glow_proxy.py <Look dir> : texture-level proxies of the Game-view glow classification (wall space: x1.6 u, x2.8 v) + skeleton junction density of Basalt_E."""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
import numpy as np
import golf_look_textures as G
d = sys.argv[1]
E = G.read_png(d + '/Basalt_E.png').astype(np.float32) / 255; N = G.read_png(d + '/Basalt_N.png').astype(np.float32) / 255 * 2 - 1
mask = G.lum(E) > 0.04
H, W = mask.shape
comps = G.label_components(mask)
vert = rung = blob = oth = 0; tot = 0
for ys, xs in comps:
    if len(ys) < 40: continue
    k = len(ys); tot += k
    # unwrap torus: shift coordinates to the component's min
    y = ys.astype(float); x = xs.astype(float)
    if y.max() - y.min() > H / 2: y = np.where(y < H / 2, y + H, y)
    if x.max() - x.min() > W / 2: x = np.where(x < W / 2, x + W, x)
    X = x * 1.6; Y = y * 2.8
    c = np.cov(np.vstack([X, Y])) if k > 2 else np.eye(2)
    ev, evec = np.linalg.eigh(c); l2, l1 = max(ev[0], 1e-6), max(ev[1], 1e-6)
    v = evec[:, 1]; ang = np.degrees(np.arctan2(abs(v[0]), abs(v[1]))); el = np.sqrt(l1 / l2)
    if el >= 2.5 and ang <= 35: vert += k
    elif el >= 2.5 and ang >= 55: rung += k
    elif el < 2.0: blob += k
    else: oth += k
print('proxy comps>=40px: n', len(comps), 'glow px', tot, 'vertical %.0f%% rung %.0f%% blob %.0f%% other %.0f%%' % tuple(100 * a / tot for a in (vert, rung, blob, oth)))
wallm = np.hypot(N[..., 0], N[..., 1]) > 0.75
nw = np.zeros_like(wallm)
for dx in range(-8, 9): nw |= np.roll(wallm, dx, 1)
for dy in range(-8, 9): nw |= np.roll(wallm, dy, 0)
print('glow near steep wall %.1f%%' % (100 * (mask & nw).sum() / mask.sum()), 'coverage %.2f%%' % (100 * mask.mean()))
sk_px, sk_j = G.skeleton_junctions(mask)
print('texture skeleton px %d junction clusters %d -> %.2f per 100 px' % (sk_px, sk_j, 100.0 * sk_j / sk_px))
