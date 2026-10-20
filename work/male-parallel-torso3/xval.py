"""cross-validation: fit with front/back (+ one back 3/4 panel), test on the other panel"""
import sys, json
sys.path.insert(0, '.')
from pmo_val import *
from slab import slab_fix
V = np.load('data/V_base.npy'); cal = json.load(open('data/q3_calib2.json'))
Tv = Torso(V); Tv.make_basis(0.012, 0.009); VL = Val(Tv)
def run(tag, extra=(), lam=0.1, lo=1.0, wextra=1.0, save=True):
    T = Torso(V); T.make_basis(0.012, 0.009)
    for nm in extra: T.add_yaw_view(nm, cal[nm], weight=wextra)
    z = np.zeros(T.m); lamv = 1.0 + (lo - 1.0) * (T.C[:, 1] < 0.90) + 1.0 * (T.C[:, 1] > 1.33)
    cF, cB = solve_lm(T, z, z, lam=lam, lam_vec=lamv, hmax=10.0, iters=14, verbose=False)
    P = T.positions(T.dy_mm(cF, cB)); P2, dF, dB = slab_fix(P, V, T.wf, T.wb)
    if save: np.save(f'data/V_{tag}.npy', P2)
    s = VL.score(P2)
    print(f'{tag:8s} fit views {["front", "back"] + list(extra)} | VAL BL {s["q3BL"]:.3f} BR {s["q3BR"]:.3f} (upper {s["q3BL_upper"]:.2f}/{s["q3BR_upper"]:.2f} lum {s["q3BL_lumbar"]:.2f}/{s["q3BR_lumbar"]:.2f} glute {s["q3BL_glute"]:.2f}/{s["q3BR_glute"]:.2f})')
if __name__ == '__main__':
    run('x0')
    run('x_BL', extra=('q3BL',)); run('x_BR', extra=('q3BR',)); run('x_both', extra=('q3BL', 'q3BR'))
