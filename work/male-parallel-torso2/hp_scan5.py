import sys, time
sys.path.insert(0, '.')
from pmo_val import *
from slab import slab_fix
V = np.load('data/V_base.npy')
def run(tag, lam=0.1, psig=2.5, hp=3, sp=0.012, sg=0.009, save=True, lo=1.0, hi=1.0, chest=1.0, chestB=1.0, zr=(1.12, 1.32), allB=1.0):
    T = Torso(V, plate_sigma=psig, hp_iters=hp); T.make_basis(sp, sg); z = np.zeros(T.m)
    lamv = 1.0 + (lo - 1.0) * (T.C[:, 1] < 0.90) + hi * (T.C[:, 1] > 1.33)
    chm = (T.C[:, 1] > zr[0]) & (T.C[:, 1] < zr[1])
    lamF = lamv * np.where(chm, chest, 1.0); lamB = lamv * np.where(chm, chestB, 1.0) * allB
    cF, cB = solve_lm(T, z, z, lam=lam, lam_vec=np.concatenate([lamF, lamB]), hmax=10.0, iters=14, verbose=False)
    P = T.positions(T.dy_mm(cF, cB)); P2, dF, dB = slab_fix(P, V, T.wf, T.wb)
    if save: np.save(f'data/V_{tag}.npy', P2)
    # validation uses the default (hp=3, blur 1.1) definition regardless of the fit settings
    Tv = Torso(V, plate_sigma=2.5, hp_iters=3); Tv.make_basis(0.012, 0.009); VL = Val(Tv); s = VL.score(P2)
    sc = T.score(cF, cB); d2 = (P2[T.zi, 1] - V[T.zi, 1]) * 1000; inner = (np.abs(V[T.zi, 0]) < 0.14) & (V[T.zi, 2] > 0.82) & (V[T.zi, 2] < 1.34)
    print(f'{tag:6s} lam {lam} psig {psig} hp {hp} sp {sp} sg {sg} | fit f {sc["front"]:.3f} b {sc["back"]:.3f} | VAL BL {s["q3BL"]:.3f} BR {s["q3BR"]:.3f} (upper {s["q3BL_upper"]:.2f}/{s["q3BR_upper"]:.2f} lum {s["q3BL_lumbar"]:.2f}/{s["q3BR_lumbar"]:.2f} glute {s["q3BL_glute"]:.2f}/{s["q3BR_glute"]:.2f}) | dy rms {np.sqrt((d2[inner]**2).mean()):.2f} max {np.abs(d2).max():.1f}')
if __name__ == '__main__':
    for tag, kw in (('b1', dict(chest=0.25, chestB=0.25)), ('b2', dict(chest=0.25, chestB=0.12)), ('b3', dict(chest=0.25, chestB=0.06)), ('b4', dict(chest=0.25, chestB=0.12, zr=(1.10, 1.38))), ('b5', dict(chest=0.25, chestB=0.25, allB=0.5)), ('b6', dict(chest=0.25, chestB=0.12, zr=(1.10, 1.38), allB=0.5))): run('s_' + tag, **kw)
