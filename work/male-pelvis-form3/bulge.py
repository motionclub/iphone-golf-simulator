"""3/4-back silhouette 'bulge profile': (plate - mesh) edge offset (mm) vs z minus the thigh-level reference (median over z 0.58-0.74), per panel edge.
python3 bulge.py <tag...>  (renders r/<tag>_s via overlay.py if missing)"""
import sys, os, numpy as np
import sil34, overlay
import panel_cmp as PC
ZS = np.arange(0.74, 1.00, 0.02) if not os.environ.get('BZ') else np.arange(*[float(v) for v in os.environ['BZ'].split(',')]); ZR = np.arange(0.58, 0.745, 0.02)
def offsets(tag, panel, zs):
    yaw, col0, mpp, sole = sil34.SH[panel][1]; t, c0, c1, r0, r1 = PC.BOX[panel][:5]; out = []
    for z in zs:
        r = int(round(sole - (z - 0.00247) / mpp)); cc0, cc1 = {'q_bl': (690, 890), 'q_br': (980, 1180), 'q_fl': (85, 285), 'q_fr': (378, 578)}[panel]
        pr = sil34.plate_runs(panel, r, cc0, cc1, sil34.BG[panel]); mr = sil34.mesh_runs(panel, tag, r)
        p = sil34.central(pr, col0) if pr else None; m = sil34.central(mr, col0) if mr else None
        out.append((np.nan, np.nan) if (p is None or m is None) else ((p[0] - m[0]) * mpp * 1000, (p[1] - m[1]) * mpp * 1000))
    return np.array(out)
PAN = os.environ.get('BPANELS', 'q_bl,q_br').split(',')
def profile(tag):
    res = {}
    for panel in PAN:
        o = offsets(tag, panel, ZS); ref = np.nanmedian(offsets(tag, panel, ZR), axis=0)
        res[panel] = o - ref
    return res
if __name__ == '__main__':
    for tag in sys.argv[1:]:
        if not os.path.exists(PC.W / f'r/{tag}_s'): overlay.render(tag)
        pr = profile(tag); print(f'== {tag}: bulge = (plate-mesh offset) - thigh reference, mm  (L edge, R edge) per panel')
        print('z    ' + ' | '.join(f'{p}.L   {p}.R' for p in PAN))
        for i, z in enumerate(ZS): print(f'{z:.2f} ' + ' | '.join(f'{pr[p][i,0]:6.1f} {pr[p][i,1]:6.1f}' for p in PAN))
