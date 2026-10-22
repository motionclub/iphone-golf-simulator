"""Torso sculpt v1: analytic displacement fields on the existing topology (indices untouched, zone only).
python3.13 sculpt.py <out.npy> [params.json]      -> data/V_<tag>.npy"""
import sys, json
import numpy as np
from zone import *
mm = 1e-3
def sstep(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)
def interp(z, tab):
    zs = np.array([t[0] for t in tab]); vs = np.array([t[1] for t in tab], float)
    # monotone smooth: PCHIP-like via cosine blending between knots
    out = np.empty_like(z)
    idx = np.clip(np.searchsorted(zs, z) - 1, 0, len(zs) - 2)
    t = (z - zs[idx]) / (zs[idx + 1] - zs[idx]); t = sstep(t)
    out = vs[idx] * (1 - t) + vs[idx + 1] * t
    out[z <= zs[0]] = vs[0]; out[z >= zs[-1]] = vs[-1]
    return out
def g(u, s): return np.exp(-0.5 * (u / s) ** 2)
def g2(x, z, cx, cz, sx, sz): return np.exp(-0.5 * (((x - cx) / sx) ** 2 + ((z - cz) / sz) ** 2))
def g2a(x, z, cx, cz, sx, szlo, szhi):
    sz = np.where(z < cz, szlo, szhi); return np.exp(-0.5 * (((x - cx) / sx) ** 2 + ((z - cz) / sz) ** 2))
def seg_dist(x, z, p0, p1):
    p0 = np.array(p0); p1 = np.array(p1); d = p1 - p0; L2 = d @ d
    t = np.clip(((x - p0[0]) * d[0] + (z - p0[1]) * d[1]) / L2, 0, 1)
    return np.hypot(x - (p0[0] + t * d[0]), z - (p0[1] + t * d[1])), t
def poly_groove(x, z, pts, sig):
    """gaussian groove along a polyline in (x,z): returns profile (0..1) and param t along the polyline (0..1)"""
    best = np.full(x.shape, 1e9); tt = np.zeros_like(x); acc = 0; lens = [np.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]; tot = sum(lens)
    for i in range(len(pts) - 1):
        d, t = seg_dist(x, z, pts[i], pts[i + 1]); m = d < best; best = np.where(m, d, best); tt = np.where(m, (acc + t * lens[i]) / tot, tt); acc += lens[i]
    return np.exp(-0.5 * (best / sig) ** 2), tt

P = dict(
    env_front=[(0.775, 0), (0.78, 0), (0.80, -12), (0.82, -7.5), (0.84, 0), (0.88, 5), (0.93, 8), (1.30, 8), (1.34, 5), (1.385, 0)],
    env_back=[(0.775, 0), (0.78, 0), (0.80, -11), (0.82, -6.5), (0.845, 0), (0.88, 5), (0.93, 8), (1.30, 10), (1.34, 6), (1.385, 0)],
    pec=9.0, sternum=3.0, clav=2.5, belly=5.0, oblique=3.0, pubic=5.0, groin=5.0, rectus=2.0,
    trap=6.0, scap=4.0, spine=2.5, erector=2.0, glute=12.0, cleft=9.0)
if len(sys.argv) > 2: P.update(json.load(open(sys.argv[2])))

