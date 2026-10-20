"""Torso sculpt v3: Taubin base clean-up + plate-positioned analytic forms, existing topology, zone only.
python3.13 sculpt3.py <out.npy> [params.json]"""
import sys, json
import numpy as np
from zone import *
from sculpt import sstep, interp, g, g2, g2a, poly_groove
mm = 1e-3
_csr = None
def csr():
    global _csr
    if _csr is None:
        nb = neighbors(); raw = np.array([len(a) for a in nb]); print('loose/zero-neighbour verts:', int((raw == 0).sum())); cnt = np.maximum(raw, 1); ptr = np.concatenate([[0], np.cumsum(raw)]); ind = np.concatenate(nb); _csr = (ptr, ind, cnt)
    return _csr
def lap(V):
    ptr, ind, cnt = csr(); raw = np.diff(ptr); s = np.zeros_like(V); ok = raw > 0; s[ok] = np.add.reduceat(V[ind], ptr[:-1][ok], axis=0) if False else 0
    s = np.zeros_like(V)
    for c in range(3): s[:, c] = np.bincount(np.repeat(np.arange(len(V)), raw), weights=V[ind, c], minlength=len(V))
    m = s / cnt[:, None]; m[raw == 0] = V[raw == 0]; return m - V
def taubin(V, w, it=8, lam=0.5, mu=-0.53):
    """w: per-vertex weight 0..1 (0 = fixed)"""
    V = V.copy()
    for _ in range(it):
        V += lam * w[:, None] * lap(V); V += mu * w[:, None] * lap(V)
    return V

DEF = dict(
    smooth_it=10, band_it=60, band_top=0.88, upper_it=14,
    env_front=[(0.775, 0), (0.83, 0), (0.88, 3), (0.93, 7), (1.22, 8), (1.30, 3), (1.34, 2), (1.385, 0)],
    env_back=[(0.775, 0), (0.83, 0), (0.88, 3), (0.93, 5), (1.0, 3.0), (1.08, 5.5), (1.24, 10), (1.30, 6), (1.34, 4), (1.385, 0)],
    pec=10.0, pec_edge=3.0, sternum=1.6, clav=0.6, belly=4.0, oblique=3.5, pubic=5.0, groin=3.5, rectus=0.8, abs_groove=0.6,
    trap=3.0, scap=2.0, spine=0.4, glute=19.0, cleft=6.5, lumbar=0.0, rib=4.0)

