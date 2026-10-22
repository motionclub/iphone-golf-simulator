"""Held-out validation views (sheet back 3/4 panels): high-passed shading correlation over the visible torso-zone vertices for a candidate mesh."""
import sys, json
sys.path.insert(0, '.')
from pmo_t import *
from plateview import ViewYaw, SHEET, visible_gen, sh2c
class Val:
    def __init__(self, T, names=('q3BL', 'q3BR'), blur=1.1):
        cal = json.load(open('data/q3_calib2.json')); self.T = T; self.v = {}; SHB = gblur(SHEET, blur)
        V0 = T.V0; N0 = T.N0; body = (V0[:, 2] < 1.40) & (np.abs(V0[:, 0]) < 0.62); x = V0[:, 0]; z = V0[:, 2]; ax = np.abs(x)
        for nm in names:
            c = cal[nm]; vw = ViewYaw(nm, c['yaw'], c['col0'], c['mpp'], c['sole_row']); vis = visible_gen(vw, V0, N0, sel=V0[:, 2] < 1.40, res=1.0, rad=1)
            col, row = vw.project(V0); I = bilinear(SHB, col, row); A = sh2c(N0, vw); fit = vis & body & ~T.Z
            cc, *_ = np.linalg.lstsq(A[fit], I[fit], rcond=None)
            wgt = np.clip(N0 @ vw.toward, 0, 1) * (1 - sstep((ax - 0.14) / 0.06)) * sstep((z - 0.795) / 0.03) * (1 - sstep((z - 1.345) / 0.03))
            sel = np.where(vis & T.Z & (wgt > 0.05))[0]
            self.v[nm] = dict(vw=vw, c=cc, I=I[sel], sel=sel, HP=T._hp(sel), w=wgt[sel])
    def score(self, P, regions=None):
        N = self.T.normals(P); out = {}
        for nm, v in self.v.items():
            M = sh2c(N[v['sel']], v['vw']) @ v['c']; a = self.T.hp(v['I'], v['HP']); b = self.T.hp(M, v['HP']); w = v['w']
            out[nm] = float(np.corrcoef(a, b)[0, 1])
            zz = self.T.V0[v['sel'], 2]
            for rn, (z0, z1) in (('upper', (1.15, 1.34)), ('lumbar', (0.90, 1.15)), ('glute', (0.80, 0.90))):
                m = (zz >= z0) & (zz < z1) & (np.abs(self.T.V0[v['sel'], 0]) < 0.12)
                out[f'{nm}_{rn}'] = float(np.corrcoef(a[m], b[m])[0, 1]) if m.sum() > 10 else float('nan')
        return out
