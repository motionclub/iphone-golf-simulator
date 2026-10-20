"""Edit e2e: reshape the ear shell (rounded top, uniform top height, thicker helix roll) as a DIFFERENCE field new-old on the existing mesh
(old = the Micro1h ear function, new = same anatomy with a top-rounded height profile).  Loops/topology untouched."""
import sys; sys.path.insert(0, '.')
from edlib import *
import sculpt as S

OLD = dict(S.PRM['ear'])
NEW = dict(OLD, S_front=5.0, S_rear=21.0, D_rear=12.5, D_front=11.5, helix=7.2, scapha=4.4, top_z=(1.574, 1.599), top_mean=19.0, top_round=0.55, top_D=5.5)


def ear_yz(yy, zz, e):
    """Micro1h ear function (copied) + optional top shaping controlled by e['top_z'], e['top_mean'], e['top_round']"""
    poly = S.ear_poly()
    d_in = -S.poly_dist(yy, zz, poly)
    yf, yr = float(S.ycol(637.0)), float(S.ycol(669.7))
    S_ = (e['S_front'] + (e['S_rear'] - e['S_front']) * sstep(yf, yr, yy) ** e['S_pow']) * mm
    S_ = S_ * (e['lobe_k'] + (1 - e['lobe_k']) * sstep(1.529, 1.548, zz))
    if 'top_z' in e:
        z0, z1 = e['top_z']
        b = sstep(z0, z1 - 0.012, zz)                                   # uniform height along the top arc ...
        S_top = (e.get('top_front', e['top_mean']) + (e['top_mean'] - e.get('top_front', e['top_mean'])) * sstep(-0.025, 0.008, yy)) * mm
        S_ = S_ * (1 - b) + S_top * b
        u = np.clip((zz - (z1 - 0.019)) / 0.019, 0.0, 1.0)              # ... falling off along a quarter circle toward the top (rounded top)
        S_ = S_ * (e['top_round'] + (1 - e['top_round']) * np.sqrt(np.maximum(1 - u * u, 0.0)))
    D = (e['D_front'] + (e['D_rear'] - e['D_front']) * sstep(-0.025, 0.0, yy)) * mm
    if 'top_D' in e:                                                  # steeper wall at the top: the helix top reads as a free rim, not a ramp/web
        bz = sstep(e['top_z'][0], e['top_z'][1] - 0.008, zz); D = D * (1 - bz) + e['top_D'] * mm * bz
    t = np.clip(d_in / D, 0, 1)
    w = np.sqrt(np.maximum(1.0 - (1.0 - t) ** 2, 0.0)) ** e['round']
    base = S_ * w
    ins = sstep(0.0, 2.0 * mm, d_in)
    wh = sstep(float(S.ycol(639.0)), float(S.ycol(645.0)), yy)
    helix = e['helix'] * mm * np.exp(-((d_in - 3.2 * mm) / (3.0 * mm)) ** 2) * wh
    scapha = -e['scapha'] * mm * np.exp(-((d_in - 8.8 * mm) / (2.8 * mm)) ** 2) * wh
    dA = np.minimum(S.polyline_dist(yy, zz, S.EAR_ANTI), np.minimum(S.polyline_dist(yy, zz, S.EAR_ANTI_UP1), S.polyline_dist(yy, zz, S.EAR_ANTI_UP2)))
    anti = e['anti'] * mm * np.exp(-(dA / (3.6 * mm)) ** 2) * sstep(0.0, 3.0 * mm, d_in)
    cy, cz = S._yz(647.5, 189.5)
    r2 = ((yy - cy) / (8.2 * mm)) ** 2 + ((zz - cz) / (11.5 * mm)) ** 2
    concha = -e['concha'] * mm * np.maximum(1 - r2, 0.0) ** 1.6
    ty, tz = S._yz(640.2, 184.5); tragus = e['tragus'] * mm * np.exp(-(((yy - ty) / (3.4 * mm)) ** 2 + ((zz - tz) / (3.8 * mm)) ** 2))
    ay_, az_ = S._yz(642.5, 197.5); antit = e['antitragus'] * mm * np.exp(-(((yy - ay_) / (3.4 * mm)) ** 2 + ((zz - az_) / (3.2 * mm)) ** 2))
    ly, lz = S._yz(646.0, 205.5); lobe = e['lobe'] * mm * np.exp(-(((yy - ly) / (7.0 * mm)) ** 2 + ((zz - lz) / (6.5 * mm)) ** 2))
    relief = (helix + scapha + anti + concha + tragus + antit + lobe) * ins
    return np.where(d_in > -0.003, base + relief, 0.0)


_GRID = {}


def field(P, e, key):
    if key not in _GRID:
        res = 0.0004
        ys = np.arange(-0.050, 0.030, res); zs = np.arange(1.505, 1.615, res)
        Y, Z = np.meshgrid(ys, zs, indexing='ij')
        G = ear_yz(Y.ravel(), Z.ravel(), e).reshape(Y.shape)
        G = S.blur2d(G, e['blur'] * mm / res)
        _GRID[key] = (ys, zs, G, res)
    ys, zs, G, res = _GRID[key]
    ax = np.abs(P[:, 0]); y = P[:, 1]; z = P[:, 2]
    region = (ax > 0.055) & (y > ys[0]) & (y < ys[-1] - res) & (z > zs[0]) & (z < zs[-1] - res)
    out = np.zeros(len(P)); idx = np.where(region)[0]
    fy = (y[idx] - ys[0]) / res; fz = (z[idx] - zs[0]) / res
    iy = np.floor(fy).astype(int); iz = np.floor(fz).astype(int); ty_ = fy - iy; tz_ = fz - iz
    out[idx] = G[iy, iz] * (1 - ty_) * (1 - tz_) + G[iy + 1, iz] * ty_ * (1 - tz_) + G[iy, iz + 1] * (1 - ty_) * tz_ + G[iy + 1, iz + 1] * ty_ * tz_
    return out


def e2e_ear_reshape(V, M, new=None, taubin_iters=2):
    V = V.copy(); sgn = np.where(V[:, 0] < 0, -1.0, 1.0)
    new = dict(NEW if new is None else new)
    f_old = field(V, OLD, 'old'); f_new = field(V, new, repr(sorted(new.items())))
    diff = f_new - f_old
    V[:, 0] += sgn * diff
    ax = np.abs(V[:, 0]); d = S.poly_dist(V[:, 1], V[:, 2], S.ear_poly())
    w = np.where(d <= 0, 0.9, 0.5 * (1 - sstep(0.0, 8 * mm, d))) * (ax > 0.062) * (V[:, 2] > 1.505)
    return M.taubin(V, w, iters=taubin_iters), diff


if __name__ == '__main__':
    tag_in, tag_out = sys.argv[1], sys.argv[2]
    V0, F, loops = load(tag_in); M = Mesh(V0, F)
    V1, diff = e2e_ear_reshape(V0, M)
    d = np.linalg.norm(V1 - V0, axis=1); print('moved', int((d > 1e-9).sum()), 'max mm %.2f' % (d.max() * 1000), 'diff range mm %.2f..%.2f' % (diff.min() * 1000, diff.max() * 1000))
    np.save(f'data/V_{tag_out}.npy', V1)
