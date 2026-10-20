"""Gate metrics for the female hands (numbers defined BEFORE measuring; thresholds in GATES).  All lengths in metres inside, reported in mm.
python metrics_f.py <flat params json> [out.json]
Computed from the assembled candidate (asm_f.assemble) + builder roles; independent geometric audits (zone, intersections) live in audit_f.py."""
import sys, json
from pathlib import Path
import numpy as np
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import fit_f, asm_f, fhand, sil_f
from femlib import *

GATES = dict(
    taper_tip_base_max=0.70, taper_tip_base_target=0.65, taper_mid_base_max=0.90, equal_run_max_frac=0.35, depth_width_base_max=1.40,
    bump_pip_min_mm=0.45, bump_dip_min_mm=0.25, cap_rows_min=6, gap_min_mm=1.5, curl_tip_min_deg=20.0,
    thenar_mound_min_mm=3.0, ip_bump_min_mm=0.40, web_dihedral_max_deg=75.0, ip_bend_min_deg=8.0, thumb_tip_ratio_max=0.65, thumb_len_diam_max=5.0, thumb_min_radius_mm=6.0,
    place_tip_y_mm=10.0, place_band_mm=10.0, weld_dihedral_max_deg=40.0, mirror_distal_max_mm=0.10, male_ratio_width_max=0.70,
)


