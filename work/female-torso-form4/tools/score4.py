"""score4.py: objective for the FORM4 bust fit.  Uses the bald plate photometrically (front view, band-pass at two scales, x-registration search),
the sub-pixel side contour, the dome slope and the seam budgets.  NOT a gate: it only ranks candidates that I then inspect by eye.
J = (1-NCC_s1) + 0.5 (1-NCC_s2) + 0.6 |ln amp| + 0.25 profile_rms + silhouette / slope / curvature / seam penalties."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import photo3 as ph
from photo3 import roi_box, plate_bp, model_multi_bp
from fplate import vertex_normals
from scipy_free import erode
import torso4 as t4
from torso4 import *
import seam
_A0 = seam.dihedral(CO0)
_NB = None

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = np.load(HERE + '/data/plate_front_fine4.npy')
BOX = roi_box('front', -0.105, 0.105, 1.14, 1.30)
SCALES = [(1.6, 9.0), (3.2, 18.0)]
PAD = 36
_c0, _r0, _c1, _r1 = BOX
PB = [plate_bp('front', (_c0 - 12, _r0, _c1 + 12, _r1), s1, s2) for s1, s2 in SCALES]       # plate with +-12 px margin for registration
NOISE = 1.1                                                                                    # plate band-pass noise floor (featureless belly std 1.17)
# 1-D plate profile through the dome columns (grey levels), for the profile term
def env_front_fast(co, zs):
    fe, be = section_extents(co); fe = fillnan(fe)
    return np.interp(zs, ZG, fe)

def dome_slope_deg(co):
    """98th-percentile |dy/dz| angle (deg) of the front surface along the dome column strip |x| .06-.085, z 1.15-1.27 (exact-height sections)"""
    fe, be = section_extents(co, strip=(0.06, 0.085))
    fe = fillnan(fe)
    zz = ZG[(ZG >= 1.15) & (ZG <= 1.27)]
    y = np.interp(zz, ZG, fe)
    g = np.abs(np.gradient(gauss1d(y, 0.004), 0.002))
    return float(np.degrees(np.arctan(np.percentile(g, 98))))

def apex_radius_cm(co):
    """curvature radius (cm) of the side envelope at its apex, parabola fit over +-2 cm"""
    zs = np.arange(1.17, 1.27, 0.002)
    y = env_front_fast(co, zs)
    i = int(np.argmin(y)); m = np.abs(zs - zs[i]) <= 0.02
    c = np.polyfit(zs[m] - zs[i], y[m], 2)
    return float(abs(1 / (2 * c[0])) * 100) if abs(c[0]) > 1e-9 else 99.0


def bust_dihedral(co):
    """worst dihedral (deg) and increase vs the original on the front bust region (interior edges that were smooth in the original)"""
    a1 = seam.dihedral(co)
    mid = 0.5 * (co[seam.PAIR_E[:, 0]] + co[seam.PAIR_E[:, 1]])
    nb = ~(BORDER[seam.PAIR_E[:, 0]] | BORDER[seam.PAIR_E[:, 1]]) & (_A0 <= 15.0)
    reg = seam.ZPAIR & nb & (mid[:, 2] >= 1.14) & (mid[:, 2] <= 1.32) & (np.abs(mid[:, 0]) <= 0.115) & (mid[:, 1] < 0)
    regc = seam.ZPAIR & (mid[:, 2] >= 1.15) & (mid[:, 2] <= 1.30) & (np.abs(mid[:, 0]) < 0.022) & (mid[:, 1] < 0)
    return float(a1[reg].max()), float((a1 - _A0)[reg].max()), float(a1[regc].max())

def evaluate(co, detail=False):
    mbs, mask = model_multi_bp(co, 'front', BOX, SCALES, pad=PAD)
    m = erode(mask, 6)
    out = {}
    nccs = []; amps = []
    best = None
    for sh in (-2, 0, 2, 4):
        tot = 0; res = []
        for pb_full, mb in zip(PB, mbs):
            pb = pb_full[:, 12 + sh:12 + sh + (_c1 - _c0)]
            a, b = pb[m], mb[m]
            a0, b0 = a - a.mean(), b - b.mean()
            ncc = float((a0 * b0).sum() / np.sqrt((a0 ** 2).sum() * (b0 ** 2).sum() + 1e-12))
            res.append((ncc, b0.std(), a0.std()))
        s = res[0][0] + 0.5 * res[1][0]
        if best is None or s > best[0]:
            best = (s, sh, res)
    _, sh, res = best
    ncc1, ncc2 = res[0][0], res[1][0]
    plate_rel = np.sqrt(max(res[0][2] ** 2 - NOISE ** 2, 0.5))
    amp = res[0][1] / plate_rel
    zs = np.arange(1.15, 1.32, 0.01)
    pf = np.interp(zs, FF[0], FF[1]); mf = env_front_fast(co, zs)
    rms = float(np.sqrt(((mf - pf) ** 2).mean()) * 1000)
    # side envelope (apex band) separately: z 1.15..1.27 must be tight, upper diagonal is limited by the neck ring
    zl = (zs <= 1.27)
    rms_low = float(np.sqrt(((mf - pf)[zl] ** 2).mean()) * 1000)
    slope = dome_slope_deg(co)
    rc = apex_radius_cm(co)
    dh, dhi, dhc = bust_dihedral(co)
    bs = seam.border_steps(co)[0]
    AMP_T = float(os.environ.get('AMP_T', '1.0')); AMP_W = float(os.environ.get('AMP_W', '1.0'))
    J = (1 - ncc1) + 0.5 * (1 - ncc2) + AMP_W * abs(np.log(max(amp / AMP_T, 1e-3)))
    pen = 0.0
    pen += 0.35 * max(0.0, rms_low - 2.5)
    pen += 0.04 * max(0.0, rms - 7.0)
    SL = float(os.environ.get('SLOPE_MAX', '36')); RCMIN = float(os.environ.get('RC_MIN', '4.2'))
    pen += 0.05 * max(0.0, slope - SL)
    pen += 0.25 * max(0.0, RCMIN - rc) + 0.04 * max(0.0, rc - 8.0)
    pen += 0.15 * max(0.0, dhc - 11.0)
    pen += 0.20 * max(0.0, dh - 28.5) + 0.20 * max(0.0, dhi - 23.5)
    pen += 3.0 * max(0.0, bs['arm']['max_mm'] - 9.5) + 3.0 * max(0.0, bs['top']['max_mm'] - 0.98) + 3.0 * max(0.0, bs['legs']['max_mm'] - 7.6)
    J += pen
    out = dict(J=float(J), ncc1=ncc1, ncc2=ncc2, amp=float(amp), rms=rms, rms_low=rms_low, slope98=slope, rc=rc, dih=dh, dihi=dhi, dihc=dhc, shift=sh, arm=bs['arm']['max_mm'], top=bs['top']['max_mm'], legs=bs['legs']['max_mm'], pen=float(pen))
    return out

if __name__ == '__main__':
    for a in sys.argv[1:]:
        tag, p = a.split('=', 1)
        co = np.load(p).astype(np.float64)
        r = evaluate(co)
        print(f"{tag:8s} J {r['J']:.3f} | ncc {r['ncc1']:.3f}/{r['ncc2']:.3f} amp {r['amp']:.2f} | sil rms {r['rms']:.1f} (low {r['rms_low']:.1f}) mm | slope98 {r['slope98']:.1f} Rc {r['rc']:.1f} | dih {r['dih']:.1f}/{r['dihi']:.1f} c{r['dihc']:.1f} | arm {r['arm']:.2f} top {r['top']:.2f} | pen {r['pen']:.2f}")
