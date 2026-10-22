"""dense grid of the ANALYTIC head surface (lower face) for shading inspection:  python3 analytic_grid.py name key=value ... -> data/grid_<name>.npz (V,F,Foff)
chart: azimuth theta in [-100,100] deg (0 = front), elevation phi in [-62, 6] deg about the centre C"""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, trial, geo

def grid(H, nth=260, nph=200, th=(-100, 100), ph=(-62, 6)):
    T = np.radians(np.linspace(th[0], th[1], nth)); Pp = np.radians(np.linspace(ph[0], ph[1], nph))
    TT, PP = np.meshgrid(T, Pp)
    u = np.stack([np.cos(PP) * np.sin(TT), -np.cos(PP) * np.cos(TT), np.sin(PP)], -1).reshape(-1, 3)
    P = H.phi(u)
    F = []
    for j in range(nph - 1):
        for i in range(nth - 1):
            a = j * nth + i; F.append([a, a + 1, a + 1 + nth, a + nth])
    return P, F

if __name__ == '__main__':
    name = sys.argv[1]; kw = {}
    for a in sys.argv[2:]:
        k, v = a.split('='); kw[k] = float(v)
    H, P = trial.make_H(**kw)
    V, F = grid(H)
    off = np.arange(0, 4 * (len(F) + 1), 4)[:len(F) + 1]
    np.savez(trial.W3 + f'data/grid_{name}.npz', V=V.astype(np.float64), F=np.array(F).ravel(), Foff=np.arange(0, 4 * len(F) + 1, 4))
    print('grid', name, V.shape, len(F), 'quads')