def _ring_geom(V, ids, LC):
    """width (|WL-WR|), depth (dorsal-mid to palmar-mid), centre, half-depths for one finger ring (ids in [WL, D1..D_{LC-1}, WR, P_{LC-1}..P1] order)"""
    P = V[ids]; NV = 2 * LC
    WL, WR = P[0], P[LC]
    dm = [LC // 2] if LC % 2 == 0 else [LC // 2, LC // 2 + 1]
    D = P[dm].mean(0); Pm = P[[(NV - j) % NV for j in dm]].mean(0)
    c = 0.5 * (WL + WR)
    return dict(width=np.linalg.norm(WL - WR), depth=np.linalg.norm(D - Pm), centre=c, hd=np.linalg.norm(D - c), hp=np.linalg.norm(Pm - c), mean_r=np.linalg.norm(P - P.mean(0), axis=1).mean())


def finger_metrics(Vn, s, P):
    out = {}
    info = s['info']; mp = s['mapping']; LC = P['m'] + 1
    G = lambda ids: Vn[[mp[i] for i in ids]]
    for k in range(4):
        rows, C = info['fin_rows'][k]
        sv, nsh, Larc, s_cap = info['fin_s'][k]
        geo = [_ring_geom(Vn, [mp[i] for i in row], LC) for row in rows]
        w = np.array([g['width'] for g in geo]); d = np.array([g['depth'] for g in geo]); sarr = np.array(sv)
        base, tip = w[0], w[nsh - 1]
        mid_i = int(np.argmin(np.abs(sarr[:nsh] - 0.5))); mid = w[mid_i]
        # monotone width profile (bumps <= 0.35 mm allowed)
        mono = bool(np.all(np.diff(w[:nsh]) <= 0.00035))
        run = 1; best = 1
        for i in range(1, nsh):
            if abs(w[i] - w[i - 1]) <= 0.03 * base: run += 1; best = max(best, run)
            else: run = 1
        # joint bumps: dorsal half depth excess over the chord between rows 0.14 before and after the joint
        hd = np.array([g['hd'] for g in geo])
        def bump(sj):
            i_a = int(np.argmin(np.abs(sarr[:nsh] - (sj - 0.16)))); i_b = int(np.argmin(np.abs(sarr[:nsh] - (sj + 0.16)))); i_j = int(np.argmin(np.abs(sarr[:nsh] - sj)))
            t = (sarr[i_j] - sarr[i_a]) / max(sarr[i_b] - sarr[i_a], 1e-9)
            return float(hd[i_j] - (hd[i_a] * (1 - t) + hd[i_b] * t))
        # cap rows: strictly decreasing mean ring radius after the last shaft ring
        rad = np.array([g['mean_r'] for g in geo[nsh - 1:]])
        capdec = bool(np.all(np.diff(rad) < 0)); ncap = len(rows) - nsh
        # curl: turning angle of the ring-centre polyline between the first and the last shaft segment
        cen = np.array([g['centre'] for g in geo])
        t0 = cen[2] - cen[0]; t1 = cen[nsh - 1] - cen[nsh - 3]
        curl = float(np.degrees(np.arccos(np.clip(np.dot(t0, t1) / np.linalg.norm(t0) / np.linalg.norm(t1), -1, 1))))
        out[k] = dict(width_base_mm=base * 1000, width_mid_mm=mid * 1000, width_tip_mm=tip * 1000, tip_base=tip / base, mid_base=mid / base, monotone=mono, equal_run_frac=best / nsh,
                      depth_width_base=float(d[0] / w[0]), bump_pip_mm=bump(P['s_pip']) * 1000, bump_dip_mm=bump(P['s_dip']) * 1000, cap_rows=ncap, cap_strictly_decreasing=capdec,
                      curl_deg=curl, length_mm=float(np.linalg.norm(Vn[mp[C]] - cen[0]) * 1000), centres=cen, widths=w, s=sarr)
    # gaps between adjacent fingers at s=0.4/0.7: distance of ring centres minus half widths
    gaps = []
    for k in range(3):
        for sj in (0.4, 0.7):
            ia = int(np.argmin(np.abs(out[k]['s'][:len(out[k]['widths'])] - sj))); ib = int(np.argmin(np.abs(out[k + 1]['s'][:len(out[k + 1]['widths'])] - sj)))
            ca = out[k]['centres'][ia]; cb = out[k + 1]['centres'][ib]
            gaps.append(float(np.linalg.norm(ca - cb) - 0.5 * (out[k]['widths'][ia] + out[k + 1]['widths'][ib])) * 1000)
    return out, gaps


def thumb_metrics(Vn, polys, s, P):
    info = s['info']; mp = s['mapping']
    rows = info['thumb_rows']
    cen = np.array([Vn[[mp[v] for v in row]].mean(0) for row in rows])
    rad = np.array([np.linalg.norm(Vn[[mp[v] for v in row]] - c, axis=1).mean() for row, c in zip(rows, cen)])
    n_cap = P['n_cap']; nsh = len(rows) - n_cap
    # IP bend: angle between the proximal chord and the distal chord of the shaft
    ush0 = np.linspace(0, 1, nsh)
    at0 = lambda u: int(np.argmin(np.abs(ush0 - u)))
    a = cen[at0(0.55)] - cen[at0(0.30)]; b = cen[at0(1.0)] - cen[at0(0.70)]       # proximal-phalanx chord vs distal-phalanx chord across the IP joint
    bend = float(np.degrees(np.arccos(np.clip(np.dot(a, b) / np.linalg.norm(a) / np.linalg.norm(b), -1, 1))))
    # IP bump in the radius profile near u = 0.64: excess over the chord between u-0.14 and u+0.14
    ush = np.linspace(0, 1, nsh)
    def at(u): return int(np.argmin(np.abs(ush - u)))
    ia, ib, ij = at(0.64 - 0.2), at(0.64 + 0.2), at(0.64)
    t = (ush[ij] - ush[ia]) / (ush[ib] - ush[ia])
    ip_bump = float(rad[ij] - (rad[ia] * (1 - t) + rad[ib] * t))
    capdec = bool(np.all(np.diff(rad[nsh - 1:]) < 0))
    tip_ratio = float(rad[nsh - 1] / rad[1])
    length = float(np.linalg.norm(Vn[mp[info['thumb_tip']]] - cen[0]))
    mean_diam = float(2 * rad[2:nsh].mean())
    # web crotch: max dihedral of edges within 25 mm of the root loop centroid
    loop = [mp[v] for v in info['thumb_loop']]; c0 = Vn[loop].mean(0)
    ef = edge_faces(polys)
    FN = face_normals(Vn, polys)
    dih = []
    for e, fl in ef.items():
        if len(fl) == 2:
            m = 0.5 * (Vn[e[0]] + Vn[e[1]])
            if np.linalg.norm(m - c0) < 0.025:
                dih.append(np.degrees(np.arccos(np.clip(np.dot(FN[fl[0]], FN[fl[1]]), -1, 1))))
    dih = np.array(dih)
    return dict(ip_bend_deg=bend, ip_bump_mm=ip_bump * 1000, cap_rows=n_cap, cap_strictly_decreasing=capdec, tip_ratio=tip_ratio, length_mm=length * 1000, mean_diam_mm=mean_diam * 1000,
                length_over_diam=length / mean_diam, min_shaft_radius_mm=float(rad[2:nsh].min() * 1000), max_dihedral_root_deg=float(dih.max()), n_edges_gt60=int((dih > 60).sum()),
                radii_mm=(rad * 1000).round(2).tolist())


def thenar_mound(par, pose, s_idx=+1):
    """height of the thenar/hypothenar mound = max displacement of the palm vertices between the hand with and without the thenar terms"""
    Va, pa, sa, _ = asm_f.assemble(par, pose, verbose=False)
    par0 = dict(par); par0['thenar'] = 0.0; par0['hypo'] = 0.0
    Vb, pb, sb, _ = asm_f.assemble(par0, pose, verbose=False)
    info = sa[s_idx]['info']; mp = sa[s_idx]['mapping']
    ids = [mp[v] for r, row in info['ring'].items() if r >= 2 for v in row if v in mp]
    ids = [i for i in ids if i in range(len(Va))]
    d = np.linalg.norm(Va[ids] - Vb[ids], axis=1)
    return float(d.max() * 1000)


def compute(x, extra_par=None):
    par, pose = fit_f.split({**fit_f.DEFAULT, **x})
    if extra_par: par.update(extra_par)
    Vn, polys, si, removed = asm_f.assemble(par, pose, verbose=False)
    Pfull = dict(fhand.P0); Pfull.update(par)
    res = {'tris': tri_count(polys), 'verts': len(Vn)}
    for side in (+1, -1):
        fm, gaps = finger_metrics(Vn, si[side], Pfull)
        tm = thumb_metrics(Vn, polys, si[side], Pfull)
        res['R' if side > 0 else 'L'] = dict(fingers={k: {kk: (vv.tolist() if isinstance(vv, np.ndarray) else vv) for kk, vv in v.items()} for k, v in fm.items()}, gaps_mm=gaps, thumb=tm)
    res['thenar_mound_mm'] = thenar_mound(par, pose)
    return res, (Vn, polys, si)


def check(res):
    g = GATES; out = []
    def add(name, ok, ev): out.append((name, bool(ok), ev))
    for side in ('R', 'L'):
        F = res[side]['fingers']
        tb = [F[k]['tip_base'] for k in F]; mb = [F[k]['mid_base'] for k in F]
        add(f'FINGER_TAPER {side}: tip/base <= {g["taper_tip_base_max"]}', max(tb) <= g['taper_tip_base_max'], f'max {max(tb):.3f} (all {[round(v, 3) for v in tb]})')
        add(f'FINGER_TAPER {side}: mid/base <= {g["taper_mid_base_max"]}', max(mb) <= g['taper_mid_base_max'], f'max {max(mb):.3f}')
        add(f'FINGER_TAPER {side}: width profile monotone', all(F[k]['monotone'] for k in F), 'bumps <= 0.35 mm tolerated')
        add(f'FINGER_TAPER {side}: longest equal-width run <= {g["equal_run_max_frac"]}', max(F[k]['equal_run_frac'] for k in F) <= g['equal_run_max_frac'], f'max {max(F[k]["equal_run_frac"] for k in F):.2f}')
        add(f'FINGER_TAPER {side}: depth/width at base <= {g["depth_width_base_max"]}', max(F[k]['depth_width_base'] for k in F) <= g['depth_width_base_max'], f'max {max(F[k]["depth_width_base"] for k in F):.2f}')
        add(f'FINGER_TAPER {side}: PIP bump >= {g["bump_pip_min_mm"]} mm / DIP >= {g["bump_dip_min_mm"]} mm', min(F[k]['bump_pip_mm'] for k in F) >= g['bump_pip_min_mm'] and min(F[k]['bump_dip_mm'] for k in F) >= g['bump_dip_min_mm'],
            f'PIP {[round(F[k]["bump_pip_mm"], 2) for k in F]} DIP {[round(F[k]["bump_dip_mm"], 2) for k in F]}')
        add(f'FINGER_TAPER {side}: pad tips >= {g["cap_rows_min"]} rounded cap rows, radii strictly decreasing', min(F[k]['cap_rows'] for k in F) >= g['cap_rows_min'] and all(F[k]['cap_strictly_decreasing'] for k in F), f'cap rows {[F[k]["cap_rows"] for k in F]}')
        add(f'FINGER_TAPER {side}: finger gaps >= {g["gap_min_mm"]} mm at 40/70 %', min(res[side]['gaps_mm']) >= g['gap_min_mm'], f'min {min(res[side]["gaps_mm"]):.2f} mm')
        add(f'FINGER_TAPER {side}: relaxed curl >= {g["curl_tip_min_deg"]} deg', min(F[k]['curl_deg'] for k in F) >= g['curl_tip_min_deg'], f'{[round(F[k]["curl_deg"], 1) for k in F]}')
        T = res[side]['thumb']
        add(f'THUMB_ANATOMY {side}: IP bend >= {g["ip_bend_min_deg"]} deg', T['ip_bend_deg'] >= g['ip_bend_min_deg'], f'{T["ip_bend_deg"]:.1f} deg')
        add(f'THUMB_ANATOMY {side}: IP knuckle bump >= {g["ip_bump_min_mm"]} mm (real phalanges)', T['ip_bump_mm'] >= g['ip_bump_min_mm'], f'{T["ip_bump_mm"]:.2f} mm')
        add(f'THUMB_ANATOMY {side}: pad tip (ratio <= {g["thumb_tip_ratio_max"]}, {T["cap_rows"]} cap rows decreasing)', T['tip_ratio'] <= g['thumb_tip_ratio_max'] and T['cap_strictly_decreasing'], f'ratio {T["tip_ratio"]:.2f}')
        add(f'THUMB_ANATOMY {side}: not a pill / not a spike (L/D <= {g["thumb_len_diam_max"]}, min r >= {g["thumb_min_radius_mm"]} mm)', T['length_over_diam'] <= g['thumb_len_diam_max'] and T['min_shaft_radius_mm'] >= g['thumb_min_radius_mm'], f'L/D {T["length_over_diam"]:.2f}, min r {T["min_shaft_radius_mm"]:.1f} mm')
        add(f'THUMB_ANATOMY {side}: web fillet (max dihedral <= {g["web_dihedral_max_deg"]} deg)', T['max_dihedral_root_deg'] <= g['web_dihedral_max_deg'], f'{T["max_dihedral_root_deg"]:.1f} deg, {T["n_edges_gt60"]} edges > 60')
    add(f'THUMB_ANATOMY: thenar mound >= {g["thenar_mound_min_mm"]} mm', res['thenar_mound_mm'] >= g['thenar_mound_min_mm'], f'{res["thenar_mound_mm"]:.2f} mm')
    return out


if __name__ == '__main__':
    x = json.load(open(sys.argv[1]))['params'] if sys.argv[1].endswith('.json') else json.loads(sys.argv[1])
    res, _ = compute(x)
    for name, ok, ev in check(res): print(('PASS ' if ok else 'FAIL ') + name + ' | ' + ev)
    if len(sys.argv) > 2: json.dump(res, open(sys.argv[2], 'w'), indent=1, default=float)
