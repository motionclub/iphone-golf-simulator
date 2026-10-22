import sys, time, numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
import golf_look_textures as G
F = G.F
def advect_disp_n(vx, vy, steps, length, n=None):
    n = n or vx.shape[0]
    xs = ((np.arange(n, dtype=F) + .5) / n)
    x0 = np.broadcast_to(xs[None, :], (n, n)).copy(); y0 = np.broadcast_to(xs[:, None], (n, n)).copy()
    px, py = x0.copy(), y0.copy(); h = length / steps
    for _ in range(steps):
        ax = G.samp(vx, px, py); ay = G.samp(vy, px, py)
        mx = px - 0.5 * h * ax; my = py - 0.5 * h * ay
        px = px - h * G.samp(vx, mx, my); py = py - h * G.samp(vy, mx, my)
    return np.stack([px - x0, py - y0], -1).astype(F)
G.advect_disp = lambda vx, vy, steps, length: advect_disp_n(vx, vy, steps, length, 1024)
Fd = G.lava_fields(1024, 1201, 2)
pu, pv = Fd['pu'], Fd['pv']
def wrapd(a, b): d = a - b; return (d + .5) % 1.0 - .5
J = np.maximum.reduce([np.abs(wrapd(np.roll(pu, -1, 1), pu)), np.abs(wrapd(np.roll(pv, -1, 1), pv)), np.abs(wrapd(np.roll(pu, -1, 0), pu)), np.abs(wrapd(np.roll(pv, -1, 0), pv))])
print('J percentiles x 2048:', [(p, round(float(np.percentile(J, p) * 2048), 2)) for p in (50, 90, 99, 99.9, 99.99)])
for t in (8, 16, 32, 64): print('share J >', t, 'texels:', float((J * 2048 > t).mean()))
np.save('raw/lava_J.npy', J.astype(np.float32))
