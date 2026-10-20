"""Edit e1: far-side tangent shaving of the chin band to the plate 3/4 contours (q3L 41 deg, q3R 36 deg), mirrored."""
import sys; sys.path.insert(0, '.')
from edlib import *


def e1_shave(V, M, rows=range(536, 600, 1), z_lo=(1.456, 1.470), z_hi=(1.500, 1.522), margin=1.0, soft=1.5, ygate=(-0.045, -0.075), amount=1.0):
    V = V.copy()
    t = q3_tangent_lines(list(rows), 'L')
    for name in ('q3L', 'q3R'):
        zs, ul = t[name]
        # drop unreliable rows (below z_lo[0]) and smooth
        sel = (zs > 1.455) & (zs < 1.53)
        zs_, ul_ = zs[sel], ul[sel]
        o = np.argsort(zs_); zs_, ul_ = zs_[o], ul_[o]
        ul_s = poly_smooth(zs_ * 1000, ul_ * 1000, 2.5) / 1000
        a = math.radians(Q3[name]['az'])
        sgn = np.where(V[:, 0] < 0, -1.0, 1.0)
        # mirrored positions (far side = x<0)
        Pm = V.copy(); Pm[:, 0] = -np.abs(V[:, 0])
        u = Pm[:, 0] * math.cos(a) + (Pm[:, 1] + 0.1254) * math.sin(a)
        uline = np.interp(V[:, 2], zs_, ul_s, left=ul_s[0], right=ul_s[-1])
        g = (uline - u) * 1000                    # mm, >0: beyond the plate contour
        s = soft; ge = s * np.log1p(np.exp((g - margin) / s))
        wz = sstep(*z_lo, V[:, 2]) * (1 - sstep(*z_hi, V[:, 2]))
        wy = sstep(ygate[0], ygate[1], V[:, 1])
        push = ge * wz * wy * amount * mm
        # displacement along the camera-right horizontal direction (cos a, sin a), mirrored back
        V[:, 0] += sgn * push * math.cos(a) * -sgn * -1 * 1.0 * 0 + 0.0
        dx = push * math.cos(a); dy = push * math.sin(a)
        V[:, 0] += -sgn * 0 + (np.where(V[:, 0] < 0, 1.0, -1.0)) * dx * (-1) * (-1) if False else 0
        # far side (x<0): move +x,+y ; near side (x>0, mirrored): move -x,+y
        V[:, 0] += np.where(V[:, 0] < 0, dx, -dx)
        V[:, 1] += dy
    return V


if __name__ == '__main__':
    V0, F, loops = load('h0'); M = Mesh(V0, F)
    V1 = e1_shave(V0, M)
    d = np.linalg.norm(V1 - V0, axis=1)
    print('moved verts', int((d > 1e-6).sum()), 'max mm %.2f' % (d.max() * 1000))
    np.save('data/V_e1.npy', V1)
    E = edges_of(F)
    C.report_q3(V1, E, rows=list(range(520, 596, 6)))
