"""Edit e2n: nose narrower at the bridge, widening toward the base (user feedback).
Lateral warp of the nose zone (x only; the sagittal profile is untouched):
  delta > 0 (bridge): scale |x| <= F_old(z) down to F_old - delta, blend back to identity by F_old + blend
  delta < 0 (base)  : push the outer wings outward by |delta| (smoothstep from x0 to F_old), nostril openings stay where the plate has them"""
import sys; sys.path.insert(0, '.')
from edlib import *
import sculpt as S

DELTA_Z = [(1.520, 0.0), (1.526, -2.4), (1.532, -4.4), (1.538, -5.4), (1.543, -5.0), (1.548, -3.2), (1.553, -0.4), (1.558, 3.0), (1.564, 5.8), (1.569, 7.0), (1.575, 6.2), (1.581, 4.5), (1.590, 2.0), (1.600, 0.0)]


def _dx(ax, z, scale, f_old_hi, f_old_lo, blend, x0):
    zt = np.array([a for a, b in DELTA_Z]); dt = np.array([b for a, b in DELTA_Z])
    delta = np.interp(z, zt, dt) * scale
    F_old = f_old_lo + (f_old_hi - f_old_lo) * sstep(1.548, 1.562, z)
    dn = np.maximum(delta, 0.0); dw = np.maximum(-delta, 0.0)
    F_new = F_old - dn; Xf = F_old + blend
    inside = ax <= F_old
    phi = np.where(inside, ax * F_new / F_old, F_new + (ax - F_old) * (Xf - F_new) / (Xf - F_old)); phi = np.where(ax >= Xf, ax, phi)
    dnar = phi - ax
    up = sstep(x0, F_old, ax) * (1.0 - sstep(F_old, F_old + blend + 3.0, ax))
    dwid = dw * np.where(ax <= F_old, sstep(x0, F_old, ax), 1.0 - sstep(F_old, F_old + blend + 3.0, ax))
    return dnar + dwid


def e2n_nose(V, scale=1.0, f_old_hi=21.0, f_old_lo=22.0, blend=10.0, x0=11.0):
    V = V.copy()
    ax = np.abs(V[:, 0]) * 1000; z = V[:, 2]; y = V[:, 1]
    dx = np.zeros(len(V))
    offs = (-2.0, -1.0, 0.0, 1.0, 2.0)
    for off in offs: dx += _dx(np.clip(ax + off, 0, None), z, scale, f_old_hi, f_old_lo, blend, x0)
    dx /= len(offs)
    poly = S.smooth_poly(S.eye_poly())
    d_eye = S.poly_dist(np.abs(V[:, 0]), z, poly) * 1000
    wgt = sstep(2.0, 7.0, d_eye) * sstep(-0.10, -0.125, y)
    sgn = np.where(V[:, 0] < 0, -1.0, 1.0)
    V[:, 0] += sgn * dx * wgt * 1e-3
    return V


if __name__ == '__main__':
    tag_in, tag_out = sys.argv[1], sys.argv[2]; sc = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    V0, F, loops = load(tag_in)
    V1 = e2n_nose(V0, scale=sc)
    d = np.linalg.norm(V1 - V0, axis=1)
    print('moved', int((d > 1e-9).sum()), 'max mm %.2f' % (d.max() * 1000))
    np.save(f'data/V_{tag_out}.npy', V1)
