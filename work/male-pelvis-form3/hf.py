"""Heightfield views of the body surface: H_rear(u,z) = rear-most y and H_front(u,z) = front-most y of the sagittal section X=+-u (u=|x|),
averaged over both sides.  Used to remap/warp the surface smoothly and evaluate the remap at the vertices' own (u,z).
numpy only (Blender python3.13)."""
import numpy as np
from common import *

class Grid:
    def __init__(self, u, z, H, name=''):
        self.u, self.z, self.H, self.name = u, z, H, name
    def sample(self, uq, zq):
        """bilinear sample with clamping; NaN cells must have been filled"""
        uq = np.clip(uq, self.u[0], self.u[-1]); zq = np.clip(zq, self.z[0], self.z[-1])
        fu = (uq - self.u[0]) / (self.u[1] - self.u[0]); fz = (zq - self.z[0]) / (self.z[1] - self.z[0])
        iu = np.clip(np.floor(fu).astype(int), 0, len(self.u) - 2); iz = np.clip(np.floor(fz).astype(int), 0, len(self.z) - 2)
        tu = fu - iu; tz = fz - iz; H = self.H
        return (H[iu, iz] * (1 - tu) * (1 - tz) + H[iu + 1, iz] * tu * (1 - tz) + H[iu, iz + 1] * (1 - tu) * tz + H[iu + 1, iz + 1] * tu * tz)

def _fill(H):
    """fill NaNs along z by nearest-valid linear interpolation, then along u"""
    H = H.copy()
    for i in range(H.shape[0]):
        r = H[i]; m = np.isfinite(r)
        if m.sum() >= 2 and (~m).any(): H[i] = np.interp(np.arange(len(r)), np.where(m)[0], r[m])
    return H

def build(V, which, u=None, z=None):
    u = np.arange(0.0, 0.2101, 0.005) if u is None else u; z = np.arange(0.70, 1.0801, 0.0025) if z is None else z
    f = rear_curve if which == 'rear' else front_curve
    H = np.full((len(u), len(z)), np.nan)
    for i, uu in enumerate(u):
        a = f(V, uu + 1e-6, z); b = f(V, -uu - 1e-6, z)
        both = np.stack([a, b]); H[i] = np.nanmean(both, axis=0) if np.isfinite(both).any() else np.nan
    return Grid(u, z, _fill(H), which)

if __name__ == '__main__':
    import time; t = time.time(); g = build(V0, 'rear'); print('built rear grid', g.H.shape, round(time.time() - t, 1), 's')
    np.savez('data/hf_rear_start.npz', u=g.u, z=g.z, H=g.H)
    g2 = build(V0, 'front'); np.savez('data/hf_front_start.npz', u=g2.u, z=g2.z, H=g2.H)
    # symmetry check: compare +u and -u sections
    za = np.arange(0.78, 1.05, 0.01)
    for uu in (0.02, 0.06, 0.10, 0.14):
        a = rear_curve(V0, uu + 1e-6, za); b = rear_curve(V0, -uu - 1e-6, za)
        print('asym rear u', uu, 'max |dy| mm', np.nanmax(np.abs(a - b)) * 1000)
