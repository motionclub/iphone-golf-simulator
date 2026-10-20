"""All hand metrics for one parameter set (FORM2 = '{}'), measured identically.  py.sh allmetrics.py <tag> '<params json>' out.json
Adds to run_metrics: thenar mound, thumb-root dihedral (25 mm), thumb IP bump, finger width runs, face quality,
PALM metrics (length / breadth / planform area / palm:finger), TIP metrics (hemisphere ratio, contour kink, flat-cap fraction, cap rows)."""
import sys, json
from pathlib import Path
import numpy as np
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import asm3, run_metrics, hand4
from hlib import *

def loc(Vn, si, side):
    m = si[side]['mapping']
    return lambda vid: to_local(Vn[[m[vid]]].astype(float), side)[0]

def polyline_turn(pts2):
    """max / mean turning angle (deg) along a 2D polyline (excluding endpoints)"""
    d = np.diff(pts2, axis=0); d = d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-12)
    ang = np.degrees(np.arccos(np.clip((d[:-1] * d[1:]).sum(1), -1, 1)))
    return ang

def tip_metrics(Vn, polys, si, side, params):
    P = si[side]['info']['P']; info = si[side]['info']; Lp = loc(Vn, si, side); n_cap = len(P['cap_angles'])
    digits = []
    for k, (rows, C) in info['fin_rows'].items(): digits.append((f'finger{k}', rows, C, 'finger'))
    digits.append(('thumb', info['thumb_rows'], info['thumb_tip'], 'thumb'))
    out = {}
    mp = si[side]['mapping']
    face_of = {}
    for fi, p in enumerate(polys):
        for v in p: face_of.setdefault(v, []).append(fi)
    Fn = face_normals(Vn.astype(np.float64), polys)
    for name, rows, C, kind in digits:
        R_ = [np.array([Lp(v) for v in r]) for r in rows]; pole = Lp(C)
        j0 = len(R_) - n_cap - 1                        # cap-start ring (last shaft ring)
        c0 = R_[j0].mean(0); cprev = R_[j0 - 2].mean(0)
        ax = c0 - cprev; ax /= np.linalg.norm(ax)
        L = float((pole - c0) @ ax)
        ring = R_[j0]
        # lateral / normal half extents of the cap-start ring in the plane perpendicular to the axis
        lat = np.cross(ax, np.array([0.0, 1.0, 0.0])); lat /= np.linalg.norm(lat)      # a'-like direction
        nrm = np.cross(lat, ax); nrm /= np.linalg.norm(nrm)
        pa = (ring - c0) @ lat; pn = (ring - c0) @ nrm
        r_lat = 0.5 * (pa.max() - pa.min()); r_n = 0.5 * (pn.max() - pn.min())
        r_mean = 0.5 * (r_lat + r_n)
        # contour turning in plan (lat-axis plane) and side (nrm-axis plane): per cap ring take extreme verts, walk the contour through the pole
        def contour(vec):
            left = []; right = []
            for r in R_[j0 - 1:]:
                s = (r - c0) @ vec; left.append(r[np.argmin(s)]); right.append(r[np.argmax(s)])
            pts = left + [pole] + right[::-1]
            return np.array([[(q - c0) @ vec, (q - c0) @ ax] for q in pts])
        turn_plan = polyline_turn(contour(lat)); turn_side = polyline_turn(contour(nrm))
        # flat-cap fraction: area fraction of tip-zone faces (within 0.9 r_mean of the pole along the axis) whose normal is within 30 deg of the axis
        ids = set(mp[v] for r in rows[j0 - 1:] for v in r) | {mp[C]}
        fa = set(f for v in ids for f in face_of.get(v, []))
        area_all = 0.0; area_flat = 0.0
        for f in fa:
            pv = Vn[list(polys[f])].astype(float); cen = to_local(pv.mean(0)[None], side)[0]
            if (pole - cen) @ ax > 0.9 * r_mean: continue
            a = 0.0
            for q in range(1, len(pv) - 1): a += 0.5 * np.linalg.norm(np.cross(pv[q] - pv[0], pv[q + 1] - pv[0]))
            nl = to_local(Vn[list(polys[f])[0]][None] + Fn[f][None] * 1e-3, side)[0] - to_local(Vn[list(polys[f])[0]][None], side)[0]
            area_all += a
            if nl @ ax > np.cos(np.radians(30)): area_flat += a
        out[name] = dict(cap_rows=n_cap, cap_len_mm=L * 1000, r_lat_mm=r_lat * 1000, r_n_mm=r_n * 1000, hemisphere_ratio=float(L / r_mean),
                         plan_ratio=float(L / r_lat), side_ratio=float(L / r_n),
                         max_turn_plan_deg=float(turn_plan.max()), max_turn_side_deg=float(turn_side.max()), mean_turn_deg=float(0.5 * (turn_plan.mean() + turn_side.mean())),
                         flat_cap_fraction=float(area_flat / max(area_all, 1e-12)))
    return out