def build(P, V=V0):
    zm = zone_mask(V); idx = np.where(zm)[0]
    n = vnormals(V, iters=2)
    x, y, z = V[:, 0], V[:, 1], V[:, 2]
    # front/back weight from the depth fraction u=(y-yc(z))/hd(z) of the central slab (pure-y moves leave the x outline untouched)
    zz = np.arange(0.76, 1.42, 0.005); yc_ = np.zeros(len(zz)); hd_ = np.zeros(len(zz))
    for i, zf in enumerate(zz):
        m = (np.abs(V[:, 2] - zf) < 0.008) & (np.abs(V[:, 0]) < 0.09)
        yc_[i] = 0.5 * (V[m, 1].min() + V[m, 1].max()); hd_[i] = 0.5 * (V[m, 1].max() - V[m, 1].min())
    k = np.ones(5) / 5; yc_ = np.convolve(np.pad(yc_, 2, mode='edge'), k, 'valid'); hd_ = np.convolve(np.pad(hd_, 2, mode='edge'), k, 'valid')
    u = (y - np.interp(z, zz, yc_)) / np.interp(z, zz, hd_)
    wf = sstep((-u - 0.12) / 0.55); wb = sstep((u - 0.12) / 0.55)
    ax = np.abs(x)
    Tx = 1 - sstep((ax - 0.13) / 0.11)                       # 1 for |x|<=.13, 0 at .24
    Tx2 = 1 - sstep((ax - 0.17) / 0.07)                      # tighter for flank-adjacent forms
    Tlo = sstep((z - 0.775) / 0.045); Thi = 1 - sstep((z - 1.30) / 0.085)
    F_ = np.zeros(len(V)); B_ = np.zeros(len(V))                # outward thickness in mm
    F_ += interp(z, P['env_front']); B_ += interp(z, P['env_back'])
    s = np.sign(x); s[s == 0] = 1
    # ---------- FRONT ----------
    pec = np.zeros(len(V))
    for sg in (-1, 1):
        pec += g2a(x, z, sg * 0.082, 1.268, 0.056, 0.030, 0.062)
    pec = np.minimum(pec, 1.0) * P['pec']
    stern = g(x, 0.011) * sstep((z - 1.17) / 0.04) * (1 - sstep((z - 1.33) / 0.04)) * -P['sternum']
    clav = np.zeros(len(V))
    for sg in (-1, 1):
        gr, t = poly_groove(x, z, [(sg * 0.025, 1.368), (sg * 0.11, 1.352), (sg * 0.20, 1.335)], 0.012); clav += gr
    clav = np.minimum(clav, 1) * P['clav']
    belly = g2(x, z, 0.0, 0.93, 0.085, 0.07) * P['belly']
    obl = (g2(x, z, 0.134, 0.97, 0.03, 0.045) + g2(x, z, -0.134, 0.97, 0.03, 0.045)) * P['oblique']
    pub = g2(x, z, 0.0, 0.855, 0.05, 0.04) * P['pubic']
    rect = (g2(x, z, 0.034, 1.07, 0.024, 0.09) + g2(x, z, -0.034, 1.07, 0.024, 0.09)) * P['rectus']
    gro = np.zeros(len(V))
    for sg in (-1, 1):
        gr, t = poly_groove(x, z, [(sg * 0.180, 0.905), (sg * 0.125, 0.845), (sg * 0.070, 0.805), (sg * 0.034, 0.778)], 0.010); gro += gr
    gro = np.minimum(gro, 1) * -P['groin']
    F_ += (pec + stern + clav + belly + obl + pub + rect + gro) * Tx2
    # ---------- BACK ----------
    trap = g2(x, z, 0.0, 1.315, 0.10, 0.05) * P['trap']
    scap = (g2(x, z, 0.085, 1.22, 0.05, 0.055) + g2(x, z, -0.085, 1.22, 0.05, 0.055)) * P['scap']
    spine = -g(x, 0.009) * sstep((z - 0.98) / 0.05) * (1 - sstep((z - 1.33) / 0.03)) * P['spine']
    ere = (g2(x, z, 0.032, 1.06, 0.022, 0.08) + g2(x, z, -0.032, 1.06, 0.022, 0.08)) * P['erector']
    glu = (g2(x, z, 0.078, 0.915, 0.062, 0.068) + g2(x, z, -0.078, 0.915, 0.062, 0.068)) * P['glute']
    cz = np.array([0.775, 0.80, 0.86, 0.93, 0.98, 1.00]); cd = np.array([0.0, 6, 9, 5, 1.5, 0.0])
    cs = interp(z, list(zip(cz, cd))); cw = 0.0065 + 0.007 * (1 - sstep((z - 0.78) / 0.12))
    cleft = -np.exp(-0.5 * (x / cw) ** 2) * cs * (P['cleft'] / 9.0)
    B_ += (trap + scap + spine + ere + glu + cleft) * Tx2
    envF = interp(z, P['env_front']); envB = interp(z, P['env_back'])
    F_ = envF * Thi + (F_ - envF) * Tx * Tlo * Thi; B_ = envB * Thi + (B_ - envB) * Tx * Tlo * Thi
    dy = (-F_ * wf + B_ * wb) * mm
    V1 = V.copy(); V1[idx, 1] += dy[idx]
    info = dict(F=F_, B=B_, wf=wf, wb=wb)
    return V1, idx, info

def smooth_field(V0_, V1, idx, it=2, lam=0.5):
    """light laplacian smoothing of the displacement (not positions) inside the zone, boundary taper preserved by zero disp outside"""
    nb = neighbors(); D = V1 - V0_
    zm = np.zeros(len(V0_), bool); zm[idx] = True
    for _ in range(it):
        D2 = D.copy()
        for i in idx:
            D2[i] = (1 - lam) * D[i] + lam * D[nb[i]].mean(0)
        D = D2
    V2 = V0_ + D; return V2

if __name__ == '__main__':
    out = sys.argv[1]; V1, idx, info = build(P)
    V2 = smooth_field(V0, V1, idx, it=int(P.get('smooth_it', 2)), lam=0.5)
    moved = np.where(np.any(V2 != V0, axis=1))[0]
    print('zone', len(idx), 'moved', len(moved), 'moved outside zone', int(np.setdiff1d(moved, idx).size), 'max |d| mm', float(np.abs(V2 - V0).max() * 1000))
    np.save(out, V2)
