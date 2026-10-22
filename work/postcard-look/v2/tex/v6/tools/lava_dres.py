"""test: advection displacement resolution vs the sawtooth fold lines of Lava_E (4-texel period = the 256 grid of D)."""
import sys, time, numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
import golf_look_textures as G
F = G.F
n_out = int(sys.argv[1]); out = sys.argv[2]
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
t0 = time.time()
G.advect_disp = lambda vx, vy, steps, length: advect_disp_n(vx, vy, steps, length, n_out)
d = G.mat_lava(1024, 1201, 2)
print('time', time.time() - t0)
E = G.enc(d['E']); np.save(out + '_E.npy', E)
open(out + '_E.raw', 'wb').write(np.ascontiguousarray(E).tobytes())