def palm_metrics(Vn, si, side):
    P = si[side]['info']['P']; info = si[side]['info']; Lp = loc(Vn, si, side); m = si[side]['mapping']
    rows = []
    for r, ids in sorted(info['ring'].items()):
        pts = np.array([Lp(v) for v in ids if v in m]); rows.append((pts[:, 2].mean(), pts[:, 0].max() - pts[:, 0].min(), pts[:, 1].max() - pts[:, 1].min()))
    rows = np.array(rows)
    w_wrist = -0.044; w_web = rows[-1, 0]
    length = (w_web - w_wrist) * 1000
    # planform area of the palm between the wrist line and the web line (trapezoid over the rows)
    ww = rows[:, 0]; wid = rows[:, 1]
    msk = ww >= w_wrist - 1e-4
    area = float(np.trapezoid(wid[msk], ww[msk])) * 1e6
    mid = float(np.interp(w_wrist + 0.5 * (w_web - w_wrist), ww, wid)) * 1000
    # mid-palm thickness at a'=0 (palmar - dorsal) at 50% of the palm length
    fing_len = []
    for k, (rws, C) in info['fin_rows'].items(): fing_len.append((Lp(C)[2] - w_web) * 1000)
    return dict(palm_length_mm=length, palm_breadth_web_mm=float(wid[-1] * 1000), palm_breadth_mid_mm=mid, palm_breadth_wrist_row_mm=float(wid[0] * 1000),
                palm_planform_area_mm2=area, finger_len_from_web_mm=fing_len, palm_over_middle_finger=float(length / fing_len[1]),
                web_line_w_mm=float(w_web * 1000))

