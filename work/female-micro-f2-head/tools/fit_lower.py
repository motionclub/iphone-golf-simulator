"""fit the loft half-width a(z) (lower face rows) so the analytic front silhouette equals the SMOOTHED plate jaw contour.
Also reports sagittal chin corner / under-chin line errors.  Used as a module (fit(...)) and as a script."""
import sys, json, copy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f2-head/tools')
import numpy as np, geo, geo2, loftf, fl, phi2, exp
from fl import sstep

sil = json.load(open(fl.W / 'data/sil.json'))
ROWS = [r for r in range(196, 253) if sil['front'].get(str(r))]
ZP = np.array([fl.zrow(r) for r in ROWS])[::-1]                       # ascending z
HWP = np.array([0.5 * (sil['front'][str(r)][1] - sil['front'][str(r)][0] + 1) * fl.K for r in ROWS])[::-1]


def smooth_plate_hw(z, sig=0.0040):
    """plate jaw half width, Gaussian-smoothed in z (kills the 1-px quantisation); neck rows (<1.4455) keep the neck value"""
    zz = np.asarray(z, float); out = np.empty_like(zz)
    for i, zi in enumerate(zz):
        w = np.exp(-0.5 * ((ZP - zi) / sig) ** 2); out[i] = (w * HWP).sum() / w.sum()
    return out


class Fit:
    def __init__(self, ctx, under, fb=exp.FB_VERT, prof=None, zlo=1.4455, zhi=1.4985, step=0.0010, a_fix=None):
        self.ctx = ctx; self.under = under; self.fb = fb; self.prof = prof if prof is not None else exp.prof_nochin()
        self.zg = np.arange(1.420, 1.5300, step)                      # correction knots
        self.da = np.zeros(len(self.zg)); self.zlo = zlo; self.zhi = zhi
        self.base_a = None

    def head(self, extra=None):
        H = exp.build(under=self.under, fb=self.fb, prof=self.prof, prm_extra=extra)
        if self.base_a is None: self.base_a = H.L.a.copy()
        H.L.a = self.base_a + np.interp(H.L.zk, self.zg, self.da)
        return H

    def silhouette(self, H, zs):
        P = H.phi(self.ctx.U)
        out = []
        for z in zs:
            m = (np.abs(P[:, 2] - z) < 0.0009) & (P[:, 1] < 0.06)
            out.append(np.abs(P[m, 0]).max() if m.sum() > 2 else np.nan)
        return np.array(out)

    def iterate(self, n=6, verbose=True, damp=0.8):
        zs = np.arange(1.436, 1.5000, 0.0015)
        tgt = smooth_plate_hw(zs)
        tgt = np.where(zs < self.zlo, np.minimum(tgt, 0.0523), tgt)
        for it in range(n):
            H = self.head()
            hw = self.silhouette(H, zs)
            err = tgt - hw
            ok = ~np.isnan(err)
            if verbose: print(f'iter {it}: hw error mm  mean|e| {np.nanmean(np.abs(err))*1000:.2f}  max|e| {np.nanmax(np.abs(err))*1000:.2f}')
            # smooth the error and apply it to the correction knots (only inside [zlo-0.01, zhi+0.01], tapered)
            e_k = np.interp(self.zg, zs[ok], err[ok], left=0.0, right=0.0)
            taper = sstep(self.zlo - 0.014, self.zlo - 0.004, self.zg) * (1.0 - sstep(self.zhi, self.zhi + 0.020, self.zg))
            self.da += damp * e_k * taper
        H = self.head(); hw = self.silhouette(H, zs); err = tgt - hw
        if verbose: print(f'final: mean|e| {np.nanmean(np.abs(err))*1000:.2f} max|e| {np.nanmax(np.abs(err))*1000:.2f}')
        return H, zs, tgt, hw
