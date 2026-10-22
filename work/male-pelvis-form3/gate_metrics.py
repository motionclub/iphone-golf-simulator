"""FORM3 hard-gate metrics as numbers.  FRONT_SMOOTH_MOUND, BUTT_ROUND_PEACH, NO_PROTRUSION (nothing hangs / points at the crotch, front or back).
python3 gate_metrics.py tag...   (V = data/V_<tag>.npy ; 'start' = chat-9 start ; reads r/sil4_<tag>/ for the slot arch if present)

Definitions (all in mm / deg, zone = pelvis):
 F1  front reach        max forward reach of the front surface (smallest y of the sagittal section) over z .74-.95 at columns |x|<=45 mm, candidate minus chat-9 start.   PASS >= -1.0   (a mound/nub that sticks out forward is negative)
 F2  (dropped)          front-bump / N2 nub-excess definitions were too crude: chat-9 itself fails them; kept in the json as informational only
 F3  front lip dihedral max dihedral angle between neighbouring faces in the front zone (y<-0.05, z .74-.90, |x|<.08).                                                    PASS <= 35
 N1  nothing hangs      centre-column (x=+-3.9 mm) tunnel-roof profile: lip height above the lowest roof point at the REAR lip (y=.057) and FRONT lip (y=-.16).       PASS >= 0 (a lip that hangs below the roof is a protrusion)
 N2  crotch nub         centre-line (|x|<12 mm) sagittal front/rear surfaces never leave the convex envelope of their own neighbours: max local excess over a 25 mm moving average of the profile; PASS <= 1.5
 B1  rear dihedral      max dihedral in the rear zone (y>0, z .74-1.0, |x|<.12).                                                                                          PASS <= 35  (p99 <= 25)
 B2  lobe roundness     horizontal sections at z .80/.84/.88/.92: rear outline y(x) sampled every 4 mm over |x|<=100: max turning angle between neighbouring 4 mm chords (outside the cleft |x|<=20 mm);
                        PASS <= 20 deg (a round lobe of R~60 mm turns ~4 deg / 4 mm)   and no concave stretch outside the cleft (|x| 25-100): y'' must stay <= +0.02 (convex)
 B3  slot top           see-through slot half width w at 4/8/12 mm below the apex (from the 4x silhouette): arch radius R = w^2/(2 dz);   PASS min R >= 9 mm (a pointed tip gives R -> 0, a round arch R >= 10)
 B4  V-ness             fold height at the rear lip z_lip(u) for u = 4/20/40 mm: V-ness = (z(20)-z(4))/(z(40)-z(4)).   U(flat bottom) -> <0.35, straight V -> 0.5 ; informational"""
import sys, json, numpy as np
sys.path.insert(0, '.')
import quality as Q
from common import V0, F, front_curve, rear_curve, section_x, section_segments
import f3_model as M