def extra(Vn, polys, si, side, params):
    info = si[side]['info']; P = info['P']; Lp = loc(Vn, si, side); m = si[side]['mapping']; N0 = asm3.N0
    out = {}
    # ---- thenar mound: vertex-wise distance to the same palm without thenar / hypothenar bumps
    P2 = dict(params); P2['thenar'] = 0.0; P2['hypo'] = 0.0
    ring = np.load(W / f'data/ring_{side}.npy'); L = to_local(asm3.V0, side)
    B2, info2 = hand4.build_hand(ring.tolist(), L[ring], N0, P2)
    best = (0.0, None)
    for r, ids in info['ring'].items():
        if r < 3 or r > len(info['ring']) - 2: continue
        for i, v in enumerate(ids):
            if v not in m: continue
            d = np.linalg.norm(Lp(v) - B2.pos[info2['ring'][r][i] - N0]) * 1000
            if d > best[0]: best = (d, (r, i))
    out['T1_thenar_mound_mm'] = float(best[0]); out['T1_at'] = best[1]
    # ---- thumb root dihedral within 25 mm of the loop centroid
    nnew = sum(len(si[s]['faces']) for s in (+1, -1)); idx0 = len(polys) - nnew
    C = to_global(np.array([info['C_loop']]), side)[0]
    Fn = face_normals(Vn.astype(np.float64), polys); ef = edge_faces(polys); mx = 0.0; n60 = 0; n45 = 0; ne = 0
    for (a, b), fs in ef.items():
        if len(fs) == 2 and fs[0] >= idx0 and fs[1] >= idx0 and np.linalg.norm(0.5 * (Vn[a] + Vn[b]) - C) < 0.025:
            ang = np.degrees(np.arccos(np.clip((Fn[fs[0]] * Fn[fs[1]]).sum(), -1, 1))); mx = max(mx, ang); ne += 1; n60 += int(ang > 60); n45 += int(ang > 45)
    out['T5_dihedral'] = dict(edges=ne, max=float(mx), gt60=n60, gt45=n45)
    # ---- thumb radius increases (IP bump)
    from metrics3 import thumb_metrics
    rad = thumb_metrics(Vn, si, side)['radii_mm']; n_cap = len(P['cap_angles'])
    sh = rad[:len(rad) - n_cap]
    out['thumb_radius_increases'] = [[j, float(sh[j + 1] - sh[j])] for j in range(1, len(sh) - 1) if sh[j + 1] - sh[j] > 0.2]
    # ---- finger width runs
    cvs = []
    for k, (rows, Cp) in info['fin_rows'].items():
        Rr = [np.array([Lp(v) for v in r]) for r in rows]; wd = np.array([abs(r[0][0] - r[5][0]) for r in Rr])[:len(Rr) - n_cap]
        dw = np.abs(np.diff(wd)) * 1000; run = best_run = 0
        for x in dw:
            run = run + 1 if x < 0.15 else 0; best_run = max(best_run, run)
        cvs.append(dict(finger=k, cv=float(wd.std() / wd.mean()), rows=len(wd), longest_equal_width_run_rows=best_run, run_frac=float(best_run / len(wd))))
    out['finger_width_cv'] = cvs
    return out

def all_metrics(params):
    out, Vn, polys, si = run_metrics.run(params, None, save_cand=False)
    out['tips'] = {}; out['palm'] = {}; out['extra'] = {}
    for side, nm in ((+1, 'R'), (-1, 'L')):
        out['tips'][nm] = tip_metrics(Vn, polys, si, side, params)
        out['palm'][nm] = palm_metrics(Vn, si, side)
        out['extra'][nm] = extra(Vn, polys, si, side, params)
    # face quality of the new faces
    nnew = sum(len(si[s]['faces']) for s in (+1, -1)); newp = polys[len(polys) - nnew:]
    areas = []; aspects = []; ntri = 0
    for p in newp:
        pv = Vn[list(p)].astype(float)
        if len(p) == 3: ntri += 1
        a = 0.0
        for q in range(1, len(pv) - 1): a += 0.5 * np.linalg.norm(np.cross(pv[q] - pv[0], pv[q + 1] - pv[0]))
        areas.append(a * 1e6)
        e = np.linalg.norm(np.roll(pv, -1, 0) - pv, axis=1); aspects.append(e.max() / max(e.min(), 1e-9))
    out['facequal'] = dict(new_faces=len(newp), new_tris=ntri, min_area_mm2=float(min(areas)), max_edge_aspect=float(max(aspects)), aspect_gt10=int(sum(a > 10 for a in aspects)), area_lt_0p3mm2=int(sum(a < 0.3 for a in areas)))
    return out, Vn, polys, si

if __name__ == '__main__':
    tag = sys.argv[1]; params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    out, Vn, polys, si = all_metrics(params)
    json.dump(out, open(sys.argv[3] if len(sys.argv) > 3 else str(W / f'data/allmetrics_{tag}.json'), 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    for nm in ('R',):
        print('PALM', nm, json.dumps({k: (round(v, 2) if isinstance(v, float) else v) for k, v in out['palm'][nm].items()}))
        for d, t in out['tips'][nm].items(): print('TIP ', d, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in t.items()})
        print('EXTRA', {k: v for k, v in out['extra'][nm].items() if k != 'finger_width_cv'})
    print('FACEQ', out['facequal'])