def build(P, V=V0):
    zm = zone_mask(V); idx = np.where(zm)[0]
    x, y, z = V[:, 0], V[:, 1], V[:, 2]; ax = np.abs(x)
    # ---- 1) low-frequency clean-up of the blockout (inner torso only; flanks/shoulder rim/zone borders stay put)
    wsm = (1 - sstep((ax - 0.12) / 0.06)) * sstep((z - 0.80) / 0.05) * (1 - sstep((z - 1.28) / 0.06)) * zm
    Vs = taubin(V, wsm, it=int(P['smooth_it'])) if P['smooth_it'] else V.copy()
    # ---- 1b) fair the pelvis shelf: heavy Taubin on the band just above the (pinned) leg-top ring
    wb_ = sstep((V[:, 2] - 0.776) / 0.012) * (1 - sstep((V[:, 2] - P['band_top'] + 0.02) / 0.04)) * zm
    if P['band_it']: Vs = taubin(Vs, wb_, it=int(P['band_it']))
    # ---- 1c) upper-back / shoulder-band ridge clean-up (z~1.31 crease)
    wu = sstep((V[:, 2] - 1.20) / 0.03) * (1 - sstep((V[:, 2] - 1.36) / 0.025)) * (1 - sstep((np.abs(V[:, 0]) - 0.17) / 0.07)) * zm
    if P['upper_it']: Vs = taubin(Vs, wu, it=int(P['upper_it']))
    # ---- 2) forms (pure y moves)
    x, y, z = Vs[:, 0], Vs[:, 1], Vs[:, 2]
    zz = np.arange(0.76, 1.42, 0.005); yc_ = np.zeros(len(zz)); hd_ = np.zeros(len(zz))
    for i, zf in enumerate(zz):
        m = (np.abs(Vs[:, 2] - zf) < 0.008) & (np.abs(Vs[:, 0]) < 0.09); yc_[i] = 0.5 * (Vs[m, 1].min() + Vs[m, 1].max()); hd_[i] = 0.5 * (Vs[m, 1].max() - Vs[m, 1].min())
    k = np.ones(5) / 5; yc_ = np.convolve(np.pad(yc_, 2, mode='edge'), k, 'valid'); hd_ = np.convolve(np.pad(hd_, 2, mode='edge'), k, 'valid')
    u = (y - np.interp(z, zz, yc_)) / np.interp(z, zz, hd_)
    wf = sstep((-u - 0.12) / 0.55); wb = sstep((u - 0.12) / 0.55)
    Tx = 1 - sstep((ax - 0.13) / 0.11); Tx2 = 1 - sstep((ax - 0.17) / 0.07)
    Tlo = sstep((z - 0.775) / 0.045); Thi = 1 - sstep((z - 1.30) / 0.085)
    envF = interp(z, P['env_front']); envB = interp(z, P['env_back'])
    F_ = np.zeros(len(V)); B_ = np.zeros(len(V))
    # FRONT forms
    pec = np.zeros(len(V))
    for sg in (-1, 1): pec += g2a(x, z, sg * 0.085, 1.238, 0.058, 0.032, 0.060)
    pec = np.minimum(pec, 1.0) * P['pec']
    edge = np.zeros(len(V))
    for sg in (-1, 1):
        gr, t = poly_groove(x, z, [(sg * 0.190, 1.218), (sg * 0.150, 1.188), (sg * 0.115, 1.172), (sg * 0.075, 1.172), (sg * 0.035, 1.182), (0, 1.193)], 0.0095); edge += gr
    edge = np.minimum(edge, 1.0) * -P['pec_edge']
    stern = g(x, 0.016) * sstep((z - 1.19) / 0.05) * (1 - sstep((z - 1.29) / 0.05)) * -P['sternum']
    clav = np.zeros(len(V))
    for sg in (-1, 1):
        gr, t = poly_groove(x, z, [(sg * 0.025, 1.368), (sg * 0.11, 1.352), (sg * 0.20, 1.335)], 0.011); clav += gr
    clav = np.minimum(clav, 1) * P['clav']
    belly = g2(x, z, 0.0, 0.95, 0.09, 0.065) * P['belly']
    obl = (g2(x, z, 0.132, 0.985, 0.028, 0.042) + g2(x, z, -0.132, 0.985, 0.028, 0.042)) * P['oblique']
    pub = g2(x, z, 0.0, 0.838, 0.048, 0.038) * P['pubic']
    rect = (g2(x, z, 0.036, 1.07, 0.022, 0.085) + g2(x, z, -0.036, 1.07, 0.022, 0.085)) * P['rectus']
    ag = -g(x, 0.006) * sstep((z - 0.90) / 0.04) * (1 - sstep((z - 1.16) / 0.03)) * P['abs_groove']
    gro = np.zeros(len(V))
    for sg in (-1, 1):
        gr, t = poly_groove(x, z, [(sg * 0.168, 0.925), (sg * 0.120, 0.875), (sg * 0.080, 0.830), (sg * 0.045, 0.790)], 0.014); gro += gr
    gro = np.minimum(gro, 1) * -P['groin']
    rib = g2(x, z, 0.0, 1.09, 0.10, 0.05) * P['rib']
    F_ = (rib + pec + edge + stern + clav + belly + obl + pub + rect + ag + gro) * Tx2 * Tlo * Thi
    # BACK forms
    trap = g2(x, z, 0.0, 1.315, 0.10, 0.05) * P['trap']
    scap = (g2(x, z, 0.085, 1.225, 0.05, 0.055) + g2(x, z, -0.085, 1.225, 0.05, 0.055)) * P['scap']
    spine = -g(x, 0.008) * sstep((z - 1.0) / 0.05) * (1 - sstep((z - 1.33) / 0.03)) * P['spine']
    lumb = -g2(x, z, 0.0, 1.02, 0.12, 0.04) * P['lumbar']
    glu = (g2a(x, z, 0.076, 0.866, 0.058, 0.046, 0.058) + g2a(x, z, -0.076, 0.866, 0.058, 0.046, 0.058)) * P['glute']
    cz = np.array([0.775, 0.80, 0.86, 0.90, 0.95, 1.00]); cd = np.array([0.0, 5.5, 8, 4.5, 1.6, 0.0])
    cs = interp(z, list(zip(cz, cd))); cw = 0.012 + 0.010 * (1 - sstep((z - 0.78) / 0.20))
    cleft = -np.exp(-0.5 * (x / cw) ** 2) * cs * (P['cleft'] / 9.0)
    B_ = (trap + scap + spine + lumb + glu + cleft) * Tx2 * Tlo * Thi
    F_ = F_ + envF * Thi * (Tx * (z > 0)); B_ = B_ + envB * Thi * (Tx * (z > 0))
    dy = (-F_ * wf + B_ * wb) * mm
    V1 = Vs.copy(); V1[idx, 1] += dy[idx]
    # nothing outside the zone moves: restore
    out = V.copy(); out[idx] = V1[idx]
    return out, idx

if __name__ == '__main__':
    P = dict(DEF)
    if len(sys.argv) > 2: P.update(json.load(open(sys.argv[2])))
    V1, idx = build(P)
    moved = np.where(np.any(V1 != V0, axis=1))[0]
    d = np.linalg.norm(V1 - V0, axis=1) * 1000
    print('zone', len(idx), 'moved', len(moved), 'outside zone', int(np.setdiff1d(moved, idx).size), 'max mm', round(float(d.max()), 2), 'mean(moved) mm', round(float(d[moved].mean()), 2))
    np.save(sys.argv[1], V1)