def gauss_lp(H, su, sz, du, dz):
    ku = np.exp(-0.5 * (np.arange(-int(3 * su / du) - 1, int(3 * su / du) + 2) * du / su) ** 2); ku /= ku.sum()
    kz = np.exp(-0.5 * (np.arange(-int(3 * sz / dz) - 1, int(3 * sz / dz) + 2) * dz / sz) ** 2); kz /= kz.sum()
    P = np.pad(H, ((len(ku) // 2, len(ku) // 2), (len(kz) // 2, len(kz) // 2)), mode='edge')
    T = np.apply_along_axis(lambda v: np.convolve(v, kz, 'valid'), 1, P); return np.apply_along_axis(lambda v: np.convolve(v, ku, 'valid'), 0, T)

def front_hf(V, us, zs):
    H = np.full((len(us), len(zs)), np.nan)
    for i, u in enumerate(us):
        a = front_curve(V, u + 1e-6, zs); b = front_curve(V, -u - 1e-6, zs); H[i] = np.nanmean(np.stack([a, b]), axis=0)
    return H

def roof_z(V, x, ys):
    S = section_x(V, x); out = np.full(len(ys), np.nan)
    for i, y in enumerate(ys):
        best = 9.0
        for (p, q) in S:
            if min(p[0], q[0]) - 0.002 <= y <= max(p[0], q[0]) + 0.002:
                for z in (p[1], q[1]):
                    if 0.72 < z < 0.80: best = min(best, z)
        out[i] = best if best < 9 else np.nan
    return out

def metrics(V, tag=None):
    r = {}
    # ---- F1 front reach ----
    zs = np.arange(0.74, 0.951, 0.005); worst = 0.0; where = None
    for u in (0.004, 0.012, 0.02, 0.03, 0.04, 0.045):
        for s in (1, -1):
            a = front_curve(V, s * u + 1e-6 * s, zs); b = front_curve(V0, s * u + 1e-6 * s, zs)
            ra = np.nanmin(a[zs >= 0.78]); rb = np.nanmin(b[zs >= 0.78]); d = (ra - rb) * 1000     # forward reach = most negative y over the mound/lip range
            if d < worst: worst, where = float(d), (u, s)
    r['F1_front_reach_mm'] = round(worst, 2)
    # ---- F2 front bump ----
    us = np.arange(0.0, 0.0601, 0.005); zz = np.arange(0.80, 0.951, 0.0025)
    H = front_hf(V, us, zz); lp = gauss_lp(np.nan_to_num(H, nan=np.nanmean(H)), 0.015, 0.020, 0.005, 0.0025)
    bump = (lp - H) * 1000                 # forward = smaller y -> lp - H > 0 where the surface sticks out forward of its low-pass
    r['F2_front_bump_mm'] = round(float(np.nanmax(bump)), 2)
    # ---- F3 / B1 dihedral ----
    dd = Q.dihedral(V); a, b = Q._ev[:, 0], Q._ev[:, 1]; mid = (V[a] + V[b]) / 2
    fz = (mid[:, 1] < -0.05) & (mid[:, 2] >= 0.74) & (mid[:, 2] <= 0.90) & (np.abs(mid[:, 0]) <= 0.08)
    rz = (mid[:, 1] > 0.0) & (mid[:, 2] >= 0.74) & (mid[:, 2] <= 1.0) & (np.abs(mid[:, 0]) <= 0.12)
    r['F3_front_dihedral_max'] = round(float(dd[fz].max()), 1); r['F3_front_dihedral_p99'] = round(float(np.percentile(dd[fz], 99)), 1)
    r['B1_rear_dihedral_max'] = round(float(dd[rz].max()), 1); r['B1_rear_dihedral_p99'] = round(float(np.percentile(dd[rz], 99)), 1)
    # ---- N1 hanging lips ----
    ys = np.array([-0.16, -0.12, -0.08, -0.04, 0.0, 0.03, 0.05, 0.057]); rzv = roof_z(V, 0.0039, ys)
    if np.isfinite(rzv).all():
        r['N1_rear_lip_above_roof_min_mm'] = round(float(rzv[-1] - np.nanmin(rzv)) * 1000, 1); r['N1_front_lip_above_roof_min_mm'] = round(float(rzv[0] - np.nanmin(rzv)) * 1000, 1)
    else: r['N1_rear_lip_above_roof_min_mm'] = r['N1_front_lip_above_roof_min_mm'] = None
    # ---- N2 crotch nub: excess of the centre-line front surface over a moving average (sagittal profile y(z) of the section at |x|=4,8,12 mm) ----
    zq = np.arange(0.76, 0.93, 0.004); exc = []
    for x in (0.004, 0.008, 0.012):
        for s in (1, -1):
            f = front_curve(V, s * x, zq); g = np.convolve(np.pad(np.nan_to_num(f, nan=np.nanmean(f)), 3, mode='edge'), np.ones(7) / 7, 'valid')    # 28 mm window
            ok = np.isfinite(f); exc.append(float(np.nanmax((g - f)[ok]) * 1000) if ok.any() else 0.0)
    r['N2_front_nub_excess_mm'] = round(max(exc), 2)
    # ---- B2 lobe roundness ----
    xs = np.arange(-0.100, 0.1001, 0.004); worst_t = 0.0; concave = 0.0
    for z in (0.80, 0.84, 0.88, 0.92):
        S = section_segments(V, z)
        y = np.full(len(xs), np.nan)
        for i, x in enumerate(xs):
            best = -9.0
            for s_ in S:
                (x0, y0), (x1, y1) = s_
                if (x0 - x) * (x1 - x) <= 0 and x0 != x1:
                    t = (x - x0) / (x1 - x0); best = max(best, y0 + t * (y1 - y0))
            y[i] = best if best > -9 else np.nan
        ok = np.isfinite(y)
        if ok.sum() < len(xs) * 0.8: continue
        yy = np.interp(xs, xs[ok], y[ok]); dy = np.diff(yy); ang = np.degrees(np.arctan2(dy, 0.004)); turn = np.abs(np.diff(ang)); xm = (xs[1:-1])
        sel = np.abs(xm) > 0.020; worst_t = max(worst_t, float(turn[sel].max()))
        y2 = (yy[2:] - 2 * yy[1:-1] + yy[:-2]) / 0.004 ** 2 * 1e-3      # curvature-ish, mm/mm^2 *1e3
        sel2 = (np.abs(xm) > 0.025) & (np.abs(xm) < 0.100); concave = max(concave, float(y2[sel2].max()))
    r['B2_lobe_max_turn_deg_per_4mm'] = round(worst_t, 1); r['B2_concave_outside_cleft'] = round(concave, 2)
    # ---- B3 slot top radius from 4x silhouette ----
    try:
        import slotw; m = slotw.measure(tag) if tag else None
        rr = []
        for v in ('front', 'back'):
            ap = m[v]['apex_z']; W = m[v]['widths_mm']
            for dz in (0.004, 0.008, 0.012):
                z_ = ap - dz; k = min(W.keys(), key=lambda s: abs(float(s) - z_))
                if abs(float(k) - z_) <= 0.0026 and W[k] > 0: rr.append((W[k] / 2) ** 2 / (2 * (ap - float(k)) * 1000) if ap - float(k) > 0.0005 else np.nan)
        r['B3_slot_arch_radius_mm'] = round(float(np.nanmin(rr)), 1) if rr and np.isfinite(rr).any() else None
        r['slot_apex'] = {v: round(m[v]['apex_z'], 4) for v in ('front', 'back')}
    except Exception as e: r['B3_slot_arch_radius_mm'] = str(e)
    # ---- B4 V-ness of the rear lip height across u ----
    zl = []
    for u in (0.004, 0.020, 0.040):
        v_ = roof_z(V, u, np.array([0.050])); zl.append(float(v_[0]))
    r['B4_V_ness'] = round((zl[1] - zl[0]) / (zl[2] - zl[0]), 2) if np.isfinite(zl).all() and abs(zl[2] - zl[0]) > 1e-4 else None
    return r

PASS = dict(F1_front_reach_mm=lambda v: v >= -1.0, F3_front_dihedral_max=lambda v: v <= 35, N1_front_lip_above_roof_min_mm=lambda v: v is not None and v >= 0,
            B1_rear_dihedral_max=lambda v: v <= 35, B2_lobe_max_turn_deg_per_4mm=lambda v: v <= 20, B2_concave_outside_cleft=lambda v: v <= 0.02, B3_slot_arch_radius_mm=lambda v: isinstance(v, (int, float)) and v >= 9,
            B4_V_ness=lambda v: v is not None and v < 0.35, N1_rear_lip_above_roof_min_mm=lambda v: v is not None and v >= 0)
GROUPS = dict(FRONT_SMOOTH_MOUND=['F1_front_reach_mm', 'F3_front_dihedral_max', 'N1_front_lip_above_roof_min_mm'],
              BUTT_ROUND_PEACH=['B1_rear_dihedral_max', 'B2_lobe_max_turn_deg_per_4mm', 'B2_concave_outside_cleft', 'B3_slot_arch_radius_mm', 'B4_V_ness', 'N1_rear_lip_above_roof_min_mm'])
def verdict(r):
    return {k: ('PASS' if f(r[k]) else 'FAIL') for k, f in PASS.items() if k in r}

if __name__ == '__main__':
    for t in sys.argv[1:]:
        V = V0 if t == 'start' else np.load(f'data/V_{t}.npy'); r = metrics(V, t); v = verdict(r)
        print(t); print('  ', json.dumps(r)); print('   verdict', {k: x for k, x in v.items()}, '=> FAILS:', [k for k, x in v.items() if x == 'FAIL'])
