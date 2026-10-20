"""Depth guard: restore the front-most / back-most y per height slab to a reference (so the side-silhouette depth cannot drift), smooth in z, tapered at the zone ends."""
import numpy as np
from zone import zone_mask
def sstep(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)
def extremes(V, Z, zs, half=0.006, xmax=0.20):
    F = np.full(len(zs), np.nan); B = np.full(len(zs), np.nan)
    for i, z in enumerate(zs):
        m = Z & (np.abs(V[:, 2] - z) < half) & (np.abs(V[:, 0]) < xmax)
        if m.sum() >= 3: F[i] = V[m, 1].min(); B[i] = V[m, 1].max()
    return F, B
def slab_fix(Vnew, Vref, wf, wb, sigma=0.010, zlo=0.80, zhi=1.36, only=None, tol=0.0):
    """returns corrected copy.  wf/wb: front/back weights per vertex (same as the sculpt).  only: optional bool mask of vertices allowed to move."""
    Z = zone_mask(Vref); zs = np.arange(0.775, 1.40, 0.0025)
    F0, B0 = extremes(Vref, Z, zs); F1, B1 = extremes(Vnew, Z, zs)
    dF = F0 - F1; dB = B0 - B1                                   # + = shift toward +y
    if tol > 0: dF = np.sign(dF) * np.maximum(np.abs(dF) - tol * 1e-3, 0); dB = np.sign(dB) * np.maximum(np.abs(dB) - tol * 1e-3, 0)   # tolerant: only the drift beyond tol (mm) is corrected
    def smooth(a):
        a = np.where(np.isnan(a), 0.0, a); k = int(3 * sigma / 0.0025); xs = np.arange(-k, k + 1) * 0.0025; w = np.exp(-0.5 * (xs / sigma) ** 2); w /= w.sum()
        return np.convolve(np.pad(a, k, mode='edge'), w, 'valid')
    dF = smooth(dF); dB = smooth(dB)
    z = Vnew[:, 2]; ax = np.abs(Vnew[:, 0])
    tz = sstep((z - zlo) / 0.03) * (1 - sstep((z - zhi) / 0.03)); tx = 1 - sstep((ax - 0.15) / 0.07)
    dy = (wf * np.interp(z, zs, dF) + wb * np.interp(z, zs, dB)) * tz * tx * Z
    if only is not None: dy = dy * only
    V2 = Vnew.copy(); V2[:, 1] += dy; return V2, dF, dB

def slab_fix_iter(Vnew, Vref, wf, wb, n=4, sigma=0.0045, tol=0.0, **kw):
    """repeat the depth guard on its own residual (finer smoothing) until the slab extremes sit on the reference"""
    V = Vnew.copy(); Z = zone_mask(Vref); zs = np.arange(0.80, 1.36, 0.0025)
    for k in range(n):
        V, dF, dB = slab_fix(V, Vref, wf, wb, sigma=sigma, tol=tol, **kw)
    F0, B0 = extremes(Vref, Z, zs); F1, B1 = extremes(V, Z, zs)
    return V, float(np.nanmax(np.abs(F1 - F0)) * 1000), float(np.nanmax(np.abs(B1 - B0)) * 1000)
