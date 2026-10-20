"""Anatomy / quality metrics for the new hands, measured on the assembled candidate (final vertex array) via the builder role maps."""
import sys, json
from pathlib import Path
import numpy as np
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
from hlib import *
import asm3

def sidepos(Vn, si, side):
    """local-coordinate position lookup for builder ids of one side"""
    m = si[side]['mapping']
    def P(vid):
        return to_local(Vn[[m[vid]]], side)[0]
    return P

def finger_metrics(Vn, si, side):
    P = sidepos(Vn, si, side); info = si[side]['info']; Pm = info['P']
    out = []
    for k, (rows, C) in info['fin_rows'].items():
        R = [np.array([P(v) for v in r]) for r in rows]                 # (10,3) each in local coords
        n = len(R)
        width = np.array([abs(r[0][0] - r[5][0]) for r in R])             # |WL - WR| along a'
        # dorsal / palmar centre points of each ring
        dors = np.array([0.5 * (r[2] + r[3]) for r in R]); palm = np.array([0.5 * (r[7] + r[8]) for r in R])
        depth = np.linalg.norm(palm - dors, axis=1)
        wpos = np.array([r.mean(0)[2] for r in R])
        # shaft rows = rows before the cap
        n_cap = len(Pm['cap_angles']); shaft = slice(0, n - n_cap)
        wsh = width[shaft]
        base = width[0]; mid = width[len(wsh) // 2]; tipw = width[n - n_cap - 1]
        # dorsal contour bumps relative to a smooth (quadratic) fit over the shaft
        ww = wpos[shaft]; nn = dors[shaft][:, 1]
        cf = np.polyfit(ww, nn, 2); dev = nn - np.polyval(cf, ww)         # negative = dorsal bump (n more negative)
        # joint rows: nearest ring to s_pip, s_dip in w
        w0 = Pm['w_knuckle']; Lw = Pm['f_tip'][k] - w0
        def joint_dev(s):
            best = (0.0, 0)
            for j in range(2, len(ww) - 2):
                if abs((ww[j] - w0) / Lw - s) <= 0.07:
                    ref = 0.5 * (nn[j - 2] + nn[j + 2]); val = float((ref - nn[j]) * 1000)      # positive = row j is more dorsal than its neighbours
                    if val > best[0]: best = (val, j)
            return best
        bp, jp = joint_dev(Pm['s_pip']); bd, jd = joint_dev(Pm['s_dip'])
        monotone = bool(np.all(np.diff(wsh) <= 0.00015))
        out.append(dict(finger=k, width_base_mm=base * 1000, width_mid_mm=mid * 1000, width_tip_shaft_mm=tipw * 1000,
                        taper_tip_over_base=float(tipw / base), taper_mid_over_base=float(mid / base), width_monotone=monotone,
                        depth_base_mm=float(depth[0] * 1000), depth_over_width_base=float(depth[0] / base),
                        depth_tip_mm=float(depth[n - n_cap - 1] * 1000), pip_bump_mm=bp, dip_bump_mm=bd, rows=n,
                        cap_rows=n_cap, length_mm=float((wpos[-1] - w0) * 1000)))
    # gaps between neighbouring fingers at mid length (a' separation of ring centres minus half widths)
    gaps = []
    for k in range(3):
        rows_a, _ = info['fin_rows'][k]; rows_b, _ = info['fin_rows'][k + 1]
        for fr in (0.4, 0.7):
            ja = int(fr * (len(rows_a) - 1 - len(Pm['cap_angles']))); jb = int(fr * (len(rows_b) - 1 - len(Pm['cap_angles'])))
            ra = np.array([P(v) for v in rows_a[ja]]); rb = np.array([P(v) for v in rows_b[jb]])
            gaps.append(float((ra[0][0] - rb[5][0] if False else (rb[0][0] - ra[5][0]))) * 1000)    # WL of finger k+1? (index at +a')
    return out, gaps

def thumb_metrics(Vn, si, side):
    P = sidepos(Vn, si, side); info = si[side]['info']; Pm = info['P']
    rows = info['thumb_rows']; R = [np.array([P(v) for v in r]) for r in rows]
    cen = [r.mean(0) for r in R]
    rad = np.array([np.mean(np.linalg.norm(r - c, axis=1)) for r, c in zip(R, cen)])
    cen = np.array(cen)
    seg = np.diff(cen, axis=0); L = np.linalg.norm(seg, axis=1)
    ang = []
    for i in range(1, len(seg)):
        a = seg[i - 1] / L[i - 1]; b = seg[i] / L[i]; ang.append(np.degrees(np.arccos(np.clip(a @ b, -1, 1))))
    n_cap = len(Pm['cap_angles'])
    shaft = rad[:len(rad) - n_cap]
    dense, cum = info['thumb_axis']; tot = cum[-1]
    # axis direction change at the IP (between first half and second half of the axis)
    a1 = dense[len(dense) // 2] - dense[len(dense) // 6]; a2 = dense[-1] - dense[len(dense) // 2]
    ip = float(np.degrees(np.arccos(np.clip(a1 @ a2 / np.linalg.norm(a1) / np.linalg.norm(a2), -1, 1))))
    imax = int(np.argmax(shaft[2:-1])) + 2
    return dict(radius_root_mm=float(shaft[0] * 1000), radius_max_shaft_mm=float(shaft.max() * 1000), radius_at_max_row=imax,
                radius_last_shaft_mm=float(shaft[-1] * 1000), taper_last_over_max=float(shaft[-1] / shaft.max()),
                radii_mm=[round(float(x) * 1000, 2) for x in rad], ip_axis_bend_deg=ip, length_mm=float(tot * 1000), rows=len(rows), cap_rows=n_cap,
                max_ring_to_ring_bend_deg=float(max(ang)) if ang else 0.0)

def dihedral_stats(Vn, polys, idx_polys):
    ef = edge_faces(polys); Fn = face_normals(Vn, polys)
    S = set(idx_polys); out = []
    for (a, b), fs in ef.items():
        if len(fs) == 2 and fs[0] in S and fs[1] in S:
            c = np.clip((Fn[fs[0]] * Fn[fs[1]]).sum(), -1, 1); out.append(np.degrees(np.arccos(c)))
    out = np.array(out)
    return dict(edges=int(len(out)), gt30=int((out > 30).sum()), gt45=int((out > 45).sum()), gt60=int((out > 60).sum()), gt90=int((out > 90).sum()), max=float(out.max()))
