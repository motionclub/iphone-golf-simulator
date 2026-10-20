"""Batch evaluator for FORM3 candidates (data/V_<tag>.npy).  python3 evalv.py [--json out.json] tag1 tag2 ...
Per tag: dihedral stats, silhouette gate (front/back), see-through slot (apex, widths), rear contour error vs the plate, FRONT forward protrusion vs the start,
roof hang at the rear lip, lip U-ness, torso band-pass non-regression (form3gate regions) + glute band-pass.   Blender renders run in parallel (10 cpus)."""
import sys, os, json, subprocess, numpy as np
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, '.')
import quality as Q, common
from common import V0, front_curve, rear_curve, section_x
import f3_model as M
B = '/Applications/Blender.app/Contents/MacOS/Blender'
ENV = dict(os.environ, PYTHONPATH='../male-micro1i/pylib')
def sh(cmd): return subprocess.run(cmd, shell=True, env=ENV, capture_output=True, text=True)

def renders(tag):
    jobs = [f'./sil_f2.sh {tag}', f'./rv.sh {tag} sil4_{tag} "front@4,back@4" sil']
    for j in jobs: sh(j)
    import metric as MT; MT.render(tag)
    return tag

def roof_z(V, x, ys):
    """lower surface height of the tunnel roof at the column x (z of the lowest section point above z=0.72 near each y)"""
    S = section_x(V, x); out = np.full(len(ys), np.nan)
    for i, y in enumerate(ys):
        best = 9.0
        for (p, q) in S:
            if min(p[0], q[0]) - 0.002 <= y <= max(p[0], q[0]) + 0.002:
                for z in (p[1], q[1]):
                    if 0.72 < z < 0.80: best = min(best, z)
        out[i] = best if best < 9 else np.nan
    return out

def evaluate(tag, V=None):
    V = (V0 if tag == 'start' else np.load(f'data/V_{tag}.npy')) if V is None else V; r = {}
    q = Q.stats(V); d = np.linalg.norm(V - V0, axis=1) * 1000; dd = Q.dihedral(V)
    r['dihedral'] = dict(p99=round(q['p99'], 1), max=round(q['max'], 1), new_sharp=q['new_sharp'])
    r['moved'] = int((d > 1e-4).sum()); r['max_move_mm'] = round(float(d.max()), 1)
    # silhouette
    try:
        s = json.load(open(f'data/sil_{tag}.json')); r['sil_front'] = round(s['bald_front']['pct'], 3); r['sil_back'] = round(s['bald_back']['pct'], 3)
    except Exception: r['sil_front'] = r['sil_back'] = None
    # slot
    try:
        import slotw; m = slotw.measure(tag)
        r['slot'] = dict(apex_front=round(m['front']['apex_z'], 4), apex_back=round(m['back']['apex_z'], 4), w_front=[m['front']['widths_mm'][k] for k in ('0.720', '0.735', '0.745')], w_back=[m['back']['widths_mm'][k] for k in ('0.720', '0.735', '0.745')])
    except Exception as e: r['slot'] = str(e)
    # rear contour vs plate
    pl = json.load(open('data/plate_rear_subpx.json')); z = np.array(pl['z']); L = np.array([np.nan if v is None else v for v in pl['left']], float); R = np.array([np.nan if v is None else v for v in pl['right']], float)
    zs = np.arange(0.77, 0.951, 0.01); mc, _ = M.rear_max_columns(V, zs); pr = np.array([np.nanmean([L[np.argmin(abs(z - zz))], R[np.argmin(abs(z - zz))]]) for zz in zs])
    e = (mc - pr) * 1000; r['contour_mm'] = dict(mean_abs=round(float(np.nanmean(np.abs(e))), 2), max_abs=round(float(np.nanmax(np.abs(e))), 2), belly_signed=round(float(np.nanmean(e[(zs >= .82) & (zs <= .86)])), 1))
    # front protrusion vs start (most negative = most forward)
    zf = np.arange(0.79, 0.901, 0.01); worst = 0.0; where = None
    for u in (0.004, 0.012, 0.02, 0.03, 0.04, 0.05):
        for sgn in (1, -1):
            a = front_curve(V, sgn * u + 1e-6 * sgn, zf); b = front_curve(V0, sgn * u + 1e-6 * sgn, zf); dlt = (a - b) * 1000
            if np.isfinite(dlt).any():
                i = int(np.nanargmin(dlt))
                if dlt[i] < worst: worst, where = float(dlt[i]), (u, round(float(zf[i]), 3))
    r['front_forward_mm'] = dict(worst=round(worst, 1), at=where)
    # roof hang: lowest roof point vs roof at the rear lip (y .055) and at the front lip (y -.16), centre column
    ys = np.array([-0.16, -0.12, -0.08, -0.04, 0.0, 0.03, 0.05, 0.057]); rz = roof_z(V, 0.0039, ys)
    r['roof_mm'] = {f'{y:+.2f}': (None if not np.isfinite(v) else round(v * 1000, 1)) for y, v in zip(ys, rz)}
    if np.isfinite(rz).all():
        r['rear_lip_above_roof_min_mm'] = round(float(rz[-1] - np.nanmin(rz)) * 1000, 1); r['front_lip_above_roof_min_mm'] = round(float(rz[0] - np.nanmin(rz)) * 1000, 1)
    # torso gate + glute band-pass
    try:
        import form3gate as G, metric as MT
        g = G.run(tag); r['torso_gate'] = g
        sc = MT.score(tag); r['glute_bp'] = {k: round(v, 3) for k, v in sc.items() if not k.endswith('_sr')}
    except Exception as ex: r['torso_gate'] = str(ex)
    return r

if __name__ == '__main__':
    a = sys.argv[1:]; outj = None
    if a and a[0] == '--json': outj = a[1]; a = a[2:]
    with ThreadPoolExecutor(8) as ex: list(ex.map(renders, a))
    res = {}
    for t in a:
        res[t] = evaluate(t); r = res[t]
        sl = r['slot']; tg = r['torso_gate']
        print(f"{t:8s} dih p99 {r['dihedral']['p99']:5.1f} max {r['dihedral']['max']:5.1f} | SIL {r['sil_front']}/{r['sil_back']} | apex {sl['apex_back'] if isinstance(sl, dict) else sl} w_b {sl['w_back'] if isinstance(sl, dict) else ''} | contour {r['contour_mm']['mean_abs']}/{r['contour_mm']['max_abs']} belly {r['contour_mm']['belly_signed']:+} | frontfwd {r['front_forward_mm']['worst']} | lip>roofmin rear {r.get('rear_lip_above_roof_min_mm')} front {r.get('front_lip_above_roof_min_mm')} | torso mean {tg.get('mean') if isinstance(tg, dict) else tg} back_pelvis {tg.get('back_pelvis') if isinstance(tg, dict) else ''} front_pelvis {tg.get('front_pelvis') if isinstance(tg, dict) else ''}")
    if outj: json.dump(res, open(outj, 'w'), indent=1, default=str)
